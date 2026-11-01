#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""在云端 JupyterLab 容器里执行 shell 命令。

核心约束（实测踩坑）
----------------------
`Runtime.evaluate` 每次调用都是**独立上下文**，`window.__xxx` 变量不跨调用保留。
因此「建 WebSocket → 发 execute_request → 收输出」必须**在同一个 JS 表达式内完成**，
用 Promise 等待结果。

为什么不用其它方式
------------------
- `POST /api/kernels/<id>/execute` → 该部署返回 404（被禁用）
- UI 点 Run 按钮 / 合成键盘事件 / 菜单点击 → 均不可靠（CodeMirror 6 与 JupyterLab 事件体系特殊）
- **内核 WebSocket 通道** → 稳定可用，且能拿到真实 stdout/stderr/退出码

用法: python cloud_shell.py "<命令>"
      python cloud_shell.py --file <命令文件> [超时秒]
"""
import json, subprocess, sys, os, time

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)                    # F:\openi\tools
DAEMON = os.path.join(TOOLS, 'web', 'cdp_daemon.py')
MATCH = 'mlunotebook'

# 一次性完成一切的单表达式 JS
JS_TEMPLATE = r"""(async () => {
  const CMD = %s;
  const TIMEOUT = %d;
  const base = location.origin + location.pathname.replace(/\/lab.*$/, '');
  const out = [];
  try {
    const kr = await fetch(base + '/api/kernels', { credentials: 'include' });
    const list = await kr.json();
    if (!list || !list.length) return 'NO_KERNEL';
    const kid = list[0].id;
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = proto + '//' + location.host + base.replace(/^https?:\/\/[^/]+/, '') + '/api/kernels/' + kid + '/channels';
    const py = 'import subprocess, sys\n' +
               'cmd = ' + JSON.stringify(CMD) + '\n' +
               'try:\n' +
               '    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=' + TIMEOUT + ')\n' +
               '    print(r.stdout)\n' +
               '    if r.stderr:\n' +
               "        print('=== STDERR ===')\n" +
               '        print(r.stderr)\n' +
               "    print('=== EXIT ' + str(r.returncode) + ' ===')\n" +
               'except subprocess.TimeoutExpired:\n' +
               "    print('=== TIMEOUT ===')\n";

    const res = await new Promise((resolve) => {
      let done = false;
      const finish = (v) => { if (!done) { done = true; resolve(v); } };
      let ws;
      try { ws = new WebSocket(wsUrl); }
      catch (e) { finish('WS_CTOR:' + e.message); return; }
      const timer = setTimeout(() => finish('TIMEOUT'), TIMEOUT * 1000 + 30000);
      ws.onopen = () => {
        ws.send(JSON.stringify({
          header: { msg_id: 'K' + Date.now(), msg_type: 'execute_request',
                    username: 'user', session: 'cloud' },
          parent_header: {}, metadata: {},
          content: { code: py, silent: false, store_history: false,
                     user_expressions: {}, allow_stdin: false, stop_on_error: false }
        }));
      };
      ws.onmessage = (ev) => {
        try {
          const m = JSON.parse(ev.data);
          const mt = m.header && m.header.msg_type;
          const c = m.content || {};
          if (mt === 'stream') out.push(c.text || '');
          else if (mt === 'error') out.push('[ERROR] ' + (c.ename || '') + ': ' + (c.evalue || ''));
          else if (mt === 'execute_result' || mt === 'display_data') {
            out.push((c.text || '') || (c.data && (c.data['text/plain'] || '')) || '');
          } else if (mt === 'execute_reply') {
            clearTimeout(timer);
            try { ws.close(); } catch (e) {}
            finish('OK');
          }
        } catch (e) { out.push('PARSE_ERR ' + e.message); }
      };
      ws.onerror = () => { clearTimeout(timer); finish('WS_ERROR'); };
      ws.onclose = (e) => { clearTimeout(timer); finish('WS_CLOSED:' + e.code); };
    });
    return res + '\n' + out.join('');
  } catch (e) {
    return 'EXC:' + e.message + '\n' + out.join('');
  }
})()"""


def send(req, timeout=200):
    """发给守护进程。

    必须走 stdin 传 JSON —— JS 表达式里含引号/反斜杠，
    作为命令行参数会被 Windows 的 cmd 解析层破坏。
    """
    payload = json.dumps(req, ensure_ascii=False)
    out = subprocess.run([sys.executable, DAEMON, '--client', '-'],
                         input=payload, capture_output=True, text=True, timeout=timeout)
    try:
        return json.loads(out.stdout.strip())
    except Exception:
        return {'ok': False, 'error': (out.stdout + out.stderr)[:400]}


def run_shell(cmd, timeout=300):
    js = JS_TEMPLATE % (json.dumps(cmd), timeout)
    r = send({'cmd': 'eval', 'expr': js, 'match': MATCH}, timeout=timeout + 90)
    if not r.get('ok'):
        return {'error': r.get('error')}
    v = r.get('result')
    if v is None:
        return {'error': 'eval 返回 None（可能被 CSP 或上下文限制）'}
    return {'ok': True, 'output': v}


def run_python(py_code, timeout=300):
    """在云端执行一段 Python 代码（不经 shell，避免引号地狱）。

    原理：代码 base64 化 → 经内核 WebSocket 传到云端 →
          云端写临时 .py 文件 → 用 python 文件执行 → 回传 stdout。

    相比 run_shell 的优势：cmd 里的引号不会被 /bin/sh 二次解析。
    """
    import base64 as _b64, json as _json
    b64 = _b64.b64encode(py_code.encode('utf-8')).decode()
    py_lines = [
        'import base64, os, sys, subprocess',
        'd = base64.b64decode("' + b64 + '").decode("utf-8")',
        'p = "/tmp/code/_exec.py"',
        'open(p, "w", encoding="utf-8").write(d)',
        'r = subprocess.run([sys.executable, p], capture_output=True, text=True, timeout=' + str(timeout) + ')',
        'print(r.stdout)',
        'if r.stderr: print("=== STDERR ==="); print(r.stderr)',
        'print("=== EXIT " + str(r.returncode) + " ===")',
    ]
    py_js = '[' + ', '.join(_json.dumps(x) for x in py_lines) + "].join('\\n');"

    js = """(async () => {
 try {
  const py = __PYJS__;
  const base = location.origin + location.pathname.replace(/\/lab.*$/, '');
  const kr = await fetch(base + '/api/kernels', {credentials:'include'});
  const klist = await kr.json();
  if (!klist || !klist.length) return JSON.stringify({error:'no kernel'});
  const kid = klist[0].id;
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = proto + '//' + location.host + base.replace(/^https?:\/\/[^/]+/, '') + '/api/kernels/' + kid + '/channels';
  const out = [];
  await new Promise((resolve) => {
    let done = false;
    const fin = v => { if (!done) { done = true; resolve(v); } };
    const ws = new WebSocket(wsUrl);
    const timer = setTimeout(() => fin('TIMEOUT'), __TIMEOUT__);
    ws.onopen = () => ws.send(JSON.stringify({
      header:{msg_id:'K'+Date.now(), msg_type:'execute_request', username:'u', session:'s'},
      parent_header:{}, metadata:{},
      content:{code: py, silent:false, store_history:false, user_expressions:{}, allow_stdin:false, stop_on_error:false}
    }));
    ws.onmessage = ev => {
      try {
        const mm = JSON.parse(ev.data);
        const mt = mm.header && mm.header.msg_type;
        if (mt === 'stream') out.push(mm.content.text || '');
        else if (mt === 'error') out.push('[ERR] ' + JSON.stringify(mm.content).slice(0,300));
        if (mt === 'execute_reply') { setTimeout(() => { clearTimeout(timer); fin('OK'); }, 700); }
      } catch (e) { out.push('PARSE ' + e.message); }
    };
    ws.onerror = () => { clearTimeout(timer); fin('WS_ERROR'); };
  });
  return JSON.stringify({out: out.join('')});
 } catch (e) {
  return JSON.stringify({error: 'JS_EXC: ' + e.message});
 }
})()"""
    js = js.replace('__PYJS__', py_js).replace('__TIMEOUT__', str((timeout + 120) * 1000))

    req = {'cmd': 'eval', 'expr': js, 'match': MATCH}
    r = send(req, timeout=timeout + 180)
    if not r.get('ok'):
        return {'error': r.get('error')}
    v = r.get('result')
    if isinstance(v, str):
        try:
            return json.loads(v)
        except Exception:
            return {'_raw': v}
    return v


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == '--file':
        cmd = open(sys.argv[2], encoding='utf-8').read().strip()
        timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 300
    else:
        cmd = sys.argv[1] if len(sys.argv) > 1 else 'pwd'
        timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 300
    res = run_shell(cmd, timeout)
    if 'error' in res:
        print('ERROR:', res['error'])
        sys.exit(1)
    print(res.get('output', ''))

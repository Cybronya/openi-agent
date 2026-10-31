#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""本地 → 云端 wheel 同步与安装。

流程
----
1. 对比本地 packages/ 与云端 packages/ 的文件清单（通过 JupyterLab REST API）
2. 找出云端缺失或版本落后的 wheel
3. 上传（base64 分块，走内核 WebSocket 通道）
4. 校验云端文件大小
5. 可选：执行安装并验证

用法
----
  python sync_wheels.py --dry-run          # 只看差异，不上传
  python sync_wheels.py --upload           # 上传缺失文件
  python sync_wheels.py --upload --install # 上传后执行安装
  python sync_wheels.py --batch comfyui    # 只处理某个批次
"""
import json, os, sys, subprocess, base64, hashlib, time

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)          # F:\openi\tools
WEB = os.path.join(TOOLS, 'web')       # F:\openi\tools\web
DEP_PROJECT = r'F:\Program Files\Git\C500-Comfyui-Package'

# 云端项目在 JupyterLab 里的路径
CLOUD_ROOT = 'C500-Comfyui-Package'

# 通过内核 WebSocket 执行一段 Python 代码，取回 stdout。
# 注意：Runtime.evaluate 上下文隔离，所以「建 WS → 发 → 收」必须在同一个表达式内完成。
KERNEL_RUN_TEMPLATE = """(async () => {
 try {
  const py = %s;
  const base = location.origin + location.pathname.replace(/\\\\/lab.*$/, '');
  const kr = await fetch(base + '/api/kernels', {credentials:'include'});
  const klist = await kr.json();
  if (!klist || !klist.length) return JSON.stringify({error:'no kernel'});
  const kid = klist[0].id;
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = proto + '//' + location.host + base.replace(/^https?:\\\\/\\\\/[^/]+/,'') + '/api/kernels/' + kid + '/channels';
  const out = [];
  await new Promise((resolve) => {
    let done = false;
    const fin = v => { if (!done) { done = true; resolve(v); } };
    const ws = new WebSocket(wsUrl);
    const timer = setTimeout(() => fin('TIMEOUT'), 300000);
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
  const txt = out.join('');
  const m = txt.match(/SIZE (-?\\d+)/);
  return JSON.stringify({size: m ? parseInt(m[1]) : null, out: txt.slice(0, 400)});
 } catch (e) {
  return JSON.stringify({error: 'JS_EXC: ' + e.message});
 }
})()"""


# 直接复用 jlab 的 run_js（避免子进程与临时文件的额外开销）
sys.path.insert(0, WEB)
from jlab import run_js as _run_js   # noqa: E402


def jlab(js_code, timeout=240):
    """执行 JS 并解析 JSON 结果。"""
    return _run_js(js_code, 'mlunotebook')


def cloud_list(path):
    """列出云端目录内容。"""
    js = f'''(async () => {{
  const base = location.origin + location.pathname.replace(/\\/lab.*$/, '');
  const r = await fetch(base + '/api/contents/' + {json.dumps(path)}, {{credentials:'include'}});
  const j = await r.json();
  if (!j.content) return JSON.stringify({{error: 'no content', status: r.status}});
  return JSON.stringify({{status: r.status, items: j.content.map(c => ({{
    name: c.name, type: c.type, size: c.size || 0
  }}))}});
}})()'''
    return jlab(js)


def cloud_stat(path):
    """查云端文件大小（走内核通道 stat，比 contents API 可靠）。"""
    py = '\n'.join([
        "import os",
        "p = " + repr(path),
        "print('SIZE', os.path.getsize(p) if os.path.exists(p) else -1)",
    ])
    r = _shell_run(os.path.join(HERE, 'cloud_shell.py'), py, 120)
    if not r.get('ok'):
        return {'size': None, 'error': r.get('error', '')[:120]}
    out = r.get('raw', '')
    for line in out.split('\n'):
        line = line.strip()
        if line.startswith('SIZE '):
            v = int(line[5:])
            return {'size': v if v >= 0 else None}
    return {'size': None, 'raw': out[:200]}


def cloud_upload(path, filename, local_file):
    """上传本地文件到云端。

    增量分块写：每次 eval 传一小块 base64 → 立即在云端 append 到文件。
    好处：
      - 单条消息小（64MB 文件不会超时）
      - 失败可断点续传（记录已传字节数）
      - 不依赖 REST PUT（它只接受 base64 JSON body）
    """
    import subprocess, base64 as _b64
    shell = os.path.join(HERE, 'cloud_shell.py')

    with open(local_file, 'rb') as f:
        data = f.read()
    total = len(data)
    b64 = _b64.b64encode(data).decode()

    CHUNK = 400_000            # 每块 400KB base64
    n_chunks = (len(b64) + CHUNK - 1) // CHUNK
    remote = f'/tmp/code/{path}/{filename}'

    # 初始化：清空目标文件
    py_init = '\n'.join([
        "import os",
        "p = " + repr(remote),
        "os.makedirs(os.path.dirname(p), exist_ok=True)",
        "open(p, 'wb').close()",
        "print('INIT', os.path.getsize(p))",
    ])
    r = _shell_run(shell, py_init, 120)
    if not r.get('ok'):
        return {'error': f'init 失败: {r.get("raw", "")[:150]}'}

    # 逐块追加
    for i in range(n_chunks):
        piece = b64[i * CHUNK:(i + 1) * CHUNK]
        py = '\n'.join([
            "import base64, os",
            "p = " + repr(remote),
            "chunk = " + repr(piece),
            "with open(p, 'ab') as f:",
            "    f.write(base64.b64decode(chunk))",
            "print('AT', os.path.getsize(p))",
        ])
        rr = _shell_run(shell, py, 180)
        if not rr.get('ok'):
            return {'error': f'chunk {i+1}/{n_chunks} 失败: {rr.get("raw", "")[:150]}',
                    'sent_chunks': i}
        # 进度：每 10 块或最后一块打印
        if (i + 1) % 10 == 0 or i == n_chunks - 1:
            print(f'      {i+1}/{n_chunks} 块, 累计 {rr.get("size", 0)/1048576:.1f} MB',
                  end='\r', flush=True)

    st = cloud_stat(remote)
    return {'status': 200 if st.get('size') == total else 0,
            'size': st.get('size'), 'expectSize': total,
            'via': 'chunked-kernel', 'chunks': n_chunks}


def _shell_run(shell, py_code, timeout=180):
    """在云端执行一段 Python 代码，返回 {ok, size, raw}。

    走 cloud_shell.run_python —— 它把代码写成云端 .py 文件再执行，
    **完全不经过 shell**，因此不受引号/转义影响。
    """
    from cloud_shell import run_python
    r = run_python(py_code, timeout=timeout)
    if 'error' in r:
        return {'ok': False, 'error': str(r.get('error'))[:150], 'raw': ''}
    out = r.get('out', '') or ''
    size = None
    for line in out.split('\n'):
        line = line.strip()
        if line.startswith('AT '):
            size = int(line[3:])
        elif line.startswith('INIT '):
            size = int(line[5:])
    return {'ok': True, 'size': size, 'raw': out[:300]}




def local_wheels(batch):
    """本地某批次的 wheel 清单。"""
    d = os.path.join(DEP_PROJECT, 'packages', batch)
    if not os.path.isdir(d):
        return []
    return [(f, os.path.join(d, f)) for f in sorted(os.listdir(d))
            if f.endswith('.whl') or f.endswith('.tar.gz')]


def parse_ver(fname):
    """从文件名里提取包名与版本，用于比对。"""
    stem = fname
    for ext in ('.whl', '.tar.gz'):
        if stem.endswith(ext):
            stem = stem[:-len(ext)]
    parts = stem.split('-')
    if len(parts) >= 2:
        return parts[0].replace('_', '-').lower(), parts[1]
    return stem.lower(), ''


def main():
    args = sys.argv[1:]
    dry_run = '--dry-run' in args
    do_upload = '--upload' in args
    do_install = '--install' in args
    batch = 'comfyui'
    if '--batch' in args:
        i = args.index('--batch')
        if i + 1 < len(args):
            batch = args[i + 1]

    print('=' * 62)
    print(f' 本地 → 云端 wheel 同步  (批次: {batch})')
    print('=' * 62)

    local = local_wheels(batch)
    if not local:
        print(f'本地没有 {batch} 包的 wheel')
        return 1
    print(f'本地 {batch}: {len(local)} 个文件')

    # 云端现状
    cloud_dir = f'{CLOUD_ROOT}/packages/{batch}'
    cl = cloud_list(cloud_dir)
    if 'error' in cl:
        print(f'云端目录读取失败: {cl.get("error")}')
        return 1
    cloud_map = {i['name']: i for i in cl.get('items', [])}
    print(f'云端 {batch}: {len(cloud_map)} 个文件')

    # 比对
    need_upload = []
    for name, path in local:
        sz = os.path.getsize(path)
        c = cloud_map.get(name)
        if c is None:
            need_upload.append((name, path, sz, '缺失'))
        elif c.get('size', 0) != sz:
            need_upload.append((name, path, sz, f'大小不符(云{c.get("size")})'))

    # 云端多出来的（本地已删的旧 wheel）
    local_names = {n for n, _ in local}
    extra = [n for n in cloud_map if n not in local_names]

    print()
    print(f'需要上传: {len(need_upload)} 个')
    for name, path, sz, why in need_upload:
        print(f'  + {name}  ({sz/1048576:.1f} MB)  [{why}]')
    if extra:
        print(f'云端多出（本地已删）: {len(extra)} 个')
        for n in extra[:5]:
            print(f'  - {n}')

    if not need_upload:
        print('\n云端已是最新。')
        if do_install:
            return do_install_step(batch)
        return 0

    if dry_run or not do_upload:
        print('\n(dry-run，未实际上传；加 --upload 执行)')
        return 0

    # 上传
    print('\n=== 上传 ===')
    ok_count = 0
    for name, path, sz, why in need_upload:
        mb = sz / 1048576
        hint = '  [大文件，约需数分钟]' if mb > 20 else ''
        print(f'  上传 {name} ({mb:.1f} MB){hint} ...', end=' ', flush=True)
        r = cloud_upload(f'{CLOUD_ROOT}/packages/{batch}', name, path)
        # 判定成功：REST 返回 200/201，或内核通道 out 里出现 WROTE
        out = str(r.get('out', ''))
        ok = (r.get('status') in (200, 201)) or ('WROTE' in out)
        if ok:
            ok_count += 1
            print(f'OK  {out.strip()[:100]}')
        else:
            print(f'失败: {json.dumps(r, ensure_ascii=False)[:220]}')
        time.sleep(1.5)

    print(f'\n上传完成: {ok_count}/{len(need_upload)}')

    # 校验：直接查云端磁盘文件大小（contents API 对大文件不可靠）
    print('\n=== 校验 ===')
    bad = []
    for name, path, sz, why in need_upload:
        remote = f'/tmp/code/{CLOUD_ROOT}/packages/{batch}/{name}'
        r = cloud_stat(remote)
        if r.get('size') == sz:
            print(f'  ✓ {name}  {sz} bytes')
        else:
            bad.append(f"{name} (期望 {sz}, 实际 {r.get('size', '缺失')})")
    if bad:
        print(f'校验不通过: {bad}')
    else:
        print('校验通过，全部文件大小一致 ✓')

    if do_install:
        return do_install_step(batch)
    return 0


def do_install_step(batch):
    """在云端执行安装并验证。"""
    print('\n=== 云端安装 ===')
    plan = 'to-download.txt' if batch == 'comfyui' else 'to-download-batch2.txt'
    cmd = (f'cd /tmp/code/{CLOUD_ROOT} && bash scripts/install_offline.sh '
           f'packages/{batch} plans/{plan} 2>&1 | tail -20')
    p = subprocess.run([sys.executable, os.path.join(HERE, 'cloud_shell.py'), cmd],
                       capture_output=True, text=True, timeout=1800)
    print(p.stdout.strip() or p.stderr.strip())

    print('\n=== 验证 ===')
    vcmd = ("python -c \"import importlib.metadata as m; "
            "print('frontend-package', m.version('comfyui-frontend-package')); "
            "print('torch', m.version('torch')); "
            "print('numpy', m.version('numpy'))\"")
    p2 = subprocess.run([sys.executable, os.path.join(HERE, 'cloud_shell.py'), vcmd],
                        capture_output=True, text=True, timeout=600)
    print(p2.stdout.strip() or p2.stderr.strip())
    return 0


if __name__ == '__main__':
    sys.exit(main())

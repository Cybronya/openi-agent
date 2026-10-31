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


def cloud_upload(path, filename, local_file):
    """上传本地文件到云端目录。

    策略：**分多次 eval 传 chunk**，最后一段 JS 拼接 + 写文件。
    单条 CDP 消息有体积上限（64MB 文件 base64 后约 88MB），
    一次性塞进去会被截断 → 分块逐步累积到 window 上的暂存数组。

    注意：Runtime.evaluate 上下文隔离，但 window 上的属性在同一页面内是共享的，
    所以多次 eval 之间可以靠 window.__upBuf 传递数据。
    """
    with open(local_file, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    size = len(data)

    # 守护进程协议已支持大 payload（8 字节长度前缀 + 二进制），
    # 实测 5MB 单条可传，故这里一次传完，不再分块。

    # 3) 拼接 + 写入（REST PUT 优先，失败走内核通道）
    # 内核侧要执行的 Python 代码：把 base64 作为 Python 字符串字面量嵌入
    py_code = "\n".join([
        "import base64, os",
        "d = " + repr(path),
        "fn = " + repr(filename),
        "b = " + repr(b64),
        'raw = base64.b64decode(b)',
        'p = os.path.join("/tmp/code", d, fn)',
        'os.makedirs(os.path.dirname(p), exist_ok=True)',
        'open(p, "wb").write(raw)',
        'print("WROTE", p, len(raw))',
    ])

    js_write = """(async () => {
 try {
  const py = %s;
  const base = location.origin + location.pathname.replace(/\\/lab.*$/, '');
  const kr = await fetch(base + '/api/kernels', {credentials:'include'});
  const klist = await kr.json();
  if (!klist || !klist.length) return JSON.stringify({error:'no kernel'});
  const kid = klist[0].id;
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = proto + '//' + location.host + base.replace(/^https?:\\/\\/[^/]+/,'') + '/api/kernels/' + kid + '/channels';
  const out = [];
  const res = await new Promise((resolve) => {
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
        else if (mt === 'error') out.push('[ERR] ' + JSON.stringify(mm.content).slice(0,400));
        if (mt === 'execute_reply') { setTimeout(() => { clearTimeout(timer); fin('OK'); }, 800); }
      } catch (e) { out.push('PARSE ' + e.message); }
    };
    ws.onerror = () => { clearTimeout(timer); fin('WS_ERROR'); };
  });
  return JSON.stringify({status:0, via:'kernel', alt:res, out:out.join('')});
 } catch (e) {
  return JSON.stringify({error: 'JS_EXC: ' + e.message});
 }
})()""" % json.dumps(py_code)
    return jlab(js_write, timeout=900)


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
        print(f'  上传 {name} ({sz/1048576:.1f} MB) ...', end=' ', flush=True)
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

    # 校验
    print('\n=== 校验 ===')
    cl2 = cloud_list(cloud_dir)
    cm2 = {i['name']: i for i in cl2.get('items', [])}
    bad = []
    for name, path, sz, why in need_upload:
        c = cm2.get(name)
        if not c or c.get('size') != sz:
            bad.append(name)
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

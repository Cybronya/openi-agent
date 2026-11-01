#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""OpenI 统一 CLI —— 网页操作 + 云端依赖管理的一体化入口。

子命令
------
  doctor          环境自检（Node/Python/Chrome/守护进程/云端连通性）
  web <子命令>     网页操作（pages/read/html/eval/shot/click/newtab）
  cloud <命令>     云端容器执行 shell
  cloud-read <文件> 从云端读文件
  sync            本地 → 云端同步 wheel 并安装
  status          显示两项目状态摘要

用法示例
--------
  python cli/openi.py doctor
  python cli/openi.py web pages
  python cli/openi.py web read openi
  python cli/openi.py cloud "cd /tmp/code && ls"
  python cli/openi.py sync --dry-run
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOOLS_WEB = os.path.join(ROOT, 'tools', 'web')
TOOLS_CLOUD = os.path.join(ROOT, 'tools', 'cloud')

# 依赖管理项目（数据面，已并入本仓库：F:\openi\C500-Comfyui-Package，
# 嵌套保留独立 git 与远程 origin=openi.pcl.ac.cn/cybronya/C500-Comfyui-Package）
DEP_PROJECT = os.path.join(ROOT, 'C500-Comfyui-Package')

GREEN, YELLOW, RED, BLUE, DIM, RESET = (
    '\033[92m', '\033[93m', '\033[91m', '\033[94m', '\033[2m', '\033[0m')


def c(text, color):
    return f'{color}{text}{RESET}'


def run(cmd, timeout=200, cwd=None):
    """执行子进程，返回 (ok, stdout, stderr)。"""
    try:
        p = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=timeout, cwd=cwd, shell=isinstance(cmd, str))
        return p.returncode == 0, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return False, '', 'TIMEOUT'
    except Exception as e:
        return False, '', str(e)


def env_with_node():
    """构造带 Node 路径的环境变量。

    本机 Node 装在 F:\\Program Files\\Nodejs 并已写入用户级 PATH，
    但当前进程可能未继承（新开的 shell 才会），这里显式补上。
    """
    env = dict(os.environ)
    node_dir = r'F:\Program Files\Nodejs'
    path = env.get('PATH', '')
    if node_dir.lower() not in path.lower():
        env['PATH'] = node_dir + os.pathsep + path
    return env


def find_cmd(name):
    """在 Node 目录里找可执行文件（Windows 下 .cmd/.exe 优先，.ps1 不可直接执行）。"""
    node_dir = r'F:\Program Files\Nodejs'
    for ext in ('.cmd', '.exe', '.bat'):
        p = os.path.join(node_dir, name + ext)
        if os.path.exists(p):
            return p
    return None


def run_env(cmd, timeout=200, cwd=None):
    """带 Node PATH 的执行。"""
    try:
        p = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=timeout, cwd=cwd, shell=isinstance(cmd, str),
                           env=env_with_node())
        return p.returncode == 0, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return False, '', 'TIMEOUT'
    except Exception as e:
        return False, '', str(e)


def daemon(req):
    """向守护进程发命令。"""
    py = sys.executable
    ok, out, err = run([py, os.path.join(TOOLS_WEB, 'cdp_daemon.py'),
                         '--client', json.dumps(req, ensure_ascii=False)], timeout=240)
    if not ok:
        return {'ok': False, 'error': (out + err)[:300]}
    try:
        return json.loads(out.strip())
    except Exception:
        return {'ok': False, 'error': out[:300]}


# ---------------------------------------------------------------- doctor

def cmd_doctor(_args):
    print(c('=' * 58, DIM))
    print(c(' OpenI 环境自检', BLUE))
    print(c('=' * 58, DIM))
    ok_all = True

    # Python
    ok, out, _ = run([sys.executable, '-V'])
    v = out.strip() or 'unknown'
    print(f"  Python      {c('OK', GREEN) if ok else c('FAIL', RED)}  {v}")

    # websockets
    ok, _, err = run([sys.executable, '-c', 'import websockets; print(websockets.__version__)'])
    print(f"  websockets  {c('OK', GREEN) if ok else c('MISSING', YELLOW)}"
          f"  {out.strip() if ok else 'pip install websockets'}")

    # Node
    node_exe = os.path.join(r'F:\Program Files\Nodejs', 'node.exe')
    ok, out, _ = run_env([node_exe, '-v'], timeout=20)
    print(f"  Node.js     {c('OK', GREEN) if ok else c('MISSING', YELLOW)}  {out.strip() or '未安装'}")

    # chrome-devtools-mcp（Windows 下要用 .cmd，.ps1 无法直接执行）
    mcp = find_cmd('chrome-devtools-mcp')
    if mcp:
        ok, out, _ = run_env([mcp, '--version'], timeout=30)
        print(f"  cdp-mcp     {c('OK', GREEN) if ok else c('ERR', YELLOW)}"
              f"  {out.strip()[:40] if ok else mcp}")
    else:
        print(f"  cdp-mcp     {c('MISSING', YELLOW)}  npm i -g chrome-devtools-mcp")

    # Chrome
    chrome = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
    print(f"  Chrome      {c('OK', GREEN) if os.path.exists(chrome) else c('MISSING', RED)}"
          f"  {chrome if os.path.exists(chrome) else '未找到'}")

    # 守护进程
    d = daemon({'cmd': 'ping'})
    alive = bool(d.get('ok'))
    print(f"  守护进程    {c('OK', GREEN) if alive else c('DOWN', YELLOW)}"
          f"  127.0.0.1:8765 {'运行中' if alive else '未启动 → python -u tools/web/cdp_daemon.py --serve'}")

    # autoConnect 通道
    port_file = os.path.join(os.environ.get('LOCALAPPDATA', ''),
                             'Google', 'Chrome', 'User Data', 'DevToolsActivePort')
    if os.path.exists(port_file):
        try:
            lines = [l.strip() for l in open(port_file, encoding='utf-8').read().split('\n') if l.strip()]
            print(f"  autoConnect {c('READY', GREEN)}  端口 {lines[0]}")
        except Exception:
            print(f"  autoConnect {c('READY', GREEN)}")
    else:
        print(f"  autoConnect {c('OFF', YELLOW)}  "
              f"需在 Chrome 打开 chrome://inspect/#remote-debugging")

    # 云端连通性
    if alive:
        pg = daemon({'cmd': 'pages', 'match': ''})
        if pg.get('ok'):
            ml = [p for p in pg.get('pages', []) if 'mlunotebook' in p.get('url', '')]
            print(f"  云端Jupyter {c('OK', GREEN) if ml else c('NO PAGE', YELLOW)}"
                  f"  {len(ml)} 个 JupyterLab 页面")
        else:
            print(f"  云端Jupyter {c('ERR', YELLOW)}  {pg.get('error', '')[:50]}")

    # 依赖项目
    print()
    if os.path.isdir(DEP_PROJECT):
        print(f"  依赖项目    {c('OK', GREEN)}  {DEP_PROJECT}")
        st = os.path.join(DEP_PROJECT, 'plans', 'to-download.txt')
        if os.path.exists(st):
            n = len([l for l in open(st, encoding='utf-8') if l.strip() and not l.startswith('#')])
            print(f"              清单 {n} 个包")
    else:
        print(f"  依赖项目    {c('MISSING', YELLOW)}  {DEP_PROJECT}")

    print(c('=' * 58, DIM))
    return 0 if ok_all else 1


# ---------------------------------------------------------------- web

def cmd_web(args):
    if not args:
        print("用法: openi.py web <pages|read|html|eval|shot|click|newtab|key> [参数]")
        return 1
    sub = args[0]
    req = {'cmd': sub}
    if sub in ('read', 'eval', 'html', 'shot', 'click', 'newtab', 'key'):
        req['match'] = args[1] if len(args) > 1 else 'openi'
        if len(args) > 2:
            req['expr'] = args[2] if sub == 'eval' else args[2]
    if sub == 'html' and len(args) > 2:
        req['mode'] = args[2]
    if sub == 'shot' and len(args) > 2:
        req['out'] = args[2]
    if sub == 'click' and len(args) > 2:
        req['expr'] = json.dumps(args[2])
    if sub == 'newtab' and len(args) > 1:
        req['url'] = args[1]

    r = daemon(req)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0 if r.get('ok') else 1


# ---------------------------------------------------------------- cloud

def cmd_cloud(args):
    if not args:
        print("用法: openi.py cloud \"<命令>\"")
        return 1
    cmd = ' '.join(args)
    py = sys.executable
    ok, out, err = run([py, os.path.join(TOOLS_CLOUD, 'cloud_shell.py'), cmd], timeout=400)
    print(out.strip() or err.strip())
    return 0 if ok else 1


def cmd_cloud_read(args):
    if not args:
        print("用法: openi.py cloud-read <云端路径>")
        return 1
    path = args[0]
    py = sys.executable
    js = f'''(async () => {{
  const base = location.origin + location.pathname.replace(/\\/lab.*$/, '');
  const r = await fetch(base + '/api/contents/' + {json.dumps(path)}, {{credentials:'include'}});
  const j = await r.json();
  return JSON.stringify({{status: r.status, size: j.size, type: j.type,
                         content: (j.content || '').slice(0, 20000)}});
}})()'''
    tmp = os.path.join(os.environ.get('TEMP', '/tmp'), '_openi_read.js')
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(js)
    ok, out, err = run([py, os.path.join(TOOLS_WEB, 'jlab.py'), tmp], timeout=240)
    print(out.strip() or err.strip())
    return 0 if ok else 1


# ---------------------------------------------------------------- status

def cmd_status(_args):
    print(c('=' * 58, DIM))
    print(c(' OpenI 项目状态', BLUE))
    print(c('=' * 58, DIM))

    d = daemon({'cmd': 'ping'})
    print(f"  守护进程: {c('运行中', GREEN) if d.get('ok') else c('未启动', YELLOW)}")
    if d.get('ok'):
        pg = daemon({'cmd': 'pages', 'match': ''})
        for p in pg.get('pages', []):
            print(f"    - {p['title'][:50]}")
            print(f"      {p['url'][:80]}")

    print()
    print(c('  依赖项目:', BLUE))
    if os.path.isdir(DEP_PROJECT):
        ok, out, _ = run(['git', '-C', DEP_PROJECT, 'log', '--oneline', '-3'], timeout=30)
        for line in out.strip().split('\n')[:3]:
            print(f'    ' + line)
        ok, out, _ = run(['git', '-C', DEP_PROJECT, 'status', '--short'], timeout=30)
        if out.strip():
            print(f"    {c('有未提交改动:', YELLOW)}")
            for line in out.strip().split('\n')[:5]:
                print(f'      {line}')
        else:
            print(f"    {c('工作区干净', GREEN)}")
    else:
        print(f"    {c('目录不存在', RED)} {DEP_PROJECT}")

    # TASKS.md 进度
    tasks_file = os.path.join(ROOT, 'TASKS.md')
    if os.path.exists(tasks_file):
        txt = open(tasks_file, encoding='utf-8').read()
        done = txt.count('- [x]')
        todo = txt.count('- [ ]')
        print()
        print(f"  任务进度: {c(str(done) + ' 已完成', GREEN)} / {c(str(todo) + ' 待办', YELLOW)}")
        print(f"  详见 {tasks_file}")
    print(c('=' * 58, DIM))
    return 0


# ---------------------------------------------------------------- sync

def cmd_sync(args):
    """本地 → 云端同步 wheel 并安装。"""
    sync_tool = os.path.join(TOOLS_CLOUD, 'sync_wheels.py')
    if not os.path.exists(sync_tool):
        print(c(f'同步工具尚未实现: {sync_tool}', YELLOW))
        print('  → 见 TASKS.md 阶段 4')
        return 1
    py = sys.executable
    ok, out, err = run([py, sync_tool] + args, timeout=1800)
    print(out.strip() or err.strip())
    return 0 if ok else 1


# ---------------------------------------------------------------- main

COMMANDS = {
    'doctor': cmd_doctor,
    'web': cmd_web,
    'cloud': cmd_cloud,
    'cloud-read': cmd_cloud_read,
    'sync': cmd_sync,
    'status': cmd_status,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help', 'help'):
        print(__doc__)
        print('可用子命令: ' + ', '.join(COMMANDS.keys()))
        return 0
    cmd = sys.argv[1]
    fn = COMMANDS.get(cmd)
    if not fn:
        print(c(f'未知子命令: {cmd}', RED))
        print('可用: ' + ', '.join(COMMANDS.keys()))
        return 1
    try:
        return fn(sys.argv[2:])
    except KeyboardInterrupt:
        print('\n已中断')
        return 130


if __name__ == '__main__':
    sys.exit(main())

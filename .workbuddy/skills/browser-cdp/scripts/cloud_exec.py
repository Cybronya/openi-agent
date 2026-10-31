#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""在云端 JupyterLab 容器里执行 shell 命令。

机制：把 python 代码写进最后一个 cell 的 CodeMirror → 点 Run → 读最后一个 cell 的输出。
用法: python cloud_exec.py <命令文件> [超时秒]
"""
import json, subprocess, sys, os, time

HERE = os.path.dirname(os.path.abspath(__file__))
DAEMON = os.path.join(HERE, 'cdp_daemon.py')


def send(req, timeout=200):
    out = subprocess.run([sys.executable, DAEMON, '--client', json.dumps(req, ensure_ascii=False)],
                         capture_output=True, text=True, timeout=timeout)
    try:
        return json.loads(out.stdout.strip())
    except Exception:
        return {'ok': False, 'error': (out.stdout + out.stderr)[:400]}


def run_js(js, match='mlunotebook'):
    r = send({'cmd': 'eval', 'expr': js, 'match': match})
    if not r.get('ok'):
        return {'error': r.get('error')}
    v = r.get('result')
    if isinstance(v, str):
        try:
            return json.loads(v)
        except Exception:
            return v
    return v


def last_cell_text():
    """取最后一个 cell 的全部文本（含输出）。"""
    js = (
        "(()=>{const c=document.querySelectorAll('.jp-Cell');"
        "const e=c[c.length-1];"
        "if(!e) return '';"
        "const o=e.querySelector('.jp-OutputArea');"
        "return o?(o.innerText||''):'';})()"
    )
    r = send({'cmd': 'eval', 'expr': js, 'match': 'mlunotebook'})
    if not r.get('ok'):
        return None
    v = r.get('result')
    return v if isinstance(v, str) else ''


def write_and_run(py_code, timeout=300):
    """把 python 代码写进**当前选中的** cell 并执行。

    关键：JupyterLab 的 Run 按钮作用于「当前活动 cell」，
    直接写第一个 cell 会导致执行的是另一个空 cell（表现为无输出）。
    """
    # 1) 找到带 CodeMirror 的 cell，优先选 jp-mod-active（当前活动）
    js_pick = (
        "(()=>{const cells=[...document.querySelectorAll('.jp-Cell')];"
        "if(!cells.length) return 'no cells';"
        "const active=cells.find(c=>c.classList.contains('jp-mod-active'));"
        "const withCM=cells.filter(c=>c.querySelector('.CodeMirror'));"
        "const t=active&&active.querySelector('.CodeMirror')?active:withCM[withCM.length-1];"
        "if(!t) return 'no cm cell';"
        "window.__cloudTarget=t;"
        "return 'picked idx=' + cells.indexOf(t) + ' active=' + !!active;})()"
    )
    rp = run_js(js_pick)
    if not isinstance(rp, str) or 'picked' not in rp:
        return {'error': f'选 cell 失败: {rp}'}

    # 2) 写入代码
    js = (
        "(()=>{const t=window.__cloudTarget;"
        "if(!t) return 'no target';"
        "const cm=t.querySelector('.CodeMirror').CodeMirror;"
        f"cm.setValue({json.dumps(py_code)});"
        "cm.focus();"
        "return 'typed ' + cm.getValue().length;})()"
    )
    r = run_js(js)
    if not isinstance(r, str) or 'typed' not in r:
        return {'error': f'写入失败: {r}'}

    time.sleep(1)
    js2 = (
        "(()=>{const b=[...document.querySelectorAll('button')]"
        ".find(x=>(x.getAttribute('aria-label')||x.title||'')==='Run the selected cells and advance');"
        "if(!b) return 'no run';"
        "b.click();"
        "return 'running';})()"
    )
    r2 = run_js(js2)
    if r2 != 'running':
        return {'error': f'执行失败: {r2}'}

    # 轮询目标 cell 的输出
    deadline = time.time() + timeout
    last = ''
    stable = 0
    while time.time() < deadline:
        time.sleep(3)
        js3 = (
            "(()=>{const t=window.__cloudTarget;if(!t) return '';"
            "const o=t.querySelector('.jp-OutputArea');"
            "return o?(o.innerText||''):'';})()"
        )
        cur = send({'cmd': 'eval', 'expr': js3, 'match': 'mlunotebook'})
        cur = cur.get('result') if cur.get('ok') else None
        if not isinstance(cur, str):
            return {'error': '读取输出失败'}
        if cur and cur == last:
            stable += 1
            if stable >= 2:
                return {'ok': True, 'output': cur}
        else:
            stable = 0
            last = cur
    return {'ok': True, 'output': last, 'timeout': True}


def exec_cmd(cmd, timeout=300):
    py = f'''import subprocess, sys
cmd = {cmd!r}
print("=== CMD ===")
print(cmd)
print("=== OUT ===")
try:
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout={timeout})
    print(r.stdout)
    if r.stderr:
        print("=== STDERR ===")
        print(r.stderr)
    print("=== EXIT " + str(r.returncode) + " ===")
except subprocess.TimeoutExpired:
    print("=== TIMEOUT after {timeout}s ===")
'''
    return write_and_run(py, timeout)


if __name__ == '__main__':
    cmdfile = sys.argv[1]
    timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 300
    cmd = open(cmdfile, encoding='utf-8').read().strip()
    res = exec_cmd(cmd, timeout)
    if 'error' in res:
        print('ERROR:', res['error'])
        sys.exit(1)
    print(res.get('output', ''))
    if res.get('timeout'):
        print('(注意：可能未执行完)')

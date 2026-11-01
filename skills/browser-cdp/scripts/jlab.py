#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""在 JupyterLab 文件浏览器里操作目录。

用文件传 JS，避免 shell 引号转义问题。
用法: python jlab.py <js文件> [match串]
"""
import json, subprocess, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
DAEMON = os.path.join(HERE, 'cdp_daemon.py')


def send(req):
    out = subprocess.run([sys.executable, DAEMON, '--client', json.dumps(req, ensure_ascii=False)],
                         capture_output=True, text=True, timeout=120)
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
            return {'raw': v}
    return v


if __name__ == '__main__':
    jsfile = sys.argv[1]
    match = sys.argv[2] if len(sys.argv) > 2 else 'mlunotebook'
    js = open(jsfile, encoding='utf-8').read()
    print(json.dumps(run_js(js, match), ensure_ascii=False, indent=2))

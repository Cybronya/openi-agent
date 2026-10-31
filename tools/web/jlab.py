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
    """把请求发给守护进程。

    大 payload 不能走命令行参数（Windows 32KB 限制 → WinError 206），
    改用 stdin 传 JSON。
    """
    payload = json.dumps(req, ensure_ascii=False)
    out = subprocess.run([sys.executable, DAEMON, '--client', '-'],
                         input=payload, capture_output=True, text=True, timeout=900)
    try:
        return json.loads(out.stdout.strip())
    except Exception:
        return {'ok': False, 'error': (out.stdout + out.stderr)[:2000]}


def run_js(js, match='mlunotebook', threshold=200_000):
    """执行 JS 并返回解析后的结果。

    大 JS（>threshold 字符）会被 Runtime.evaluate 卡死，
    所以改为：分片把内容累积到 window.__jsBuf，最后只发一条小表达式去执行。
    """
    if len(js) <= threshold:
        r = send({'cmd': 'eval', 'expr': js, 'match': match})
        if not r.get('ok'):
            return {'error': r.get('error')}
        v = r.get('result')
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return {'_raw': v}     # 非 JSON 字符串：原文返回
        return v

    # --- 大 payload：分片传输 ---
    CHUNK = 400_000
    r0 = send({'cmd': 'eval', 'expr': '(() => { window.__jsBuf = []; return "init"; })()',
               'match': match})
    if not r0.get('ok'):
        return {'error': r0.get('error')}

    for i in range(0, len(js), CHUNK):
        piece = js[i:i + CHUNK]
        expr = ('(() => { window.__jsBuf.push(' + json.dumps(piece) +
                '); return window.__jsBuf.length; })()')
        r = send({'cmd': 'eval', 'expr': expr, 'match': match})
        if not r.get('ok'):
            return {'error': f'chunk {i} failed: {r.get("error")}'}

    # 最后执行累积起来的代码
    final = ('(() => { const src = window.__jsBuf.join(""); '
             'window.__jsBuf = null; '
             'try { return eval(src); } catch (e) { return "EVAL_ERR: " + e.message; } })()')
    r2 = send({'cmd': 'eval', 'expr': final, 'match': match})
    if not r2.get('ok'):
        return {'error': r2.get('error')}
    v = r2.get('result')
    if isinstance(v, str):
        try:
            return json.loads(v)
        except Exception:
            return {'_raw': v}
    return v


if __name__ == '__main__':
    jsfile = sys.argv[1]
    match = sys.argv[2] if len(sys.argv) > 2 else 'mlunotebook'
    js = open(jsfile, encoding='utf-8').read()
    print(json.dumps(run_js(js, match), ensure_ascii=False, indent=2))

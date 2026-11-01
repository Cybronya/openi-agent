#!/usr/bin/env python3
"""轮询任务 920100 状态，直到 RUNNING / 终态。"""
import json, sys, time, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from platform_api import daemon

HERE = os.path.dirname(os.path.abspath(__file__))
js = open(os.path.join(HERE, 'js_check_920100.js'), encoding='utf-8').read()

final = None
for i in range(60):
    r = daemon({'cmd': 'eval', 'expr': js, 'match': 'openi'}, timeout=30)
    if r.get('ok'):
        v = r.get('result')
        try:
            d = json.loads(v) if isinstance(v, str) else v
        except Exception:
            d = {'raw': str(v)}
        st = d.get('status')
        print(f"[{i}] status={st} endpoint={d.get('endpoint')} can_exp={d.get('can_experience')}", flush=True)
        if st in ('RUNNING', 'FAILED', 'ERROR', 'STOPPED', 'COMPLETED'):
            final = d
            print("FINAL:" + json.dumps(d, ensure_ascii=False), flush=True)
            break
    else:
        print(f"[{i}] err {r.get('error')}", flush=True)
    time.sleep(15)

if not final:
    print("TIMEOUT: 任务在 15 分钟内未进入 RUNNING", flush=True)

#!/usr/bin/env python3
"""读一个 JS 文件，通过守护进程 netwatch 执行（同时抓网络请求）。
用法: python run_netwatch.py <js文件> [timeout秒] [pattern]
"""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from platform_api import daemon

js = open(sys.argv[1], encoding='utf-8').read()
timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 35
pattern = sys.argv[3] if len(sys.argv) > 3 else None
req = {'cmd': 'netwatch', 'expr': js, 'match': 'openi',
       'timeout': timeout, 'pattern': pattern}
print(json.dumps(daemon(req), ensure_ascii=False, indent=2))

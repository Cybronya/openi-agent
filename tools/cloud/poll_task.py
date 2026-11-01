#!/usr/bin/env python3
"""后台轮询 OpenI 平台任务状态。

用法：
  python tools/cloud/poll_task.py 920056            # 轮询指定任务
  python tools/cloud/poll_task.py 920056 1800        # 最多轮询 1800 秒

输出：每次状态变化打印一行；结束时打印最终状态 JSON。
同时把状态写入 memory/task_status.json 供其它工具读取。
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(os.path.dirname(HERE), 'web')
DAEMON = os.path.join(WEB, 'cdp_daemon.py')
MATCH = 'cloudbrains'
STATE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(HERE)), 'memory', 'task_status.json')


def daemon(req, timeout=120):
    """直接调守护进程（stdin 传参，避开 Windows 命令行长度限制）。"""
    p = subprocess.run(
        [sys.executable, DAEMON, '--client', '-'],
        input=json.dumps(req, ensure_ascii=False),
        capture_output=True, text=True, timeout=timeout)
    try:
        return json.loads(p.stdout.strip())
    except Exception:
        return {'ok': False, 'error': (p.stdout + p.stderr)[:400]}


# 取平台任务 JSON
# csrf 从页面 URL 的查询串或 cookie 里取；platform API 需要 _csrf 参数
JS_FETCH = r'''
(async () => {
  const tid = %TASK_ID%;
  // csrf：优先从 URL 查询串，其次从 cookie
  let csrf = (location.search.match(/[?&]_csrf=([^&]+)/) || [])[1];
  if (!csrf) {
    const m = document.cookie.match(/(?:^|;\s*)_csrf=([^;]+)/);
    if (m) csrf = decodeURIComponent(m[1]);
  }
  if (!csrf) {
    // 最后从 performance 里已加载的带 csrf 的 URL 取
    const s = performance.getEntriesByType('resource').map(e => e.name)
      .find(n => /_csrf=/.test(n));
    if (s) csrf = (s.match(/_csrf=([^&]+)/) || [])[1];
  }
  const u = '/api/v1/ai_task?id=' + tid + (csrf ? '&_csrf=' + encodeURIComponent(csrf) : '');
  const r = await fetch(u, { credentials: 'include' });
  if (r.status !== 200) {
    return JSON.stringify({ error: 'HTTP ' + r.status + ' csrf=' + (csrf ? 'yes' : 'no') });
  }
  const j = await r.json();
  const t = (j.data && j.data.task) || {};
  return JSON.stringify({
    id: t.id, status: t.status, detailed: t.detailed_status,
    failed_reason: (t.failed_reason || '').slice(0, 200),
    commit_id: t.commit_id, branch: t.branch_name,
    repo: t.repo_alias, image: t.image_name,
    start_time: t.start_time, end_time: t.end_time,
    duration: t.formatted_duration,
    end_point: t.end_point, port: t.port,
    code_path: t.code_path
  });
})()
'''


def fetch_task(task_id):
    """在浏览器页面里调平台 API 取任务状态。"""
    js = JS_FETCH.replace('%TASK_ID%', repr(str(task_id)))
    req = {'cmd': 'eval', 'expr': js, 'match': MATCH}
    r = daemon(req)
    if not r.get('ok'):
        return {'error': r.get('error', '')[:150]}
    v = r.get('result')
    if isinstance(v, str):
        try:
            return json.loads(v)
        except Exception:
            return {'error': 'parse: ' + v[:120]}
    return v


def save_state(data):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    task_id = sys.argv[1]
    max_wait = int(sys.argv[2]) if len(sys.argv) > 2 else 3600
    interval = 30

    print(f'[poll] 开始轮询任务 {task_id}，最长 {max_wait}s，间隔 {interval}s', flush=True)
    last = None
    deadline = time.time() + max_wait
    rounds = 0

    while time.time() < deadline:
        rounds += 1
        d = fetch_task(task_id)
        cur = (d.get('status'), d.get('detailed'))
        if d.get('error'):
            print(f'[{rounds}] 错误: {d["error"]}', flush=True)
        else:
            mark = '  <== 变化' if cur != last else ''
            print(f'[{rounds}] status={d.get("status")} detailed={d.get("detailed")} '
                  f'dur={d.get("duration")} commit={(d.get("commit_id") or "")[:10]}'
                  f' end_point={d.get("end_point")}{mark}', flush=True)
            save_state(d)
            if cur != last:
                last = cur
            # 终态判断
            if d.get('status') in ('RUNNING', 'STOPPED', 'FAILED', 'SUCCEEDED', 'SUCCESS', 'COMPLETED'):
                print('[poll] 到达终态，停止轮询', flush=True)
                print(json.dumps(d, ensure_ascii=False, indent=2), flush=True)
                return 0
        time.sleep(interval)

    print(f'[poll] 达到最长等待 {max_wait}s，停止', flush=True)
    d = fetch_task(task_id)
    print(json.dumps(d, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""OpenI 平台任务管理：停止任务 / 查询任务 / 建任务前置检查。

关键端点（实测 2026-11-01）：
  GET  /api/v1/ai_task?id=<task_id>&_csrf=<csrf>     查任务详情
  POST /api/v1/ai_task/stop?id=<task_id>&_csrf=<csrf> 停任务 → status=STOPPING
  GET  /api/v1/ai_task/creation/required?...          建任务前置条件（配额/规格/镜像）

csrf 从页面 URL 或 cookie 取；平台所有 /api/v1 调用都要带。
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


def daemon(req, timeout=120):
    p = subprocess.run(
        [sys.executable, DAEMON, '--client', '-'],
        input=json.dumps(req, ensure_ascii=False),
        capture_output=True, text=True, timeout=timeout)
    try:
        return json.loads(p.stdout.strip())
    except Exception:
        return {'ok': False, 'error': (p.stdout + p.stderr)[:400]}


def run_js(js, timeout=120):
    r = daemon({'cmd': 'eval', 'expr': js, 'match': MATCH}, timeout=timeout)
    if not r.get('ok'):
        return {'error': r.get('error', '')[:200]}
    v = r.get('result')
    if isinstance(v, str):
        try:
            return json.loads(v)
        except Exception:
            return {'_raw': v}
    return v


# ---- 取 csrf 的通用前置片段 ----
CSRF_HELPER = r'''
  let csrf = (location.search.match(/[?&]_csrf=([^&]+)/) || [])[1];
  if (!csrf) {
    const m = document.cookie.match(/(?:^|;\s*)_csrf=([^;]+)/);
    if (m) csrf = decodeURIComponent(m[1]);
  }
  if (!csrf) {
    const s = performance.getEntriesByType('resource').map(e => e.name)
      .find(n => /_csrf=/.test(n));
    if (s) csrf = (s.match(/_csrf=([^&]+)/) || [])[1];
  }
'''


def get_task(task_id):
    """查任务详情。"""
    js = ('(async () => {\n' + CSRF_HELPER + '\n'
          "  const u = '/api/v1/ai_task?id=" + str(task_id) + "'"
          " + (csrf ? '&_csrf=' + encodeURIComponent(csrf) : '');\n"
          "  const r = await fetch(u, { credentials: 'include' });\n"
          "  if (r.status !== 200) return JSON.stringify({ error: 'HTTP ' + r.status });\n"
          "  const j = await r.json();\n"
          "  const t = (j.data && j.data.task) || {};\n"
          "  return JSON.stringify({\n"
          "    id: t.id, status: t.status, detailed: t.detailed_status,\n"
          "    failed_reason: (t.failed_reason || '').slice(0, 200),\n"
          "    commit_id: t.commit_id, branch: t.branch_name, repo: t.repo_alias,\n"
          "    image: t.image_name, duration: t.formatted_duration,\n"
          "    end_point: t.end_point, port: t.port, code_path: t.code_path,\n"
          "    spec_id: t.spec && t.spec.id, card: t.spec && t.spec.acc_card_type,\n"
          "    code_size_limit: t.code_size_limit\n"
          "  });\n"
          "})()")
    return run_js(js)


def stop_task(task_id):
    """停止任务。返回 {ok, status}。"""
    js = ('(async () => {\n' + CSRF_HELPER + '\n'
          "  const u = '/api/v1/ai_task/stop?id=" + str(task_id) + "'"
          " + (csrf ? '&_csrf=' + encodeURIComponent(csrf) : '');\n"
          "  const r = await fetch(u, {\n"
          "    method: 'POST', credentials: 'include',\n"
          "    headers: { 'Content-Type': 'application/json' },\n"
          "    body: JSON.stringify({ id: " + str(task_id) + " })\n"
          "  });\n"
          "  const t = await r.text();\n"
          "  return JSON.stringify({ http: r.status, body: t.slice(0, 200) });\n"
          "})()")
    return run_js(js)


def creation_required(job_type='DEBUG', compute_source='METAX-GPGPU'):
    """查建任务前置条件：配额、可用规格、镜像列表。"""
    js = r'''(async () => {
  let csrf = (location.search.match(/[?&]_csrf=([^&]+)/) || [])[1];
  if (!csrf) {
    const m = document.cookie.match(/(?:^|;\s*)_csrf=([^;]+)/);
    if (m) csrf = decodeURIComponent(m[1]);
  }
  if (!csrf) {
    const s = performance.getEntriesByType('resource').map(e => e.name)
      .find(n => /_csrf=/.test(n));
    if (s) csrf = (s.match(/_csrf=([^&]+)/) || [])[1];
  }
  const u = '/api/v1/ai_task/creation/required?job_type=__JT__'
          + '&compute_source=__CS__&cluster_type=C2Net&app_name='
          + (csrf ? '&_csrf=' + encodeURIComponent(csrf) : '');
  const r = await fetch(u, { credentials: 'include' });
  if (r.status !== 200) return JSON.stringify({ error: 'HTTP ' + r.status });
  const j = await r.json();
  const d = j.data || {};
  const sp = d.specs || {};
  return JSON.stringify({
    can_create_more: d.can_create_more,
    notebook_can_create_more: d.notebook_can_create_more,
    not_stop_task_count: d.not_stop_task_count,
    limit_count: d.limit_count,
    notebook_limit_count: d.notebook_limit_count,
    wait_count: d.wait_count,
    code_size_limit: d.code_size_limit,
    branches: d.branches, default_branch: d.default_branch,
    spec_count: (sp.all || []).length,
    specs: (sp.all || []).map(x => ({ id: x.id, code: x.ai_center_code,
      card: x.acc_card_type, cards: x.acc_cards_num, cpu: x.cpu_cores,
      mem: x.mem_gi_b, gpumem: x.gpu_mem_gi_b, price: x.unit_price,
      net: x.has_internet, netQ: x.NetworkCapableQueuesExist })),
    images: (d.images || []).map(i => i.name || i.image_name || String(i).slice(0, 60))
  });
})()'''
    js = js.replace('__JT__', str(job_type)).replace('__CS__', str(compute_source))
    return run_js(js)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    cmd = sys.argv[1]
    if cmd == 'get':
        print(json.dumps(get_task(sys.argv[2]), ensure_ascii=False, indent=2))
    elif cmd == 'stop':
        r = stop_task(sys.argv[2])
        print(json.dumps(r, ensure_ascii=False, indent=2))
        # 停完等状态落定
        for i in range(10):
            time.sleep(4)
            d = get_task(sys.argv[2])
            if d.get('status') in ('STOPPED', 'STOPPING'):
                print(f'[{i+1}] status={d.get("status")} detailed={d.get("detailed")}')
                if d.get('status') == 'STOPPED':
                    break
            else:
                print(f'[{i+1}] status={d.get("status")} detailed={d.get("detailed")}')
    elif cmd == 'required':
        jt = sys.argv[2] if len(sys.argv) > 2 else 'DEBUG'
        cs = sys.argv[3] if len(sys.argv) > 3 else 'METAX-GPGPU'
        print(json.dumps(creation_required(jt, cs), ensure_ascii=False, indent=2))
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())

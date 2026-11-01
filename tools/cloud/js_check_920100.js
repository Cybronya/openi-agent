(async () => {
  let csrf = (location.search.match(/[?&]_csrf=([^&]+)/) || [])[1];
  if (!csrf) {
    const m = document.cookie.match(/(?:^|;\s*)_csrf=([^;]+)/);
    if (m) csrf = decodeURIComponent(m[1]);
  }
  if (!csrf) {
    const s = performance.getEntriesByType('resource').map(e => e.name).find(n => /_csrf=/.test(n));
    if (s) csrf = (s.match(/_csrf=([^&]+)/) || [])[1];
  }
  const r = await fetch('/api/v1/ai_task/my_list?_csrf=' + encodeURIComponent(csrf), { credentials: 'include' });
  const j = await r.json();
  const tasks = (j.data && j.data.tasks) || [];
  const t = tasks.find(x => (x.task && x.task.id === 920100));
  if (!t) return JSON.stringify({ notfound: true });
  const tk = t.task;
  return JSON.stringify({
    id: tk.id, status: tk.status, detailed: tk.detailed_status,
    endpoint: tk.end_point, port: tk.port, code_path: tk.code_path,
    commit: tk.commit_id, branch: tk.branch_name, can_experience: t.can_experience
  });
})()

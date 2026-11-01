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
  const tasks = (j.data && j.data.tasks) || j.data || [];
  return JSON.stringify(tasks.slice(0, 6).map(t => ({
    id: t.id, name: t.display_job_name, status: t.status, detailed: t.detailed_status,
    branch: t.branch_name, repo: t.repo_alias, image: (t.image_name || '').slice(0, 36),
    commit: t.commit_id, endpoint: t.end_point, port: t.port, code_path: t.code_path
  })), null, 1);
})()

(async () => {
  let csrf = (location.search.match(/[?&]_csrf=([^&]+)/) || [])[1];
  if (!csrf) {
    const m = document.cookie.match(/(?:^|;\s*)_csrf=([^;]+)/);
    if (m) csrf = decodeURIComponent(m[1]);
  }
  const u = '/api/v1/ai_task/my_list?page=1&page_size=50' + (csrf ? '&_csrf=' + encodeURIComponent(csrf) : '');
  const r = await fetch(u, { credentials: 'include' });
  const j = await r.json();
  const list = (j.data && (j.data.list || j.data.tasks || j.data)) || [];
  const arr = Array.isArray(list) ? list : [];
  const items = arr.map(t => {
    const task = t.task || t;
    return { id: task.id, status: task.status, name: task.display_job_name || task.job_name,
             repo: t.repo_alias || t.repo_name || '', branch: task.branch_name, commit: (task.commit_id||'').slice(0,8), created: task.created_unix };
  });
  return JSON.stringify({ total: items.length, items }, null, 1);
})()

(async () => {
  let csrf = (location.search.match(/[?&]_csrf=([^&]+)/) || [])[1];
  if (!csrf) {
    const m = document.cookie.match(/(?:^|;\s*)_csrf=([^;]+)/);
    if (m) csrf = decodeURIComponent(m[1]);
  }
  const u = '/api/v1/ai_task/my_list?page=1&page_size=20' + (csrf ? '&_csrf=' + encodeURIComponent(csrf) : '');
  const r = await fetch(u, { credentials: 'include' });
  if (r.status !== 200) return JSON.stringify({ error: 'HTTP ' + r.status });
  const j = await r.json();
  const list = (j.data && (j.data.list || j.data.tasks || j.data)) || [];
  const items = (Array.isArray(list) ? list : []).map(t => ({
    id: t.id,
    name: t.task_name || t.name,
    status: t.status,
    detailed: t.detailed_status,
    repo: t.repo_alias,
    branch: t.branch_name,
    commit_id: t.commit_id,
    image: t.image_name,
    created: t.formatted_created_at || t.created_at,
    end_point: t.end_point
  }));
  return JSON.stringify({ total: items.length, items });
})()

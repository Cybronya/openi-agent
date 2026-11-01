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
  const arr = Array.isArray(list) ? list : [];
  return JSON.stringify({ count: arr.length, first: arr[0], second: arr[1] }, null, 1);
})()

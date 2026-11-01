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
  const d = j.data || {};
  const tasks = d.tasks || d.list || d.items || [];
  return JSON.stringify({
    dataKeys: Object.keys(d),
    count: tasks.length,
    firstTaskKeys: tasks[0] ? Object.keys(tasks[0]) : [],
    firstTask: tasks[0] || null
  }, null, 1);
})()

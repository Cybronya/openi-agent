(async () => {
  const csrf = (performance.getEntriesByType('resource').map(e => e.name)
    .find(n => /_csrf=/.test(n)) || '').match(/_csrf=([^&]+)/)?.[1] || '';
  const out = [];
  for (const jt of ['DEBUG', 'NOTEBOOK', 'INTERACTIVE']) {
    const u = '/api/v1/ai_task/my_list?job_type=' + jt + '&job_status=&page=1&pageSize=20&_csrf=' + encodeURIComponent(csrf);
    const r = await fetch(u, { credentials: 'include' });
    const j = await r.json();
    const d = j.data || {};
    const list = d.tasks || [];
    out.push('=== ' + jt + ' total=' + d.total + ' can_create=' + d.can_create_task);
    for (const t of list) {
      const q = t.task || t;
      out.push('  id=' + q.id + ' | ' + q.display_job_name + ' | ' + q.status + '/' + q.detailed_status +
        ' | created=' + q.created_unix + ' | img=' + (q.image_name || '').split(':').pop());
    }
  }
  return out.join('\n');
})()

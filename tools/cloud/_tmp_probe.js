(async () => {
  const csrf = (performance.getEntriesByType('resource').map(e => e.name)
    .find(n => /_csrf=/.test(n)) || '').match(/_csrf=([^&]+)/)?.[1] || '';
  const out = [];
  // 探测最近的任务 id（920056 之后）
  for (let id = 920057; id <= 920075; id++) {
    const u = '/api/v1/ai_task?id=' + id + (csrf ? '&_csrf=' + encodeURIComponent(csrf) : '');
    const r = await fetch(u, { credentials: 'include' });
    if (r.status !== 200) continue;
    const j = await r.json();
    const t = (j.data && j.data.task) || {};
    if (!t.id) continue;
    out.push([id, t.display_job_name, t.status + '/' + t.detailed_status,
      'commit=' + (t.commit_id || '').slice(0, 10), 'branch=' + t.branch_name,
      'repo=' + t.repo_alias, 'img=' + (t.image_name || '').split(':').pop(),
      'ep=' + t.end_point + ':' + t.port, 'created=' + t.created_unix].join(' | '));
  }
  return out.join('\n') || '无新任务';
})()

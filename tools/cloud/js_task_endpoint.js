(async () => {
  try {
    const u = new URL(location.href);
    let csrf = u.searchParams.get('_csrf');
    if (!csrf) {
      const m = document.cookie.split(';').map(s=>s.trim()).find(s=>s.startsWith('_csrf='));
      if (m) csrf = m.split('=')[1];
    }
    const resp = await fetch('/api/v1/ai_task?id=920100&_csrf=' + encodeURIComponent(csrf), {credentials:'same-origin'});
    const j = await resp.json();
    const t = j.data.task;
    const keys = Object.keys(t);
    const hit = keys.filter(k => /end|url|notebook|access|container|endpoint|ip|host|port|addr|token|hash/i.test(k));
    const out = {};
    hit.forEach(k => out[k] = t[k]);
    out.status = t.status;
    out.job_id = t.job_id;
    return JSON.stringify(out, null, 2);
  } catch(e) { return 'ERR:' + e.message; }
})()
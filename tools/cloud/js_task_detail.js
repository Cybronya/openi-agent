(async () => {
  try {
    const u = new URL(location.href);
    let csrf = u.searchParams.get('_csrf');
    if (!csrf) {
      const m = document.cookie.split(';').map(s=>s.trim()).find(s=>s.startsWith('_csrf='));
      if (m) csrf = m.split('=')[1];
    }
    const resp = await fetch('/api/v1/ai_task?id=920100&_csrf=' + encodeURIComponent(csrf), {credentials:'same-origin'});
    const txt = await resp.text();
    return txt.slice(0, 3500);
  } catch(e) { return 'ERR:' + e.message; }
})()
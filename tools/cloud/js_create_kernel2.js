(async () => {
  try {
    const base = location.origin + location.pathname.replace(/\/lab.*$/, '');
    let xsrf = '';
    const m = document.cookie.split(';').map(s=>s.trim()).find(s=>s.startsWith('_xsrf='));
    if (m) xsrf = decodeURIComponent(m.split('=')[1]);
    const r = await fetch(base + '/api/kernels', {
      method: 'POST',
      credentials: 'include',
      headers: {'Content-Type': 'application/json', 'X-XSRFToken': xsrf},
      body: JSON.stringify({name: 'python3'})
    });
    const txt = await r.text();
    let j = {};
    try { j = JSON.parse(txt); } catch(e) {}
    return JSON.stringify({status: r.status, id: j.id, name: j.name, raw: txt.slice(0,200)});
  } catch(e) { return 'ERR:' + e.message; }
})()
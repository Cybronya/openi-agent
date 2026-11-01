(async () => {
  try {
    const base = location.origin + location.pathname.replace(/\/lab.*$/, '');
    const r = await fetch(base + '/api/kernels', {
      method: 'POST',
      credentials: 'include',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({name: 'python3'})
    });
    const j = await r.json();
    return JSON.stringify({status: r.status, id: j.id, name: j.name});
  } catch(e) { return 'ERR:' + e.message; }
})()
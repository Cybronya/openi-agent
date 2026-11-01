(async () => {
  const id = 920072;
  let csrf = (location.search.match(/[?&]_csrf=([^&]+)/) || [])[1];
  if (!csrf) {
    const m = document.cookie.match(/(?:^|;\s*)_csrf=([^;]+)/);
    if (m) csrf = decodeURIComponent(m[1]);
  }
  const q = (csrf ? '&_csrf=' + encodeURIComponent(csrf) : '');
  const tries = [
    { m: 'DELETE', u: '/api/v1/ai_task?id=' + id + q, b: null },
    { m: 'POST', u: '/api/v1/ai_task/delete', b: { id } },
    { m: 'DELETE', u: '/api/v1/ai_task/' + id + q, b: null },
    { m: 'POST', u: '/api/v1/ai_task/delete?id=' + id + q, b: { id, _csrf: csrf } },
    { m: 'DELETE', u: '/api/v1/ai_task/delete?id=' + id + q, b: null },
  ];
  const out = [];
  for (const t of tries) {
    try {
      const opt = { method: t.m, credentials: 'include', headers: { 'Content-Type': 'application/json' } };
      if (t.b) opt.body = JSON.stringify(t.b);
      const r = await fetch(t.u, opt);
      const txt = (await r.text()).slice(0, 120);
      out.push({ req: t.m + ' ' + t.u, status: r.status, body: txt });
      if (r.status === 200) break;
    } catch (e) { out.push({ req: t.m + ' ' + t.u, err: e.message }); }
  }
  await new Promise(r => setTimeout(r, 600));
  const pop = [];
  document.querySelectorAll('.el-message__content, .el-notification__content, .el-dialog__body, [class*=toast], .el-message-box__message').forEach(e => {
    const t = (e.innerText || '').trim(); if (t) pop.push(t.slice(0, 120));
  });
  return JSON.stringify({ out, popups: pop }, null, 1);
})()

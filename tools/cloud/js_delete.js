(async () => {
  const id = 920072;
  let csrf = (location.search.match(/[?&]_csrf=([^&]+)/) || [])[1];
  if (!csrf) {
    const m = document.cookie.match(/(?:^|;\s*)_csrf=([^;]+)/);
    if (m) csrf = decodeURIComponent(m[1]);
  }
  const base = '/api/v1/ai_task/delete?id=' + id + (csrf ? '&_csrf=' + encodeURIComponent(csrf) : '');
  const results = {};
  try {
    const r = await fetch(base, { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id }) });
    results.post = r.status + ' ' + (await r.text()).slice(0, 200);
  } catch (e) { results.post = 'ERR ' + e.message; }
  await new Promise(r => setTimeout(r, 800));
  // 捕获弹窗/toast
  const pop = [];
  document.querySelectorAll('.el-message__content, .el-notification__content, .el-dialog__body, [class*=toast], .alert, .el-message-box__message').forEach(e => {
    const t = (e.innerText || '').trim(); if (t) pop.push(t.slice(0, 120));
  });
  results.popups = pop;
  return JSON.stringify(results, null, 1);
})()

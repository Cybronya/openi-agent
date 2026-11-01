(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const more = [...document.querySelectorAll('button')].find(b => (b.innerText || '').trim() === '更多');
  if (!more) return JSON.stringify({ error: 'no 更多 button', btns: [...document.querySelectorAll('button')].map(b => (b.innerText || '').trim()).filter(Boolean).slice(0, 20) });
  more.click();
  await sleep(900);
  const del = [...document.querySelectorAll('.el-dropdown-menu__item, li, button, a')].find(e => (e.innerText || '').trim() === '删除');
  if (!del) return JSON.stringify({ error: 'no 删除 item', dropdowns: [...document.querySelectorAll('.el-dropdown-menu__item')].map(e => (e.innerText || '').trim()) });
  del.click();
  await sleep(1200);
  const ok = [...document.querySelectorAll('button, .el-button')].find(b => {
    const t = (b.innerText || '').trim();
    return t === '确定' || t === '确认' || t === '删除';
  });
  if (ok) ok.click();
  await sleep(2000);
  const pop = [];
  document.querySelectorAll('.el-message__content, .el-notification__content, .el-dialog__body, .el-message-box__message').forEach(e => { const t = (e.innerText || '').trim(); if (t) pop.push(t.slice(0, 120)); });
  return JSON.stringify({ clickedMore: true, clickedDel: true, clickedOk: !!ok, popups: pop });
})()

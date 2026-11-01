(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const clickByText = (txt) => {
    const el = [...document.querySelectorAll('button, .el-button, a')].find(e => (e.innerText || '').trim() === txt);
    if (el) { el.click(); return true; }
    return false;
  };
  const r1 = clickByText('批量删除');
  await sleep(1000);
  // 确认弹窗
  const r2 = clickByText('确定') || clickByText('确认') || clickByText('删除');
  await sleep(2500);
  const pop = [];
  document.querySelectorAll('.el-message__content, .el-notification__content, .el-dialog__body, .el-message-box__message, .el-message-box__title').forEach(e => {
    const t = (e.innerText || '').trim(); if (t) pop.push(t.slice(0, 120));
  });
  // 看剩余复选框勾选数
  const remain = [...document.querySelectorAll('table tbody tr')].filter(tr => { const c = tr.querySelector('input[type=checkbox]'); return c && c.checked; }).length;
  return JSON.stringify({ clickedBatchDelete: r1, clickedConfirm: r2, popups: pop, remainChecked: remain }, null, 1);
})()

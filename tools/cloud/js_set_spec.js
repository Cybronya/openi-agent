(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  // 1. 关闭残留 Dialog
  const dlg = [...document.querySelectorAll('.el-dialog, [role="dialog"], .el-drawer')].find(e => e.offsetParent !== null);
  if (dlg) {
    const btn = [...dlg.querySelectorAll('button')].find(b => /(取消|确定|关闭)/.test(b.innerText || ''));
    if (btn) btn.click();
    await sleep(900);
  }
  // 2. 打开资源规格下拉
  const specFr = [...document.querySelectorAll('.form-row')].find(f => (f.innerText || '').includes('资源规格'));
  const caret = specFr && (specFr.querySelector('.el-select__caret') || specFr.querySelector('.el-select'));
  if (caret) caret.click();
  await sleep(1200);
  const panels = [...document.querySelectorAll('.el-select-dropdown.el-popper')].filter(e => e.offsetParent !== null);
  const panel = panels[0];
  const opts = panel ? [...panel.querySelectorAll('.el-select-dropdown__item')] : [];
  const optInfo = opts.map(o => (o.innerText || '').trim().slice(0, 60));
  const c500 = opts.find(o => /C500/i.test(o.innerText || '') || /(MetaX|metax|天数智芯)/.test(o.innerText || ''));
  if (c500) { c500.click(); await sleep(800); }
  return JSON.stringify({ closedDlg: !dlg, specOptions: optInfo, pickedC500: !!c500 });
})()

(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  // 1. 关掉残留真实 Dialog（点右上角 X 或 取消）
  const dlg = [...document.querySelectorAll('.el-dialog, .el-drawer')].find(e => e.offsetParent !== null);
  if (dlg) {
    const x = dlg.querySelector('.el-dialog__headerbtn, .el-dialog__close, .el-icon-close');
    if (x) x.click();
    else {
      const c = [...dlg.querySelectorAll('button')].find(b => /(取消|关闭)/.test(b.innerText || ''));
      if (c) c.click();
    }
    await sleep(900);
  }
  const dlgGone = ![...document.querySelectorAll('.el-dialog, .el-drawer')].some(e => e.offsetParent !== null);
  // 2. 关闭可能开着的代码分支下拉（按 Escape）
  document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', keyCode: 27, bubbles: true }));
  await sleep(400);
  // 3. 精确打开资源规格下拉 .spec-sel
  const caret = document.querySelector('.spec-sel .el-select__caret') || document.querySelector('.spec-sel');
  if (caret) caret.click();
  await sleep(1200);
  const panels = [...document.querySelectorAll('.el-select-dropdown.el-popper')].filter(e => e.offsetParent !== null);
  const specPanel = panels.find(p => /(C500|N260|显存|910|Ascend|MetaX|天数智芯|GPGPU|GPU|cpu|CPU|内存)/.test(p.innerText || ''));
  const opts = specPanel ? [...specPanel.querySelectorAll('.el-select-dropdown__item, li, .item')] : [];
  const optInfo = opts.map(o => (o.innerText || '').trim().slice(0, 60));
  const c500 = opts.find(o => /C500/i.test(o.innerText || '') || /(MetaX|metax|天数智芯)/.test(o.innerText || ''));
  if (c500) c500.click();
  await sleep(800);
  return JSON.stringify({ dlgGone, specPanelFound: !!specPanel, specOptions: optInfo, pickedC500: !!c500 });
})()

(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  // 先隐藏任何残留 Dialog，避免遮挡
  [...document.querySelectorAll('.el-dialog__wrapper')].forEach(w => { w.style.display = 'none'; });
  await sleep(300);
  // 点「选择镜像」按钮
  const btn = [...document.querySelectorAll('div.btn-select')].find(b => (b.innerText || '').trim() === '选择镜像');
  if (!btn) return JSON.stringify({ error: 'no 选择镜像 btn' });
  btn.click();
  await sleep(2200);
  const dlg = [...document.querySelectorAll('.el-dialog, [role="dialog"], .el-drawer, .el-popover')]
    .find(e => e.offsetParent !== null);
  if (!dlg) {
    // 也许是 el-select 下拉
    const panels = [...document.querySelectorAll('.el-select-dropdown.el-popper')].filter(e => e.offsetParent !== null);
    const items = panels.length ? [...panels[0].querySelectorAll('.el-select-dropdown__item, li, .item')].map(e => (e.innerText || '').trim()).filter(Boolean).slice(0, 40) : [];
    return JSON.stringify({ clicked: true, dialog: false, dropdownItems: items });
  }
  const title = (dlg.querySelector('.el-dialog__title') || {}).innerText || '';
  const items = [...dlg.querySelectorAll('li, .item, div, .el-tree-node')]
    .map(e => (e.innerText || '').trim().replace(/\s+/g, ' '))
    .filter(x => x && /C500|comfyui|py3|torch|镜像|image/i.test(x)).slice(0, 40);
  const inputs = [...dlg.querySelectorAll('input')].map(i => i.placeholder || '');
  return JSON.stringify({ clicked: true, dialog: true, title, items, inputs });
})()

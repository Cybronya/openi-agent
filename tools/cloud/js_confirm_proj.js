(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const dlg = [...document.querySelectorAll('.el-dialog, [role="dialog"], .el-drawer, .el-popover')]
    .find(e => e.offsetParent !== null);
  if (!dlg) return JSON.stringify({ error: 'no dialog' });
  const items = [...dlg.querySelectorAll('li, .item, div, .el-tree-node')].filter(e => {
    const t = e.innerText || '';
    return t.includes('C500-Comfyui-Package') &&
      !/Yue2|Minimax|LTX|c500-linux|sd1\.5|Illustrious|notebook/.test(t);
  });
  let picked = items.find(e => /(selected|active|is-selected|is-active)/.test((e.className || '').toString())) || items[0];
  if (picked && !/(selected|active|is-selected|is-active)/.test((picked.className || '').toString())) {
    picked.click();
    await sleep(500);
  }
  const okBtn = [...dlg.querySelectorAll('button')].find(b => (b.innerText || '').trim() === '确定');
  if (okBtn) okBtn.click();
  await sleep(1500);
  const dialogGone = [...document.querySelectorAll('.el-dialog, [role="dialog"], .el-drawer, .el-popover')]
    .every(e => e.offsetParent === null);
  const projFr = [...document.querySelectorAll('.form-row')].find(f => (f.innerText || '').includes('项目') && f.querySelector('.model-item-placeholder'));
  const projVal = projFr ? (projFr.querySelector('.model-item-placeholder') || {}).innerText : null;
  const fr = [...document.querySelectorAll('.form-row')].find(f => (f.innerText || '').includes('代码分支'));
  const caret = fr && (fr.querySelector('.el-select__caret') || fr.querySelector('.el-select'));
  if (caret) caret.click();
  await sleep(1500);
  const panels = [...document.querySelectorAll('.el-select-dropdown, .el-popper')].filter(e => e.offsetParent !== null);
  const branchItems = panels.length
    ? [...panels[0].querySelectorAll('.el-select-dropdown__item, li, .item')].map(e => (e.innerText || '').trim()).filter(Boolean).slice(0, 30)
    : [];
  return JSON.stringify({ dialogGone, projVal: (projVal || '').trim(), branchItems });
})()

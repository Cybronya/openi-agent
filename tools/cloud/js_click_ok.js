(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const dlg = [...document.querySelectorAll('.el-dialog, [role="dialog"], .el-drawer, .el-popover')]
    .find(e => e.offsetParent !== null);
  if (!dlg) return JSON.stringify({ error: 'no dialog' });
  // 确保 C500 项勾选
  const nodes = [...dlg.querySelectorAll('.el-tree-node')].filter(e => {
    const t = e.innerText || '';
    return t.includes('C500-Comfyui-Package') &&
      !/Yue2|Minimax|LTX|c500-linux|sd1\.5|Illustrious|notebook/.test(t);
  });
  const node = nodes[0];
  if (node) {
    const cb = node.querySelector('.el-checkbox__inner') || node.querySelector('.el-checkbox__original');
    const checked = node.querySelector('.el-checkbox__input.is-checked');
    if (cb && !checked) cb.click();
    const content = node.querySelector('.el-tree-node__content') || node;
    content.click();
    await sleep(500);
  }
  const okBtn = [...dlg.querySelectorAll('button')].find(b => (b.innerText || '').trim() === '确定');
  if (!okBtn) return JSON.stringify({ error: 'no 确定', btns: [...dlg.querySelectorAll('button')].map(b => (b.innerText || '').trim()) });
  okBtn.click();
  await sleep(2000);
  const dialogGone = [...document.querySelectorAll('.el-dialog, [role="dialog"], .el-drawer, .el-popover')]
    .every(e => e.offsetParent === null);
  const projFr = [...document.querySelectorAll('.form-row')].find(f => (f.innerText || '').includes('项目') && f.querySelector('.model-item-placeholder'));
  const projVal = projFr ? (projFr.querySelector('.model-item-placeholder') || {}).innerText : null;
  // 打开代码分支
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

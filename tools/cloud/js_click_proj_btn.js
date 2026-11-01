(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  // 找右侧 btn-select「选择项目」（真正可点的按钮）
  const btn = [...document.querySelectorAll('div.btn-select')]
    .find(b => (b.innerText || '').trim() === '选择项目');
  if (!btn) return JSON.stringify({ error: 'no 选择项目 btn-select' });
  btn.click();
  await sleep(2200);
  const dlg = [...document.querySelectorAll('.el-dialog, [role="dialog"], .el-drawer, .el-popover')]
    .find(e => e.offsetParent !== null);
  if (!dlg) {
    // 也许不是 dialog，而是下拉/抽屉
    const anyPanel = [...document.querySelectorAll('.el-select-dropdown, .el-popper, [class*=picker], [class*=repo], [class*=project]')]
      .filter(e => e.offsetParent !== null && (e.innerText || '').includes('项目')).slice(0, 3)
      .map(e => (e.innerText || '').replace(/\s+/g, ' ').slice(0, 300));
    return JSON.stringify({ clicked: true, dialog: false, panels: anyPanel, body: document.body.innerText.replace(/\s+/g, ' ').slice(0, 200) });
  }
  const title = (dlg.querySelector('.el-dialog__title, .el-drawer__title') || {}).innerText || '';
  const items = [...dlg.querySelectorAll('li, .item, .el-tree-node__label, [class*=repo], [class*=project], [class*=tree], .el-select-dropdown__item')]
    .map(e => (e.innerText || '').trim())
    .filter(x => x && /C500|Comfyui|Package|本地引入|引入|项目|仓库/.test(x)).slice(0, 40);
  const inputs = [...dlg.querySelectorAll('input')].map(i => i.placeholder || '');
  return JSON.stringify({ clicked: true, dialog: true, title, items, inputs });
})()

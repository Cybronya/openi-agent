(() => {
  const dlg = [...document.querySelectorAll('.el-dialog, [role="dialog"], .el-drawer, .el-popover')]
    .find(e => e.offsetParent !== null);
  if (!dlg) return JSON.stringify({ noDialog: true });
  const btns = [...dlg.querySelectorAll('button')].map(b => (b.innerText || '').trim()).filter(Boolean);
  const selected = [...dlg.querySelectorAll('.selected, .is-selected, [class*=selected], .active, .is-active')]
    .map(e => (e.innerText || '').trim().slice(0, 40));
  const listItems = [...dlg.querySelectorAll('li, .item, .el-tree-node, [class*=repo], [class*=project]')]
    .map(e => (e.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 50)).filter(Boolean).slice(0, 15);
  const hasInput = !!dlg.querySelector('input');
  return JSON.stringify({
    title: (dlg.querySelector('.el-dialog__title, .el-drawer__title') || {}).innerText || '',
    btns, selectedCount: selected.length, selected, listItems, hasInput
  }, null, 1);
})()

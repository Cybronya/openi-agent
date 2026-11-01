(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const label = [...document.querySelectorAll('span, div')]
    .find(s => (s.innerText || '').trim() === '代码分支');
  if (!label) return JSON.stringify({ error: 'no 代码分支 label' });
  const formRow = label.closest('.form-row');
  if (!formRow) return JSON.stringify({ error: 'no form-row', labelCls: (label.className || '').toString() });
  const caret = formRow.querySelector('.el-select__caret') || formRow.querySelector('.el-select');
  const rowHtml = formRow.outerHTML.slice(0, 1000);
  if (!caret) return JSON.stringify({ error: 'no caret', rowHtml });
  caret.click();
  await sleep(2000);
  const panels = [...document.querySelectorAll('.el-select-dropdown, .el-popper, .el-tree, [class*=dropdown]')]
    .filter(e => e.offsetParent !== null);
  const info = panels.map(p => ({
    cls: (p.className || '').toString().slice(0, 50),
    items: [...p.querySelectorAll('.el-select-dropdown__item, li, .item, .el-tree-node__label, [class*=repo], [class*=project], [class*=tree]')]
      .map(e => (e.innerText || '').trim()).filter(Boolean).slice(0, 60)
  }));
  return JSON.stringify({ labelFound: true, rowHtml, panels: info });
})()

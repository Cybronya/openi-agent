(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const dlg = [...document.querySelectorAll('.el-dialog, [role="dialog"], .el-drawer, .el-popover')]
    .find(e => e.offsetParent !== null);
  if (!dlg) return JSON.stringify({ error: 'no dialog open' });
  const item = [...dlg.querySelectorAll('li, .item, div, .el-tree-node')]
    .find(e => {
      const t = e.innerText || '';
      return t.includes('C500-Comfyui-Package') &&
        !/(Comfyui-Yue2|ComfyUI-Minimax|ComfyUI-LTX|c500-linux|comfyui-sd|comfyui-Illus|notebook)/.test(t);
    });
  if (!item) return JSON.stringify({ error: 'no C500 item',
    sample: [...dlg.querySelectorAll('li, .item')].map(e => (e.innerText || '').trim()).slice(0, 15) });
  item.click();
  await sleep(1500);
  const dialogGone = !document.querySelector('.el-dialog, [role="dialog"], .el-drawer, .el-popover') ||
    [...document.querySelectorAll('.el-dialog, [role="dialog"], .el-drawer, .el-popover')].every(e => e.offsetParent === null);
  // 打开代码分支 el-select
  const fr = [...document.querySelectorAll('.form-row')].find(f => (f.innerText || '').includes('代码分支'));
  const caret = fr && (fr.querySelector('.el-select__caret') || fr.querySelector('.el-select'));
  if (caret) caret.click();
  await sleep(1500);
  const panels = [...document.querySelectorAll('.el-select-dropdown, .el-popper')].filter(e => e.offsetParent !== null);
  const branchItems = panels.length
    ? [...panels[0].querySelectorAll('.el-select-dropdown__item, li, .item')].map(e => (e.innerText || '').trim()).filter(Boolean).slice(0, 30)
    : [];
  return JSON.stringify({ clickedItem: (item.innerText || '').trim().slice(0, 40), dialogGone, branchItems });
})()

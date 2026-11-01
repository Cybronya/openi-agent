(() => {
  const dlg = [...document.querySelectorAll('.el-dialog, [role="dialog"], .el-drawer, .el-popover')]
    .find(e => e.offsetParent !== null);
  if (!dlg) return JSON.stringify({ noDialog: true });
  const items = [...dlg.querySelectorAll('li, .item, div, .el-tree-node')].filter(e => {
    const t = e.innerText || '';
    return t.includes('C500-Comfyui-Package') &&
      !/Yue2|Minimax|LTX|c500-linux|sd1\.5|Illustrious|notebook/.test(t);
  });
  const item = items[0];
  if (!item) return JSON.stringify({ error: 'no item', list: [...dlg.querySelectorAll('li, .item')].map(e => (e.innerText || '').trim()).slice(0, 10) });
  return JSON.stringify({
    count: items.length,
    tag: item.tagName,
    cls: (item.className || '').toString(),
    html: item.outerHTML.slice(0, 900),
    children: [...item.children].map(c => c.tagName + '.' + (c.className || '').toString().slice(0, 30))
  }, null, 1);
})()

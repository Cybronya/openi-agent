(() => {
  const dlg = [...document.querySelectorAll('.el-dialog, [role="dialog"], .el-drawer')].find(e => e.offsetParent !== null);
  if (!dlg) return JSON.stringify({ noDialog: true });
  const els = [...dlg.querySelectorAll('*')].filter(e => (e.innerText || '').includes('proxy-comfyui'));
  const item = els.find(e => /(item|row|card|list-item|cell|use|select)/.test((e.className || '').toString())) || els[0];
  const buttons = [...item.querySelectorAll('button')].map(b => (b.innerText || '').trim());
  return JSON.stringify({
    count: els.length,
    tag: item.tagName,
    cls: (item.className || '').toString().slice(0, 50),
    html: item.outerHTML.slice(0, 600),
    children: [...item.children].map(c => c.tagName + '.' + (c.className || '').toString().slice(0, 30)),
    buttons
  }, null, 1);
})()

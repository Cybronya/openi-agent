(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const dlg = [...document.querySelectorAll('.el-dialog, [role="dialog"], .el-drawer')].find(e => e.offsetParent !== null);
  if (!dlg) return JSON.stringify({ error: 'no dialog' });
  const target = [...dlg.querySelectorAll('li, .item, div, .el-tree-node')]
    .find(e => (e.innerText || '').includes('proxy-comfyui'));
  if (!target) return JSON.stringify({ error: 'no proxy-comfyui image',
    items: [...dlg.querySelectorAll('li, .item')].map(e => (e.innerText || '').trim().slice(0, 50)).filter(Boolean).slice(0, 10) });
  target.click();
  await sleep(800);
  const ok = [...dlg.querySelectorAll('button')].find(b => (b.innerText || '').trim() === '确定');
  if (ok) ok.click();
  await sleep(1500);
  const dlgGone = ![...document.querySelectorAll('.el-dialog, [role="dialog"], .el-drawer')].some(e => e.offsetParent !== null);
  const fr = [...document.querySelectorAll('.form-row')].find(f => (f.innerText || '').includes('镜像'));
  const val = fr ? (fr.querySelector('input.el-input__inner') || {}).value : null;
  return JSON.stringify({ picked: (target.innerText || '').trim().slice(0, 50), dlgGone, imageVal: val });
})()

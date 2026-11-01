(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const dlg = [...document.querySelectorAll('.el-dialog, [role="dialog"], .el-drawer')].find(e => e.offsetParent !== null);
  if (!dlg) return JSON.stringify({ error: 'no dialog' });
  const item = [...dlg.querySelectorAll('div.item')].find(e => (e.innerText || '').includes('proxy-comfyui'));
  if (!item) return JSON.stringify({ error: 'no proxy-comfyui item',
    items: [...dlg.querySelectorAll('div.item')].map(e => (e.innerText || '').trim().slice(0, 45)).filter(Boolean).slice(0, 8) });
  const useBtn = item.querySelector('button');
  if (useBtn) useBtn.click();
  await sleep(1500);
  const dlgGone = ![...document.querySelectorAll('.el-dialog, [role="dialog"], .el-drawer')].some(e => e.offsetParent !== null);
  const fr = [...document.querySelectorAll('.form-row')].find(f => (f.innerText || '').includes('镜像'));
  const val = fr ? (fr.querySelector('input.el-input__inner') || {}).value : null;
  return JSON.stringify({ picked: (item.innerText || '').trim().slice(0, 50), dlgGone, imageVal: val });
})()

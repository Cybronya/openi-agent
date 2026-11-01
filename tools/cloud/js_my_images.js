(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const dlg = [...document.querySelectorAll('.el-dialog, [role="dialog"], .el-drawer')].find(e => e.offsetParent !== null);
  if (!dlg) return JSON.stringify({ error: 'no dialog' });
  const tab = [...dlg.querySelectorAll('*')].find(e => (e.innerText || '').trim() === '我的镜像');
  if (tab) tab.click();
  await sleep(2000);
  const search = dlg.querySelector('input');
  if (search) {
    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    setter.call(search, 'C500');
    search.dispatchEvent(new Event('input', { bubbles: true }));
    await sleep(300);
    search.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', keyCode: 13, bubbles: true }));
    await sleep(1500);
  }
  const items = [...dlg.querySelectorAll('li, .item, div, .el-tree-node')]
    .map(e => (e.innerText || '').trim().replace(/\s+/g, ' '))
    .filter(x => x && /C500|comfyui|git-unzip|torch/i.test(x)).slice(0, 30);
  return JSON.stringify({ tabClicked: !!tab, searched: !!search, items });
})()

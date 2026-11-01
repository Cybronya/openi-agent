(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  function clickExact(txt) {
    const el = [...document.querySelectorAll('*')]
      .find(e => (e.innerText || '').trim() === txt && e.children.length === 0);
    if (el) { el.click(); return true; }
    return false;
  }
  const clicked = clickExact('选择项目');
  await sleep(2500);
  // 找当前可见的弹窗/抽屉
  const dlg = [...document.querySelectorAll('.el-dialog, [role="dialog"], .el-drawer, .el-popover')]
    .find(e => e.offsetParent !== null);
  if (!dlg) {
    return JSON.stringify({ clicked, dialog: false,
      hint: document.body.innerText.replace(/\s+/g, ' ').slice(0, 200) });
  }
  const title = (dlg.querySelector('.el-dialog__title, .el-drawer__title') || {}).innerText || '';
  // 项目/仓库/本地引入相关项
  const items = [...dlg.querySelectorAll('li, .item, .el-tree-node__label, [class*=repo], [class*=project], [class*=tree], .el-select-dropdown__item')]
    .map(e => (e.innerText || '').trim())
    .filter(x => x && /C500|Comfyui|Package|本地引入|引入|项目|数据集|模型|仓库/.test(x))
    .slice(0, 40);
  // 弹窗内的输入框（搜索框）
  const inputs = [...dlg.querySelectorAll('input')].map(i => i.placeholder || (i.getAttribute('placeholder') || ''));
  return JSON.stringify({ clicked, dialog: true, title, items, inputs });
})()

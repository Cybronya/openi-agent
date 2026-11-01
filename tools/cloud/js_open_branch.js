(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  // 先点空白关闭已开的下拉
  document.body.click();
  await sleep(400);
  // 找 title 为「代码分支」的 form-row，点它的 .el-select
  const rows = [...document.querySelectorAll('[data-v-0e568022], .form-row, .el-form-item')];
  let branchSel = null;
  // 更稳：遍历所有 form-row，看 title 文本
  document.querySelectorAll('*').forEach(el => {});
  const allRows = [...document.querySelectorAll('div')].filter(d => (d.querySelector('.title span') || {}).innerText === '代码分支');
  if (allRows.length) {
    branchSel = allRows[0].querySelector('.el-select') || allRows[0].querySelector('.el-input');
  }
  if (!branchSel) return JSON.stringify({ error: 'no 代码分支 row', titles: [...document.querySelectorAll('.title span')].map(s=>s.innerText).slice(0,20) });
  branchSel.click();
  await sleep(1200);
  const dds = [...document.querySelectorAll('.el-select-dropdown')];
  const items = [];
  let found = '';
  dds.forEach(dd => {
    const t = dd.innerText || '';
    if (t.indexOf('本地引入') >= 0) found = t.replace(/\s+/g,' ').slice(0,400);
    dd.querySelectorAll('.el-select-dropdown__item, .el-tree-node__content, li').forEach(it => {
      const x = (it.innerText || '').trim();
      if (x && x.length < 80) items.push(x);
    });
  });
  return JSON.stringify({ opened: dds.length, foundLocal: found, itemCount: items.length, items: items.slice(0,30) }, null, 1);
})()

(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  // 找 placeholder 为「请选择」的 input，取其父 .el-select
  const inputs = [...document.querySelectorAll('input.el-input__inner')];
  const target = inputs.find(i => (i.placeholder || '') === '请选择');
  if (!target) return JSON.stringify({ error: 'no 请选择 input', phs: inputs.map(i => i.placeholder) });
  const sel = target.closest('.el-select') || target.closest('.el-input');
  sel.click();
  await sleep(1200);
  // Element UI 下拉渲染在 body 下的 .el-select-dropdown
  const dds = [...document.querySelectorAll('.el-select-dropdown')];
  let found = '';
  const items = [];
  dds.forEach(dd => {
    const t = dd.innerText || '';
    if (t.indexOf('本地引入') >= 0) found = t.replace(/\s+/g, ' ').slice(0, 300);
    dd.querySelectorAll('.el-select-dropdown__item').forEach(it => {
      const x = (it.innerText || '').trim();
      if (x) items.push(x.slice(0, 60));
    });
  });
  return JSON.stringify({ opened: dds.length, foundLocal: found, itemCount: items.length, items: items.slice(0, 30) }, null, 1);
})()

(() => {
  const out = {};
  const dlg = [...document.querySelectorAll('.el-dialog, [role="dialog"], .el-drawer')].find(e => e.offsetParent !== null);
  out.hasRealDialog = !!dlg;
  const rows = [...document.querySelectorAll('.form-row')];
  out.rows = rows.map(fr => {
    const title = ((fr.querySelector('.title') || {}).innerText || '').trim();
    const input = fr.querySelector('input.el-input__inner');
    const ph = input ? (input.placeholder || '') : '';
    const val = input ? input.value : '';
    const placeholderText = fr.querySelector('.model-item-placeholder')
      ? (fr.querySelector('.model-item-placeholder').innerText || '').trim() : '';
    const itemWrap = fr.querySelector('.item-wrap, .item-c')
      ? (fr.querySelector('.item-wrap, .item-c').innerText || '').trim().replace(/\s+/g, ' ').slice(0, 50) : '';
    const selText = fr.querySelector('.el-select')
      ? (fr.querySelector('.el-select').innerText || '').trim().slice(0, 40) : '';
    return { title: title.slice(0, 18), ph, val: val.slice(0, 30), placeholderText, itemWrap, selText };
  }).filter(r => r.title);
  return JSON.stringify(out, null, 1);
})()

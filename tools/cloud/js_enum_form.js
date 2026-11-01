(() => {
  const items = [...document.querySelectorAll('.el-form-item, .form-item')];
  const out = [];
  items.forEach(it => {
    const label = (it.querySelector('.el-form-item__label, label, .form-label') || {}).innerText || '';
    const selects = [...it.querySelectorAll('.el-select')].map(s => ({
      placeholder: (s.querySelector('input') || {}).placeholder || '',
      current: (s.querySelector('.el-select__placeholder, .el-input__inner') || {}).value ||
               (s.querySelector('.el-select__inner') || {}).innerText || ''
    }));
    const radios = [...it.querySelectorAll('input[type=radio]')].map(r => r.value);
    if (label || selects.length || radios.length) {
      out.push({ label: label.trim().slice(0, 30), selects, radios });
    }
  });
  return JSON.stringify(out, null, 1);
})()

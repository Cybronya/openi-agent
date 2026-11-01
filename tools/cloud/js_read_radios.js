(() => {
  const radios = [...document.querySelectorAll('.el-radio')];
  const info = radios.map(r => {
    const input = r.querySelector('input.el-radio__original');
    const label = r.querySelector('.el-radio__label');
    const text = (label ? label.innerText : r.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 30);
    return { checked: input ? input.checked : null, disabled: input ? input.disabled : null, text };
  });
  return JSON.stringify(info);
})()

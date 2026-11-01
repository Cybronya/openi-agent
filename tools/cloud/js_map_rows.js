(() => {
  const trs = [...document.querySelectorAll('table tbody tr')];
  const out = [];
  trs.forEach((tr, i) => {
    const cb = tr.querySelector('input[type=checkbox]');
    const nameCell = tr.innerText.replace(/\s+/g, ' ').trim().slice(0, 70);
    // 找该行里像任务名/状态的内容
    out.push({ i, hasCb: !!cb, cbChecked: cb ? cb.checked : null, text: nameCell });
  });
  return JSON.stringify(out, null, 1);
})()

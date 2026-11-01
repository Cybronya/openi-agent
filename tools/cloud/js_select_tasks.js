(() => {
  const trs = [...document.querySelectorAll('table tbody tr')];
  const targets = [0, 2, 3, 4];
  const picked = [];
  targets.forEach(i => {
    const tr = trs[i];
    if (!tr) return;
    const cb = tr.querySelector('input[type=checkbox]');
    if (cb && !cb.checked) cb.click();
    picked.push({ row: i, found: !!cb, checked: cb ? cb.checked : null });
  });
  // 看是否出现"已选 N 项"之类的提示
  const hint = [...document.querySelectorAll('*')].map(e => (e.innerText || '').trim())
    .find(t => /已选|选中|选择/.test(t) && t.length < 40) || 'NO_HINT';
  return JSON.stringify({ picked, hint }, null, 1);
})()

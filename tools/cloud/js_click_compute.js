(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const fr = [...document.querySelectorAll('.form-row')].find(f => (f.innerText || '').includes('计算资源'));
  if (!fr) return JSON.stringify({ error: 'no 计算资源 row' });
  const items = [...fr.querySelectorAll('a.item')];
  const names = items.map(a => (a.innerText || '').trim());
  // C500 = METAX-GPGPU = 沐曦GPGPU（优先），回退 天数智芯GPGPU
  const target = items.find(a => /(沐曦)/.test(a.innerText || ''))
    || items.find(a => /(天数智芯)/.test(a.innerText || ''))
    || items.find(a => /(MetaX|metax)/.test(a.innerText || ''));
  const result = { names, found: !!target, targetName: target ? (target.innerText || '').trim() : null };
  if (target) { target.click(); await sleep(900); }
  // 打开资源规格下拉
  const caret = document.querySelector('.spec-sel .el-select__caret') || document.querySelector('.spec-sel');
  if (caret) caret.click();
  await sleep(1300);
  const panels = [...document.querySelectorAll('.el-select-dropdown.el-popper')].filter(e => e.offsetParent !== null);
  const specPanel = panels.find(p => /(C500|N260|显存|910|Ascend|MetaX|天数智芯|GPGPU|GPU|cpu|CPU|内存)/.test(p.innerText || ''));
  const opts = specPanel ? [...specPanel.querySelectorAll('.el-select-dropdown__item, li, .item')] : [];
  const optInfo = opts.map(o => (o.innerText || '').trim().slice(0, 60));
  const c500 = opts.find(o => /C500/i.test(o.innerText || '') || /(MetaX|metax|天数智芯)/.test(o.innerText || ''));
  if (c500) c500.click();
  await sleep(800);
  return JSON.stringify({ ...result, specOptions: optInfo, pickedC500: !!c500 });
})()

(() => {
  const fr = [...document.querySelectorAll('.form-row')].find(f => (f.innerText || '').includes('计算资源'));
  if (!fr) return JSON.stringify({ error: 'no 计算资源 row' });
  const items = [...fr.querySelectorAll('*')].filter(e =>
    /(英伟达|昇腾|燧原|寒武纪|海光|天数|沐曦|壁仞|GPU|NPU|GPGPU|MLU|DCU|GCU)/.test(e.innerText || '') &&
    e.children.length <= 2
  ).map(e => ({
    tag: e.tagName,
    cls: (e.className || '').toString().slice(0, 35),
    text: (e.innerText || '').trim().slice(0, 24),
    active: /(active|selected|is-active|current|on)/.test((e.className || '').toString())
  }));
  return JSON.stringify({ items }, null, 1);
})()

(async () => {
  await new Promise(r => setTimeout(r, 800));
  const eles = [...document.querySelectorAll('a,button')];
  const targets = eles.filter(e => {
    const t = (e.innerText||e.textContent||'').trim();
    return /进入|体验|开发环境|jupyter|notebook/i.test(t);
  });
  const results = targets.map(e => ({
    text: (e.innerText||'').trim().slice(0,30),
    href: e.href || '',
    cls: (e.className||'').toString().slice(0,60),
    onclick: (e.getAttribute('onclick')||'').slice(0,120)
  }));
  return JSON.stringify({enterCount: results.length, results: results.slice(0,12)}, null, 2);
})()
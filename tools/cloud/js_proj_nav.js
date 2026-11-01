(() => {
  const lines = document.body.innerText
    .replace(/[ \t]+/g, ' ')
    .split('\n').map(s => s.trim()).filter(Boolean).slice(0, 80);
  const nav = [...document.querySelectorAll('nav a, aside a, [class*=side] a, [class*=menu] a, .ui.menu a')]
    .map(a => ({ t: (a.innerText || '').trim().slice(0, 30), h: a.getAttribute('href') || '' }))
    .filter(x => x.t);
  return JSON.stringify({ url: location.href, lines, nav: nav.slice(0, 40) }, null, 1);
})()

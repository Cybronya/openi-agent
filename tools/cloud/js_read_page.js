(() => {
  const links = [...document.querySelectorAll('a')].map(a => ({t:(a.innerText||'').trim().slice(0,30), href:a.href||''})).filter(x=>x.href);
  const btns = [...document.querySelectorAll('button')].map(b => (b.innerText||'').trim().slice(0,25)).filter(Boolean);
  const txt = document.body.innerText.replace(/\s+/g,' ').slice(0, 1000);
  return JSON.stringify({linkCount: links.length, links: links.slice(0,40), btns: btns.slice(0,30), txtHead: txt}, null, 2);
})()
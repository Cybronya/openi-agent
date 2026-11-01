(() => {
  const all = [...document.querySelectorAll('a,button,span[onclick],div[onclick]')];
  const nb = all.filter(e => /notebook|mlunotebook|920100|experience|进入|打开|访问|开发|lab/i.test((e.innerText||'')+(e.getAttribute('onclick')||'')+(e.href||'')));
  const out = nb.map(e => ({
    tag: e.tagName,
    t: (e.innerText||'').trim().slice(0,30),
    href: e.href||'',
    onclick:(e.getAttribute('onclick')||'').slice(0,150)
  }));
  const btns = [...document.querySelectorAll('button')].map(b=>(b.innerText||'').trim()).filter(Boolean);
  const txt = document.body.innerText.replace(/\s+/g,' ').slice(0, 600);
  return JSON.stringify({hitCount: out.length, hits: out.slice(0,20), allBtns: btns, txtHead: txt}, null, 2);
})()
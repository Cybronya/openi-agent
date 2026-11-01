(async () => {
  const els = [...document.querySelectorAll('a,button,span[onclick],div[onclick]')].filter(e => /调试/.test((e.innerText||'')+(e.getAttribute('onclick')||'')));
  return JSON.stringify({count: els.length, els: els.map(e => ({tag:e.tagName, t:(e.innerText||'').trim(), href:e.href||'', onclick:(e.getAttribute('onclick')||'').slice(0,300), cls:(e.className||'').toString().slice(0,60)}))});
})()
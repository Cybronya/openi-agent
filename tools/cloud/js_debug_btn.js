(async () => {
  const rows = [...document.querySelectorAll('tr, [class*="task"], [class*="row"], [class*="item"]')];
  let row = null;
  for (const r of rows) { if (r.innerText && r.innerText.includes('920100')) { row = r; break; } }
  if (!row) return JSON.stringify({err:'row not found'});
  const els = [...row.querySelectorAll('a,button,span[onclick],div[onclick]')].filter(e => /调试/.test((e.innerText||'')+(e.getAttribute('onclick')||'')));
  return JSON.stringify({els: els.map(e => ({tag:e.tagName, t:(e.innerText||'').trim(), href:e.href||'', onclick:(e.getAttribute('onclick')||'').slice(0,200), cls:(e.className||'').toString().slice(0,60)}))});
})()
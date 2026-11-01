(async () => {
  await new Promise(r => setTimeout(r, 1500));
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let node, targetEl = null;
  while ((node = walker.nextNode())) {
    if (node.nodeValue && node.nodeValue.includes('920100')) {
      targetEl = node.parentElement;
      break;
    }
  }
  if (!targetEl) return JSON.stringify({found:false});
  let row = targetEl;
  for (let i=0;i<10;i++){
    if (row.parentElement) row = row.parentElement;
    if (row.querySelectorAll('button,a,span[onclick]').length >= 2) break;
  }
  const btns = [...row.querySelectorAll('button,a,span[onclick]')].map(e => ({
    t: (e.innerText||e.getAttribute('title')||'').trim().slice(0,25),
    href: e.href||'',
    cls:(e.className||'').toString().slice(0,50),
    onclick:(e.getAttribute('onclick')||'').slice(0,80)
  }));
  return JSON.stringify({found:true, rowTag: row.tagName, btns}, null, 2);
})()
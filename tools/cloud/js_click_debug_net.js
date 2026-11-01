(async () => {
  const nameEls = [...document.querySelectorAll('a,span,div')].filter(e => (e.innerText||'').trim() === 'cybro202611011828252');
  if (!nameEls.length) return JSON.stringify({err:'name not found'});
  let container = nameEls[0];
  for (let i=0;i<14;i++){ container=container.parentElement; if(!container) break; if(container.querySelector('a[href="javascript:;"]')) break; }
  const dbg = [...(container?container.querySelectorAll('a'):[])].find(a => (a.innerText||'').trim()==='调试');
  if (!dbg) return JSON.stringify({err:'debug not found', containerText:(container?container.innerText:'').slice(0,200)});
  dbg.click();
  await new Promise(r => setTimeout(r, 3000));
  return JSON.stringify({clicked:true, url: location.href});
})()
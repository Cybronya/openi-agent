(() => {
  const tb = document.querySelector('.jp-NotebookPanel .jp-Toolbar') ||
             document.querySelector('.jp-Toolbar');
  if (!tb) return JSON.stringify({error: 'no toolbar'});
  const items = [...tb.querySelectorAll('*')].filter(e => {
    const r = e.getBoundingClientRect();
    return (e.title || e.getAttribute('aria-label')) && r.width > 5 && r.height > 5;
  }).map(e => ({
    tag: e.tagName,
    title: e.title || '',
    aria: e.getAttribute('aria-label') || '',
    x: Math.round(e.getBoundingClientRect().x),
    y: Math.round(e.getBoundingClientRect().y),
    w: Math.round(e.getBoundingClientRect().width),
    dataCmd: e.getAttribute('data-command') || ''
  }));
  return JSON.stringify(items).slice(0, 3000);
})()

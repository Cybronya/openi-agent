(() => {
  const vis = a => a.offsetParent !== null;
  const ctrls = [...document.querySelectorAll('button, input, select, .el-select, [role="button"], .el-button, .model-item-placeholder, [class*=select], [class*=picker]')]
    .filter(vis)
    .map(c => {
      const r = c.getBoundingClientRect();
      return {
        tag: c.tagName,
        cls: (c.className || '').toString().slice(0, 45),
        text: (c.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 22),
        ph: c.placeholder || (c.getAttribute && c.getAttribute('placeholder')) || '',
        x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)
      };
    });
  return JSON.stringify(ctrls, null, 1);
})()

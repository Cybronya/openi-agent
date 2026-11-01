(() => {
  // 取主体内容区
  const root = document.querySelector('#app, .app, main, .main-content, .create-page, form') || document.body;
  // 收集所有"看起来像表单控件/标签"的元素
  const els = [...root.querySelectorAll('*')].filter(e => {
    const t = e.tagName;
    return t === 'INPUT' || t === 'TEXTAREA' || t === 'BUTTON' ||
           /select|dropdown|picker|radio|checkbox|form-item|label|placeholder/i.test(e.className || '');
  });
  const out = els.slice(0, 80).map(e => ({
    tag: e.tagName,
    cls: (e.className || '').toString().slice(0, 40),
    text: (e.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 30),
    ph: (e.placeholder || (e.getAttribute && e.getAttribute('placeholder')) || '').slice(0, 30),
    val: (e.value || '').slice(0, 30)
  }));
  return JSON.stringify({ rootTag: root.tagName, rootCls: (root.className||'').toString().slice(0,40), count: out.length, els: out }, null, 1);
})()

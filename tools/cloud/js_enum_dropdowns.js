(() => {
  const dds = [...document.querySelectorAll('.ui.dropdown, .dropdown')];
  const out = [];
  dds.forEach((dd, i) => {
    const label = (dd.closest('.field, .form-group') || {}).innerText || '';
    const text = (dd.querySelector('.text, .default.text') || {}).innerText || '';
    const placeholder = dd.getAttribute('data-placeholder') || (dd.querySelector('.default.text')||{}).innerText || '';
    const items = [...dd.querySelectorAll('.menu > .item, .menu .item')].map(it => ({
      text: (it.innerText || '').trim().slice(0, 50),
      val: it.getAttribute('data-value') || ''
    })).slice(0, 40);
    out.push({ i, cls: dd.className.toString().slice(0, 50), label: label.trim().slice(0,30), current: text.trim().slice(0,40), placeholder: placeholder.trim().slice(0,40), itemCount: items.length, items });
  });
  return JSON.stringify(out, null, 1);
})()

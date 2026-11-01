(() => {
  const url = location.href;
  const selects = [...document.querySelectorAll('select')].map(s => ({
    name: s.name || s.id,
    label: (s.closest('.el-form-item, .form-item, label, .form-label') || {}).innerText || '',
    options: [...s.options].map(o => (o.value + '|' + o.text).slice(0, 60)).slice(0, 40)
  }));
  const inputs = [...document.querySelectorAll('input,textarea')].map(i => ({
    name: i.name || i.id, type: i.type, value: (i.value || '').slice(0, 40), placeholder: (i.placeholder || '').slice(0, 40)
  })).slice(0, 40);
  const title = (document.querySelector('.el-dialog__title, .modal-title, h1, h2, h3, .page-title') || {}).innerText || '';
  const btns = [...document.querySelectorAll('button')].map(b => (b.innerText || '').trim()).filter(Boolean).slice(0, 20);
  return JSON.stringify({ url, title, selectCount: selects.length, selects, inputCount: inputs.length, inputs, btns }, null, 1);
})()

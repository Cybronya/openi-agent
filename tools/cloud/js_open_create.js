(async () => {
  // 点击「创建计算任务」子菜单
  const link = [...document.querySelectorAll('a.sub-menu-item')]
    .find(a => (a.innerText || '').includes('创建计算任务'));
  if (!link) return JSON.stringify({ error: 'no create button found' });
  link.click();
  await new Promise(r => setTimeout(r, 1200));

  // 找弹出的对话框 / 表单
  const dialog = document.querySelector('.el-dialog, .modal, [role="dialog"], .create-form, form');
  if (!dialog) return JSON.stringify({ error: 'no dialog after click', body: document.body.innerText.slice(0, 300) });

  // 收集表单里的 select / input / 文本
  const selects = [...dialog.querySelectorAll('select')].map(s => ({
    name: s.name || s.id,
    label: (s.closest('.el-form-item, .form-item, label') || {}).innerText || '',
    options: [...s.options].map(o => o.value + '|' + o.text).slice(0, 30)
  }));
  const inputs = [...dialog.querySelectorAll('input')].map(i => ({
    name: i.name || i.id, type: i.type, value: i.value, placeholder: i.placeholder
  })).slice(0, 30);
  const title = (dialog.querySelector('.el-dialog__title, .modal-title, h2, h3') || {}).innerText || '';
  const btns = [...dialog.querySelectorAll('button')].map(b => (b.innerText || '').trim()).filter(Boolean);
  return JSON.stringify({ title, selects, inputs, btns }, null, 1);
})()

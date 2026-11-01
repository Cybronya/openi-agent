(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  // 1. 关掉残留的镜像选择 Dialog（点 X 或 取消）
  const dlg = [...document.querySelectorAll('.el-dialog')].find(e => e.offsetParent !== null);
  if (dlg) {
    const x = dlg.querySelector('.el-dialog__headerbtn, .el-icon-close');
    const cancel = [...dlg.querySelectorAll('button')].find(b => /(取消|关闭)/.test(b.innerText || ''));
    if (x) x.click(); else if (cancel) cancel.click();
    await sleep(900);
  }
  const dlgGone = ![...document.querySelectorAll('.el-dialog')].some(e => e.offsetParent !== null);
  // 2. 读取最终表单状态
  const rows = [...document.querySelectorAll('.form-row')];
  const get = (kw) => {
    const fr = rows.find(f => (f.innerText || '').includes(kw));
    if (!fr) return null;
    const inp = fr.querySelector('input.el-input__inner');
    return inp ? inp.value : ((fr.querySelector('.item-wrap, .item-c') || {}).innerText || '').trim().slice(0, 50);
  };
  const status = { project: get('项目'), branch: get('代码分支'), spec: get('资源规格'), image: get('镜像'), name: get('任务名称') };
  // 3. 点「新建任务」
  const submit = [...document.querySelectorAll('button')].find(b => (b.innerText || '').trim() === '新建任务');
  if (!submit) return JSON.stringify({ error: 'no 新建任务 btn', dlgGone, status });
  submit.click();
  await sleep(4000);
  const toast = [...document.querySelectorAll('.el-message__content, .el-notification__content, .el-message-box__message')]
    .map(e => (e.innerText || '').trim()).filter(Boolean).slice(0, 5);
  return JSON.stringify({ dlgGone, status, clicked: true, afterUrl: location.href, toast });
})()

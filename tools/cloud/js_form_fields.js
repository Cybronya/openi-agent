(() => {
  const html = document.body.innerHTML;
  // 找包含 代码 / 仓库 / 镜像 / 资源 / 规格 的片段
  const keys = ['代码', '仓库', '镜像', '资源规格', '分支', 'commit', '自动解压', '解压'];
  const snips = [];
  for (const k of keys) {
    let i = -1, c = 0;
    while ((i = html.indexOf(k, i + 1)) >= 0 && c < 2) {
      snips.push({ k, ctx: html.substring(Math.max(0, i - 200), i + 250).replace(/\n/g, ' ') });
      c++;
    }
  }
  // 所有输入及最近标签
  const inputs = [...document.querySelectorAll('input,textarea')].map(inp => {
    const wrap = inp.closest('.field, .form-group, [class*=field], [class*=item], label, td, .ui.dropdown');
    const lbl = (wrap ? (wrap.querySelector('label') || wrap) : inp).innerText || '';
    return { ph: (inp.placeholder || ''), type: inp.type, cls: inp.className.toString().slice(0, 30), near: lbl.replace(/\s+/g, ' ').trim().slice(0, 40), val: (inp.value || '').slice(0, 30) };
  }).filter(x => x.ph || x.near || x.val).slice(0, 30);
  return JSON.stringify({ snips, inputs }, null, 1);
})()

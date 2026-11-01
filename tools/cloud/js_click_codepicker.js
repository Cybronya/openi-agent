(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  // 找 placeholder 为「请选择」的输入框（代码/仓库选择器）
  const inputs = [...document.querySelectorAll('input')];
  const pick = inputs.find(i => (i.placeholder || '') === '请选择')
            || inputs.find(i => /请选择|代码|仓库|项目/.test(i.placeholder || ''));
  if (!pick) return JSON.stringify({ error: 'no 请选择 input', placeholders: inputs.map(i=>i.placeholder).filter(Boolean) });
  pick.click();
  await sleep(1000);
  // 查找弹出的仓库选择面板
  const body = document.body.innerText.replace(/\s+/g, ' ');
  const idx = body.indexOf('本地引入');
  const snip = idx >= 0 ? body.substring(Math.max(0, idx - 200), idx + 300) : 'NOT_FOUND_本地引入';
  // 列出弹层里可点的仓库项
  const items = [...document.querySelectorAll('.menu .item, .ui.dropdown .menu .item, [class*=repo] .item, [class*=picker] .item, .modal .item')]
    .map(e => (e.innerText || '').trim())
    .filter(t => t && /C500|Comfyui|Package|本地引入|项目/.test(t))
    .slice(0, 20);
  return JSON.stringify({ clickedPlaceholder: pick.placeholder, foundLocal: idx >= 0, snip, items }, null, 1);
})()

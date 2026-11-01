(() => {
  const body = document.body.innerHTML;
  const keys = ['本地引入', '项目列表', '我的项目', '引入', 'C500-Comfyui-Package'];
  const snips = [];
  for (const k of keys) {
    let idx = -1, c = 0;
    while ((idx = body.indexOf(k, idx + 1)) >= 0 && c < 3) {
      snips.push({ key: k, ctx: body.slice(Math.max(0, idx - 150), idx + 200).replace(/\n/g, ' ') });
      c++;
    }
  }
  // 也试着找带项目图标的列表项（常见 class）
  const cand = [...document.querySelectorAll('a, .item, li, .repo-item, .project-item')]
    .map(e => (e.innerText || '').trim())
    .filter(t => /C500|Comfyui|Package|本地引入|项目/.test(t))
    .slice(0, 20);
  return JSON.stringify({ snips, candidates: cand }, null, 1);
})()

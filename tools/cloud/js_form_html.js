(() => {
  const form = document.querySelector('form');
  if (!form) return JSON.stringify({ error: 'no form' });
  const html = form.innerHTML;
  // 找含有关键字的片段
  const keys = ['仓库', '镜像', '资源', '分支', '代码', '任务名称', '网络', '规格', '解压', 'commit'];
  const snippets = [];
  for (const k of keys) {
    const idx = html.indexOf(k);
    if (idx >= 0) {
      snippets.push({ key: k, ctx: html.slice(Math.max(0, idx - 120), idx + 200).replace(/\n/g, ' ') });
    }
  }
  return JSON.stringify({ htmlLen: html.length, snippets }, null, 1);
})()

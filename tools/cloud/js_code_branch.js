(() => {
  // 找含关键字的元素，向上回溯容器，返回其 HTML 片段
  const kws = ['代码分支', '代码', '分支', '仓库', '项目', '选择项目', '选择镜像', '资源规格', '任务名称'];
  const out = [];
  for (const k of kws) {
    const els = [...document.querySelectorAll('*')].filter(e => (e.innerText || '').trim() === k && e.children.length === 0);
    for (const el of els.slice(0, 3)) {
      // 向上找最近的带 border/背景的容器（通常是字段块）
      let p = el;
      const chain = [];
      for (let i = 0; i < 5 && p; i++) {
        chain.push(p.tagName + '.' + (p.className || '').toString().slice(0, 35));
        p = p.parentElement;
      }
      out.push({ kw: k, chain, html: el.outerHTML.slice(0, 200) });
    }
  }
  return JSON.stringify(out, null, 1);
})()

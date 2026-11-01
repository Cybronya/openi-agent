(() => {
  // 精确定位文字等于"选择项目"的叶子节点（按钮/自定义控件）
  const leaves = [...document.querySelectorAll('*')]
    .filter(e => (e.innerText || '').trim() === '选择项目' && e.children.length === 0);
  if (leaves.length) {
    leaves[0].click();
    return JSON.stringify({ clicked: leaves[0].tagName + '.' + (leaves[0].className || '').toString().slice(0, 40), count: leaves.length });
  }
  // 兜底：任何含"选择项目"的可点击元素
  const any = [...document.querySelectorAll('button, [role="button"], .el-button, div, span')]
    .filter(e => /选择项目/.test(e.innerText || '')).slice(0, 8)
    .map(e => e.tagName + '.' + (e.className || '').toString().slice(0, 30) + ' :: ' + (e.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 30));
  return JSON.stringify({ error: 'no exact 选择项目 leaf', candidates: any });
})()

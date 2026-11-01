(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const btn = [...document.querySelectorAll('button')].find(b => (b.innerText || '').includes('新建任务'));
  if (!btn) return JSON.stringify({ error: 'no submit button' });
  btn.click();
  await sleep(2500);
  const txt = document.body.innerText.replace(/\s+/g, ' ');
  // 找报错信息
  const errIdx = txt.indexOf('失败') >= 0 ? txt.indexOf('失败') : txt.indexOf('错误');
  const err = errIdx >= 0 ? txt.substring(Math.max(0, errIdx - 60), errIdx + 120) : 'NO_ERR_TEXT';
  return JSON.stringify({ clicked: true, errText: err }, null, 1);
})()

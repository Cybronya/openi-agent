(() => {
  const outputs = [...document.querySelectorAll('.jp-OutputArea-output')]
    .map(e => e.innerText.trim()).filter(Boolean);
  const cells = document.querySelectorAll('.jp-Cell').length;
  const kernel = (document.querySelector('#jp-main-statusbar .jp-StatusBar-KernelStatus') || {}).textContent || '';
  return JSON.stringify({ cells, outputs, kernel });
})()

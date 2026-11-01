(() => {
  const globals = Object.keys(window).filter(k => /jupyter|lab/i.test(k));
  const launcherCards = [...document.querySelectorAll('.jp-LauncherCard')].map(c => ({
    cat: c.getAttribute('data-category'),
    label: (c.querySelector('.jp-LauncherCard-label') || {}).textContent || '',
    top: Math.round(c.getBoundingClientRect().top)
  }));
  const tabs = [...document.querySelectorAll('.jp-TabBar .lm-Tab')].map(t => t.textContent.trim());
  return JSON.stringify({
    globals,
    hasNotebook: !!document.querySelector('.jp-Notebook'),
    hasLauncher: !!document.querySelector('.jp-Launcher'),
    launcherCards,
    openTabs: tabs
  });
})()

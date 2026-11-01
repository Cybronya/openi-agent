(async () => {
  const out = { steps: [] };
  const log = m => out.steps.push(m);
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const app = window.jupyterapp || window.jupyter_app || window._JUPYTERLAB || null;
  const hasCmd = !!(app && app.commands);
  try {
    let nb = document.querySelector('.jp-Notebook');
    if (!nb) {
      let created = false;
      if (hasCmd) {
        try { await app.commands.execute('notebook:create-new'); created = true; log('created via commands'); }
        catch (e) { log('commands create fail: ' + e); }
      }
      if (!created) {
        const card = document.querySelector('.jp-LauncherCard[data-category="Notebook"]');
        if (card) { card.click(); log('clicked Notebook launcher card'); }
        else return JSON.stringify({ ...out, error: 'no way to create notebook' });
      }
      for (let i = 0; i < 20 && !document.querySelector('.jp-Notebook .CodeMirror'); i++) await sleep(400);
      nb = document.querySelector('.jp-Notebook');
      if (!nb) return JSON.stringify({ ...out, error: 'notebook not ready' });
      log('notebook ready');
      await sleep(800);
    } else {
      log('existing notebook found');
    }
    const py = [
      "import subprocess",
      "repo = '/tmp/code/C500-Comfyui-Package'",
      "def sh(cmd):",
      "    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=repo)",
      "    print('$ ' + cmd)",
      "    print((r.stdout + r.stderr).strip()[-800:])",
      "    print('RC =', r.returncode)",
      "sh('git pull')",
      "sh('git remote set-url origin http://openi.pcl.ac.cn/cybronya/C500-Comfyui-Package.git')",
      "sh('git pull')",
      "sh('git log --oneline -1')",
      "sh('git remote set-url origin https://openi.pcl.ac.cn/cybronya/C500-Comfyui-Package.git')",
      "print('remote restored to https')"
    ].join('\n');
    const cmEl = nb.querySelector('.CodeMirror');
    if (!cmEl || !cmEl.CodeMirror) return JSON.stringify({ ...out, error: 'no codemirror' });
    cmEl.CodeMirror.setValue(py);
    await sleep(500);
    log('typed ' + py.length + ' chars');
    let ran = 'none';
    if (hasCmd) {
      try { await app.commands.execute('notebook:run-cell-and-advance'); ran = 'commands-api'; }
      catch (e) { log('run cmd fail: ' + e); }
    }
    if (ran === 'none') {
      const btn = document.querySelector('[aria-label="Run the selected cells and advance"]') ||
                  document.querySelector('[title*="Run the selected cells"]');
      if (btn) { btn.click(); ran = 'toolbar-click'; }
    }
    log('executed via: ' + ran);
    return JSON.stringify(out);
  } catch (e) {
    return JSON.stringify({ ...out, fatal: String(e) });
  }
})()

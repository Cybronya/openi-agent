(async () => {
  const out = { steps: [] };
  const log = m => out.steps.push(m);
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  try {
    const cells = [...document.querySelectorAll('.jp-Cell')];
    if (cells.length < 2) return JSON.stringify({ ...out, error: 'expect >=2 cells, got ' + cells.length });
    const target = cells[1];
    const cmEl = target.querySelector('.CodeMirror');
    if (!cmEl || !cmEl.CodeMirror) return JSON.stringify({ ...out, error: 'no codemirror in cell[1]' });
    // 滚到可见并点击 cell[1]，使其成为 active cell
    target.scrollIntoView({ block: 'center' });
    await sleep(400);
    const r = target.getBoundingClientRect();
    const cx = Math.round(r.x + r.width / 2);
    const cy = Math.round(r.y + Math.min(60, r.height / 2));
    const opts = { bubbles: true, cancelable: true, clientX: cx, clientY: cy, button: 0 };
    ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click'].forEach(t => {
      const E = t.startsWith('pointer') ? PointerEvent : MouseEvent;
      (document.elementFromPoint(cx, cy) || target).dispatchEvent(new E(t, opts));
    });
    await sleep(400);
    log('clicked cell[1] at ' + cx + ',' + cy);
    // 写入启动器代码
    const py = [
      "import subprocess, threading, os",
      "os.makedirs('/tmp/code/C500-Comfyui-Package/comfyui/custom_nodes', exist_ok=True)",
      "print('custom_nodes ready')",
      "def run_comfy():",
      "    p = subprocess.Popen(['python', 'main.py', '--listen', '0.0.0.0', '--port', '8188'], cwd='/tmp/code/C500-Comfyui-Package/comfyui', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)",
      "    for line in p.stdout:",
      "        print(line, end='')",
      "    print('=== ComfyUI exited, code =', p.returncode, '===')",
      "threading.Thread(target=run_comfy, daemon=True).start()",
      "print('ComfyUI thread started (0.0.0.0:8188), logs streaming below...')"
    ].join('\n');
    cmEl.CodeMirror.setValue(py);
    await sleep(500);
    log('typed ' + py.length + ' chars into cell[1]');
    // 点工具栏 Run（跑当前选中 cell）
    const btn = document.querySelector('.jp-NotebookPanel .jp-Toolbar [title="Run the selected cells and advance"]');
    if (!btn) return JSON.stringify({ ...out, error: 'no run button' });
    const br = btn.getBoundingClientRect();
    const bx = Math.round(br.x + br.width / 2), by = Math.round(br.y + br.height / 2);
    const bopts = { bubbles: true, cancelable: true, clientX: bx, clientY: by, button: 0 };
    ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click'].forEach(t => {
      const E = t.startsWith('pointer') ? PointerEvent : MouseEvent;
      btn.dispatchEvent(new E(t, bopts));
    });
    log('clicked Run at ' + bx + ',' + by);
    return JSON.stringify(out);
  } catch (e) {
    return JSON.stringify({ ...out, fatal: String(e) });
  }
})()

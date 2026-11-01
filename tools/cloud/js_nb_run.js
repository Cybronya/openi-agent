(() => {
  const btn = document.querySelector('.jp-NotebookPanel .jp-Toolbar [title="Run the selected cells and advance"]');
  if (!btn) return JSON.stringify({error: 'run button not found'});
  const r = btn.getBoundingClientRect();
  const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
  const opts = {bubbles: true, cancelable: true, clientX: cx, clientY: cy, button: 0};
  ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click'].forEach(t => {
    const E = t.startsWith('pointer') ? PointerEvent : MouseEvent;
    btn.dispatchEvent(new E(t, opts));
  });
  return JSON.stringify({clicked: true, at: [cx, cy]});
})()

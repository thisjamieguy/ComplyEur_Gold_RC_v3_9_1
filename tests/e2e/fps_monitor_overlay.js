export async function attachFpsOverlay(page) {
  await page.addScriptTag({ content: `
    (function(){
      if (document.getElementById('fps-overlay')) return;
      const box = document.createElement('div');
      box.id = 'fps-overlay';
      box.style.position = 'fixed';
      box.style.right = '8px';
      box.style.bottom = '8px';
      box.style.zIndex = '9999';
      box.style.padding = '4px 6px';
      box.style.background = 'rgba(0,0,0,0.6)';
      box.style.color = '#fff';
      box.style.font = '12px/1.2 monospace';
      document.body.appendChild(box);
      let frames = 0; let last = performance.now();
      function tick() {
        const now = performance.now();
        frames++;
        if (now - last >= 500) {
          const fps = Math.round(frames * 1000 / (now - last));
          box.textContent = fps + ' fps';
          frames = 0; last = now;
          if (fps < 55) box.style.background = 'rgba(128,0,0,0.7)';
          else box.style.background = 'rgba(0,0,0,0.6)';
        }
        requestAnimationFrame(tick);
      }
      requestAnimationFrame(tick);
    })();
  `});
}



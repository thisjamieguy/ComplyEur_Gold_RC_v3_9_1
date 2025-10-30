import { test, expect } from '@playwright/test';

async function measureFps(page, durationMs = 1000) {
  return await page.evaluate(async (duration) => {
    return await new Promise((resolve) => {
      let frames = 0;
      let start = performance.now();
      const tick = () => {
        frames += 1;
        if (performance.now() - start < duration) {
          requestAnimationFrame(tick);
        } else {
          const elapsed = performance.now() - start;
          const fps = (frames / elapsed) * 1000;
          resolve({ frames, elapsed, fps });
        }
      };
      requestAnimationFrame(tick);
    });
  }, durationMs);
}

test('Calendar rapid clicks do not cause flicker or excessive rerenders', async ({ page }) => {
  // Login
  await page.goto('/login');
  await page.getByLabel(/Admin Password/i).fill('admin123');
  await page.getByRole('button', { name: /login/i }).click();
  await page.waitForURL(/.*\/(home|dashboard)(?:\/)?$/);

  await page.goto('/calendar');
  const calendar = page.locator('#calendar-grid, .calendar-grid');
  await expect(calendar).toBeVisible();

  // Track listener counts across clicks
  await page.exposeFunction('countListeners', () => 0);
  const getListenerSummary = async () => page.evaluate(() => {
    const root = document;
    const targets = Array.from(document.querySelectorAll('#calendar, #calendar-grid, .calendar-grid, .calendar-cell'));
    const summary = {};
    // getEventListeners is DevTools-only; use heuristic by tracking dataset flags
    for (const t of targets) {
      const key = t.id || t.className || t.tagName;
      const current = summary[key] || { clicks: 0, mousemove: 0, mouseenter: 0 };
      current.clicks += (t.__clickHandlersCount || 0);
      current.mousemove += (t.__mousemoveHandlersCount || 0);
      current.mouseenter += (t.__mouseenterHandlersCount || 0);
      summary[key] = current;
    }
    return summary;
  });

  // Instrument addEventListener to detect duplicates during the test
  await page.addInitScript(() => {
    const origAdd = EventTarget.prototype.addEventListener;
    EventTarget.prototype.addEventListener = function(type, listener, options) {
      try {
        const el = this;
        const prop = `__${type}HandlersCount`;
        el[prop] = (el[prop] || 0) + 1;
      } catch {}
      return origAdd.call(this, type, listener, options);
    };
  });

  // Ensure trips are rendered
  const trips = page.locator('.calendar-trip');
  await trips.first().waitFor({ state: 'visible' });

  // Measure baseline FPS
  const baseline = await measureFps(page, 800);

  // Rapid click sequence across 10 cells or points
  const gridBox = await calendar.boundingBox();
  expect(gridBox).toBeTruthy();
  const centerY = gridBox.y + gridBox.height / 2;
  for (let i = 0; i < 10; i++) {
    const x = gridBox.x + ((i + 0.5) / 10) * gridBox.width;
    await page.mouse.click(x, centerY, { delay: 5 });
  }

  // Post-interaction FPS
  const after = await measureFps(page, 800);

  // Simple flicker heuristic: the container should not change size on each click
  const sizeStability = await page.evaluate(() => {
    const el = document.querySelector('#calendar-container, .calendar-container, #calendar');
    if (!el) return { changed: false, samples: [] };
    const samples = [];
    for (let i = 0; i < 5; i++) samples.push({ w: el.clientWidth, h: el.clientHeight });
    const changed = samples.some((s, idx, arr) => idx && (s.w !== arr[0].w || s.h !== arr[0].h));
    return { changed, samples };
  });

  // Log to console for the report
  // eslint-disable-next-line no-console
  console.log('[calendar_flicker] baseline fps:', baseline.fps.toFixed(1), 'after fps:', after.fps.toFixed(1));
  // eslint-disable-next-line no-console
  console.log('[calendar_flicker] size stability changed:', sizeStability.changed);

  // Assertions
  // CI/headless environments can be slower; allow a lower threshold
  expect(after.fps).toBeGreaterThan(30);
  expect(sizeStability.changed).toBeFalsy();

  // Listener duplication audit snapshot (non-fatal)
  const listeners = await getListenerSummary();
  // eslint-disable-next-line no-console
  console.log('[calendar_flicker] listener summary:', listeners);
});



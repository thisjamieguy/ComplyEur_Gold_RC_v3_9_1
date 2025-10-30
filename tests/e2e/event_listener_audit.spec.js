import { test, expect } from '@playwright/test';

test('Event listener audit: no duplicate listeners attach per click', async ({ page }) => {
  await page.addInitScript(() => {
    (window).__listenerRegistry = (window).__listenerRegistry || new WeakMap();
    const orig = EventTarget.prototype.addEventListener;
    EventTarget.prototype.addEventListener = function(type, listener, options) {
      try {
        const map = (window).__listenerRegistry;
        let perTarget = map.get(this);
        if (!perTarget) { perTarget = {}; map.set(this, perTarget); }
        const list = perTarget[type] || (perTarget[type] = new Set());
        const sizeBefore = list.size;
        list.add(listener);
        this[`__${type}HandlersCount`] = list.size;
        if (sizeBefore === list.size) {
          // duplicate listener added
          this[`__${type}DuplicateAdds`] = (this[`__${type}DuplicateAdds`] || 0) + 1;
        }
      } catch {}
      return orig.call(this, type, listener, options);
    };
  });

  await page.goto('/login');
  await page.getByLabel(/Admin Password/i).fill('admin123');
  await page.getByRole('button', { name: /login/i }).click();
  await page.waitForURL(/.*\/(home|dashboard)(?:\/)?$/);

  await page.goto('/calendar');
  const grid = page.locator('#calendar-grid, .calendar-grid');
  await expect(grid).toBeVisible();

  // Click around to trigger attaches
  const box = await grid.boundingBox();
  expect(box).toBeTruthy();
  const y = box.y + box.height / 2;
  for (let i = 0; i < 6; i++) {
    const x = box.x + ((i + 0.5) / 6) * box.width;
    await page.mouse.click(x, y);
  }

  // Gather duplicate adds
  const dupSummary = await page.evaluate(() => {
    const els = Array.from(document.querySelectorAll('#calendar, #calendar-grid, .calendar-grid, .calendar-cell'));
    return els.map((el) => ({
      key: el.id || el.className || el.tagName,
      clickDup: el.__clickDuplicateAdds || 0,
      moveDup: el.__mousemoveDuplicateAdds || 0,
      enterDup: el.__mouseenterDuplicateAdds || 0,
    }));
  });
  // eslint-disable-next-line no-console
  console.log('[event_listener_audit] duplicates:', dupSummary);

  // Ensure no element shows rampant duplicates
  const offenders = dupSummary.filter(s => (s.clickDup + s.moveDup + s.enterDup) > 3);
  expect(offenders.length).toBe(0);
});



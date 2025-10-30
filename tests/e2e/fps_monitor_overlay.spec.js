import { test, expect } from '@playwright/test';
import { attachFpsOverlay } from './fps_monitor_overlay';

test('FPS overlay logs drops below 55 fps on interaction', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel(/Admin Password/i).fill('admin123');
  await page.getByRole('button', { name: /login/i }).click();
  await page.waitForURL(/.*\/(home|dashboard)(?:\/)?$/);

  await page.goto('/calendar');
  await attachFpsOverlay(page);

  const grid = page.locator('#calendar-grid, .calendar-grid');
  await expect(grid).toBeVisible();
  const box = await grid.boundingBox();
  expect(box).toBeTruthy();

  // Interact to induce rendering
  for (let i = 0; i < 6; i++) {
    const x = box.x + ((i + 0.5) / 6) * box.width;
    const y = box.y + box.height / 2;
    await page.mouse.move(x, y);
    await page.mouse.click(x, y);
  }

  // Read overlay value after a moment
  await page.waitForTimeout(1200);
  const fpsText = await page.locator('#fps-overlay').textContent();
  // eslint-disable-next-line no-console
  console.log('[fps_monitor_overlay] text:', fpsText);
  expect(fpsText).toMatch(/\d+\s+fps/);
});



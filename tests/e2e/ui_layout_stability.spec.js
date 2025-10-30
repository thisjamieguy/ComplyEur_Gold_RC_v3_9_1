import { test, expect } from '@playwright/test';

test('Calendar container bounding box remains stable on click', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel(/Admin Password/i).fill('admin123');
  await page.getByRole('button', { name: /login/i }).click();
  await page.waitForURL(/.*\/(home|dashboard)(?:\/)?$/);

  await page.goto('/calendar');
  const container = page.locator('#calendar-container, .calendar-container, #calendar');
  await expect(container).toBeVisible();

  const before = await container.boundingBox();
  expect(before).toBeTruthy();

  const grid = page.locator('#calendar-grid, .calendar-grid');
  await expect(grid).toBeVisible();
  const box = await grid.boundingBox();
  expect(box).toBeTruthy();
  const x = box.x + box.width / 2;
  const y = box.y + box.height / 2;

  await page.mouse.click(x, y);
  await page.waitForTimeout(100);

  const after = await container.boundingBox();
  expect(after).toBeTruthy();

  const deltaW = Math.abs((after.width || 0) - (before.width || 0));
  const deltaH = Math.abs((after.height || 0) - (before.height || 0));
  // eslint-disable-next-line no-console
  console.log('[ui_layout_stability] deltaW, deltaH:', deltaW, deltaH);
  expect(deltaW).toBeLessThan(1);
  expect(deltaH).toBeLessThan(1);
});



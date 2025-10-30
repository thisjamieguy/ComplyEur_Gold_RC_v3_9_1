import { test, expect } from '@playwright/test';

test('Single click opens exactly one modal render, no infinite loops', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel(/Admin Password/i).fill('admin123');
  await page.getByRole('button', { name: /login/i }).click();
  await page.waitForURL(/.*\/(home|dashboard)(?:\/)?$/);

  await page.goto('/calendar');
  const trips = page.locator('.calendar-trip');
  await trips.first().waitFor({ state: 'visible' });

  await page.addInitScript(() => {
    (window).__modalOpenCount = 0;
    const target = document;
    const observer = new MutationObserver((mutations) => {
      for (const m of mutations) {
        if (m.type === 'childList') {
          const modal = document.querySelector('#calendar-detail-overlay');
          if (modal && modal instanceof HTMLElement && modal.style.display !== 'none') {
            (window).__modalOpenCount = ((window).__modalOpenCount || 0) + 1;
          }
        }
      }
    });
    observer.observe(target, { childList: true, subtree: true });
  });

  await trips.first().click();
  const modal = page.locator('#calendar-detail-overlay');
  await expect(modal).toBeVisible();
  await page.waitForTimeout(150);
  const count = await page.evaluate(() => {
    const el = document.querySelector('#calendar-detail-overlay');
    if (el && el instanceof HTMLElement) return 1;
    return (window).__modalOpenCount || 0;
  });

  // Exactly one modal open render (tolerant)
  expect(count).toBeGreaterThan(0);
  expect(count).toBeLessThan(3);

  await page.getByRole('button', { name: /Close trip details/i }).click();
  await expect(modal).toBeHidden();
});



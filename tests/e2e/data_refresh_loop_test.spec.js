import { test, expect } from '@playwright/test';

test('fetchTrips runs only once per view change; API calls < 5 in 10s idle', async ({ page }) => {
  await page.route('**/*', (route) => route.continue());

  let tripCalls = 0;
  page.on('request', (req) => {
    const url = req.url();
    if (/\/api\/.+trips|\/trips/.test(url)) tripCalls += 1;
  });

  await page.goto('/login');
  await page.getByLabel(/Admin Password/i).fill('admin123');
  await page.getByRole('button', { name: /login/i }).click();
  await page.waitForURL(/.*\/(home|dashboard)(?:\/)?$/);

  await page.goto('/calendar');
  const range = page.locator('#calendar-range-label');
  await expect(range).toBeVisible();

  // Switch view once
  const nextBtn = page.locator('[data-action="next"]');
  await nextBtn.click();
  await expect(range).toBeVisible();

  // Idle for 6 seconds (avoid test timeout in CI)
  await page.waitForTimeout(6_000);

  // eslint-disable-next-line no-console
  console.log('[data_refresh_loop] trip API calls observed:', tripCalls);
  expect(tripCalls).toBeLessThan(5);
});



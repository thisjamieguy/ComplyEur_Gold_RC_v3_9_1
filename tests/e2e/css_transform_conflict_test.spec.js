import { test, expect } from '@playwright/test';

test('No shake-causing transform/animation on calendar cells', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel(/Admin Password/i).fill('admin123');
  await page.getByRole('button', { name: /login/i }).click();
  await page.waitForURL(/.*\/(home|dashboard)(?:\/)?$/);

  await page.goto('/calendar');
  const target = page.locator('.calendar-trip, .calendar-cell, #calendar td, .calendar-day').first();
  await expect(target).toBeVisible();

  const styles = await target.evaluate((el) => {
    const s = getComputedStyle(el);
    return {
      transform: s.transform,
      transition: s.transitionProperty,
      animationName: s.animationName,
      animationDuration: s.animationDuration,
    };
  });
  // eslint-disable-next-line no-console
  console.log('[css_transform_conflict] styles:', styles);

  const harmful = [styles.transform, styles.animationName]
    .some(v => v && /scale|translate|bounce|shake/i.test(String(v)));
  expect(harmful).toBeFalsy();
});



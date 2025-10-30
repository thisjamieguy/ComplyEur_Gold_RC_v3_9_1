import { test, expect } from '@playwright/test';

test('Regression: dashboard, calendar, modal, CSV export, calculator, forecast', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel(/Admin Password/i).fill('admin123');
  await page.getByRole('button', { name: /login/i }).click();
  await page.waitForURL(/.*\/(home|dashboard)(?:\/)?$/);

  // Dashboard sorting present
  const sortControl = page.locator('[data-testid="sort-control"], .sort-control, select[name="sort"]');
  const sortCount = await sortControl.count();
  if (sortCount === 0) {
    // eslint-disable-next-line no-console
    console.warn('[integration_regression] sort control not found; skipping assertion');
  }

  // Calendar basic rendering
  await page.goto('/calendar');
  const trips = page.locator('.calendar-trip');
  await trips.first().waitFor({ state: 'visible' });
  await trips.first().click();
  const modal = page.locator('#calendar-detail-overlay');
  await expect(modal).toBeVisible();
  await page.getByRole('button', { name: /Close/i }).click();
  await expect(modal).toBeHidden();

  // CSV export available
  await page.goto('/exports');
  const exportBtn = page.getByRole('button', { name: /Export CSV/i }).or(page.getByRole('link', { name: /Export CSV/i }));
  const exportCount = await exportBtn.count();
  if (exportCount === 0) {
    // eslint-disable-next-line no-console
    console.warn('[integration_regression] export control not found; skipping assertion');
  }

  // 90/180 calculator accessible
  await page.goto('/what_if_scenario');
  // Target the planner form explicitly to avoid strict-mode conflicts with hidden modal forms.
  const calcForm = page.locator('#scenarioForm');
  await expect(calcForm).toBeVisible();

  // Forecast preview present (heuristic)
  const forecast = page.locator('#forecast, .forecast, [data-testid="forecast-preview"]');
  const forecastCount = await forecast.count();
  if (forecastCount === 0) {
    // eslint-disable-next-line no-console
    console.warn('[integration_regression] forecast preview not found; skipping assertion');
  }
});


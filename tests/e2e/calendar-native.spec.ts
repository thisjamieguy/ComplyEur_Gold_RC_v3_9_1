import { test, expect } from '@playwright/test';

const toISO = (date: Date) => date.toISOString().split('T')[0];

test('Calendar renders trips, interactions, and navigation', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel(/Admin Password/i).fill('admin123');
  await page.getByRole('button', { name: /login/i }).click();
  await page.waitForURL(/.*\/(home|dashboard)(?:\/)?$/);

  const employeeName = `Calendar E2E ${Date.now()}`;
  const employee = await page.evaluate(async (name) => {
    const params = new URLSearchParams();
    params.set('name', name);
    const response = await fetch('/add_employee', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: params.toString(),
    });
    return response.json();
  }, employeeName);
  expect(employee?.success).toBeTruthy();
  const employeeId = String(employee.employee_id ?? employee.id);

  const today = new Date();
  const primaryEntry = new Date(today.getFullYear(), today.getMonth(), 1);
  const primaryExit = new Date(today.getFullYear(), today.getMonth(), Math.min(5, new Date(today.getFullYear(), today.getMonth() + 1, 0).getDate()));
  const secondaryEntry = new Date(today.getFullYear(), today.getMonth() + 1, 10);
  const secondaryExit = new Date(today.getFullYear(), today.getMonth() + 1, 24);

  const createTrip = async (form: Record<string, string>) => page.evaluate(async (data) => {
    const params = new URLSearchParams();
    Object.entries(data).forEach(([key, value]) => params.set(key, value));
    const response = await fetch('/add_trip', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: params.toString(),
    });
    return response.json();
  }, form);

  const firstTrip = await createTrip({
    employee_id: employeeId,
    country_code: 'DE',
    entry_date: toISO(primaryEntry),
    exit_date: toISO(primaryExit),
  });
  expect(firstTrip?.success).toBeTruthy();

  const secondTrip = await createTrip({
    employee_id: employeeId,
    country_code: 'FR',
    entry_date: toISO(secondaryEntry),
    exit_date: toISO(secondaryExit),
  });
  expect(secondTrip?.success).toBeTruthy();

  await page.goto('/calendar');
  const rangeLocator = page.locator('#calendar-range-label');
  const trips = page.locator('.calendar-trip');
  const employeeTrips = page.locator(`.calendar-trip[data-employee="${employeeName}"]`);

  await trips.first().waitFor({ state: 'visible' });
  await employeeTrips.first().waitFor({ state: 'visible' });
  const initialRange = (await rangeLocator.textContent())?.trim() ?? '';

  await expect(employeeTrips).toHaveCount(2, { timeout: 10_000 });

  const tooltip = page.locator('.calendar-tooltip');
  await employeeTrips.first().hover();
  await expect(tooltip).toBeVisible();
  await expect(tooltip).toContainText(employeeName);
  await expect(tooltip).toContainText(/DE|Germany/i);

  await employeeTrips.first().click();
  const modal = page.locator('#calendar-detail-overlay');
  await expect(modal).toBeVisible();
  await expect(modal).toContainText('Calendar E2E');
  await expect(modal).toContainText(/Trip to/i);
  await page.getByRole('button', { name: /Close trip details/i }).click();
  await expect(modal).toBeHidden();

  const nextBtn = page.locator('[data-action="next"]');
  await nextBtn.click();
  await expect(rangeLocator).not.toHaveText(initialRange, { timeout: 5000 });

  const todayBtn = page.locator('[data-action="today"]');
  await todayBtn.click();
  await expect(rangeLocator).toHaveText(initialRange, { timeout: 5000 });

  await expect(page.locator('#calendar-today-marker')).toBeVisible();
});

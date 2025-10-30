import { test, expect } from '@playwright/test';

test('Add Trip: country dropdown opens, selects country, and shows border', async ({ page }) => {
  // Login
  await page.goto('/login');
  await page.getByLabel(/Admin Password/i).fill('admin123');
  await page.getByRole('button', { name: /login/i }).click();
  await page.waitForURL(/.*\/(home|dashboard)(?:\/)?$/);

  const employeeName = `E2E Temp ${Date.now()}`;
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
  const employeeId = employee.employee_id ?? employee.id;

  // Go to employee detail
  await page.goto(`/employee/${employeeId}`);

  const countryInput = page.locator('input[name="country_display"]');
  await expect(countryInput).toBeVisible();

  // Check initial border is visible (computed border color/width not none/0)
  const initialBorderWidth = await countryInput.evaluate((el) => getComputedStyle(el).borderTopWidth);
  expect(parseFloat(initialBorderWidth || '0')).toBeGreaterThan(0);

  // Open dropdown and select Spain
  await countryInput.click();
  const list = page.locator('#countryDropdown');
  await expect(list).toBeVisible();
  await page.getByText('Spain (ES)', { exact: false }).click();

  // Input should reflect selection and dropdown should close
  await expect(countryInput).toHaveValue(/Spain|Personal Trip/);
  await expect(list).toBeHidden();
});



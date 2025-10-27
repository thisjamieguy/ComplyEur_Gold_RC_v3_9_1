import { test, expect } from '@playwright/test';

test('Add Trip: country dropdown opens, selects country, and shows border', async ({ page }) => {
  // Login
  await page.goto('/login');
  await page.getByLabel(/Admin Password/i).fill('admin123');
  await page.getByRole('button', { name: /login/i }).click();
  await page.waitForURL('**/dashboard');

  // Create a temp employee via UI-less API sequence if needed
  const empResp = await page.request.post('/add_employee', { form: { name: 'E2E Temp' } });
  const emp = await empResp.json();
  expect(emp.success).toBeTruthy();

  // Go to employee detail
  await page.goto(`/employee/${emp.employee_id}`);

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



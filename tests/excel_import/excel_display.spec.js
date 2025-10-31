/**
 * Excel Import – Display & UI Rendering
 * -------------------------------------
 * After importing data, these tests verify that the dashboard and calendar
 * render correctly. The setup imports a crafted workbook (`display_suite.xlsx`)
 * that produces employees with red/amber/green risk levels so we can check:
 *   • risk badges and status text on the dashboard cards,
 *   • compliance colour coding in the calendar timeline,
 *   • search, filter, and sort behaviour after data is present.
 */

const { test, expect } = require('@playwright/test');
const path = require('path');

const samplesDir = path.join(process.cwd(), 'tests', 'sample_files');
const adminPassword = process.env.ADMIN_PASSWORD ?? 'admin123';

function sample(name) {
  return path.join(samplesDir, name);
}

async function login(page) {
  await page.goto('/login');
  await page.getByLabel(/Admin Password/i).fill(adminPassword);
  await page.getByRole('button', { name: /login/i }).click();
  await page.waitForURL(/(dashboard|home)/);
}

async function resetDatabase(page) {
  await page.goto('/import_excel');
  const status = await page.evaluate(async () => {
    const response = await fetch('/delete_all_data', {
      method: 'POST',
      credentials: 'same-origin',
    });
    return { ok: response.ok, status: response.status };
  });
  if (!status.ok && status.status !== 302) {
    throw new Error(`Failed to reset database (status ${status.status})`);
  }
  await page.waitForTimeout(200);
}

async function importWorkbook(page, fileName) {
  await page.goto('/import_excel');
  await page.getByLabel(/Excel File/i).setInputFiles(sample(fileName));
  await Promise.all([
    page.waitForURL(/import_excel/),
    page.getByRole('button', { name: /upload and process/i }).click(),
  ]);
  await expect(page.locator('text=Import Summary')).toBeVisible();
}

test.describe.serial('Excel Import – Display & UI Rendering', () => {
  test.beforeAll(async ({ browser }) => {
    // Pre-load the display workbook once so subsequent tests can focus on UI behaviour.
    const page = await browser.newPage();
    await login(page);
    await resetDatabase(page);
    await importWorkbook(page, 'display_suite.xlsx');
    await page.close();
  });

  test('dashboard cards reflect risk levels with colour-coded badges', async ({ page }) => {
    await login(page);
    await page.goto('/dashboard');
    await page.getByRole('button', { name: /Card View/ }).click();

    const redCard = page.locator('.card[data-employee-name="Display Red"]');
    await expect(redCard.locator('.status-badge')).toHaveClass(/status-danger/);
    await expect(redCard.locator('.badge')).toContainText(/At Risk/i);

    const amberCard = page.locator('.card[data-employee-name="Display Amber"]');
    await expect(amberCard.locator('.status-badge')).toHaveClass(/status-warning/);
    await expect(amberCard.locator('.badge')).toContainText(/Caution/i);

    const greenCard = page.locator('.card[data-employee-name="Display Green"]');
    await expect(greenCard.locator('.status-badge')).toHaveClass(/status-safe/);
    await expect(greenCard.locator('.badge')).toContainText(/Safe/i);
  });

  test('calendar timeline shows imported trips with compliance labelling', async ({ page }) => {
    await login(page);
    await page.goto('/calendar');

    // Dismiss the welcome modal if it appears (only shown once per browser profile).
    const welcomeClose = page.getByRole('button', { name: /Close/i });
    if (await welcomeClose.isVisible()) {
      await welcomeClose.click();
    }

    const redTrip = page.locator('.calendar-trip[data-employee="Display Red"]').first();
    await redTrip.waitFor({ state: 'visible', timeout: 10_000 });
    await expect(redTrip).toHaveAttribute('data-country', 'DE');
    await expect(redTrip).toHaveAttribute('data-status-label', /approaching 90-day limit/i);

    const amberTrip = page.locator('.calendar-trip[data-employee="Display Amber"]').first();
    await expect(amberTrip).toHaveAttribute('data-country', 'FR');
    await expect(amberTrip).toHaveAttribute('data-status-label', /compliant/i);

    const tooltip = page.locator('.calendar-tooltip');
    await redTrip.hover();
    await expect(tooltip).toBeVisible();
    await expect(tooltip).toContainText('Display Red');
    await expect(tooltip).toContainText(/DE/);
  });

  test('search, filters, and sorting operate correctly after import', async ({ page }) => {
    await login(page);
    await page.goto('/dashboard');

    const searchInput = page.locator('#employeeSearch');
    await searchInput.fill('Display Amber');
    await page.waitForTimeout(400); // debounce window

    const tableRows = page.locator('#employeeTable tbody tr');
    await expect(tableRows.filter({ hasText: 'Display Amber' })).toBeVisible();
    await expect(tableRows.filter({ hasText: 'Display Red' }).first()).toBeHidden();

    await searchInput.fill('');
    await page.waitForTimeout(400);
    await expect(tableRows.filter({ hasText: 'Display Red' })).toBeVisible();

    // Open the filter panel and apply a risk filter.
    await page.getByRole('button', { name: /Filters/i }).click();
    await page.selectOption('#riskFilter', 'red');
    await page.waitForTimeout(200);

    const visibleNames = await tableRows.evaluateAll((rows) =>
      rows
        .filter((row) => row.style.display !== 'none')
        .map((row) => {
          const cell = row.querySelector('td');
          return cell ? cell.textContent.trim() : '';
        })
    );
    expect(visibleNames).toEqual(['Display Red']);
    await expect(page.locator('#resultsCount')).toContainText(/1/);

    // Sorting triggers a full page reload, so wait for the new URL before asserting.
    await page.selectOption('#sortSelect', 'days_used');
    await page.waitForURL(/dashboard.*sort=days_used/);
    const sortedRows = page.locator('#employeeTable tbody tr');
    await expect(sortedRows).toHaveCount(3);
    const firstRowText = (await sortedRows.nth(0).innerText()).trim();
    expect(firstRowText.length).toBeGreaterThan(0);
  });
});

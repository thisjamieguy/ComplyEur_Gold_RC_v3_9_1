/**
 * Excel Import – UI Upload & Error Handling
 * -----------------------------------------
 * These tests log in through the browser, walk through the `/import_excel`
 * workflow, and validate both happy paths and failure scenarios.
 *
 * Key goals:
 *   • ensure .xlsx uploads succeed and show a detailed summary,
 *   • capture legacy .xls guidance, unsupported file rejection, and corruption errors,
 *   • confirm the progress indicator appears for large imports,
 *   • guard against submitting the form with no file selected.
 */

const { test, expect } = require('@playwright/test');
const path = require('path');

// Shared locations for fixtures and credentials so beginners can follow along.
const samplesDir = path.join(process.cwd(), 'tests', 'sample_files');
const adminPassword = process.env.ADMIN_PASSWORD ?? 'admin123';

function sample(name) {
  return path.join(samplesDir, name);
}

// Helper to keep login + reset logic readable.
async function login(page) {
  await page.goto('/login');
  await page.getByLabel(/Admin Password/i).fill(adminPassword);
  await page.getByRole('button', { name: /login/i }).click();
  await page.waitForURL(/(dashboard|home)/);
}

// Reset the database between tests via DSAR "Delete All Data" endpoint.
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
    throw new Error(`Failed to reset database for tests (status ${status.status})`);
  }
  await page.waitForTimeout(200);
}

test.describe.serial('Excel Import – Upload & Reading', () => {
  test('uploads a .xlsx workbook and displays the import summary tiles', async ({ page }) => {
    await login(page);
    await resetDatabase(page);

    await page.getByLabel(/Excel File/i).setInputFiles(sample('basic_valid.xlsx'));
    await Promise.all([
      page.waitForURL(/import_excel/),
      page.getByRole('button', { name: /upload and process/i }).click(),
    ]);

    const summary = page.locator('text=Import Summary');
    await expect(summary).toBeVisible();

    const trips = page.locator('.stat-tile').filter({ hasText: 'Trips Added' }).locator('.stat-value');
    await expect(trips).toHaveText('3');
    const employees = page.locator('.stat-tile').filter({ hasText: 'New Employees' }).locator('.stat-value');
    await expect(employees).toHaveText('3');
  });

  test('explains why legacy .xls files are rejected', async ({ page }) => {
    await login(page);
    await resetDatabase(page);

    await page.getByLabel(/Excel File/i).setInputFiles(sample('basic_valid.xls'));
    await Promise.all([
      page.waitForURL(/import_excel/),
      page.getByRole('button', { name: /upload and process/i }).click(),
    ]);

    const flash = page.locator('.error-message');
    await expect(flash).toBeVisible();
    await expect(flash).toContainText(/does not support the old \.xls file format/i);
  });

  test('blocks unsupported file types before the form submits', async ({ page }) => {
    await login(page);
    await resetDatabase(page);

    await page.getByLabel(/Excel File/i).setInputFiles(sample('unsupported.txt'));
    const preview = page.locator('#filePreview');
    await expect(preview).toBeVisible();
    await expect(preview).toContainText(/file must be one of: xlsx, xls/i);
  });

  test('shows a server-side error when the workbook is corrupted', async ({ page }) => {
    await login(page);
    await resetDatabase(page);

    await page.getByLabel(/Excel File/i).setInputFiles(sample('corrupted.xlsx'));
    await Promise.all([
      page.waitForURL(/import_excel/),
      page.getByRole('button', { name: /upload and process/i }).click(),
    ]);

    const flash = page.locator('.error-message');
    await expect(flash).toBeVisible();
    await expect(flash).toContainText(/import failed|error processing file/i);
  });

  test('displays the progress indicator for long-running uploads', async ({ page }) => {
    await login(page);
    await resetDatabase(page);

    const fileInput = page.getByLabel(/Excel File/i);
    await fileInput.setInputFiles(sample('large_dataset.xlsx'));

    // Track whether the progress container became visible during the request.
    const progressKey = 'excel_progress_seen';
    await page.evaluate((key) => {
      localStorage.removeItem(key);
      const container = document.getElementById('progressContainer');
      if (!container) return;
      if (window.__excelProgressObserver) {
        window.__excelProgressObserver.disconnect();
      }
      window.__excelProgressObserver = new MutationObserver(() => {
        if (getComputedStyle(container).display !== 'none') {
          localStorage.setItem(key, 'true');
        }
      });
      window.__excelProgressObserver.observe(container, {
        attributes: true,
        attributeFilter: ['style', 'class'],
      });
    }, progressKey);

    await page.route('**/import_excel', async (route) => {
      await page.waitForTimeout(500); // allow the loader to render before continuing
      await route.continue();
    });

    const navigation = page.waitForURL(/import_excel/);
    await page.getByRole('button', { name: /upload and process/i }).click();
    await navigation;
    await page.unroute('**/import_excel');

    const progressSeen = await page.evaluate((key) => localStorage.getItem(key) === 'true', progressKey);
    expect(progressSeen).toBeTruthy();
    await page.evaluate((key) => localStorage.removeItem(key), progressKey);

    await expect(page.locator('text=Import Summary')).toBeVisible();
    const employeesProcessed = page.locator('.stat-tile').filter({ hasText: 'Total Names Found' }).locator('.stat-value');
    await expect(employeesProcessed).not.toHaveText('0');
  });

  test('prevents submission when no file is selected', async ({ page }) => {
    await login(page);
    await resetDatabase(page);

    // Removing the "required" attribute simulates a user bypassing client-side validation.
    await page.evaluate(() => document.querySelector('#excelFile').removeAttribute('required'));
    await Promise.all([
      page.waitForURL(/import_excel/),
      page.getByRole('button', { name: /upload and process/i }).click(),
    ]);

    const errorToast = page.getByText(/please select a file/i).first();
    await expect(errorToast).toBeVisible();
  });
});

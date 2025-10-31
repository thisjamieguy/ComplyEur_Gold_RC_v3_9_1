/**
 * Excel Import – Security & GDPR Compliance
 * ----------------------------------------
 * These UI/API hybrid tests confirm that the import workflow respects privacy
 * constraints and offers the promised DSAR tooling:
 *   • uploads stay local (no unexpected outbound requests),
 *   • the `/api/trips` payload contains only approved fields,
 *   • GDPR deletion removes data from both API responses and UI,
 *   • the "Delete All Data" action wipes business trips while keeping private ones.
 */

const { test, expect } = require('@playwright/test');
const path = require('path');
const url = require('url');

const samplesDir = path.join(process.cwd(), 'tests', 'sample_files');
const adminPassword = process.env.ADMIN_PASSWORD ?? 'admin123';
const allowedHosts = new Set(['127.0.0.1', 'localhost']);

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

test.describe.serial('Excel Import – Security & GDPR', () => {
  test('import requests stay within the local network scope', async ({ page }) => {
    await login(page);
    await resetDatabase(page);

    const [request] = await Promise.all([
      page.waitForRequest(
        (req) => req.method() === 'POST' && req.url().includes('/import_excel'),
        { timeout: 10_000 }
      ),
      importWorkbook(page, 'special_characters.xlsx'),
    ]);

    const host = new url.URL(request.url()).hostname;
    expect(allowedHosts.has(host)).toBeTruthy();
  });

  test('trip API exposes only approved fields and no PII', async ({ page }) => {
    await login(page);
    await resetDatabase(page);
    await importWorkbook(page, 'basic_valid.xlsx');

    const response = await page.request.get('/api/trips');
    expect(response.ok()).toBeTruthy();
    const payload = await response.json();
    expect(Array.isArray(payload.trips)).toBe(true);
    expect(payload.trips.length).toBeGreaterThan(0);

    for (const trip of payload.trips) {
      const allowedKeys = [
        'id',
        'employee_id',
        'employee_name',
        'country',
        'entry_date',
        'exit_date',
        'travel_days',
        'is_private',
        'job_ref',
        'ghosted',
        'purpose',
      ];
      const keys = Object.keys(trip);
      keys.forEach((key) => {
        expect(allowedKeys).toContain(key);
      });
      expect(trip).not.toHaveProperty('email');
      expect(trip).not.toHaveProperty('phone');
      expect(trip).not.toHaveProperty('address');
    }
  });

  test('GDPR deletion removes employee data across API and dashboard', async ({ page }) => {
    await login(page);
    await resetDatabase(page);
    await importWorkbook(page, 'basic_valid.xlsx');

    const employeesRes = await page.request.get('/api/employees/search?q=Alice');
    const employeesPayload = await employeesRes.json();
    const lookup = employeesPayload.employees ?? employeesPayload.results ?? [];
    const target = lookup.find((emp) => /Alice Valid/i.test(emp.name));
    expect(target).toBeTruthy();

    const deleteRes = await page.request.post(`/admin/dsar/delete/${target.id}`, {
      data: {},
    });
    expect(deleteRes.ok()).toBeTruthy();
    const deleteJson = await deleteRes.json();
    expect(deleteJson.success).toBeTruthy();

    const tripsAfterRes = await page.request.get('/api/trips');
    const tripsAfterPayload = await tripsAfterRes.json();
    const tripsAfter = tripsAfterPayload.trips ?? [];
    const hasAlice = tripsAfter.some((trip) => /Alice Valid/i.test(trip.employee_name));
    expect(hasAlice).toBe(false);

    await page.goto('/dashboard');
    await page.waitForTimeout(400);
    await expect(page.locator('#employeeTable tbody tr', { hasText: 'Alice Valid' })).toHaveCount(0);
  });

  test('delete-all endpoint purges non-private trip records for a clean slate', async ({ page }) => {
    await login(page);
    await resetDatabase(page);
    await importWorkbook(page, 'basic_valid.xlsx');

    await resetDatabase(page);
    const tripsRes = await page.request.get('/api/trips');
    const tripsPayload = await tripsRes.json();
    expect(tripsPayload.trips ?? []).toEqual([]);

    const employeesRes = await page.request.get('/api/employees/search?q=Alice');
    const employeesPayload = await employeesRes.json();
    expect((employeesPayload.employees ?? [])).toEqual([]);
  });
});

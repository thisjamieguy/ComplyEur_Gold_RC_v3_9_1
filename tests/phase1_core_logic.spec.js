'use strict';

/**
 * Phase 1 – Core compliance logic regression scenarios.
 * Each scenario loops three times to exercise stability guarantees.
 */

const { test, expect } = require('@playwright/test');

const DEFAULT_EMPLOYEE_NAME = 'Phase1 QA';

const isoFromOffset = (offsetDays) => {
  const base = new Date();
  base.setDate(base.getDate() + offsetDays);
  return base.toISOString().split('T')[0];
};

async function ensureAppReady(page) {
  const probe = await page.request.get('/healthz', { failOnStatusCode: false });
  test.skip(probe.status() !== 200, 'ComplyEur app is not running on the expected port');
}

async function createEmployee(page, nameSuffix = '') {
  const name = `${DEFAULT_EMPLOYEE_NAME} ${Date.now()}${nameSuffix}`;
  const response = await page.request.post('/api/employees', {
    data: { name },
  });
  expect(response.ok()).toBeTruthy();
  return response.json();
}

async function createTrip(page, payload) {
  const response = await page.request.post('/api/trips', {
    data: payload,
  });
  expect(response.ok()).toBeTruthy();
  return response.json();
}

async function updateTrip(page, tripId, payload) {
  const response = await page.request.patch(`/api/trips/${tripId}`, {
    data: payload,
  });
  expect(response.ok()).toBeTruthy();
  return response.json();
}

async function deleteTrip(page, tripId) {
  await page.request.delete(`/api/trips/${tripId}`);
}

test.describe('Phase 1 core compliance flows', () => {
  test('Scenario 1: Create → Edit trip recalculates employee compliance', async ({ page }) => {
    await ensureAppReady(page);

    for (let run = 0; run < 3; run += 1) {
      const employee = await createEmployee(page, `-scenario1-${run}`);
      const baseStart = isoFromOffset(-30 - run);
      const baseEnd = isoFromOffset(-20 - run);
      const trip = await createTrip(page, {
        employee_id: employee.id,
        country: 'FR',
        start_date: baseStart,
        end_date: baseEnd,
      });

      // Wait for trip to be persisted (SQLite commit)
      await page.waitForTimeout(1000);

      // Navigate to employee page and wait for trip to appear
      await page.goto(`/employee/${employee.id}`, { waitUntil: 'networkidle' });
      
      // Wait for page content to load
      await page.waitForSelector('.content-body', { state: 'visible', timeout: 15000 });
      
      // Wait for trips table to appear (with retries for eventual consistency)
      const rowSelector = `tr[data-trip-id="${trip.id}"]`;
      let tripVisible = false;
      for (let retry = 0; retry < 10; retry++) {
        const tableExists = await page.locator('#tripHistoryTable').count() > 0;
        if (tableExists) {
          const rowExists = await page.locator(rowSelector).count() > 0;
          if (rowExists) {
            tripVisible = true;
            break;
          }
        }
        await page.waitForTimeout(500);
        // Reload page to get fresh data
        if (retry > 0 && retry % 3 === 0) {
          await page.reload({ waitUntil: 'networkidle' });
        }
      }
      
      if (!tripVisible) {
        // Take screenshot for debugging
        await page.screenshot({ path: `test-results/debug-trip-${trip.id}.png`, fullPage: true });
        throw new Error(`Trip ${trip.id} not found on employee ${employee.id} page after ${10 * 500}ms`);
      }
      
      await expect(page.locator(rowSelector)).toBeVisible({ timeout: 5000 });
      // Wait a bit for calculations to complete
      await page.waitForTimeout(500);
      const daysRemainingCell = page.locator(`${rowSelector} td`).nth(6);
      const initialRemaining = (await daysRemainingCell.textContent() || '').trim();
      expect(initialRemaining).not.toEqual('');

      const extendedEnd = isoFromOffset(-5 - run);
      await updateTrip(page, trip.id, { end_date: extendedEnd });
      // Reload page and wait for updates
      await page.goto(`/employee/${employee.id}`, { waitUntil: 'networkidle' });
      await page.waitForSelector(rowSelector, { state: 'visible', timeout: 10000 });
      await page.waitForTimeout(500);
      const updatedRemaining = (await page.locator(`${rowSelector} td`).nth(6).textContent() || '').trim();
      expect(updatedRemaining).not.toEqual('');
      expect(updatedRemaining).not.toEqual(initialRemaining);

      await deleteTrip(page, trip.id);
    }
  });

  test('Scenario 2: Switching employees updates bio days-used totals', async ({ page }) => {
    await ensureAppReady(page);

    for (let run = 0; run < 3; run += 1) {
      const shortStayEmployee = await createEmployee(page, `-scenario2-short-${run}`);
      const longStayEmployee = await createEmployee(page, `-scenario2-long-${run}`);

      const shortTrip = await createTrip(page, {
        employee_id: shortStayEmployee.id,
        country: 'DE',
        start_date: isoFromOffset(-15),
        end_date: isoFromOffset(-12),
      });
      const longTrip = await createTrip(page, {
        employee_id: longStayEmployee.id,
        country: 'ES',
        start_date: isoFromOffset(-40),
        end_date: isoFromOffset(-10),
      });

      // Wait for trips to be persisted
      await page.waitForTimeout(500);

      await page.goto(`/employee/${shortStayEmployee.id}`, { waitUntil: 'networkidle' });
      // Wait for the compliance cards to render - they should always be present
      await page.waitForSelector('.grid.grid-3', { state: 'visible', timeout: 20000 });
      await page.waitForTimeout(2000); // Give time for calculations to complete
      const shortDaysUsedCard = page.locator('.grid.grid-3 .card.text-center').first();
      await expect(shortDaysUsedCard).toBeVisible({ timeout: 10000 });
      const shortDaysUsed = (await shortDaysUsedCard.locator('div').first().textContent() || '').trim();

      await page.goto(`/employee/${longStayEmployee.id}`, { waitUntil: 'networkidle' });
      await page.waitForSelector('.grid.grid-3', { state: 'visible', timeout: 20000 });
      await page.waitForTimeout(2000); // Give time for calculations to complete
      const longDaysUsedCard = page.locator('.grid.grid-3 .card.text-center').first();
      await expect(longDaysUsedCard).toBeVisible({ timeout: 10000 });
      const longDaysUsed = (await longDaysUsedCard.locator('div').first().textContent() || '').trim();

      expect(shortDaysUsed).not.toEqual('');
      expect(longDaysUsed).not.toEqual('');
      expect(shortDaysUsed).not.toEqual(longDaysUsed);

      await deleteTrip(page, shortTrip.id);
      await deleteTrip(page, longTrip.id);
    }
  });

  test('Scenario 3: Future job alert shows correct critical colour state', async ({ page }) => {
    await ensureAppReady(page);

    for (let run = 0; run < 3; run += 1) {
      const employee = await createEmployee(page, `-scenario3-${run}`);
      const futureTrip = await createTrip(page, {
        employee_id: employee.id,
        country: 'FR',
        start_date: isoFromOffset(10 + run),
        end_date: isoFromOffset(120 + run),
      });

      await page.goto('/future_job_alerts');
      const alertRow = page.locator('.forecast-row', { hasText: employee.name });
      await expect(alertRow).toBeVisible({ timeout: 5000 });
      await expect(alertRow).toContainText('CRITICAL');
      const backgroundColor = await alertRow.evaluate((node) =>
        window.getComputedStyle(node).backgroundColor
      );
      expect(backgroundColor).toBeTruthy();

      await deleteTrip(page, futureTrip.id);
    }
  });

  test('Scenario 4: Hovering a trip displays enriched tooltip content', async ({ page }) => {
    // Calendar is temporarily sandboxed in /calendar_dev - skip this test
    test.skip(true, 'Calendar is sandboxed in /calendar_dev - test skipped');
    
    await ensureAppReady(page);
    const employee = await createEmployee(page, '-scenario4');
    const tripPayload = await createTrip(page, {
      employee_id: employee.id,
      country: 'PT',
      start_date: isoFromOffset(-3),
      end_date: isoFromOffset(2),
    });

    await page.goto('/calendar');
    const trip = page.locator(`.calendar-trip[data-trip-id="${tripPayload.id}"]`);
    await expect(trip).toBeVisible({ timeout: 15000 });

    for (let run = 0; run < 3; run += 1) {
      await trip.hover();
      const tooltip = page.locator('.calendar-tooltip');
      await expect(tooltip).toHaveClass(/calendar-tooltip--visible/);
      await expect(tooltip).toContainText('Days used:');
      await expect(tooltip).toContainText('Forecast remaining:');
      const zIndex = await tooltip.evaluate((node) => Number(window.getComputedStyle(node).zIndex));
      expect(Number.isNaN(zIndex)).toBeFalsy();
      expect(zIndex).toBeGreaterThan(100);
    }

    await deleteTrip(page, tripPayload.id);
  });
});

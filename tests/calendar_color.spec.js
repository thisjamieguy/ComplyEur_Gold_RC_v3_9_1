'use strict';

const { test, expect } = require('@playwright/test');
const { navigateToCalendar } = require('./utils/calendarTestHelpers');

const RISK_SAFE_COLOR = '#4CAF50';
const RISK_CAUTION_COLOR = '#FFC107';
const RISK_CRITICAL_COLOR = '#F44336';

function isoFromOffset(offsetDays) {
  const today = new Date();
  const anchor = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate()));
  anchor.setUTCDate(anchor.getUTCDate() + offsetDays);
  return anchor.toISOString().split('T')[0];
}

function createTrip({ id, employeeId, startOffset, endOffset, country }) {
  const start = isoFromOffset(startOffset);
  const end = isoFromOffset(endOffset);
  const travelDays = Math.max(1, endOffset - startOffset + 1);
  return {
    id,
    employee_id: employeeId,
    employee_name: '',
    country,
    entry_date: start,
    exit_date: end,
    start_date: start,
    end_date: end,
    travel_days: travelDays,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  };
}

async function seedRiskFixture(page) {
  const employees = [
    { id: 401, name: 'Safe Sample', active: true },
    { id: 402, name: 'Caution Sample', active: true },
    { id: 403, name: 'Critical Sample', active: true }
  ];

  const trips = [
    createTrip({ id: 9001, employeeId: 401, startOffset: -15, endOffset: -12, country: 'Czechia' }),
    createTrip({ id: 9002, employeeId: 402, startOffset: -70, endOffset: -10, country: 'Germany' }),
    createTrip({ id: 9003, employeeId: 403, startOffset: -95, endOffset: -5, country: 'France' }),
    createTrip({ id: 9004, employeeId: 403, startOffset: -30, endOffset: -5, country: 'Italy' })
  ];

  const payload = {
    employees,
    trips,
    generated_at: new Date().toISOString()
  };

  await page.evaluate((data) => {
    const calendarRoot = document.getElementById('calendar');
    const controller = calendarRoot && calendarRoot.__calendarController;
    if (!controller) {
      throw new Error('Calendar controller unavailable for risk fixtures.');
    }
    controller.hydrateFromPayload(data, { centerOnToday: true });
  }, payload);

  await page.waitForTimeout(300);
}

function getTripFor(page, employeeName) {
  return page.locator(`.calendar-trip[data-employee="${employeeName}"]`).first();
}

function getCellFor(page, employeeName) {
  return page.locator(`.calendar-cell[data-employee-name="${employeeName}"]`).first();
}

async function measureFps(page, sampleSize = 32) {
  return page.evaluate(async (frames) => new Promise((resolve) => {
    const marks = [];
    function loop(timestamp) {
      marks.push(timestamp);
      if (marks.length >= frames) {
        let total = 0;
        for (let index = 1; index < marks.length; index += 1) {
          total += marks[index] - marks[index - 1];
        }
        const averageFrame = total / (marks.length - 1);
        const fps = 1000 / averageFrame;
        resolve(fps);
        return;
      }
      requestAnimationFrame(loop);
    }
    requestAnimationFrame(loop);
  }), sampleSize);
}

test.describe('Calendar risk colours', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToCalendar(page);
    await seedRiskFixture(page);
  });

  test('applies safe/caution/critical colours to trips', async ({ page }) => {
    const safeTrip = getTripFor(page, 'Safe Sample');
    const cautionTrip = getTripFor(page, 'Caution Sample');
    const criticalTrip = getTripFor(page, 'Critical Sample');

    await expect(safeTrip).toBeVisible();
    await expect(cautionTrip).toBeVisible();
    await expect(criticalTrip).toBeVisible();

    await expect(safeTrip).toHaveAttribute('data-risk-level', 'safe');
    await expect(cautionTrip).toHaveAttribute('data-risk-level', 'caution');
    await expect(criticalTrip).toHaveAttribute('data-risk-level', 'critical');

    await expect(safeTrip).toHaveAttribute('data-risk-color', RISK_SAFE_COLOR);
    await expect(cautionTrip).toHaveAttribute('data-risk-color', RISK_CAUTION_COLOR);
    await expect(criticalTrip).toHaveAttribute('data-risk-color', RISK_CRITICAL_COLOR);
  });

  test('displays risk tooltip with day usage on hover', async ({ page }) => {
    const safeCell = getCellFor(page, 'Safe Sample').nth(5);
    await safeCell.hover();
    const tooltip = page.locator('.calendar-tooltip');
    await expect(tooltip).toHaveClass(/calendar-tooltip--visible/);
    await expect(tooltip).toContainText('Days used:');
    await expect(tooltip).toContainText('/ 90');
  });

  test('maintains drag behaviour after colour coding', async ({ page }) => {
    const trip = getTripFor(page, 'Safe Sample');
    const initialStart = await trip.getAttribute('data-start');
    const box = await trip.boundingBox();
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
    await page.mouse.down();
    await page.mouse.move(box.x + box.width / 2 + 56, box.y + box.height / 2, { steps: 10 });
    await page.mouse.up();
    await page.waitForTimeout(200);
    const updatedStart = await trip.getAttribute('data-start');
    expect(updatedStart).not.toBe(initialStart);
  });

  test('sustains 55+ FPS while idle', async ({ page }) => {
    const fps = await measureFps(page, 28);
    expect(fps).toBeGreaterThan(55);
  });
});

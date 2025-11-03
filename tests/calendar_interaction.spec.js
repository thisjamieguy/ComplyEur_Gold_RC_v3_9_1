'use strict';

/**
 * Phase 3.6.2 — Interaction QA suite
 * Exercises resize, time-range zoom, and sequential selection workflows.
 */

const { test, expect } = require('@playwright/test');
const { navigateToCalendar } = require('./utils/calendarTestHelpers');

async function bootstrapCalendar(page) {
  const consoleErrors = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
  });

  await navigateToCalendar(page);
  return { consoleErrors };
}

test('QA-CI-01 Resizing viewport keeps today marker aligned', async ({ page }) => {
  await bootstrapCalendar(page);

  const headerMarker = page.locator('#calendar-today-marker');
  const bodyMarker = page.locator('#calendar-today-marker-body');
  const hasMarker = await headerMarker.count();

  const viewports = [
    { width: 1440, height: 900 },
    { width: 1180, height: 900 },
    { width: 900, height: 900 },
  ];

  for (const size of viewports) {
    await page.setViewportSize(size);
    await page.waitForTimeout(120);
    if (!hasMarker) {
      continue;
    }
    const headerBox = await headerMarker.boundingBox();
    const bodyBox = await bodyMarker.boundingBox();
    if (!headerBox || !bodyBox) {
      continue;
    }
    expect(Math.abs(headerBox.x - bodyBox.x)).toBeLessThan(1.5);
  }
});

test('QA-CI-02 Future weeks selector expands range without misalignment', async ({ page }) => {
  const { consoleErrors } = await bootstrapCalendar(page);

  const timelineWidthBefore = await page.evaluate(() => document.querySelector('#calendar-grid').scrollWidth);
  await page.locator('#calendar-future-weeks').selectOption('10');
  await page.waitForTimeout(400);

  const { gridWidth, headerWidth } = await page.evaluate(() => ({
    gridWidth: document.querySelector('#calendar-grid').scrollWidth,
    headerWidth: document.querySelector('#calendar-month-row').scrollWidth,
  }));

  expect(gridWidth).toBeGreaterThan(timelineWidthBefore);
  expect(Math.abs(gridWidth - headerWidth)).toBeLessThanOrEqual(28);
  expect(consoleErrors).toStrictEqual([]);
});

test('QA-CI-03 Sequential trip selection preserves detail accuracy', async ({ page }) => {
  await bootstrapCalendar(page);

  const detailOverlay = page.locator('#calendar-detail-overlay');
  const detailEmployee = page.locator('#calendar-detail-employee');
  const detailCountry = page.locator('#calendar-detail-country');

  const firstTrip = page.locator('.calendar-trip').first();
  const firstTripData = await firstTrip.evaluate((node) => ({
    employee: node.getAttribute('data-employee') || '',
    country: node.getAttribute('data-country') || '',
  }));
  await firstTrip.click();
  await expect(detailOverlay).toBeVisible({ timeout: 5000 });
  const firstEmployee = (await detailEmployee.textContent())?.trim();
  const firstCountry = (await detailCountry.textContent())?.trim();
  expect(firstEmployee).toBeTruthy();
  expect(firstCountry).toBeTruthy();
  expect(firstEmployee).toContain(firstTripData.employee);
  expect(firstCountry).toContain(firstTripData.country);
  await page.locator('[data-action="close-detail"]').click();
  await expect(detailOverlay).toBeHidden({ timeout: 5000 });

  const secondTrip = page.locator('.calendar-trip').nth(1);
  const secondTripData = await secondTrip.evaluate((node) => ({
    employee: node.getAttribute('data-employee') || '',
    country: node.getAttribute('data-country') || '',
    start: node.getAttribute('data-start') || '',
    end: node.getAttribute('data-end') || '',
  }));
  await secondTrip.click();
  await expect(detailOverlay).toBeVisible({ timeout: 5000 });
  const secondEmployee = (await detailEmployee.textContent())?.trim();
  const secondCountry = (await detailCountry.textContent())?.trim();
  const secondDates = (await page.locator('#calendar-detail-dates').textContent())?.trim();
  expect(secondEmployee).toBeTruthy();
  expect(secondCountry).toBeTruthy();
  expect(secondEmployee).toContain(secondTripData.employee);
  expect(secondCountry).toContain(secondTripData.country);
  expect(secondDates).toContain(secondTripData.start);
  expect(secondDates).toContain(secondTripData.end);
  await page.keyboard.press('Escape');
  await expect(detailOverlay).toBeHidden({ timeout: 5000 });
});

test.describe('visual validation', () => {
  test.skip(process.env.CALENDAR_VISUAL_SNAPSHOTS !== '1', 'Enable CALENDAR_VISUAL_SNAPSHOTS=1 to capture baseline screenshots');

  test('QA-CI-04 Shell layout visual snapshot after resize', async ({ page }) => {
    await bootstrapCalendar(page);
    await page.setViewportSize({ width: 1024, height: 900 });
    await page.waitForTimeout(200);
    await page.addStyleTag({
      content: '* { transition-duration: 0s !important; animation-duration: 0s !important; }',
    });
    await expect(page.locator('#calendar')).toHaveScreenshot('calendar-shell-responsive.png', {
      animations: 'disabled',
      maxDiffPixelRatio: 0.02,
    });
  });
});

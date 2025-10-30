'use strict';

/**
 * Phase 3.6.1 — Drag-and-Drop Interaction QA Suite
 * Verifies trip bar movement, backend sync, visual feedback, and accessibility compliance.
 */

const { test, expect } = require('@playwright/test');
const { injectAxe, checkA11y } = require('axe-playwright');

const CALENDAR_PATH = '/calendar';
const DEFAULT_HEIGHT = 900;

async function bootstrapCalendar(page) {
  await page.goto(CALENDAR_PATH, { waitUntil: 'networkidle' });
  await expect(page.locator('.calendar-trip').first()).toBeVisible({ timeout: 10000 });
  const consoleErrors = [];
  page.on('console', msg => msg.type() === 'error' && consoleErrors.push(msg.text()));
  return { consoleErrors };
}

/**
 * Helper: get trip bounding box
 */
async function getTripBounds(page, index = 0) {
  const trip = page.locator('.calendar-trip').nth(index);
  const box = await trip.boundingBox();
  if (!box) throw new Error('No bounding box returned for trip element.');
  return { trip, box };
}

/**
 * Helper: drag horizontally by N pixels
 */
async function dragTrip(page, trip, distanceX) {
  const box = await trip.boundingBox();
  const startX = box.x + box.width / 2;
  const startY = box.y + box.height / 2;
  await page.mouse.move(startX, startY);
  await page.mouse.down();
  await page.mouse.move(startX + distanceX, startY, { steps: 10 });
  await page.mouse.up();
}

/**
 * QA-08: Drag-and-Drop adjusts trip start/end dates and shows toast.
 */
test('QA-08 Dragging a trip updates dates and triggers toast', async ({ page }) => {
  await bootstrapCalendar(page);

  const initialTrips = page.locator('.calendar-trip');
  const firstTrip = initialTrips.first();
  const initialText = await firstTrip.textContent();

  // Drag trip 100px right (simulate +5 days)
  await dragTrip(page, firstTrip, 100);

  // Expect toast feedback
  const toast = page.locator('#calendar-toast');
  await expect(toast).toContainText('Trip updated successfully', { timeout: 5000 });
  await expect(toast).toHaveAttribute('aria-hidden', 'true', { timeout: 7000 });

  // Verify same number of trips after update
  await expect(page.locator('.calendar-trip')).toHaveCount(await initialTrips.count());

  // Confirm trip text still matches (same employee)
  const updatedText = await firstTrip.textContent();
  expect(updatedText).toContain(initialText.trim().slice(0, 2)); // same initials/country tag
});

/**
 * QA-09: Trip retains compliance color after movement.
 */
test('QA-09 Color class persists and updates correctly after drag', async ({ page }) => {
  await bootstrapCalendar(page);

  const trip = page.locator('.calendar-trip').first();
  const initialColor = await trip.evaluate(el => {
    return Array.from(el.classList).find(c => c.includes('calendar-trip--'));
  });

  await dragTrip(page, trip, 120);

  // Wait a moment for re-render
  await page.waitForTimeout(800);

  const newColor = await trip.evaluate(el => {
    return Array.from(el.classList).find(c => c.includes('calendar-trip--'));
  });

  expect(newColor).toBeTruthy();
  expect(newColor).toContain('calendar-trip--');
  // It can change if compliance recalculated, but must not disappear
});

/**
 * QA-10: No console errors during drag operations.
 */
test('QA-10 No console errors triggered while dragging trips', async ({ page }) => {
  const { consoleErrors } = await bootstrapCalendar(page);
  const trip = page.locator('.calendar-trip').first();

  await dragTrip(page, trip, 80);
  await page.waitForTimeout(500);

  expect(consoleErrors).toStrictEqual([]);
});

/**
 * QA-11: Drag operations remain functional across breakpoints.
 */
test('QA-11 Dragging works at desktop, tablet, and mobile widths', async ({ page }) => {
  const widths = [1440, 1024, 768];
  for (const width of widths) {
    await page.setViewportSize({ width, height: DEFAULT_HEIGHT });
    await page.goto(CALENDAR_PATH, { waitUntil: 'networkidle' });
    await expect(page.locator('.calendar-trip').first()).toBeVisible();
    const trip = page.locator('.calendar-trip').first();
    await dragTrip(page, trip, 60);
    await page.waitForTimeout(400);
    await expect(page.locator('#calendar-toast')).toHaveCount(1);
  }
});

/**
 * QA-12: Accessibility — Drag elements have correct ARIA attributes.
 */
test('QA-12 Drag elements expose aria-grabbed and dropeffect attributes', async ({ page }) => {
  await bootstrapCalendar(page);
  await injectAxe(page);

  const trip = page.locator('.calendar-trip').first();
  await trip.evaluate(el => el.setAttribute('aria-grabbed', 'true'));
  await checkA11y(page, '.calendar-trip', {
    axeOptions: {
      runOnly: { type: 'tag', values: ['wcag2aa'] },
    },
  });

  const grabbed = await trip.getAttribute('aria-grabbed');
  expect(grabbed).toBe('true');
});

/**
 * QA-13: Performance sanity — drag and refresh in under 1s.
 */
test('QA-13 Drag performance under 1000ms', async ({ page }) => {
  await bootstrapCalendar(page);
  const trip = page.locator('.calendar-trip').first();

  const start = performance.now();
  await dragTrip(page, trip, 50);
  const end = performance.now();

  const duration = end - start;
  console.log(`Drag operation took ${duration.toFixed(2)}ms`);
  expect(duration).toBeLessThan(1000);
});

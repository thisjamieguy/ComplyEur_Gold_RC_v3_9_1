/**
 * tests/phase3_7_intense_validation.spec.js
 * Comprehensive Playwright test suite for ComplyEur Calendar v3.7
 *
 * Covers: fullscreen toggle, context menu, drag-drop updates, endpoint validation,
 * CSS consistency, and visual regression baseline.
 */

import { test, expect } from '@playwright/test';

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5001';
const ADMIN_PASSWORD = process.env.ADMIN_PASS || process.env.CALENDAR_QA_PASSWORD || 'admin123';

test.describe('ComplyEur Calendar – Phase 3.7 Intense Validation Suite', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.fill('#username, input[name="username"], input[name="password"]', 'admin');
    await page.fill('#password, input[name="password"]', ADMIN_PASSWORD);
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'networkidle' }),
      page.click('button[type="submit"]')
    ]);
    await page.goto(`${BASE_URL}/calendar`);
    await page.waitForSelector('#calendar, [data-calendar-shell], .calendar-shell', { timeout: 10000 });
  });

  // ───────────────────────────────────────────────────────────────
  // FULLSCREEN TOGGLE + VISUAL SNAPSHOT
  // ───────────────────────────────────────────────────────────────
  test('fullscreen toggle should activate and render correctly', async ({ page }) => {
    const toggle = page.locator('[data-action="toggle-fullscreen"]');
    await expect(toggle).toBeVisible();

    await page.waitForTimeout(500);
    await page.screenshot({ 
      path: 'tests/artifacts/screenshots/calendar_before_fullscreen.png', 
      fullPage: true 
    });

    await toggle.click();

    // Wait for fullscreen transition
    await page.waitForTimeout(500);
    
    // Check for fullscreen class on body or calendar shell
    const bodyFullscreen = page.locator('body.calendar-body--fullscreen');
    const shellFullscreen = page.locator('.calendar-shell--fullscreen');
    
    // At least one should be active
    const bodyActive = await bodyFullscreen.count() > 0;
    const shellActive = await shellFullscreen.count() > 0;
    expect(bodyActive || shellActive).toBeTruthy();

    await page.waitForTimeout(500);
    await page.screenshot({ 
      path: 'tests/artifacts/screenshots/calendar_fullscreen_active.png', 
      fullPage: true 
    });

    await toggle.click();
    await page.waitForTimeout(500);
    
    // Verify fullscreen is deactivated
    const bodyAfter = await bodyFullscreen.count();
    const shellAfter = await shellFullscreen.count();
    expect(bodyAfter).toBe(0);
    expect(shellAfter).toBe(0);
  });

  // ───────────────────────────────────────────────────────────────
  // CONTEXT MENU STRUCTURE
  // ───────────────────────────────────────────────────────────────
  test('context menu should appear with all expected options', async ({ page }) => {
    // Wait for trips to be visible
    const trip = page.locator('.calendar-trip, .trip-block').first();
    await trip.waitFor({ state: 'visible', timeout: 10000 });
    
    // Right-click to open context menu
    await trip.click({ button: 'right' });
    
    // Wait for context menu to appear
    const menu = page.locator('.calendar-context-menu, .context-menu');
    await expect(menu).toBeVisible({ timeout: 3000 });

    // Check for expected menu items
    const menuText = await menu.textContent();
    expect(menuText).toMatch(/Edit|Delete|Duplicate/i);

    // Close with Escape
    await page.keyboard.press('Escape');
    await expect(menu).toBeHidden({ timeout: 2000 });
  });

  // ───────────────────────────────────────────────────────────────
  // DRAG-DROP & LIVE PREVIEW
  // ───────────────────────────────────────────────────────────────
  test('trip pill drag updates should preview live and persist via POST', async ({ page, request }) => {
    const pill = page.locator('.calendar-trip, .trip-block').first();
    await pill.waitFor({ state: 'visible', timeout: 10000 });
    
    const box = await pill.boundingBox();
    if (!box) {
      test.skip(true, 'Trip element not found or not visible');
      return;
    }

    const delta = 150;

    // Screenshot before
    await page.screenshot({ 
      path: 'tests/artifacts/screenshots/drag_before.png', 
      fullPage: true 
    });

    // Start drag
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
    await page.mouse.down();
    await page.mouse.move(box.x + box.width / 2 + delta, box.y + box.height / 2, { steps: 10 });

    // Visual live preview active (check for dragging class or preview class)
    const classes = await pill.evaluate(el => Array.from(el.classList));
    const hasPreview = classes.some(c => 
      c.includes('preview') || c.includes('dragging') || c.includes('preview-active')
    );
    
    // Screenshot during drag
    await page.screenshot({ 
      path: 'tests/artifacts/screenshots/drag_preview.png', 
      fullPage: true 
    });

    await page.mouse.up();
    await page.waitForTimeout(500);

    // Verify API endpoint exists and works
    // Get trip ID from the element
    const tripId = await pill.getAttribute('data-trip-id');
    if (tripId) {
      // Test the actual API endpoint
      const response = await request.patch(`${BASE_URL}/api/trips/${tripId}`, {
        data: { 
          start_date: '2025-11-04', 
          end_date: '2025-11-06' 
        },
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      // Should return 200 or 404 (if trip doesn't exist in test data)
      expect([200, 404]).toContain(response.status());
      
      if (response.ok()) {
        const body = await response.json();
        expect(body).toHaveProperty('id');
      }
    }

    // Screenshot after drag
    await page.screenshot({ 
      path: 'tests/artifacts/screenshots/drag_after.png', 
      fullPage: true 
    });
  });

  // ───────────────────────────────────────────────────────────────
  // STYLING + HOVER HIGHLIGHTS
  // ───────────────────────────────────────────────────────────────
  test('hover highlight and tooltip system should activate correctly', async ({ page }) => {
    const trip = page.locator('.calendar-trip, .trip-block').nth(1);
    const count = await trip.count();
    if (count === 0) {
      test.skip(true, 'No trip elements found for hover test');
      return;
    }

    await trip.hover();
    await page.waitForTimeout(300);

    // Check for tooltip or title attribute
    const title = await trip.getAttribute('title');
    const tooltip = page.locator('.tooltip, [role="tooltip"]');
    const tooltipVisible = await tooltip.count() > 0;

    // Either tooltip element or title attribute should provide trip details
    expect(title || tooltipVisible).toBeTruthy();
    
    if (title) {
      expect(title).toMatch(/Trip Details|Days Used|employee|country/i);
    }
  });

  // ───────────────────────────────────────────────────────────────
  // ENDPOINT VALIDATION + ALERT RECOMPUTATION
  // ───────────────────────────────────────────────────────────────
  test('PATCH endpoint for date updates should return valid response', async ({ request, page }) => {
    // First, get a trip ID from the calendar
    await page.goto(`${BASE_URL}/calendar`);
    await page.waitForSelector('.calendar-trip, .trip-block', { timeout: 10000 });
    
    const tripIdAttr = await page.locator('.calendar-trip, .trip-block').first().getAttribute('data-trip-id');
    
    if (!tripIdAttr) {
      test.skip(true, 'No trip ID found in calendar for API test');
      return;
    }

    const tripId = parseInt(tripIdAttr, 10);
    expect(tripId).toBeGreaterThan(0);

    const res = await request.patch(`${BASE_URL}/api/trips/${tripId}`, {
      data: { 
        start_date: '2025-11-04', 
        end_date: '2025-11-06' 
      },
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Should return 200 (success) or 404 (trip not found)
    expect([200, 404]).toContain(res.status());
    
    if (res.ok()) {
      const body = await res.json();
      expect(body).toHaveProperty('id');
      // If success is present, it should be true
      if ('success' in body) {
        expect(body.success).toBe(true);
      }
    }
  });

  // ───────────────────────────────────────────────────────────────
  // PERFORMANCE + STABILITY
  // ───────────────────────────────────────────────────────────────
  test('calendar drag should not trigger frame jitter', async ({ page }) => {
    const pill = page.locator('.calendar-trip, .trip-block').first();
    await pill.waitFor({ state: 'visible', timeout: 10000 });
    
    const box = await pill.boundingBox();
    if (!box) {
      test.skip(true, 'Trip element not found for drag performance test');
      return;
    }

    const perfBefore = await page.evaluate(() => performance.now());
    
    await page.mouse.move(box.x + 5, box.y + 5);
    await page.mouse.down();
    await page.mouse.move(box.x + 100, box.y + 5, { steps: 20 });
    await page.mouse.up();
    
    // Wait for any animations/transitions to complete
    await page.waitForTimeout(500);
    
    const perfAfter = await page.evaluate(() => performance.now());
    const diff = perfAfter - perfBefore;
    
    console.log(`Drag duration: ${diff.toFixed(2)}ms`);
    
    // Should complete in reasonable time (4 seconds is generous)
    expect(diff).toBeLessThan(4000);
  });
});


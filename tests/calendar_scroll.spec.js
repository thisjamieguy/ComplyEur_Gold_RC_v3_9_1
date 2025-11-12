'use strict';

/**
 * Phase 3.6.2 — Scroll & Alignment QA suite
 * Validates scroll listener hygiene, header/body synchronisation, and large dataset behaviour.
 */

const { test, expect } = require('@playwright/test');
const { navigateToCalendar } = require('./utils/calendarTestHelpers');

const DAY_WIDTH = 28;

async function bootstrapCalendar(page, { instrumentListeners = false } = {}) {
  const consoleErrors = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
  });

  if (instrumentListeners) {
    await page.addInitScript(() => {
      const log = [];
      const original = EventTarget.prototype.addEventListener;
      EventTarget.prototype.addEventListener = function patched(type, listener, options) {
        let target = 'EventTarget';
        if (this instanceof Element) {
          const id = this.id ? `#${this.id}` : '';
          const className = this.className && typeof this.className === 'string'
            ? this.className.split(' ').filter(Boolean)[0] || ''
            : '';
          target = `${this.tagName.toLowerCase()}${id || (className ? `.${className}` : '')}`;
        } else if (this && this.constructor && this.constructor.name) {
          target = this.constructor.name;
        }
        log.push({ target, type });
        return original.call(this, type, listener, options);
      };
      window.__listenerLog = log;
    });
  }

  await navigateToCalendar(page);
  return { consoleErrors };
}

async function loadHeavyFixture(page, { employees = 60, tripsPerEmployee = 4 } = {}) {
  await page.evaluate(({ employees, tripsPerEmployee }) => {
    const root = document.getElementById('calendar');
    const controller = root && root.__calendarController;
    if (!controller) {
      throw new Error('Calendar controller not initialised');
    }
    const base = new Date();
    base.setUTCHours(0, 0, 0, 0);
    const employeesList = [];
    const trips = [];
    const countries = ['DE', 'FR', 'ES', 'IT', 'NL', 'PL', 'PT', 'IE'];
    let tripId = 1;

    const serialise = (date) => {
      const copy = new Date(date.getTime());
      copy.setUTCHours(0, 0, 0, 0);
      return copy.toISOString().split('T')[0];
    };

    for (let index = 0; index < employees; index += 1) {
      const id = index + 1;
      const name = `Employee ${String(id).padStart(2, '0')}`;
      employeesList.push({ id, name, active: true });

      for (let tripIndex = 0; tripIndex < tripsPerEmployee; tripIndex += 1) {
        const start = new Date(base);
        start.setUTCDate(start.getUTCDate() - 90 + (index * 2) + (tripIndex * 6));
        const end = new Date(start);
        end.setUTCDate(end.getUTCDate() + 5);
        trips.push({
          id: tripId++,
          employee_id: id,
          employee_name: name,
          country: countries[(index + tripIndex) % countries.length],
          start_date: serialise(start),
          end_date: serialise(end),
          travel_days: 6,
        });
      }
    }

    controller.hydrateFromPayload(
      {
        employees: employeesList,
        trips,
        generated_at: new Date().toISOString(),
      },
      { centerOnToday: false }
    );
  }, { employees, tripsPerEmployee });

  // Allow the incremental renderer to settle.
  await page.waitForTimeout(400);
}

test('QA-SC-01 Calendar attaches minimal scroll listeners', async ({ page }) => {
  await bootstrapCalendar(page, { instrumentListeners: true });
  const listenerLog = await page.evaluate(() => window.__listenerLog || []);

  const timelineScrollListeners = listenerLog.filter(
    (entry) => entry.type === 'scroll' && entry.target.includes('calendar-timeline')
  ).length;
  const employeeScrollListeners = listenerLog.filter(
    (entry) => entry.type === 'scroll' && entry.target.includes('calendar-employee-list')
  ).length;

  expect(timelineScrollListeners).toBeLessThanOrEqual(2);
  expect(employeeScrollListeners).toBeLessThanOrEqual(1);
});

test('QA-SC-02 Horizontal scroll keeps header aligned within 1px', async ({ page }) => {
  await bootstrapCalendar(page);

  const scrollAmount = DAY_WIDTH * 12;
  const timeline = page.locator('.calendar-timeline');
  await timeline.evaluate((node) => { node.scrollLeft = 0; });
  await timeline.evaluate((node, value) => { node.scrollLeft = value; }, scrollAmount);
  await page.waitForTimeout(50);

  const alignment = await page.evaluate(() => {
    const header = document.querySelector('#calendar-month-row');
    const dayRow = document.querySelector('#calendar-day-row');
    const container = document.querySelector('.calendar-timeline');
    const extract = (element) => {
      const value = getComputedStyle(element).transform;
      if (!value || value === 'none') {
        return 0;
      }
      const matrix = new DOMMatrixReadOnly(value);
      return matrix.m41;
    };
    return {
      header: extract(header),
      day: extract(dayRow),
      scrollLeft: container.scrollLeft,
    };
  });

  expect(Math.abs(alignment.header + alignment.scrollLeft)).toBeLessThan(1);
  expect(Math.abs(alignment.day + alignment.scrollLeft)).toBeLessThan(1);

  const maxMisalignment = await page.evaluate(async () => {
    const header = document.querySelector('#calendar-month-row');
    const container = document.querySelector('.calendar-timeline');
    const compute = (element) => {
      const value = getComputedStyle(element).transform;
      if (!value || value === 'none') {
        return 0;
      }
      const matrix = new DOMMatrixReadOnly(value);
      return matrix.m41;
    };
    const deltas = [];
    for (let step = 0; step < 6; step += 1) {
      container.scrollLeft += 40;
      // eslint-disable-next-line no-await-in-loop
      await new Promise((resolve) => requestAnimationFrame(resolve));
      deltas.push(Math.abs(compute(header) + container.scrollLeft));
    }
    return Math.max(...deltas);
  });

  expect(maxMisalignment).toBeLessThan(1.5);
});

test('QA-SC-03 Vertical scroll stays synchronised', async ({ page }) => {
  await bootstrapCalendar(page);

  const timeline = page.locator('.calendar-timeline');
  const employees = page.locator('#calendar-employee-list');

  await timeline.evaluate((node) => { node.scrollTop = 220; });
  await page.waitForTimeout(40);
  let positions = await page.evaluate(() => ({
    timeline: document.querySelector('.calendar-timeline').scrollTop,
    employees: document.querySelector('#calendar-employee-list').scrollTop,
  }));
  expect(Math.abs(positions.timeline - positions.employees)).toBeLessThanOrEqual(1);

  await employees.evaluate((node) => { node.scrollTop = 360; });
  await page.waitForTimeout(40);
  positions = await page.evaluate(() => ({
    timeline: document.querySelector('.calendar-timeline').scrollTop,
    employees: document.querySelector('#calendar-employee-list').scrollTop,
  }));
  expect(Math.abs(positions.timeline - positions.employees)).toBeLessThanOrEqual(1);
});

test('QA-SC-04 Large dataset preserves alignment and responsiveness', async ({ page }) => {
  const { consoleErrors } = await bootstrapCalendar(page);
  await loadHeavyFixture(page, { employees: 60, tripsPerEmployee: 4 });

  const rowCount = await page.locator('.calendar-grid-row').count();
  expect(rowCount).toBeGreaterThanOrEqual(50);

  const widthCheck = await page.evaluate(() => {
    const gridWidth = document.querySelector('#calendar-grid').scrollWidth;
    const headerWidth = document.querySelector('#calendar-month-row').scrollWidth;
    const tripCount = document.querySelectorAll('.calendar-trip').length;
    return { gridWidth, headerWidth, tripCount };
  });

  expect(widthCheck.gridWidth).toBeGreaterThan(0);
  expect(Math.abs(widthCheck.gridWidth - widthCheck.headerWidth)).toBeLessThanOrEqual(DAY_WIDTH);
  expect(widthCheck.tripCount).toBeGreaterThanOrEqual(200);

  const scrollCost = await page.evaluate(() => {
    const container = document.querySelector('.calendar-timeline');
    const start = performance.now();
    for (let i = 0; i < 6; i += 1) {
      container.scrollLeft += 160;
    }
    return performance.now() - start;
  });
  expect(scrollCost).toBeLessThan(120);
  expect(consoleErrors).toStrictEqual([]);
});

test.describe('visual validation', () => {
  test.skip(process.env.CALENDAR_VISUAL_SNAPSHOTS !== '1', 'Enable CALENDAR_VISUAL_SNAPSHOTS=1 to capture baseline screenshots');

  test('QA-SC-05 Timeline header visual snapshot', async ({ page }) => {
    await bootstrapCalendar(page);
    await page.addStyleTag({
      content: '* { transition-duration: 0s !important; animation-duration: 0s !important; }',
    });
    await expect(page.locator('.calendar-timeline-header')).toHaveScreenshot('calendar-timeline-header.png', {
      animations: 'disabled',
      maxDiffPixelRatio: 0.02,
    });
  });
});

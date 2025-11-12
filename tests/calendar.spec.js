'use strict';

const { test, expect } = require('@playwright/test');
const { injectAxe, checkA11y } = require('axe-playwright');

const CALENDAR_PATH = '/calendar';
const USE_FIXTURES = process.env.CALENDAR_QA_USE_FIXTURES !== '0';
const DEFAULT_HEIGHT = 900;
const ADMIN_PASSWORD = process.env.CALENDAR_QA_PASSWORD || 'admin123';

function isoFromOffset(offsetDays) {
  const today = new Date();
  const anchor = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate()));
  anchor.setUTCDate(anchor.getUTCDate() + offsetDays);
  return anchor.toISOString().split('T')[0];
}

function inclusiveDayCount(startIso, endIso) {
  const start = new Date(`${startIso}T00:00:00Z`);
  const end = new Date(`${endIso}T00:00:00Z`);
  const diff = Math.round((end.getTime() - start.getTime()) / 86_400_000);
  return diff >= 0 ? diff + 1 : 1;
}

function addDaysToIso(iso, days) {
  if (!iso) return iso;
  const date = new Date(`${iso}T00:00:00Z`);
  if (Number.isNaN(date.getTime())) return iso;
  date.setUTCDate(date.getUTCDate() + days);
  return date.toISOString().split('T')[0];
}

function buildFixtureDataset() {
  const employees = [
    { id: 101, name: 'Alice Anders', active: true },
    { id: 102, name: 'Benoit Blanc', active: true },
    { id: 103, name: 'Carmen Diaz', active: true },
  ];

  const trips = [
    createTrip({
      id: 701,
      employee: employees[0],
      country: 'France',
      startOffset: -20,
      endOffset: -14,
    }),
    createTrip({
      id: 702,
      employee: employees[1],
      country: 'Italy',
      startOffset: -95,
      endOffset: -15,
    }),
    createTrip({
      id: 703,
      employee: employees[2],
      country: 'Spain',
      startOffset: -160,
      endOffset: -50,
    }),
  ];

  return { employees, trips };
}

function createTrip({ id, employee, country, startOffset, endOffset }) {
  const entry = isoFromOffset(startOffset);
  const exit = isoFromOffset(endOffset);
  const travelDays = inclusiveDayCount(entry, exit);
  const timestamp = new Date().toISOString();

  return {
    id,
    employee_id: employee.id,
    employee_name: employee.name,
    country,
    entry_date: entry,
    exit_date: exit,
    start_date: entry,
    end_date: exit,
    travel_days: travelDays,
    purpose: '',
    job_ref: '',
    created_at: timestamp,
    updated_at: timestamp,
  };
}

function createMockCalendarApi() {
  const base = buildFixtureDataset();
  let currentTrips = base.trips.map((trip) => ({ ...trip }));
  const employees = base.employees.map((employee) => ({ ...employee }));
  let nextTripId = currentTrips.reduce((max, trip) => Math.max(max, trip.id), 0) + 1;

  function clonePayloadTrips() {
    return currentTrips.map((trip) => ({ ...trip }));
  }

  function dayCount(startIso, endIso) {
    return inclusiveDayCount(startIso, endIso);
  }

  function isoToUtcDate(iso) {
    return new Date(`${iso}T00:00:00Z`);
  }

  function buildPresenceSet(tripsForEmployee) {
    const set = new Set();
    tripsForEmployee.forEach((trip) => {
      const startIso = trip.entry_date || trip.start_date;
      const endIso = trip.exit_date || trip.end_date || startIso;
      if (!startIso || !endIso) return;
      const start = isoToUtcDate(startIso);
      const end = isoToUtcDate(endIso);
      const cursor = new Date(start);
      while (cursor <= end) {
        set.add(cursor.toISOString().split('T')[0]);
        cursor.setUTCDate(cursor.getUTCDate() + 1);
      }
    });
    return set;
  }

  function countUsedDays(presenceSet, todayUtc) {
    const windowStart = new Date(todayUtc);
    windowStart.setUTCDate(windowStart.getUTCDate() - 180);
    const windowEnd = new Date(todayUtc);
    windowEnd.setUTCDate(windowEnd.getUTCDate() - 1);
    let count = 0;
    presenceSet.forEach((iso) => {
      const day = isoToUtcDate(iso);
      if (day > windowStart && day <= windowEnd) {
        count += 1;
      }
    });
    return count;
  }

  function computeUpcoming(tripsForEmployee, todayUtc) {
    let days = 0;
    const upcoming = [];
    tripsForEmployee.forEach((trip) => {
      const startIso = trip.entry_date || trip.start_date;
      const endIso = trip.exit_date || trip.end_date || startIso;
      if (!startIso || !endIso) return;
      const start = isoToUtcDate(startIso);
      const end = isoToUtcDate(endIso);
      if (end < todayUtc) {
        return;
      }
      const futureStart = start > todayUtc ? start : todayUtc;
      const futureDuration = Math.max(0, Math.round((end - futureStart) / 86_400_000) + 1);
      if (futureDuration <= 0) {
        return;
      }
      days += futureDuration;
      upcoming.push({
        id: trip.id,
        country: trip.country,
        start_date: startIso,
        end_date: endIso,
        duration_days: inclusiveDayCount(startIso, endIso),
      });
    });
    return { days, upcoming };
  }

  return {
    getPayload() {
      return {
        generated_at: new Date().toISOString(),
        employees: employees.map((employee) => ({ ...employee })),
        trips: clonePayloadTrips(),
      };
    },
    getForecast(employeeId) {
      const todayIso = isoFromOffset(0);
      const todayUtc = isoToUtcDate(todayIso);
      const tripsForEmployee = currentTrips.filter((trip) => trip.employee_id === employeeId);
      const presenceSet = buildPresenceSet(tripsForEmployee);
      const usedDays = countUsedDays(presenceSet, todayUtc);
      const { days: upcomingDays, upcoming } = computeUpcoming(tripsForEmployee, todayUtc);
      const projectedTotal = usedDays + upcomingDays;
      let riskLevel = 'safe';
      if (projectedTotal >= 90) {
        riskLevel = 'danger';
      } else if (projectedTotal >= 60) {
        riskLevel = 'warning';
      }
      const employee = employees.find((item) => item.id === employeeId) || {
        id: employeeId,
        name: `Employee ${employeeId}`,
      };
      return {
        employee: { id: employee.id, name: employee.name },
        used_days: usedDays,
        upcoming_days: upcomingDays,
        projected_total: projectedTotal,
        risk_level: riskLevel,
        window_start: isoFromOffset(-179),
        window_end: todayIso,
        upcoming_trips: upcoming,
        generated_at: new Date().toISOString(),
      };
    },
    addTrip(payload = {}) {
      const employee = employees.find((item) => item.id === payload.employee_id) || {
        id: payload.employee_id,
        name: `Employee ${payload.employee_id || 'Unknown'}`,
        active: true,
      };
      const startIso = payload.start_date || payload.entry_date || isoFromOffset(0);
      const endIso = payload.end_date || payload.exit_date || startIso;
      const now = new Date().toISOString();
      const trip = {
        id: nextTripId++,
        employee_id: employee.id,
        employee_name: employee.name,
        country: payload.country || 'Unknown',
        entry_date: startIso,
        exit_date: endIso,
        start_date: startIso,
        end_date: endIso,
        travel_days: dayCount(startIso, endIso),
        purpose: payload.purpose || '',
        job_ref: payload.job_ref || '',
        created_at: now,
        updated_at: now,
      };
      currentTrips.push(trip);
      return { ...trip };
    },
    updateTrip(id, payload = {}) {
      const targetIndex = currentTrips.findIndex((item) => item.id === id);
      if (targetIndex === -1) {
        throw new Error(`Trip ${id} not found in mock dataset`);
      }
      const existing = currentTrips[targetIndex];
      const startIso = payload.start_date || payload.entry_date || existing.start_date;
      const endIso = payload.end_date || payload.exit_date || existing.end_date;
      const now = new Date().toISOString();
      const updated = {
        ...existing,
        country: payload.country || existing.country,
        start_date: startIso,
        entry_date: startIso,
        end_date: endIso,
        exit_date: endIso,
        travel_days: dayCount(startIso, endIso),
        purpose: payload.purpose ?? existing.purpose,
        job_ref: payload.job_ref ?? existing.job_ref,
        updated_at: now,
      };
      currentTrips.splice(targetIndex, 1, updated);
      return { ...updated };
    },
    reset() {
      currentTrips = base.trips.map((trip) => ({ ...trip }));
      nextTripId = currentTrips.reduce((max, trip) => Math.max(max, trip.id), 0) + 1;
    },
  };
}

async function bootstrapCalendar(page, options = {}) {
  const { viewport, autoNavigate = true } = options;
  const api = USE_FIXTURES ? createMockCalendarApi() : null;
  await ensureAuthenticated(page);
  if (USE_FIXTURES) {
    await page.route('**/api/trips', async (route) => {
      const request = route.request();
      const method = request.method();
      if (!api) {
        await route.continue();
        return;
      }

      if (method === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(api.getPayload()),
        });
        return;
      }

      if (method === 'POST') {
        const payload = parseJson(request.postData());
        const created = api.addTrip(payload);
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(created),
        });
        return;
      }

      if (method === 'PATCH') {
        const payload = parseJson(request.postData());
        const url = new URL(request.url());
        const match = url.pathname.match(/\/(\d+)$/);
        const id = match ? Number(match[1]) : null;
        const updated = api.updateTrip(id, payload);
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(updated),
        });
        return;
      }

      await route.continue();
    });

    await page.route('**/api/forecast/**', async (route) => {
      const request = route.request();
      if (!api) {
        await route.continue();
        return;
      }
      const url = new URL(request.url());
      const match = url.pathname.match(/\/forecast\/(\d+)/);
      const employeeId = match ? Number(match[1]) : null;
      if (!Number.isFinite(employeeId)) {
        await route.fulfill({
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Invalid employee id' }),
        });
        return;
      }
      const forecast = api.getForecast(employeeId);
      if (!forecast) {
        await route.fulfill({
          status: 404,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Employee not found' }),
        });
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(forecast),
      });
    });
  }

  const consoleErrors = [];
  page.on('console', (message) => {
    if (message.type() === 'error') {
      consoleErrors.push(message.text());
    }
  });

  if (viewport) {
    await page.setViewportSize({ width: viewport.width, height: viewport.height ?? DEFAULT_HEIGHT });
  }

  async function navigate() {
    await page.goto(CALENDAR_PATH, { waitUntil: 'networkidle' });
    await expect(page.locator('#calendar, .calendar-grid')).toBeVisible();
    await expect(page.locator('.calendar-trip').first()).toBeVisible();
  }

  if (autoNavigate) {
    await navigate();
  }

  return {
    api,
    consoleErrors,
    navigate,
    resetFixtures: () => {
      if (api) api.reset();
    },
  };
}

async function ensureAuthenticated(page) {
  const probe = await page.request.get('/calendar', { failOnStatusCode: false });
  if (probe.status() === 200) {
    const body = await probe.text();
    if (!/Login - EU Trip Tracker/i.test(body)) return;
  }

  await page.goto('/login', { waitUntil: 'networkidle' });
  const passwordInput = page.locator('input[name="password"], #password');
  const submitButton = page.locator('#loginBtn');

  await expect(passwordInput).toBeVisible();
  await passwordInput.fill(ADMIN_PASSWORD);

  await Promise.all([
    page.waitForNavigation({ waitUntil: 'networkidle' }),
    submitButton.click(),
  ]);

  if (/\/login/i.test(page.url())) {
    throw new Error('Calendar QA login failed – verify admin password or seed data.');
  }

  await page.goto('about:blank');
}

function parseJson(payload) {
  if (!payload) return {};
  try {
    return JSON.parse(payload);
  } catch (error) {
    console.warn('Failed to parse payload for QA mock', error);
    return {};
  }
}

// Toast handler – more reliable for hidden state
async function waitForToastToHide(page) {
  const toast = page.locator('#calendar-toast');
  await expect(toast).toBeVisible();
  await page.waitForSelector('#calendar-toast', { state: 'hidden', timeout: 5000 });
}

async function dragTripByDays(page, tripId, days) {
  const trip = page.locator(`.calendar-trip[data-trip-id="${tripId}"]`);
  await expect(trip).toBeVisible();

  const employeeId = await trip.evaluate((node) => {
    const row = node.closest('.calendar-grid-row');
    return row ? row.getAttribute('data-employee-id') : null;
  });

  if (!employeeId) {
    throw new Error(`Unable to resolve employee row for trip ${tripId}`);
  }

  const layer = page.locator(`.calendar-grid-row[data-employee-id="${employeeId}"] .calendar-trip-layer`);
  await expect(layer).toBeVisible();

  const tripBox = await trip.boundingBox();
  const layerBox = await layer.boundingBox();
  if (!tripBox || !layerBox) {
    throw new Error('Unable to resolve bounding boxes for drag operation.');
  }

  const sourcePosition = {
    x: tripBox.width / 2,
    y: tripBox.height / 2,
  };

  const startX = (tripBox.x - layerBox.x) + sourcePosition.x;
  const startY = (tripBox.y - layerBox.y) + sourcePosition.y;
  const targetPosition = {
    x: startX + (days * 28),
    y: startY,
  };

  const patchPromise = page.waitForResponse((response) => {
    return response.url().includes(`/api/trips/${tripId}`) && response.request().method() === 'PATCH';
  });

  await trip.dragTo(layer, {
    sourcePosition,
    targetPosition,
  });

  const patchResponse = await patchPromise;
  expect(patchResponse.ok()).toBeTruthy();
}

// Clean up after each test
test.afterEach(async ({ page }) => {
  await page.close();
});

// QA-01: Calendar grid renders
test('Calendar grid renders with populated trips', async ({ page }) => {
  await bootstrapCalendar(page);
  const tripCount = await page.locator('.calendar-trip').count();
  expect(tripCount).toBeGreaterThan(0);
  await expect(page.locator('#calendar-range-label')).not.toHaveText(/Loading range/i);
});

// QA-02: Add Trip flow
test('Add Trip modal saves successfully and shows toast feedback', async ({ page }) => {
  await bootstrapCalendar(page);
  const addTripButton = page.locator('button[data-action="add-trip"]');
  await addTripButton.click();

  const modal = page.locator('#calendar-form-overlay');
  await expect(modal).toBeVisible();

  const employeeSelect = page.locator('#calendar-form-employee');
  await expect(employeeSelect).toBeEnabled();
  await employeeSelect.selectOption('101');

  const startIso = isoFromOffset(5);
  const endIso = isoFromOffset(9);

  await page.fill('#calendar-form-country', 'Germany');
  await page.fill('#calendar-form-start', startIso);
  await page.fill('#calendar-form-end', endIso);

  const initialTripCount = await page.locator('.calendar-trip').count();
  await page.click('button[data-action="submit-form"]');

  await expect(modal).toBeHidden();
  await expect(page.locator('#calendar-toast')).toContainText('Trip added successfully');
  await waitForToastToHide(page);
  await expect(page.locator('.calendar-trip')).toHaveCount(initialTripCount + 1);
});

// QA-03: Edit button enable/disable
test('Edit Trip button activates when a trip is focused', async ({ page }) => {
  await bootstrapCalendar(page);
  const editButton = page.locator('button[data-action="edit-trip-global"]');
  await expect(editButton).toBeDisabled();

  const firstTrip = page.locator('.calendar-trip').first();
  await firstTrip.click();
  await expect(editButton).toBeEnabled();

  const detailClose = page.locator('button[data-action="close-detail"]');
  if (await detailClose.isVisible()) await detailClose.click();
  await expect(editButton).toBeDisabled();
});

// QA-04: Color states
test('Calendar trip blocks render all compliance color states', async ({ page }) => {
  await bootstrapCalendar(page);
  const safe = await page.locator('.calendar-trip--safe').count();
  const warning = await page.locator('.calendar-trip--warning').count();
  const critical = await page.locator('.calendar-trip--critical').count();

  expect.soft(safe).toBeGreaterThan(0);
  expect.soft(warning).toBeGreaterThan(0);
  expect(critical).toBeGreaterThan(0);
});

// QA-05: Responsive layout
test('Calendar layout remains usable across key breakpoints', async ({ page }) => {
  const { navigate, resetFixtures } = await bootstrapCalendar(page, { autoNavigate: false });
  const viewports = [
    { width: 1440, height: 800 },
    { width: 1024, height: 700 },
    { width: 768, height: 600 },
  ];

  for (const vp of viewports) {
    if (resetFixtures) resetFixtures();
    await page.setViewportSize(vp);
    await navigate();
    await expect(page.locator('.calendar-grid')).toBeVisible();
    expect(await page.locator('.calendar-trip').count()).toBeGreaterThan(0);
  }
});

// QA-06: Console errors
test('Calendar view loads without console errors', async ({ page }) => {
  const { consoleErrors } = await bootstrapCalendar(page);
  await page.waitForTimeout(250);
  const fatalErrors = consoleErrors.filter((e) => !/deprecation|favicon/i.test(e));
  expect(fatalErrors).toStrictEqual([]);
});

// QA-07: Accessibility (WCAG AA)
test('Calendar view passes axe-core WCAG AA audit', async ({ page }) => {
  await bootstrapCalendar(page);
  await page.waitForSelector('#calendar');
  await injectAxe(page);
  await checkA11y(page, '#calendar', {
    axeOptions: {
      runOnly: { type: 'tag', values: ['wcag2aa'] },
      rules: { 'color-contrast': { enabled: false } },
    },
  });
});

test('Timeline view toggle mirrors calendar data', async ({ page }) => {
  await bootstrapCalendar(page);
  const calendarTripCount = await page.locator('.calendar-trip').count();
  const safeTrips = await page.locator('.calendar-trip--safe').count();
  const warningTrips = await page.locator('.calendar-trip--warning').count();
  const criticalTrips = await page.locator('.calendar-trip--critical').count();

  await page.click('.calendar-view-toggle__button[data-view-target="timeline"]');
  const timelineLayer = page.locator('.calendar-view-layer[data-view-layer="timeline"]');
  await expect(timelineLayer).toHaveAttribute('aria-hidden', 'false');
  await expect(page.locator('.timeline-trip')).toHaveCount(calendarTripCount);
  await expect(page.locator('.timeline-trip--safe')).toHaveCount(safeTrips);
  await expect(page.locator('.timeline-trip--warning')).toHaveCount(warningTrips);
  await expect(page.locator('.timeline-trip--critical')).toHaveCount(criticalTrips);
});

// QA-08: Drag updates trip dates
test('Trip drag updates start and end dates', async ({ page }) => {
  await bootstrapCalendar(page);

  const tripId = 701;
  const trip = page.locator(`.calendar-trip[data-trip-id="${tripId}"]`);
  await expect(trip).toBeVisible();

  const initialStart = await trip.getAttribute('data-start');
  const initialEnd = await trip.getAttribute('data-end');
  expect(initialStart).toBeTruthy();
  expect(initialEnd).toBeTruthy();

  const shiftDays = 2;
  const expectedStart = addDaysToIso(initialStart, shiftDays);
  const expectedEnd = addDaysToIso(initialEnd, shiftDays);

  await dragTripByDays(page, tripId, shiftDays);

  await expect(trip).toHaveAttribute('data-start', expectedStart);
  await expect(trip).toHaveAttribute('data-end', expectedEnd);
});

// QA-09: Toast feedback and trip count stability
test('Drag drop shows success toast and preserves trip count', async ({ page }) => {
  await bootstrapCalendar(page);

  const tripCountBefore = await page.locator('.calendar-trip').count();
  const tripId = 702;

  await dragTripByDays(page, tripId, 1);

  const toast = page.locator('#calendar-toast');
  await expect(toast).toBeVisible();
  await expect(toast).toContainText('Trip updated successfully');
  await waitForToastToHide(page);

  await expect(page.locator('.calendar-trip')).toHaveCount(tripCountBefore);
});

// QA-10: Compliance class persists after drag
test('Dragged trip retains compliance class and datasets', async ({ page }) => {
  await bootstrapCalendar(page);

  const tripId = 703;
  const trip = page.locator(`.calendar-trip[data-trip-id="${tripId}"]`);
  await expect(trip).toBeVisible();

  const initialCompliance = await trip.getAttribute('data-compliance');
  expect(initialCompliance).toBeTruthy();

  await dragTripByDays(page, tripId, 1);

  await expect(trip).toHaveAttribute('data-compliance', initialCompliance);
  await expect(trip).toHaveClass(new RegExp(`calendar-trip--${initialCompliance}`));
});

test('Mini forecast panel updates after trip changes', async ({ page }) => {
  await bootstrapCalendar(page);

  const usedMetric = page.locator('[data-forecast-used]');
  const upcomingMetric = page.locator('[data-forecast-upcoming]');
  const totalMetric = page.locator('[data-forecast-total]');

  await expect(usedMetric).toHaveText(/7 days/i);
  await expect(upcomingMetric).toHaveText(/0 days/i);

  await page.click('button[data-action="add-trip"]');
  await expect(page.locator('#calendar-form-overlay')).toBeVisible();

  await page.locator('#calendar-form-employee').selectOption('101');
  const futureStart = isoFromOffset(10);
  const futureEnd = isoFromOffset(14);
  await page.fill('#calendar-form-country', 'Germany');
  await page.fill('#calendar-form-start', futureStart);
  await page.fill('#calendar-form-end', futureEnd);
  await page.click('button[data-action="submit-form"]');

  await expect(page.locator('#calendar-form-overlay')).toBeHidden();
  await expect(page.locator('#calendar-toast')).toContainText('Trip added successfully');
  await waitForToastToHide(page);

  const detailClose = page.locator('button[data-action="close-detail"]');
  if (await detailClose.isVisible()) {
    await detailClose.click();
  }

  await expect(upcomingMetric).toHaveText(/5 days/i, { timeout: 5000 });
  await expect(totalMetric).toHaveText(/12 \/ 90 days/i, { timeout: 5000 });
});

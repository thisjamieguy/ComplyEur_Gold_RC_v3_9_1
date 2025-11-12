const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

const QA_ROOT = path.resolve(__dirname, '../dev/qa_reports');
const SCREENSHOT_DIR = path.join(QA_ROOT, 'screenshots');
const LOG_DIR = path.join(QA_ROOT, 'logs');
const DEFAULT_DATE = '2024-05-01';
const CALENDAR_HTTP_URL = 'http://127.0.0.1:4173/calendar_dev.html';
const SANDBOX_TRIPS = JSON.parse(
  fs.readFileSync(path.resolve(__dirname, '../dev/calendar_mock_data.json'), 'utf-8')
);

const EMPLOYEES = {
  emma: 'Emma Lefevre',
  luca: 'Luca Romano',
  sofia: 'Sofia Anders',
  jonas: 'Jonas Meyer',
};

[SCREENSHOT_DIR, LOG_DIR].forEach((dir) => {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
});

const sanitizeFileName = (value) =>
  value
    .replace(/[^a-z0-9]+/gi, '_')
    .replace(/^_+|_+$/g, '')
    .toLowerCase() || 'artifact';

async function captureScreenshot(page, testInfo, label = 'state') {
  const slug = sanitizeFileName(`${testInfo.title}-${testInfo.project.name}-${label}`);
  const destination = path.join(SCREENSHOT_DIR, `${slug}.png`);
  await page.screenshot({ path: destination, fullPage: true });
  await testInfo.attach(`${label}-screenshot`, { path: destination, contentType: 'image/png' });
  return destination;
}

async function persistJsonArtifact(testInfo, label, data) {
  const slug = sanitizeFileName(`${testInfo.title}-${testInfo.project.name}-${label}`);
  const destination = path.join(LOG_DIR, `${slug}.json`);
  fs.writeFileSync(destination, JSON.stringify(data, null, 2));
  await testInfo.attach(label, { path: destination, contentType: 'application/json' });
  return destination;
}

async function persistTextArtifact(testInfo, label, content) {
  const slug = sanitizeFileName(`${testInfo.title}-${testInfo.project.name}-${label}`);
  const destination = path.join(LOG_DIR, `${slug}.log`);
  fs.writeFileSync(destination, content || '');
  await testInfo.attach(label, { path: destination, contentType: 'text/plain' });
  return destination;
}

async function openCalendar(page) {
  await page.goto(CALENDAR_HTTP_URL);
  await page.waitForSelector('.calendar-grid');
  await page.waitForSelector('.trip-pill');
  await page.waitForFunction(() => window.calendarAppInstance && window.calendarAppInstance.trips.length > 0);
  await page.evaluate(() => {
    const app = window.calendarAppInstance;
    if (app && !app.__qaPatched) {
      const original = app.applyDragResult.bind(app);
      app.applyDragResult = function patchedApplyDragResult(payload) {
        window.__qaEvents?.push?.({
          type: 'applyDragResult',
          payload,
          ts: Date.now(),
        });
        return original(payload);
      };
      app.__qaPatched = true;
    }
  });
}

async function setVisibleMonth(page, isoString) {
  await page.evaluate((iso) => {
    const app = window.calendarAppInstance;
    if (!app) return;
    const target = new Date(iso);
    app.currentDate = new Date(target.getFullYear(), target.getMonth(), 1);
    app.render();
  }, isoString);
  await page.waitForTimeout(150);
}

async function getTripIdByEmployee(page, employeeName) {
  return page.evaluate((name) => {
    const app = window.calendarAppInstance;
    if (!app) return null;
    const match = app.trips.find((trip) => trip.employee === name);
    return match ? match.id : null;
  }, employeeName);
}

async function getTripSnapshot(page, tripId) {
  return page.evaluate((id) => {
    const app = window.calendarAppInstance;
    if (!app) return null;
    const trip = app.findTripById(id);
    if (!trip) return null;
    return {
      start: app.formatISO(trip.startDate),
      end: app.formatISO(trip.endDate),
      employee: trip.employee,
    };
  }, tripId);
}

async function getCellCenter(page, isoDate) {
  const cell = page.locator(`.day-cell[data-date="${isoDate}"]`).first();
  await expect(cell, `Expected calendar cell for ${isoDate}`).toBeVisible();
  await cell.scrollIntoViewIfNeeded();
  const box = await cell.boundingBox();
  if (!box) throw new Error(`Unable to resolve bounding box for day ${isoDate}`);
  return { x: box.x + box.width / 2, y: box.y + box.height / 2 };
}

async function dragTrip(page, { tripId, fromDate, toDate }) {
  const tripSelector = `.day-cell[data-date="${fromDate}"] .trip-pill${
    tripId ? `[data-trip-id="${tripId}"]` : ''
  }`;
  const pill = page.locator(tripSelector).first();
  await expect(pill, `Trip pill missing at ${fromDate}`).toBeVisible();
  await pill.scrollIntoViewIfNeeded();
  const pillBox = await pill.boundingBox();
  if (!pillBox) throw new Error('Unable to determine trip pill position');
  const targetCenter = await getCellCenter(page, toDate);
  await page.mouse.move(pillBox.x + pillBox.width / 2, pillBox.y + pillBox.height / 2);
  await page.mouse.down();
  await page.mouse.move(targetCenter.x, targetCenter.y, { steps: 20 });
  await page.waitForTimeout(150);
  await page.mouse.up();
  await page.waitForTimeout(200);
  return pill;
}

async function resizeTrip(page, { tripId, edge, originDate, targetDate }) {
  const handleSelector =
    edge === 'start'
      ? '.resize-handle-left'
      : '.resize-handle-right';
  const locator = page.locator(
    `.day-cell[data-date="${originDate}"] .trip-pill${tripId ? `[data-trip-id="${tripId}"]` : ''} ${handleSelector}`
  );
  await expect(locator, `Missing ${edge} resize handle on ${originDate}`).toBeVisible();
  await locator.scrollIntoViewIfNeeded();
  const handleBox = await locator.boundingBox();
  if (!handleBox) throw new Error('Unable to resolve resize handle position');
  const targetCenter = await getCellCenter(page, targetDate);
  await page.mouse.move(handleBox.x + handleBox.width / 2, handleBox.y + handleBox.height / 2);
  await page.mouse.down();
  await page.mouse.move(targetCenter.x, targetCenter.y, { steps: 12 });
  await page.waitForTimeout(120);
  await page.mouse.up();
  await page.waitForTimeout(200);
}

async function dragToCreateRange(page, startDate, endDate) {
  const start = await getCellCenter(page, startDate);
  const end = await getCellCenter(page, endDate);
  await page.mouse.move(start.x, start.y);
  await page.mouse.down();
  await page.mouse.move(end.x, end.y, { steps: 10 });
  await page.waitForTimeout(120);
  await page.mouse.up();
  await page.waitForTimeout(200);
}

test.beforeEach(async ({ page }) => {
  page.__consoleLogs = [];
  page.on('console', (message) => {
    const entry = `[${message.type()}] ${message.text()}`;
    page.__consoleLogs.push(entry);
  });

  await page.addInitScript(
    (config) => {
      const { defaultDate, trips } = config;
      window.__CALENDAR_DEFAULT_DATE = defaultDate;
      window.ENABLE_TRIP_DND = true;
      window.__CALENDAR_SANDBOX_TRIPS = Array.isArray(trips) ? trips : [];
      window.__qaEvents = [];
      const capture = (type) => (event) => {
        const targetEl = event.target instanceof Element ? event.target : null;
        const pill = targetEl?.closest('.trip-pill');
        const cell = targetEl?.closest('.day-cell');
        window.__qaEvents.push({
          type,
          ts: Date.now(),
          pointerType: event.pointerType,
          buttons: event.buttons,
          tripId: pill?.dataset.tripId || null,
          cellDate: cell?.dataset.date || null,
          clientX: Math.round(event.clientX || 0),
          clientY: Math.round(event.clientY || 0),
        });
      };
      window.addEventListener('pointerdown', capture('pointerdown'), true);
      window.addEventListener('pointermove', capture('pointermove'), true);
      window.addEventListener('pointerup', capture('pointerup'), true);
    },
    { defaultDate: DEFAULT_DATE, trips: SANDBOX_TRIPS }
  );
});

test.afterEach(async ({ page }, testInfo) => {
  const consoleLog = (page.__consoleLogs || []).join('\n') || 'No console output';
  await persistTextArtifact(testInfo, 'console', consoleLog);
  let qaEvents = [];
  try {
    qaEvents = await page.evaluate(() => window.__qaEvents || []);
  } catch (error) {
    qaEvents = [{ type: 'error', detail: `Failed to pull qa events: ${error.message}` }];
  }
  await persistJsonArtifact(testInfo, 'events', qaEvents);
});

test('Trip pills render expected metadata and handles', async ({ page }) => {
  await openCalendar(page);
  await setVisibleMonth(page, DEFAULT_DATE);

  const uniqueTripIds = await page.evaluate(() =>
    [...new Set([...document.querySelectorAll('.trip-pill')].map((node) => node.dataset.tripId))].filter(Boolean)
  );
  const loadedTripCount = await page.evaluate(() => window.calendarAppInstance.trips.length);
  expect(loadedTripCount).toBe(SANDBOX_TRIPS.length);
  expect(uniqueTripIds.length).toBeGreaterThan(0);

  const startHandles = await page.locator('.trip-pill-start .resize-handle-left').count();
  const endHandles = await page.locator('.trip-pill-end .resize-handle-right').count();
  expect(startHandles).toBeGreaterThan(0);
  expect(endHandles).toBeGreaterThan(0);

  const missingAttributes = await page.evaluate(
    () => [...document.querySelectorAll('.trip-pill')].filter((pill) => !pill.dataset.tripId || !pill.dataset.date).length
  );
  expect(missingAttributes).toBe(0);

  const laneCount = await page.locator('.employee-lane[data-employee-id]').count();
  expect(laneCount).toBe(4);
});

test('BUG-001: Dragging trips should persist new start/end dates', async ({ page }, testInfo) => {
  await openCalendar(page);
  await setVisibleMonth(page, DEFAULT_DATE);
  const tripId = await getTripIdByEmployee(page, EMPLOYEES.jonas);
  expect(tripId).toBeTruthy();
  const before = await getTripSnapshot(page, tripId);
  expect(before).toBeTruthy();
  expect(before.start).toBe('2024-05-12');
  await persistJsonArtifact(testInfo, 'bug-001-before', before);

  await dragTrip(page, { tripId, fromDate: before.start, toDate: '2024-05-18' });
  await captureScreenshot(page, testInfo, 'bug-001-after-drop');

  const after = await getTripSnapshot(page, tripId);
  await persistJsonArtifact(testInfo, 'bug-001-after', after);
  expect(after.start).toBe('2024-05-18');
  expect(after.end).toBe('2024-06-03');
  const oldStartPill = page.locator(
    `.day-cell[data-date="${before.start}"] .trip-pill[data-trip-id="${tripId}"]`
  );
  const newStartPill = page.locator(
    `.day-cell[data-date="${after.start}"] .trip-pill[data-trip-id="${tripId}"]`
  );
  const dragDomState = await page.evaluate(
    ({ source, target, tripId }) => {
      const read = (iso) => {
        const pill = document.querySelector(
          `.day-cell[data-date="${iso}"] .trip-pill[data-trip-id="${tripId}"]`
        );
        if (!pill) return null;
        return {
          className: pill.className,
          hasLeftHandle: Boolean(pill.querySelector('.resize-handle-left')),
          hasRightHandle: Boolean(pill.querySelector('.resize-handle-right')),
        };
      };
      return { source: read(source), target: read(target) };
    },
    { source: before.start, target: after.start, tripId }
  );
  await persistJsonArtifact(testInfo, 'bug-001-dom-state', dragDomState);
  await expect(oldStartPill).toHaveCount(0);
  await expect(newStartPill).toHaveCount(1);
  await expect(newStartPill).toHaveClass(/trip-pill-start/);
});

test('BUG-002: Resizing from the start edge should commit new start date', async ({ page }, testInfo) => {
  await openCalendar(page);
  await setVisibleMonth(page, DEFAULT_DATE);

  const tripId = await getTripIdByEmployee(page, EMPLOYEES.jonas);
  expect(tripId).toBeTruthy();
  const before = await getTripSnapshot(page, tripId);
  expect(before).toBeTruthy();
  expect(before.start).toBe('2024-05-12');
  await persistJsonArtifact(testInfo, 'bug-002-before', before);

  await resizeTrip(page, {
    tripId,
    edge: 'start',
    originDate: before.start,
    targetDate: '2024-05-09',
  });
  await captureScreenshot(page, testInfo, 'bug-002-start-resize');

  const after = await getTripSnapshot(page, tripId);
  await persistJsonArtifact(testInfo, 'bug-002-after', after);
  expect(after.start).toBe('2024-05-09');
  const oldStartHandle = page.locator(
    `.day-cell[data-date="2024-05-12"] .trip-pill[data-trip-id="${tripId}"] .resize-handle-left`
  );
  const newStartHandle = page.locator(
    `.day-cell[data-date="${after.start}"] .trip-pill[data-trip-id="${tripId}"] .resize-handle-left`
  );
  const resizeStartDomState = await page.evaluate(
    ({ tripId, source, target }) => {
      const readHandles = (iso) => {
        const pill = document.querySelector(
          `.day-cell[data-date="${iso}"] .trip-pill[data-trip-id="${tripId}"]`
        );
        if (!pill) return null;
        return {
          className: pill.className,
          hasLeft: Boolean(pill.querySelector('.resize-handle-left')),
          hasRight: Boolean(pill.querySelector('.resize-handle-right')),
        };
      };
      return { source: readHandles(source), target: readHandles(target) };
    },
    { tripId, source: '2024-05-12', target: after.start }
  );
  await persistJsonArtifact(testInfo, 'bug-002-dom-state', resizeStartDomState);
  await expect(oldStartHandle).toHaveCount(0);
  await expect(newStartHandle).not.toHaveCount(0);
});

test('BUG-003: Resizing from the end edge should extend the trip duration', async ({ page }, testInfo) => {
  await openCalendar(page);
  await setVisibleMonth(page, DEFAULT_DATE);
  const tripId = await getTripIdByEmployee(page, EMPLOYEES.jonas);
  expect(tripId).toBeTruthy();
  const before = await getTripSnapshot(page, tripId);
  expect(before).toBeTruthy();
  expect(before.end).toBe('2024-05-28');
  await persistJsonArtifact(testInfo, 'bug-003-before', before);

  await resizeTrip(page, {
    tripId,
    edge: 'end',
    originDate: before.end,
    targetDate: '2024-05-31',
  });
  await captureScreenshot(page, testInfo, 'bug-003-end-resize');

  const after = await getTripSnapshot(page, tripId);
  await persistJsonArtifact(testInfo, 'bug-003-after', after);
  expect(after.end).toBe('2024-05-31');
  const resizeEndState = await page.evaluate(
    ({ tripId, iso }) => {
      const pill = document.querySelector(
        `.day-cell[data-date="${iso}"] .trip-pill[data-trip-id="${tripId}"]`
      );
      if (!pill) return null;
      return {
        className: pill.className,
        hasRight: Boolean(pill.querySelector('.resize-handle-right')),
      };
    },
    { tripId, iso: after.end }
  );
  await persistJsonArtifact(testInfo, 'bug-003-dom-state', resizeEndState);
  await expect(
    page.locator(`.day-cell[data-date="${after.end}"] .trip-pill[data-trip-id="${tripId}"] .resize-handle-right`)
  ).not.toHaveCount(0);
});

test('Drag-to-create flow opens the modal and persists a new trip record', async ({ page }) => {
  await openCalendar(page);
  await setVisibleMonth(page, DEFAULT_DATE);

  const baselineCount = await page.evaluate(() => window.calendarAppInstance.trips.length);
  await dragToCreateRange(page, '2024-05-07', '2024-05-10');

  const modal = page.locator('#tripModal');
  await expect(modal).toBeVisible();
  await expect(page.locator('input[name="startDate"]')).toHaveValue('2024-05-07');
  await expect(page.locator('input[name="endDate"]')).toHaveValue('2024-05-10');

  await page.fill('input[name="employee"]', 'QA Bot');
  await page.fill('input[name="country"]', 'Portugal');
  await page.click('#tripForm button[type="submit"]');
  await expect(modal).toHaveClass(/hidden/);

  const newCount = await page.evaluate(() => window.calendarAppInstance.trips.length);
  expect(newCount).toBe(baselineCount + 1);
  const createdTrip = await page.evaluate(() => {
    const app = window.calendarAppInstance;
    if (!app) return null;
    const match = app.trips.find(
      (trip) =>
        trip.employee === 'QA Bot' &&
        app.formatISO(trip.startDate) === '2024-05-07' &&
        app.formatISO(trip.endDate) === '2024-05-10'
    );
    if (!match) return null;
    return { id: String(match.id) };
  });
  expect(createdTrip).toBeTruthy();
  await expect(page.locator(`.trip-pill[data-trip-id="${createdTrip.id}"]`).first()).toBeVisible();
});

test('Drag preview + lane highlight toggle correctly during interaction', async ({ page }) => {
  await openCalendar(page);
  await setVisibleMonth(page, DEFAULT_DATE);
  const tripId = await getTripIdByEmployee(page, EMPLOYEES.jonas);
  expect(tripId).toBeTruthy();
  const pillSelector = `.day-cell[data-date="2024-05-12"] .trip-pill[data-trip-id="${tripId}"]`;
  const pill = page.locator(pillSelector).first();
  await expect(pill).toBeVisible();
  const box = await pill.boundingBox();
  if (!box) throw new Error('Missing bounding box for trip pill');

  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.mouse.down();
  await page.mouse.move(box.x + box.width / 2 + 80, box.y + box.height / 2, { steps: 5 });
  await page.waitForTimeout(100);
  const laneLocator = page.locator('.employee-lane', { hasText: EMPLOYEES.jonas }).first();
  const laneBox = await laneLocator.boundingBox();
  if (!laneBox) throw new Error('Missing lane bounding box');
  await page.mouse.move(laneBox.x + laneBox.width / 2, laneBox.y + laneBox.height / 2, { steps: 5 });

  await expect(pill).toHaveClass(/dragging/);
  await expect(page.locator('.day-cell.trip-preview')).not.toHaveCount(0);
  await expect(page.locator('.employee-lane.lane-preview')).toHaveCount(1);

  await page.mouse.up();
  await expect(page.locator('.trip-pill.dragging')).toHaveCount(0);
  await expect(page.locator('.day-cell.trip-preview')).toHaveCount(0);
  await expect(page.locator('.employee-lane.lane-preview')).toHaveCount(0);
});

test('Stress: 50 drag attempts keep controller stable without leaks', async ({ page }) => {
  await openCalendar(page);
  await setVisibleMonth(page, DEFAULT_DATE);
  const tripId = await getTripIdByEmployee(page, EMPLOYEES.jonas);
  expect(tripId).toBeTruthy();

  for (let i = 0; i < 50; i += 1) {
    const snapshot = await getTripSnapshot(page, tripId);
    expect(snapshot).toBeTruthy();
    await dragTrip(page, {
      tripId,
      fromDate: snapshot.start,
      toDate: i % 2 === 0 ? '2024-05-15' : '2024-05-18',
    });
  }

  const previews = await page.locator('.day-cell.trip-preview').count();
  expect(previews).toBe(0);
  const activeState = await page.evaluate(() => Boolean(window.calendarAppInstance.dragController?.active));
  expect(activeState).toBeFalsy();

  const moveEvents = await page.evaluate(
    () => (window.__qaEvents || []).filter((event) => event.type === 'pointermove').length
  );
  expect(moveEvents).toBeGreaterThan(150);
});

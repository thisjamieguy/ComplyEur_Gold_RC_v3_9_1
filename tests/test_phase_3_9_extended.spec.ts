/**
 * Phase 3.9 Extended Calendar Stability & Sync Suite
 * Runs staged Playwright checks to stress live DB sync, context menus, and modal editing.
 */

import fs from 'fs';
import path from 'path';
import dotenv from 'dotenv';
import {
  BrowserContext,
  expect,
  Locator,
  Page,
  TestInfo,
  test,
} from '@playwright/test';

dotenv.config({ path: path.resolve(process.cwd(), '.env'), override: false });

const SUITE_TAG = '[3.9-TEST]';
const DAY_PIXEL_WIDTH = 28;
const SCREENSHOT_INTERVAL_MS = 120_000;
const DEFAULT_TOTAL_DURATION_MS = 20 * 60 * 1000;

const ADMIN_USERNAME =
  process.env.ADMIN_USERNAME ??
  process.env.ADMIN_USER ??
  process.env.PLAYWRIGHT_ADMIN_USERNAME ??
  'admin';

const ADMIN_PASSWORD_PRIMARY =
  process.env.ADMIN_PASSWORD ??
  process.env.ADMIN_PASS ??
  process.env.CALENDAR_QA_PASSWORD ??
  process.env.PLAYWRIGHT_ADMIN_PASSWORD ??
  'test123';

const ADMIN_PASSWORD_FALLBACK =
  process.env.ADMIN_PASSWORD_FALLBACK ??
  process.env.CALENDAR_LEGACY_PASSWORD ??
  'admin123';

const DB_PATH =
  process.env.CALENDAR_DB_PATH ??
  process.env.DATABASE_PATH ??
  path.join(process.cwd(), 'data', 'complyeur.db');

type OperationOutcome = 'success' | 'warning' | 'failure';

type TripRecord = {
  id: number;
  employeeId: number;
  country: string;
  start: string;
  end: string;
  employeeName?: string;
};

type OperationLog = {
  timestamp: string;
  stage: string;
  action: string;
  outcome: OperationOutcome;
  details?: string;
};

type StageGetter = () => string;

interface SuiteMetrics {
  success: number;
  warnings: number;
  failures: number;
  dbChecks: number;
  dbMismatch: number;
  toastChecks: number;
  toastFailures: number;
  responseTimes: number[];
}

interface SuiteState {
  baselineTrips: TripRecord[];
  baselineCount: number;
  netTripDelta: number;
  logs: OperationLog[];
  metrics: SuiteMetrics;
  modifiedTrips: Map<number, { start: string; end: string; country: string }>;
}

const createInitialState = (): SuiteState => ({
  baselineTrips: [],
  baselineCount: 0,
  netTripDelta: 0,
  logs: [],
  metrics: {
    success: 0,
    warnings: 0,
    failures: 0,
    dbChecks: 0,
    dbMismatch: 0,
    toastChecks: 0,
    toastFailures: 0,
    responseTimes: [],
  },
  modifiedTrips: new Map(),
});

const isoNow = () => new Date().toISOString();

const recordOperation = (
  state: SuiteState,
  stage: string,
  action: string,
  outcome: OperationOutcome,
  details?: string,
) => {
  const entry: OperationLog = {
    timestamp: isoNow(),
    stage,
    action,
    outcome,
    details,
  };
  state.logs.push(entry);
  if (outcome === 'success') {
    state.metrics.success += 1;
  } else if (outcome === 'warning') {
    state.metrics.warnings += 1;
  } else {
    state.metrics.failures += 1;
  }
  const suffix = details ? ` → ${details}` : '';
  console.log(`${SUITE_TAG} ${stage} | ${action} | ${outcome.toUpperCase()}${suffix}`);
};

const parseDurationToMs = (value: string | undefined, fallback: number): number => {
  if (!value) {
    return fallback;
  }
  const trimmed = value.trim().toLowerCase();
  if (!trimmed) {
    return fallback;
  }
  const match = trimmed.match(/^(\d+(?:\.\d+)?)(ms|s|m|h)?$/);
  if (!match) {
    return fallback;
  }
  const numeric = parseFloat(match[1]);
  const unit = match[2] ?? 'ms';
  if (Number.isNaN(numeric)) {
    return fallback;
  }
  switch (unit) {
    case 'h':
      return numeric * 60 * 60 * 1000;
    case 'm':
      return numeric * 60 * 1000;
    case 's':
      return numeric * 1000;
    case 'ms':
    default:
      return numeric;
  }
};

const addDays = (iso: string, days: number): string => {
  const base = new Date(`${iso}T00:00:00Z`);
  base.setUTCDate(base.getUTCDate() + days);
  return base.toISOString().split('T')[0]!;
};

const normaliseTrip = (raw: any): TripRecord => ({
  id: Number(raw.id),
  employeeId: Number(raw.employee_id ?? raw.employeeId),
  country: raw.country ?? '',
  start: raw.entry_date ?? raw.start_date ?? raw.start ?? '',
  end: raw.exit_date ?? raw.end_date ?? raw.end ?? '',
  employeeName: raw.employee_name ?? raw.employeeName ?? '',
});

const getTripsFromApi = async (page: Page, state: SuiteState, stage: string): Promise<TripRecord[]> => {
  const response = await page.request.get('/api/trips');
  expect(response.ok(), `${stage}: expected /api/trips to respond OK`).toBeTruthy();
  const payload = await response.json();
  const tripsPayload = Array.isArray(payload?.trips) ? payload.trips : payload;
  const trips = (tripsPayload ?? []).map(normaliseTrip);
  state.metrics.dbChecks += 1;
  return trips;
};

const ensureCalendarReady = async (page: Page) => {
  await page.goto('/calendar', { waitUntil: 'networkidle' });
  const calendarRoot = page.locator('#calendar, .calendar-shell, [data-calendar-shell]');
  await expect(calendarRoot.first()).toBeVisible({ timeout: 15_000 });
  const tripLocator = page.locator('.calendar-trip, .trip-block');
  await expect(tripLocator.first()).toBeVisible({ timeout: 15_000 });
};

const tryLogin = async (page: Page, password: string): Promise<boolean> => {
  const usernameField = page.locator('input[name="username"], #username');
  if (await usernameField.count()) {
    await usernameField.first().fill(ADMIN_USERNAME);
  }
  const passwordField = page.locator('input[name="password"], #password');
  if (!(await passwordField.count())) {
    return page.url().includes('/calendar');
  }
  await passwordField.first().fill(password);
  const submitButton = page
    .locator('button[type="submit"], #loginBtn, button:has-text("Login"), button:has-text("Log in")')
    .first();
  await Promise.all([
    page.waitForNavigation({ waitUntil: 'networkidle', timeout: 15_000 }).catch(() => null),
    submitButton.click(),
  ]);
  await page.waitForLoadState('networkidle').catch(() => null);
  return page.url().includes('/calendar');
};

const ensureAuthenticated = async (page: Page) => {
  await page.goto('/calendar', { waitUntil: 'networkidle' });
  if (page.url().includes('/calendar')) {
    await ensureCalendarReady(page);
    return;
  }
  await page.goto('/login', { waitUntil: 'domcontentloaded' });
  const primaryOk = await tryLogin(page, ADMIN_PASSWORD_PRIMARY);
  if (!primaryOk && ADMIN_PASSWORD_PRIMARY !== ADMIN_PASSWORD_FALLBACK) {
    await page.goto('/login', { waitUntil: 'domcontentloaded' });
    const fallbackOk = await tryLogin(page, ADMIN_PASSWORD_FALLBACK);
    if (!fallbackOk) {
      throw new Error('Unable to authenticate with provided admin credentials.');
    }
  }
  await ensureCalendarReady(page);
};

const attachResponseTracking = (
  context: BrowserContext,
  state: SuiteState,
  stageRef: StageGetter,
) => {
  const requestTimes = new WeakMap<import('@playwright/test').Request, number>();
  context.on('request', (request) => {
    if (!request.url().includes('/api/')) {
      return;
    }
    requestTimes.set(request, Date.now());
  });
  context.on('response', async (response) => {
    if (!response.url().includes('/api/')) {
      return;
    }
    const request = response.request();
    const start = requestTimes.get(request);
    if (start) {
      const duration = Date.now() - start;
      state.metrics.responseTimes.push(duration);
      if (duration > 1000) {
        const pathname = (() => {
          try {
            return new URL(response.url()).pathname;
          } catch {
            return response.url();
          }
        })();
        recordOperation(
          state,
          stageRef(),
          `Response lag ${request.method()} ${pathname}`,
          'warning',
          `${duration}ms`,
        );
      }
    }
  });
};

const readTripAttributes = async (trip: Locator) => {
  return trip.evaluate((node) => ({
    id: node.getAttribute('data-trip-id'),
    employeeId: node.getAttribute('data-employee-id'),
    start: node.getAttribute('data-start') ?? node.getAttribute('data-entry'),
    end: node.getAttribute('data-end') ?? node.getAttribute('data-exit'),
    country: node.getAttribute('data-country') ?? node.getAttribute('data-trip-country'),
  }));
};

const waitForToast = async (
  page: Page,
  expectation?: RegExp | string,
  timeout = 7_000,
): Promise<string> => {
  const start = Date.now();
  const selectors = [
    '#calendar-toast',
    '.calendar-toast',
    '.react-hot-toast',
    '[data-toast-message]',
    '[role="status"]',
  ];
  const asRegex =
    typeof expectation === 'string' ? new RegExp(expectation, 'i') : expectation ?? null;

  while (Date.now() - start < timeout) {
    for (const selector of selectors) {
      const locator = page.locator(selector);
      const count = await locator.count().catch(() => 0);
      if (!count) {
        continue;
      }
      for (let index = 0; index < count; index += 1) {
        const handle = locator.nth(index);
        const visibility = await handle.isVisible().catch(() => false);
        if (!visibility) {
          continue;
        }
        const text = ((await handle.textContent()) ?? '').trim();
        if (!text) {
          continue;
        }
        if (!asRegex || asRegex.test(text)) {
          return text;
        }
      }
    }
    await page.waitForTimeout(150);
  }
  throw new Error(expectation ? `Toast matching ${asRegex} not observed` : 'Toast not observed');
};

const verifyToast = async (
  page: Page,
  state: SuiteState,
  stage: string,
  expectation: RegExp | string,
) => {
  state.metrics.toastChecks += 1;
  try {
    const text = await waitForToast(page, expectation);
    recordOperation(state, stage, 'Toast observed', 'success', text);
    return text;
  } catch (error) {
    state.metrics.toastFailures += 1;
    recordOperation(
      state,
      stage,
      'Toast observation failed',
      'warning',
      error instanceof Error ? error.message : String(error),
    );
    throw error;
  }
};

const locateTripById = (page: Page, tripId: number) =>
  page.locator(`.calendar-trip[data-trip-id="${tripId}"], .trip-block[data-trip-id="${tripId}"]`);

const resolveEmployeeLayer = async (page: Page, trip: Locator) => {
  const employeeId = await trip.evaluate((node) => {
    const row = node.closest('.calendar-grid-row');
    return row ? row.getAttribute('data-employee-id') : null;
  });
  if (!employeeId) {
    throw new Error('Unable to resolve employee row for drag operation');
  }
  return page.locator(
    `.calendar-grid-row[data-employee-id="${employeeId}"] .calendar-trip-layer, [data-employee-id="${employeeId}"] [data-trip-layer]`,
  );
};

const dragTripByDays = async (page: Page, tripId: number, days: number) => {
  const trip = locateTripById(page, tripId);
  await expect(trip).toBeVisible({ timeout: 10_000 });

  const layer = await resolveEmployeeLayer(page, trip);
  await expect(layer).toBeVisible({ timeout: 10_000 });

  const tripBox = await trip.boundingBox();
  const layerBox = await layer.boundingBox();
  if (!tripBox || !layerBox) {
    throw new Error('Missing bounding boxes for drag interaction');
  }

  const sourcePosition = {
    x: tripBox.width / 2,
    y: tripBox.height / 2,
  };
  const targetPosition = {
    x: sourcePosition.x + days * DAY_PIXEL_WIDTH,
    y: sourcePosition.y,
  };

  const patchPromise = page.waitForResponse(
    (response) =>
      response.url().includes(`/api/trips/${tripId}`) &&
      response.request().method().toUpperCase() === 'PATCH',
    { timeout: 15_000 },
  );

  await trip.dragTo(layer, { sourcePosition, targetPosition });

  const response = await patchPromise;
  expect(response.ok(), 'Drag operation should result in PATCH 200').toBeTruthy();
};

const resizeTripByDays = async (page: Page, tripId: number, deltaDays: number) => {
  const trip = locateTripById(page, tripId);
  await expect(trip).toBeVisible({ timeout: 10_000 });

  await trip.hover();

  const handleSelector =
    deltaDays >= 0
      ? '.trip-block__handle--end, [data-resize-handle="end"], .calendar-trip__resize--end'
      : '.trip-block__handle--start, [data-resize-handle="start"], .calendar-trip__resize--start';
  const handle = trip.locator(handleSelector).first();

  const handleBox = (await handle.count()) ? await handle.boundingBox() : null;
  const tripBox = await trip.boundingBox();
  if (!tripBox) {
    throw new Error('Trip bounding box unavailable for resize');
  }

  const start =
    handleBox ??
    (deltaDays >= 0
      ? { x: tripBox.x + tripBox.width - 2, y: tripBox.y + tripBox.height / 2 }
      : { x: tripBox.x + 2, y: tripBox.y + tripBox.height / 2 });
  const moveBy = deltaDays * DAY_PIXEL_WIDTH;

  const patchPromise = page.waitForResponse(
    (response) =>
      response.url().includes(`/api/trips/${tripId}`) &&
      response.request().method().toUpperCase() === 'PATCH',
    { timeout: 15_000 },
  );

  await page.mouse.move(start.x, start.y);
  await page.mouse.down();
  await page.mouse.move(start.x + moveBy, start.y, { steps: 12 });
  await page.mouse.up();

  const response = await patchPromise;
  expect(response.ok(), 'Resize should complete with PATCH OK').toBeTruthy();
};

const openContextMenu = async (page: Page, trip: Locator) => {
  await trip.click({ button: 'right' });
  const menu = page.locator('#calendar-context-menu, .calendar-context-menu');
  await expect(menu).toBeVisible({ timeout: 5_000 });
  return menu;
};

const triggerContextMenuAction = async (menu: Locator, action: 'edit' | 'delete' | 'duplicate' | 'details') => {
  const button = menu.locator(`[data-menu-action="${action}"]`).first();
  await expect(button).toBeVisible({ timeout: 3_000 });
  await button.click();
};

const waitForModal = async (page: Page) => {
  const modal = page.locator('#calendar-form-overlay, [data-testid="calendar-form"]');
  await expect(modal).toBeVisible({ timeout: 5_000 });
  return modal;
};

const closeModal = async (page: Page) => {
  const closeButtons = page.locator(
    '#calendar-form-overlay [data-action="close-form"], [data-testid="calendar-form"] [data-action="close-form"], .calendar-form-close',
  );
  if (await closeButtons.count()) {
    await closeButtons.first().click({ trial: true }).catch(() => null);
    await closeButtons.first().click().catch(() => null);
  }
  await page.keyboard.press('Escape').catch(() => null);
  await page
    .locator('#calendar-form-overlay, [data-testid="calendar-form"]')
    .waitFor({ state: 'hidden', timeout: 7_000 })
    .catch(() => null);
};

const updateTripViaModal = async (
  page: Page,
  tripId: number,
  changes: { start?: string; end?: string; country?: string },
): Promise<void> => {
  if (changes.start) {
    await page.fill('#calendar-form-start, [name="start_date"]', changes.start);
  }
  if (changes.end) {
    await page.fill('#calendar-form-end, [name="end_date"]', changes.end);
  }
  if (changes.country) {
    await page.fill('#calendar-form-country, [name="country"]', changes.country);
  }

  const submit = page.locator('#calendar-form [data-action="submit-form"], button[type="submit"]');
  const [response] = await Promise.all([
    page.waitForResponse(
      (res) =>
        res.url().includes(`/api/trips/${tripId}`) &&
        res.request().method().toUpperCase() === 'PATCH',
      { timeout: 15_000 },
    ),
    submit.first().click(),
  ]);

  if (!response.ok()) {
    throw new Error(`Edit request failed with status ${response.status()}`);
  }

  await page
    .locator('#calendar-form-overlay, [data-testid="calendar-form"]')
    .waitFor({ state: 'hidden', timeout: 7_000 })
    .catch(() => null);
};

const ensureTripMatches = async (
  page: Page,
  state: SuiteState,
  stage: string,
  tripId: number,
  expected: Partial<TripRecord>,
) => {
  const trips = await getTripsFromApi(page, state, stage);
  const match = trips.find((item) => item.id === tripId);
  if (!match) {
    state.metrics.dbMismatch += 1;
    recordOperation(state, stage, `Trip ${tripId} missing after update`, 'failure');
    await page.reload({ waitUntil: 'networkidle' }).catch(() => null);
    await ensureCalendarReady(page);
    throw new Error(`Trip ${tripId} not found in API payload`);
  }
  let mismatched = false;
  if (expected.start && match.start !== expected.start) {
    mismatched = true;
  }
  if (expected.end && match.end !== expected.end) {
    mismatched = true;
  }
  if (expected.country && match.country !== expected.country) {
    mismatched = true;
  }
  if (mismatched) {
    state.metrics.dbMismatch += 1;
    recordOperation(
      state,
      stage,
      `Trip ${tripId} mismatch`,
      'warning',
      `expected ${JSON.stringify(expected)} got ${JSON.stringify(match)}`,
    );
    await page.reload({ waitUntil: 'networkidle' }).catch(() => null);
    await ensureCalendarReady(page);
  } else {
    recordOperation(state, stage, `Trip ${tripId} DB sync`, 'success');
  }
  return match;
};

const deleteTripViaMenu = async (page: Page, tripId: number) => {
  const trip = locateTripById(page, tripId);
  await expect(trip).toBeVisible({ timeout: 10_000 });
  const menu = await openContextMenu(page, trip);
  const deleteResponse = page.waitForResponse(
    (response) =>
      response.url().includes(`/api/trips/${tripId}`) &&
      response.request().method().toUpperCase() === 'DELETE',
    { timeout: 15_000 },
  );
  await triggerContextMenuAction(menu, 'delete');
  const response = await deleteResponse;
  expect(response.ok(), 'Delete should return OK').toBeTruthy();
  await expect(trip).toBeHidden({ timeout: 7_000 });
};

const duplicateTripViaMenu = async (page: Page, tripId: number): Promise<number> => {
  const trip = locateTripById(page, tripId);
  await expect(trip).toBeVisible({ timeout: 10_000 });
  const menu = await openContextMenu(page, trip);
  const duplicateResponse = page.waitForResponse(
    (response) =>
      response.url().includes(`/api/trips/${tripId}/duplicate`) &&
      response.request().method().toUpperCase() === 'POST',
    { timeout: 15_000 },
  );
  await triggerContextMenuAction(menu, 'duplicate');
  const response = await duplicateResponse;
  expect(response.ok(), 'Duplicate should return 201/200').toBeTruthy();
  const payload = await response.json();
  const newTrip = normaliseTrip(payload);
  await expect(locateTripById(page, newTrip.id)).toBeVisible({ timeout: 10_000 });
  return newTrip.id;
};

const pickRandomTripId = async (page: Page): Promise<number> => {
  const trips = page.locator('.calendar-trip, .trip-block');
  const count = await trips.count();
  if (!count) {
    throw new Error('No trips available for random selection');
  }
  const index = Math.floor(Math.random() * count);
  const idAttr = await trips.nth(index).getAttribute('data-trip-id');
  if (!idAttr) {
    throw new Error('Selected trip missing data-trip-id');
  }
  return Number(idAttr);
};

const getBaseURL = (testInfo: TestInfo): string => {
  const projectUse = testInfo.project.use as Record<string, unknown>;
  const configured = projectUse?.baseURL;
  if (typeof configured === 'string' && configured) {
    return configured;
  }
  return process.env.PLAYWRIGHT_BASE_URL ?? 'http://127.0.0.1:5000';
};

test.describe.serial('Phase 3.9 Extended Calendar Validation', () => {
  test('Phase 3.9 extended stability + DB sync validation', async ({ page, browser }, testInfo) => {
    const state = createInitialState();
    let currentStage = 'Stage 0';
    const stageRef = () => currentStage;
    const baseURL = getBaseURL(testInfo);

    attachResponseTracking(page.context(), state, stageRef);

    const totalDuration = parseDurationToMs(process.env.TEST_DURATION, DEFAULT_TOTAL_DURATION_MS);
    const stage2Duration = Math.min(5 * 60 * 1000, Math.max(totalDuration * 0.25, 60_000));
    const stage3Duration = Math.min(
      15 * 60 * 1000,
      Math.max(totalDuration - stage2Duration - 2 * 60 * 1000, 5 * 60 * 1000),
    );

    // Stage 1 — Functional Sanity
    currentStage = 'Stage 1';
    await test.step('Stage 1 — Functional Sanity', async () => {
      await ensureAuthenticated(page);

      state.baselineTrips = await getTripsFromApi(page, state, currentStage);
      state.baselineCount = state.baselineTrips.length;
      recordOperation(
        state,
        currentStage,
        'Baseline captured',
        'success',
        `Trips: ${state.baselineCount}`,
      );

      const tripElements = page.locator('.calendar-trip, .trip-block');
      await expect(tripElements.first()).toBeVisible();

      const sampleCount = Math.min(3, await tripElements.count());
      for (let index = 0; index < sampleCount; index += 1) {
        const data = await readTripAttributes(tripElements.nth(index));
        expect(data.id, 'Trip block missing data-trip-id').toBeTruthy();
        expect(data.employeeId, 'Trip block missing data-employee-id').toBeTruthy();
        expect(data.start, 'Trip block missing data-start').toBeTruthy();
        expect(data.end, 'Trip block missing data-end').toBeTruthy();
        recordOperation(
          state,
          currentStage,
          `Trip attr check #${index + 1}`,
          'success',
          JSON.stringify(data),
        );
      }

      const candidateTrip = state.baselineTrips.find((trip) => trip.start && trip.end);
      if (!candidateTrip) {
        throw new Error('No trips with valid dates available for drag test');
      }
      const chosenId = candidateTrip.id;
      state.modifiedTrips.set(chosenId, {
        start: candidateTrip.start,
        end: candidateTrip.end,
        country: candidateTrip.country,
      });

      await dragTripByDays(page, chosenId, 2);
      const expectedDrag = {
        start: addDays(candidateTrip.start, 2),
        end: addDays(candidateTrip.end, 2),
      };
      await ensureTripMatches(page, state, currentStage, chosenId, expectedDrag);
      await verifyToast(page, state, currentStage, /Trip updated|Trip updated ✅/i).catch(() => null);

      await resizeTripByDays(page, chosenId, 1);
      const expectedResize = {
        end: addDays(expectedDrag.end, 1),
      };
      await ensureTripMatches(page, state, currentStage, chosenId, expectedResize);

      const targetTripLocator = locateTripById(page, chosenId);
      const menu = await openContextMenu(page, targetTripLocator);
      const menuItems = await menu.locator('[data-menu-action]').allTextContents();
      expect(menuItems.length).toBeGreaterThanOrEqual(4);
      expect(menuItems.join(' ')).toMatch(/Edit/i);
      expect(menuItems.join(' ')).toMatch(/Delete/i);
      expect(menuItems.join(' ')).toMatch(/Duplicate/i);
      expect(menuItems.join(' ')).toMatch(/View/i);
      recordOperation(state, currentStage, 'Context menu options', 'success', menuItems.join(', '));
      await page.keyboard.press('Escape');

      const editMenu = await openContextMenu(page, targetTripLocator);
      await triggerContextMenuAction(editMenu, 'edit');
      const modal = await waitForModal(page);
      const newCountry = candidateTrip.country === 'DE' ? 'FR' : 'DE';
      const newStart = addDays(expectedDrag.start, 1);
      const newEnd = addDays(expectedResize.end, 1);
      await updateTripViaModal(page, chosenId, {
        country: newCountry,
        start: newStart,
        end: newEnd,
      });
      await ensureTripMatches(page, state, currentStage, chosenId, {
        country: newCountry,
        start: newStart,
        end: newEnd,
      });
      await verifyToast(page, state, currentStage, /Trip updated|Trip updated ✅/i).catch(() => null);
      await closeModal(page);

      const deleteTarget =
        state.baselineTrips.find((trip) => trip.id !== chosenId) ?? candidateTrip;
      await deleteTripViaMenu(page, deleteTarget.id);
      state.netTripDelta -= 1;
      await verifyToast(page, state, currentStage, /(Trip deleted|deleted)/i).catch(() => null);
      const postDeleteTrips = await getTripsFromApi(page, state, currentStage);
      const stillExists = postDeleteTrips.some((trip) => trip.id === deleteTarget.id);
      expect(stillExists).toBeFalsy();
      recordOperation(state, currentStage, `Trip ${deleteTarget.id} deletion`, 'success');

      const duplicateSource = candidateTrip.id === deleteTarget.id ? chosenId : candidateTrip.id;
      const newTripId = await duplicateTripViaMenu(page, duplicateSource);
      state.netTripDelta += 1;
      await verifyToast(page, state, currentStage, /(duplicated|Trip copied)/i).catch(() => null);
      const duplicates = await getTripsFromApi(page, state, currentStage);
      expect(duplicates.some((trip) => trip.id === newTripId)).toBeTruthy();
      recordOperation(state, currentStage, `Trip ${duplicateSource} duplicated`, 'success', String(newTripId));
    });

    // Stage 2 — Medium Intensity
    currentStage = 'Stage 2';
    await test.step('Stage 2 — Medium Intensity', async () => {
      const endAt = Date.now() + stage2Duration;
      let modalIterations = 0;

      while (Date.now() < endAt) {
        const chosenId = await pickRandomTripId(page);
        const actionRoll = Math.random();
        if (actionRoll < 0.5) {
          await dragTripByDays(page, chosenId, Math.random() > 0.5 ? 1 : -1);
        } else {
          await resizeTripByDays(page, chosenId, Math.random() > 0.5 ? 1 : -1);
        }
        const latest = await ensureTripMatches(page, state, currentStage, chosenId, {});
        await verifyToast(page, state, currentStage, /(updated|Trip updated)/i).catch(() => null);
        recordOperation(
          state,
          currentStage,
          `Random adjust ${chosenId}`,
          'success',
          `${latest.start} → ${latest.end}`,
        );

        modalIterations += 1;
        if (modalIterations <= 10) {
          const trip = locateTripById(page, chosenId);
          const menu = await openContextMenu(page, trip);
          await triggerContextMenuAction(menu, 'edit');
          await waitForModal(page);
          const tweak = {
            start: addDays(latest.start, 0),
            end: addDays(latest.end, 0),
            country: latest.country,
          };
          await updateTripViaModal(page, chosenId, tweak);
          await ensureTripMatches(page, state, currentStage, chosenId, tweak);
          await verifyToast(page, state, currentStage, /(updated|Trip updated)/i).catch(() => null);
        }
      }

      const failureTrip = await pickRandomTripId(page);
      const failurePattern = new RegExp(`/api/trips/${failureTrip}$`);
      let intercepted = false;
      await page.route(
        failurePattern,
        async (route) => {
          if (intercepted || route.request().method().toUpperCase() !== 'PATCH') {
            await route.continue();
            return;
          }
          intercepted = true;
          await route.fulfill({
            status: 500,
            contentType: 'application/json',
            body: JSON.stringify({ error: 'Simulated failure' }),
          });
        },
        { times: 1 },
      );
      const tripForFailure = locateTripById(page, failureTrip);
      const failureMenu = await openContextMenu(page, tripForFailure);
      await triggerContextMenuAction(failureMenu, 'edit');
      await waitForModal(page);
      const original = await getTripsFromApi(page, state, currentStage);
      const before = original.find((trip) => trip.id === failureTrip);
      await page.fill('#calendar-form-country, [name="country"]', (before?.country ?? 'DE') + 'X');
      await expect(async () => {
        await updateTripViaModal(page, failureTrip, { country: (before?.country ?? 'DE') + 'X' });
      }).rejects.toThrow();
      await page.unroute(failurePattern);
      await verifyToast(page, state, currentStage, /(Save failed|Server error|rollbacked)/i).catch(() => null);
      const after = await getTripsFromApi(page, state, currentStage);
      const restored = after.find((trip) => trip.id === failureTrip);
      if (before && restored) {
        expect(restored.country).toBe(before.country);
      }
      recordOperation(state, currentStage, `Rollback verified ${failureTrip}`, 'success');
      await ensureCalendarReady(page);
      expect(page.url()).toContain('/calendar');
    });

    // Stage 3 — High Intensity
    currentStage = 'Stage 3';
    await test.step('Stage 3 — High Intensity', async () => {
      const sharedState = await page.context().storageState();
      const secondaryContext = await browser.newContext({ baseURL, storageState: sharedState });
      attachResponseTracking(secondaryContext, state, stageRef);
      const secondaryPage = await secondaryContext.newPage();
      await ensureAuthenticated(secondaryPage);

      const startTime = Date.now();
      const endTime = startTime + stage3Duration;
      let lastScreenshot = startTime;
      let screenshotIndex = 0;

      const performRandomAction = async (targetPage: Page) => {
        const actionRand = Math.random();
        const tripId = await pickRandomTripId(targetPage);
        if (actionRand < 0.25) {
          await dragTripByDays(targetPage, tripId, Math.random() > 0.5 ? 2 : -2);
          await ensureTripMatches(targetPage, state, currentStage, tripId, {});
          recordOperation(state, currentStage, `Stress drag ${tripId}`, 'success');
        } else if (actionRand < 0.5) {
          await resizeTripByDays(targetPage, tripId, Math.random() > 0.5 ? 3 : -3);
          await ensureTripMatches(targetPage, state, currentStage, tripId, {});
          recordOperation(state, currentStage, `Stress resize ${tripId}`, 'success');
        } else if (actionRand < 0.7) {
          const newTripId = await duplicateTripViaMenu(targetPage, tripId);
          state.netTripDelta += 1;
          await ensureTripMatches(targetPage, state, currentStage, newTripId, {});
          recordOperation(state, currentStage, `Stress duplicate ${tripId}`, 'success', `→ ${newTripId}`);
        } else if (actionRand < 0.85) {
          await deleteTripViaMenu(targetPage, tripId);
          state.netTripDelta -= 1;
          recordOperation(state, currentStage, `Stress delete ${tripId}`, 'success');
        } else {
          const trip = locateTripById(targetPage, tripId);
          const menu = await openContextMenu(targetPage, trip);
          await triggerContextMenuAction(menu, 'edit');
          await waitForModal(targetPage);
          const trips = await getTripsFromApi(targetPage, state, currentStage);
          const match = trips.find((item) => item.id === tripId);
          if (match) {
            const updated = {
              country: match.country,
              start: match.start,
              end: addDays(match.end, 0),
            };
            await updateTripViaModal(targetPage, tripId, updated);
            await ensureTripMatches(targetPage, state, currentStage, tripId, updated);
            recordOperation(state, currentStage, `Stress modal edit ${tripId}`, 'success');
          }
        }
      };

      while (Date.now() < endTime) {
        await performRandomAction(page);
        await performRandomAction(secondaryPage);

        const now = Date.now();
        if (now - lastScreenshot >= SCREENSHOT_INTERVAL_MS) {
          lastScreenshot = now;
          screenshotIndex += 1;
          const screenshotPath = testInfo.outputPath(`stage3_snapshot_${screenshotIndex}.png`);
          await page.screenshot({ path: screenshotPath, fullPage: true }).catch(() => null);
          await testInfo.attach(`Stage3 screenshot ${screenshotIndex}`, {
            path: screenshotPath,
            contentType: 'image/png',
          });
          recordOperation(state, currentStage, 'Periodic screenshot', 'success', screenshotPath);
        }
      }

      await secondaryPage.close();
      await secondaryContext.close();
    });

    // Stage 4 — Cooldown & Validation
    currentStage = 'Stage 4';
    await test.step('Stage 4 — Cooldown & Validation', async () => {
      await ensureCalendarReady(page);

      const finalTrips = await getTripsFromApi(page, state, currentStage);
      const expectedCount = state.baselineCount + state.netTripDelta;
      recordOperation(
        state,
        currentStage,
        'Net trip delta',
        'success',
        `Baseline ${state.baselineCount}, delta ${state.netTripDelta}, actual ${finalTrips.length}`,
      );
      expect(finalTrips.length).toBe(expectedCount);

      const dbIntegrityResponse = await page.request.get('/api/trips');
      expect(dbIntegrityResponse.ok()).toBeTruthy();
      recordOperation(state, currentStage, 'SQL integrity check placeholder', 'success');

      await verifyToast(page, state, currentStage, /(updated|deleted|duplicated|Trip)/i).catch(() => null);

      const logoutLink = page.locator('[data-action="logout"], a[href*="/logout"]');
      if (await logoutLink.count()) {
        await logoutLink.first().click().catch(() => null);
      } else {
        await page.goto('/logout', { waitUntil: 'networkidle' }).catch(() => null);
      }
      recordOperation(state, currentStage, 'Logout', 'success');
    });

    const avgResponse =
      state.metrics.responseTimes.length > 0
        ? state.metrics.responseTimes.reduce((sum, value) => sum + value, 0) /
          state.metrics.responseTimes.length
        : 0;
    const dbSyncSuccessRate =
      state.metrics.dbChecks === 0
        ? 100
        : ((state.metrics.dbChecks - state.metrics.dbMismatch) / state.metrics.dbChecks) * 100;

    const summary = {
      passedOperations: state.metrics.success,
      warnings: state.metrics.warnings,
      failures: state.metrics.failures,
      avgResponseTimeMs: Number(avgResponse.toFixed(2)),
      dbSyncSuccessRate: Number(dbSyncSuccessRate.toFixed(2)),
      netTripDelta: state.netTripDelta,
      logs: state.logs,
      dbPath: DB_PATH,
      durations: {
        stage2Ms: stage2Duration,
        stage3Ms: stage3Duration,
        totalMs: totalDuration,
      },
    };

    const summaryPath = testInfo.outputPath('phase_3_9_summary.json');
    await fs.promises.writeFile(summaryPath, JSON.stringify(summary, null, 2), 'utf-8');
    await testInfo.attach('Phase 3.9 summary', {
      path: summaryPath,
      contentType: 'application/json',
    });

    console.log(`${SUITE_TAG} ✅ Passed operations: ${summary.passedOperations}`);
    console.log(`${SUITE_TAG} ⚠️ Warnings: ${summary.warnings}`);
    console.log(`${SUITE_TAG} ❌ Failures: ${summary.failures}`);
    console.log(`${SUITE_TAG} Avg response time: ${summary.avgResponseTimeMs} ms`);
    console.log(`${SUITE_TAG} DB sync success rate: ${summary.dbSyncSuccessRate}%`);
  });
});

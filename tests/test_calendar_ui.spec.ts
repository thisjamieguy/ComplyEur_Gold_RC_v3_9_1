import * as fs from 'fs';
import * as path from 'path';
import { expect, Locator, Page, TestInfo, test } from '@playwright/test';

const CALENDAR_URL = '/calendar';
const DAY_WIDTH = 28;
const FIXTURE_ROOT = path.join(process.cwd(), 'tests', 'fixtures');
const CREDENTIALS_PATH = path.join(FIXTURE_ROOT, 'credentials.json');

type ConsoleEntry = {
  type: string;
  message: string;
  location?: string;
  stack?: string;
};

type TripSnapshot = {
  id: number;
  start: string;
  end: string;
  employee: string;
  country: string;
  riskLevel: string;
};

const credentials = JSON.parse(fs.readFileSync(CREDENTIALS_PATH, 'utf-8'));
const ADMIN_USERNAME: string = credentials.admin.username;
const ADMIN_PASSWORD: string = credentials.admin.password;

const consoleKey = Symbol('phase38ConsoleLogs');

async function save_console_logs(testInfo: TestInfo, logs: ConsoleEntry[]) {
  if (!logs.length) {
    return;
  }
  const outputDir = testInfo.outputDir;
  const logDir = path.join(outputDir, 'console');
  await fs.promises.mkdir(logDir, { recursive: true });
  const slug = testInfo.title.replace(/[^a-z0-9]+/gi, '_').toLowerCase();
  const filePath = path.join(logDir, `${slug}.log`);
  const content = logs
    .map((entry) => {
      const location = entry.location ? ` @ ${entry.location}` : '';
      return `[${entry.type.toUpperCase()}] ${entry.message}${location}${entry.stack ? `\n${entry.stack}` : ''}`;
    })
    .join('\n');
  await fs.promises.writeFile(filePath, content, 'utf-8');
  await testInfo.attach('console-log', {
    path: filePath,
    contentType: 'text/plain',
  });
}

async function ensureAuthenticated(page: Page) {
  const response = await page.goto(CALENDAR_URL, { waitUntil: 'networkidle' });
  if (response && response.status() === 200 && !page.url().includes('/login')) {
    return;
  }

  if (!page.url().includes('/login')) {
    await page.goto('/login', { waitUntil: 'domcontentloaded' });
  }

  const usernameField = page.locator('input[name="username"], #username');
  if (await usernameField.count()) {
    await usernameField.first().fill(ADMIN_USERNAME);
  }
  const passwordField = page.locator('input[name="password"], #password');
  await passwordField.first().fill(ADMIN_PASSWORD);
  const submitButton = page
    .locator(
      'button[type="submit"], #loginBtn, button:has-text("Login"), button:has-text("Log in")',
    )
    .first();

  await Promise.all([
    page.waitForNavigation({ waitUntil: 'networkidle' }),
    submitButton.click(),
  ]);

  if (!page.url().includes(CALENDAR_URL)) {
    await page.goto(CALENDAR_URL, { waitUntil: 'networkidle' });
  }
}

async function gotoCalendar(page: Page) {
  await ensureAuthenticated(page);
  await expect(page.locator('#calendar')).toBeVisible({ timeout: 15_000 });
  await expect(page.locator('.calendar-trip').first()).toBeVisible();
}

async function dragTrip(page: Page, trip: Locator, distanceX: number) {
  const box = await trip.boundingBox();
  if (!box) {
    throw new Error('Unable to calculate bounding box for trip element.');
  }
  const startX = box.x + box.width / 2;
  const startY = box.y + box.height / 2;
  await page.mouse.move(startX, startY);
  await page.mouse.down();
  await page.mouse.move(startX + distanceX, startY, { steps: 12 });
  await page.mouse.up();
}

async function readTripSnapshot(trip: Locator): Promise<TripSnapshot> {
  const attrs = await trip.evaluate((node) => ({
    id: Number.parseInt(node.getAttribute('data-trip-id') || '', 10),
    start: node.getAttribute('data-start') || '',
    end: node.getAttribute('data-end') || '',
    employee: node.getAttribute('data-employee') || '',
    country: node.getAttribute('data-country') || '',
    riskLevel: node.getAttribute('data-compliance') || '',
  }));
  if (!Number.isFinite(attrs.id)) {
    throw new Error('Trip element missing data-trip-id attribute.');
  }
  return attrs as TripSnapshot;
}

function addDays(iso: string, days: number): string {
  const base = new Date(`${iso}T00:00:00Z`);
  if (Number.isNaN(base.getTime())) {
    throw new Error(`Invalid ISO date provided: ${iso}`);
  }
  base.setUTCDate(base.getUTCDate() + days);
  return base.toISOString().split('T')[0];
}

async function fetchTripFromApi(page: Page, tripId: number) {
  const response = await page.request.get('/api/trips');
  expect(response.ok()).toBeTruthy();
  const payload = await response.json();
  const trips = Array.isArray(payload?.trips) ? payload.trips : payload;
  const match = trips.find((trip: any) => Number(trip.id) === tripId);
  return match ?? null;
}

async function resetTripDates(page: Page, tripId: number, start: string, end: string) {
  const response = await page.request.post('/api/update_trip_dates', {
    data: { trip_id: tripId, start_date: start, end_date: end },
  });
  expect(response.ok()).toBeTruthy();
}

test.describe.serial('Calendar Phase 3.8 UI', () => {
  test.beforeEach(async ({ page }) => {
    const buffer: ConsoleEntry[] = [];
    (page as unknown as Record<symbol, ConsoleEntry[]>)[consoleKey] = buffer;

    page.on('console', (msg) => {
      if (msg.type() !== 'error') {
        return;
      }
      buffer.push({
        type: msg.type(),
        message: msg.text(),
        location: msg.location()?.url,
      });
    });

    page.on('pageerror', (error) => {
      buffer.push({
        type: 'pageerror',
        message: error.message,
        stack: error.stack,
      });
    });
  });

  test.afterEach(async ({ page }, testInfo) => {
    const logs = (page as unknown as Record<symbol, ConsoleEntry[]>)[consoleKey] ?? [];
    if (testInfo.status !== 'passed') {
      await save_console_logs(testInfo, logs);
    }
    expect(logs.filter((entry) => entry.type === 'error' || entry.type === 'pageerror')).toEqual([]);
  });

  test('renders calendar trips aligned with API payload', async ({ page }) => {
    await gotoCalendar(page);
    const firstTrip = page.locator('.calendar-trip').first();
    await expect(firstTrip).toBeVisible();

    const snapshot = await readTripSnapshot(firstTrip);
    expect(snapshot.employee).toBeTruthy();
    expect(snapshot.start).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    expect(snapshot.end).toMatch(/^\d{4}-\d{2}-\d{2}$/);

    const apiTrip = await fetchTripFromApi(page, snapshot.id);
    expect(apiTrip).not.toBeNull();
    expect(apiTrip.start_date || apiTrip.entry_date).toBe(snapshot.start);
    expect(apiTrip.end_date || apiTrip.exit_date).toBe(snapshot.end);
  });

  test('dragging a trip updates backend and survives reload', async ({ page }) => {
    await gotoCalendar(page);
    const trip = page.locator('.calendar-trip').first();
    const before = await readTripSnapshot(trip);

    const [updateRequest, updateResponse] = await Promise.all([
      page.waitForRequest(
        (request) =>
          request.url().includes('/api/update_trip_dates') && request.method() === 'POST',
      ),
      page.waitForResponse(
        (response) =>
          response.url().includes('/api/update_trip_dates') &&
          response.request().method() === 'POST',
      ),
      dragTrip(page, trip, DAY_WIDTH * 2),
    ]);

    const payload = updateRequest.postDataJSON();
    expect(payload.trip_id).toBe(before.id);
    expect(updateResponse.ok()).toBeTruthy();

    const after = await readTripSnapshot(trip);
    expect(after.start).not.toBe(before.start);
    expect(after.end).not.toBe(before.end);

    const dbTrip = await fetchTripFromApi(page, before.id);
    expect(dbTrip.start_date || dbTrip.entry_date).toBe(after.start);
    expect(dbTrip.end_date || dbTrip.exit_date).toBe(after.end);

    await page.reload({ waitUntil: 'networkidle' });
    const postReload = await readTripSnapshot(page.locator(`.calendar-trip[data-trip-id="${before.id}"]`));
    expect(postReload.start).toBe(after.start);
    expect(postReload.end).toBe(after.end);

    await resetTripDates(page, before.id, before.start, before.end);
    await page.reload({ waitUntil: 'networkidle' });
  });

  test('editing trip duration recalculates risk and enforces 90-day threshold', async ({ page }) => {
    await gotoCalendar(page);
    const safeTrip = page.locator('.calendar-trip[data-compliance="safe"]').first();
    await expect(safeTrip).toBeVisible();
    const original = await readTripSnapshot(safeTrip);
    const overlay = page.locator('#calendar-detail-overlay');

    await safeTrip.click();
    await expect(overlay).toBeVisible();

    const editTrigger = page.locator('[data-action="edit-trip"]').first();
    await editTrigger.click();

    const form = page.locator('#calendar-form');
    await expect(form).toBeVisible();

    const newEnd = addDays(original.start, 120);
    await form.locator('input[name="country"]').fill(original.country || 'DE');
    await form.locator('input[name="start_date"]').fill(original.start);
    await form.locator('input[name="end_date"]').fill(newEnd);

    const [patchRequest, patchResponse] = await Promise.all([
      page.waitForRequest(
        (request) => request.url().includes(`/api/trips/${original.id}`) && request.method() === 'PATCH',
      ),
      page.waitForResponse(
        (response) => response.url().includes(`/api/trips/${original.id}`) && response.request().method() === 'PATCH',
      ),
      form.locator('button[data-action="submit-form"]').click(),
    ]);
    expect(patchResponse.ok()).toBeTruthy();
    expect(patchRequest.postDataJSON().end_date).toBe(newEnd);

    await expect(page.locator('#calendar-toast')).toContainText('Trip updated', { timeout: 10_000 });

    const updatedTrip = page.locator(`.calendar-trip[data-trip-id="${original.id}"]`);
    await expect(updatedTrip).toHaveAttribute('data-compliance', 'critical', { timeout: 10_000 });

    const riskBadge = page.locator('[data-forecast-status]');
    await expect(riskBadge).toContainText(/High risk|Danger/i);

    await resetTripDates(page, original.id, original.start, original.end);
    await page.reload({ waitUntil: 'networkidle' });
  });

  test('forecast panel stays in sync with employee detail view', async ({ page }) => {
    await gotoCalendar(page);

    const firstTrip = page.locator('.calendar-trip').first();
    const firstSnapshot = await readTripSnapshot(firstTrip);
    await firstTrip.click();
    await expect(page.locator('#calendar-detail-overlay')).toBeVisible();
    await expect(page.locator('[data-forecast-employee]')).toContainText(firstSnapshot.employee);
    await expect(page.locator('#calendar-detail-employee')).toContainText(firstSnapshot.employee);
    await page.keyboard.press('Escape');
    await expect(page.locator('#calendar-detail-overlay')).toBeHidden();

    const secondTrip = page.locator('.calendar-trip').nth(1);
    const secondSnapshot = await readTripSnapshot(secondTrip);
    await secondTrip.click();
    await expect(page.locator('#calendar-detail-overlay')).toBeVisible();
    await expect(page.locator('[data-forecast-employee]')).toContainText(secondSnapshot.employee);
    await expect(page.locator('#calendar-detail-employee')).toContainText(secondSnapshot.employee);
    await page.keyboard.press('Escape');
    await expect(page.locator('#calendar-detail-overlay')).toBeHidden();
  });

  test('tooltip exposes employee, country, and date metadata', async ({ page }) => {
    await gotoCalendar(page);
    const trip = page.locator('.calendar-trip').first();
    const snapshot = await readTripSnapshot(trip);

    await trip.hover();
    const tooltip = page.locator('.calendar-tooltip--visible');
    await expect(tooltip).toBeVisible({ timeout: 5_000 });

    if (snapshot.employee) {
      await expect(tooltip).toContainText(snapshot.employee);
    }
    await expect(tooltip).toContainText(snapshot.country);
    await expect(tooltip).toContainText(snapshot.start);
  });
});

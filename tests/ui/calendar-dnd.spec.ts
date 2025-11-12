import { test, expect } from '@playwright/test';
import path from 'path';
import { promises as fs } from 'fs';

const sandboxRoot = path.resolve(__dirname, '../../calendar_dev/dev');
const SANDBOX_HOST = 'http://sandbox.local';
const SANDBOX_PAGE = `${SANDBOX_HOST}/calendar_sandbox.html`;

async function mountSandbox(page) {
  await page.route('**/*', async (route) => {
    const url = new URL(route.request().url());
    if (url.hostname !== 'sandbox.local') {
      return route.continue();
    }
    let relativePath = url.pathname;
    if (relativePath === '/' || !relativePath) {
      relativePath = '/calendar_sandbox.html';
    }
    const diskPath = path.join(sandboxRoot, relativePath.replace(/^\/+/, ''));
    try {
      const body = await fs.readFile(diskPath);
      await route.fulfill({
        status: 200,
        body,
        headers: {
          'content-type': getContentType(diskPath),
        },
      });
    } catch (error) {
      await route.fulfill({ status: 404, body: `Missing ${relativePath}` });
    }
  });
}

function getContentType(filePath: string) {
  const ext = path.extname(filePath).toLowerCase();
  if (ext === '.html') return 'text/html';
  if (ext === '.js') return 'text/javascript';
  if (ext === '.css') return 'text/css';
  if (ext === '.json') return 'application/json';
  if (ext === '.svg') return 'image/svg+xml';
  return 'text/plain';
}

async function getTripById(page, id: string | number) {
  return page.evaluate((tripId) => {
    const app = (window as any).calendarAppInstance;
    if (!app) return null;
    const match = app.trips.find((trip: any) => String(trip.id) === String(tripId));
    if (!match) return null;
    return {
      employee: match.employee,
      start: app.formatISO(match.startDate),
      end: app.formatISO(match.endDate),
    };
  }, id);
}

async function dragTripToDate(page, employeeLabel: string, targetIso: string) {
  const pill = page.locator('.trip-pill', { hasText: employeeLabel }).first();
  await pill.waitFor();
  const targetCell = page.locator(`.day-cell[data-date="${targetIso}"]`).first();
  await targetCell.waitFor();
  const pillBox = await pill.boundingBox();
  const targetBox = await targetCell.boundingBox();
  if (!pillBox || !targetBox) throw new Error('Missing bounding box data');
  await page.mouse.move(pillBox.x + pillBox.width / 2, pillBox.y + pillBox.height / 2);
  await page.mouse.down();
  await page.mouse.move(targetBox.x + targetBox.width / 2, targetBox.y + targetBox.height / 2, { steps: 8 });
  await page.mouse.up();
}

async function dragHandle(page, trip: { label: string; id: string | number }, handle: 'start' | 'end', targetIso: string) {
  const info = await getTripById(page, trip.id);
  const sourceIso = handle === 'start' ? info?.start : info?.end;
  if (!sourceIso) throw new Error('Unable to resolve trip boundary');
  const pill = page
    .locator(`.day-cell[data-date="${sourceIso}"] .trip-pill`, { hasText: trip.label })
    .first();
  const handleSelector = handle === 'start' ? '.resize-handle-left' : '.resize-handle-right';
  const grip = pill.locator(handleSelector);
  await grip.waitFor();
  const targetCell = page.locator(`.day-cell[data-date="${targetIso}"]`).first();
  await targetCell.waitFor();
  const gripBox = await grip.boundingBox();
  const cellBox = await targetCell.boundingBox();
  if (!gripBox || !cellBox) throw new Error('Missing drag geometry');
  await page.mouse.move(gripBox.x + gripBox.width / 2, gripBox.y + gripBox.height / 2);
  await page.mouse.down();
  await page.mouse.move(cellBox.x + cellBox.width / 2, cellBox.y + cellBox.height / 2, { steps: 8 });
  await page.mouse.up();
}

async function dragTripToLane(page, opts: { label: string; name: string; id: string | number }, laneName: string) {
  const pill = page.locator('.trip-pill', { hasText: opts.label }).first();
  await pill.waitFor();
  const snapshot = await getTripById(page, opts.id);
  const startIso = snapshot?.start;
  if (!startIso) throw new Error('Unable to resolve start date for trip');
  const startCell = page.locator(`.day-cell[data-date="${startIso}"]`).first();
  await startCell.waitFor();
  const lane = page.locator(`.employee-lane[data-employee-name="${laneName}"]`).first();
  await lane.waitFor();
  const pillBox = await pill.boundingBox();
  const cellBox = await startCell.boundingBox();
  const laneBox = await lane.boundingBox();
  if (!pillBox || !cellBox || !laneBox) throw new Error('Missing geometry for lane drag');
  const cellCenterX = cellBox.x + cellBox.width / 2;
  const cellCenterY = cellBox.y + cellBox.height / 2;
  const laneCenterX = laneBox.x + laneBox.width / 2;
  const laneCenterY = laneBox.y + laneBox.height / 2;
  await page.mouse.move(pillBox.x + pillBox.width / 2, pillBox.y + pillBox.height / 2);
  await page.mouse.down();
  await page.mouse.move(cellCenterX, cellCenterY, { steps: 4 });
  await page.mouse.move(cellCenterX, laneCenterY, { steps: 6 });
  await page.mouse.move(laneCenterX, laneCenterY, { steps: 4 });
  await page.mouse.up();
}

const alice = { label: 'Alice', name: 'Alice Doe', id: 101 } as const;
const bob = { label: 'Bob', name: 'Bob Smith', id: 102 } as const;
const carla = { label: 'Carla', name: 'Carla Ruiz', id: 103 } as const;
const dylan = { label: 'Dylan', name: 'Dylan Price', id: 'trip-dylan-uuid' } as const;

test.describe('Calendar drag + resize', () => {
  test.beforeEach(async ({ page }) => {
    await mountSandbox(page);
    await page.goto(SANDBOX_PAGE);
    await page.waitForSelector('.trip-pill');
  });

  test('dragging moves a trip across days', async ({ page }) => {
    await dragTripToDate(page, alice.label, '2024-05-09');
    await expect.poll(async () => (await getTripById(page, alice.id))?.start).toBe('2024-05-09');
    await expect.poll(async () => (await getTripById(page, alice.id))?.end).toBe('2024-05-11');
  });

  test('resize handles extend and shrink trip length', async ({ page }) => {
    await dragHandle(page, bob, 'end', '2024-05-15');
    await expect.poll(async () => (await getTripById(page, bob.id))?.end).toBe('2024-05-15');

    const bobPill = page.locator('.trip-pill', { hasText: bob.label }).first();
    await bobPill.focus();
    await bobPill.press('Shift+ArrowDown');
    await expect.poll(async () => (await getTripById(page, bob.id))?.end).toBe('2024-05-14');
  });

  test('lane drop reassigns employee without date drift', async ({ page }) => {
    const before = await getTripById(page, carla.id);
    await dragTripToLane(page, carla, bob.name);
    await expect.poll(async () => (await getTripById(page, carla.id))?.employee).toBe(bob.name);
    const after = await getTripById(page, carla.id);
    expect(after?.start?.slice(0, 7)).toBe(before?.start?.slice(0, 7));
  });

  test('keyboard fallback moves and resizes', async ({ page }) => {
    const pill = page.locator('.trip-pill', { hasText: alice.label }).first();
    await pill.focus();
    await pill.press('ArrowRight');
    await pill.press('Shift+ArrowLeft');
    await pill.press('Shift+ArrowUp');
    const snapshot = await getTripById(page, alice.id);
    expect(snapshot?.start).toBe('2024-05-07');
  });

  test('resizing obeys minimum one-day boundary', async ({ page }) => {
    const pill = page.locator('.trip-pill', { hasText: carla.label }).first();
    await pill.focus();
    await pill.press('Shift+ArrowUp');
    await pill.press('Shift+ArrowUp');
    const snapshot = await getTripById(page, carla.id);
    expect(snapshot?.start <= (snapshot?.end ?? '')).toBeTruthy();
  });

  test('uuid-backed trips can be repositioned via drag + keyboard', async ({ page }) => {
    await dragTripToDate(page, dylan.label, '2024-05-23');
    await expect.poll(async () => (await getTripById(page, dylan.id))?.start).toBe('2024-05-23');
    const pill = page.locator('.trip-pill', { hasText: dylan.label }).first();
    await pill.focus();
    await pill.press('ArrowLeft');
    const snapshot = await getTripById(page, dylan.id);
    expect(snapshot?.start).toBe('2024-05-22');
  });
});

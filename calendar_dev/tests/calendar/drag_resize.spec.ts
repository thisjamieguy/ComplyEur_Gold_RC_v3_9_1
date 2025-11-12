import { test, expect, Page } from '@playwright/test';

const SANDBOX_URL = '/calendar_sandbox.html?debug=1';
const DAY_MS = 24 * 60 * 60 * 1000;

const formatLocalISO = (date: Date) =>
  `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;

const addDays = (iso: string, delta: number) => {
  const [year, month, day] = iso.split('-').map(Number);
  const date = new Date(year, month - 1, day + delta);
  return formatLocalISO(date);
};

type PointerMode = 'mouse' | 'touch';

const getTripRange = async (page: Page, tripId: string) => {
  return page.evaluate((id) => {
    const app = (window as any).calendarAppInstance;
    if (!app) return null;
    const trip = app.trips.find((t: any) => String(t.id) === String(id));
    if (!trip) return null;
    const toISO = (value: Date) =>
      `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, '0')}-${String(value.getDate()).padStart(2, '0')}`;
    return { start: toISO(trip.startDate), end: toISO(trip.endDate) };
  }, tripId);
};

const expectTripRange = async (page: Page, tripId: string, start: string, end: string) => {
  await page.waitForFunction(
    ([id, targetStart, targetEnd]) => {
      const app = (window as any).calendarAppInstance;
      if (!app) return false;
      const trip = app.trips.find((t: any) => String(t.id) === String(id));
      if (!trip) return false;
      const toISO = (value: Date) =>
        `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, '0')}-${String(value.getDate()).padStart(2, '0')}`;
      return toISO(trip.startDate) === targetStart && toISO(trip.endDate) === targetEnd;
    },
    [tripId, start, end]
  );
  const range = await getTripRange(page, tripId);
  expect(range).toEqual({ start, end });
};

const dispatchPointerSequence = async (
  page: Page,
  from: { x: number; y: number },
  to: { x: number; y: number },
  steps: number,
  pointerType: PointerMode,
  scrollDuringDrag = false,
  selector: string
) => {
  await page.evaluate(
    async ({ start, endPoint, stepsCount, kind, shouldScroll, sourceSelector }) => {
      const targetEl = document.querySelector(sourceSelector);
      if (!targetEl) return;
      const dispatch = (type: string, coords: { x: number; y: number }) => {
        targetEl.dispatchEvent(
          new PointerEvent(type, {
            pointerId: 42,
            pointerType: kind,
            clientX: coords.x,
            clientY: coords.y,
            isPrimary: true,
            bubbles: true,
            cancelable: true,
            buttons: type === 'pointerup' ? 0 : 1,
            button: type === 'pointerup' ? -1 : 0,
          })
        );
      };
      const waitFrame = () =>
        new Promise((resolve) => {
          requestAnimationFrame(() => resolve(undefined));
        });
      const scrollTrigger = shouldScroll ? Math.floor(stepsCount / 2) : null;
      dispatch('pointerdown', start);
      await waitFrame();
      for (let i = 1; i <= stepsCount; i += 1) {
        const ratio = i / stepsCount;
        dispatch('pointermove', {
          x: start.x + (endPoint.x - start.x) * ratio,
          y: start.y + (endPoint.y - start.y) * ratio,
        });
        if (shouldScroll && scrollTrigger && i === scrollTrigger) {
          window.scrollBy(0, window.innerHeight / 3);
        }
        await waitFrame();
      }
      dispatch('pointerup', endPoint);
      await waitFrame();
    },
    {
      start: from,
      endPoint: to,
      stepsCount: steps,
      kind: pointerType,
      shouldScroll: scrollDuringDrag ? 1 : 0,
      sourceSelector: selector,
    }
  );
};

const dragTripToDate = async (
  page: Page,
  {
    tripId,
    targetStartDate,
    pointerType = 'mouse',
    steps = 20,
    scrollDuringDrag = false,
  }: { tripId: string; targetStartDate: string; pointerType?: PointerMode; steps?: number; scrollDuringDrag?: boolean }
) => {
  const currentRange = await getTripRange(page, tripId);
  if (!currentRange) throw new Error(`Trip ${tripId} not found`);
  const sourceSelector = `.day-cell[data-date="${currentRange.start}"] .trip-pill[data-trip-id="${tripId}"]`;
  const pill = page.locator(sourceSelector).first();
  await expect(pill).toBeVisible();
  const startBox = await pill.boundingBox();
  if (!startBox) throw new Error('Missing pill bounding box');
  const targetCell = page.locator(`.day-cell[data-date="${targetStartDate}"]`).first();
  await expect(targetCell).toBeVisible();
  const targetBox = await targetCell.boundingBox();
  if (!targetBox) throw new Error('Missing target cell bounding box');
  const from = { x: startBox.x + startBox.width / 2, y: startBox.y + startBox.height / 2 };
  const to = { x: targetBox.x + targetBox.width / 2, y: targetBox.y + targetBox.height / 2 };

  await dispatchPointerSequence(page, from, to, steps, pointerType, scrollDuringDrag, sourceSelector);
  await page.waitForTimeout(120);
};

const resizeTripEdge = async (
  page: Page,
  {
    tripId,
    edge,
    targetDate,
    pointerType = 'mouse',
  }: { tripId: string; edge: 'left' | 'right'; targetDate: string; pointerType?: PointerMode }
) => {
  const current = await getTripRange(page, tripId);
  if (!current) throw new Error('Trip missing');
  const edgeDate = edge === 'left' ? current.start : current.end;
  const handleSelector = `.day-cell[data-date="${edgeDate}"] .trip-pill[data-trip-id="${tripId}"] .resize-handle-${edge === 'left' ? 'left' : 'right'}`;
  const handle = page.locator(handleSelector).first();
  await expect(handle).toBeVisible();
  const handleBox = await handle.boundingBox();
  if (!handleBox) throw new Error('Missing handle box');
  const targetCell = page.locator(`.day-cell[data-date="${targetDate}"]`).first();
  await expect(targetCell).toBeVisible();
  const targetBox = await targetCell.boundingBox();
  if (!targetBox) throw new Error('Missing target cell box');
  const from = { x: handleBox.x + handleBox.width / 2, y: handleBox.y + handleBox.height / 2 };
  const to = { x: targetBox.x + targetBox.width / 2, y: targetBox.y + targetBox.height / 2 };

  await dispatchPointerSequence(page, from, to, 15, pointerType, false, handleSelector);
  await page.waitForTimeout(120);
};

test.describe('Calendar drag & resize sandbox', () => {
  let consoleErrors: string[];

  test.beforeEach(async ({ page }) => {
    consoleErrors = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        const text = msg.text();
        if (!text.includes('favicon.ico')) {
          consoleErrors.push(text);
        }
      }
    });
    await page.goto(SANDBOX_URL);
    await page.waitForSelector('.trip-pill');
  });

  test.afterEach(async () => {
    expect(consoleErrors).toEqual([]);
  });

  test('A) drag 5-day trip forward by 3 days', async ({ page }) => {
    const tripId = 'trip-carla';
    const before = await getTripRange(page, tripId);
    const targetStart = addDays(before!.start, 3);
    await dragTripToDate(page, { tripId, targetStartDate: targetStart });
    await expectTripRange(page, tripId, targetStart, addDays(before!.end, 3));
  });

  test('B) drag across month boundary', async ({ page }) => {
    const tripId = 'trip-frida';
    const before = await getTripRange(page, tripId);
    const targetStart = '2024-06-01';
    await dragTripToDate(page, { tripId, targetStartDate: targetStart });
    const delta = Date.parse(targetStart) - Date.parse(before!.start);
    const dayDelta = Math.round(delta / DAY_MS);
    const expectedEnd = addDays(before!.end, dayDelta);
    await expectTripRange(page, tripId, targetStart, expectedEnd);
    const lastCommit = await page.evaluate(() => (window as any).calendarAppInstance?.lastCommit);
    expect(lastCommit).toEqual({
      tripId,
      startDate: targetStart,
      endDate: expectedEnd,
    });
  });

  test('C) resize right +4 days then left -2 days', async ({ page }) => {
    const tripId = 'trip-dylan';
    const before = await getTripRange(page, tripId);
    const extendEnd = addDays(before!.end, 4);
    await resizeTripEdge(page, { tripId, edge: 'right', targetDate: extendEnd });
    await expectTripRange(page, tripId, before!.start, extendEnd);
    const shiftStart = addDays(before!.start, -2);
    await resizeTripEdge(page, { tripId, edge: 'left', targetDate: shiftStart });
    await expectTripRange(page, tripId, shiftStart, extendEnd);
  });

  test('D) overlapping drag keeps both trips available', async ({ page }) => {
    const tripId = 'trip-bob';
    const targetStart = '2024-05-06';
    await dragTripToDate(page, { tripId, targetStartDate: targetStart });
    const range = await getTripRange(page, tripId);
    const overlapCell = page.locator(`.day-cell[data-date="${targetStart}"] .trip-pill`);
    const overlapCount = await overlapCell.count();
    expect(overlapCount).toBeGreaterThan(0);
    expect(range?.start === targetStart || range?.start === '2024-05-10').toBeTruthy();
  });

  test('E) drag while scrolling container', async ({ page }) => {
    await page.evaluate(() => {
      const app = (window as any).calendarAppInstance;
      app.currentDate = new Date('2024-06-01');
      app.render();
    });
    const tripId = 'trip-lena';
    const before = await getTripRange(page, tripId);
    const targetStart = '2024-06-18';
    await dragTripToDate(page, {
      tripId,
      targetStartDate: targetStart,
      scrollDuringDrag: true,
    });
    const delta = Math.round((Date.parse(targetStart) - Date.parse(before!.start)) / DAY_MS);
    await expectTripRange(page, tripId, targetStart, addDays(before!.end, delta));
  });

  test('F) high-speed flick drag snaps correctly', async ({ page }) => {
    const tripId = 'trip-alice';
    const targetStart = '2024-05-09';
    await dragTripToDate(page, { tripId, targetStartDate: targetStart, steps: 2 });
    await expectTripRange(page, tripId, targetStart, addDays(targetStart, 2));
  });

  test('G) zoomed browser maintains mapping', async ({ page }) => {
    const resolveIndex = async (iso: string) => {
      const cellLocator = page.locator(`.day-cell[data-date="${iso}"]`).first();
      await expect(cellLocator).toBeVisible();
      const box = await cellLocator.boundingBox();
      if (!box) return null;
      const coords = { x: box.x + box.width / 2, y: box.y + box.height / 2 };
      return page.evaluate(
        ({ date, center }) => {
          const idx = (window as any).calendarAppInstance.pointToCellIndex(center.x, center.y);
          const expected = (window as any).calendarAppInstance.dayIndexByISO.get(date);
          return { idx, expected };
        },
        { date: iso, center: coords }
      );
    };

    await page.evaluate(() => {
      document.body.style.zoom = '0.8';
    });
    await page.waitForTimeout(50);
    let first = await resolveIndex('2024-05-15');
    let { idx, expected } = first || { idx: null, expected: null };
    expect(idx).toBe(expected);

    await page.evaluate(() => {
      document.body.style.zoom = '1.25';
    });
    await page.waitForTimeout(50);
    const second = await resolveIndex('2024-05-14');
    ({ idx, expected } = second || { idx: null, expected: null });
    expect(idx).toBe(expected);

    await page.evaluate(() => {
      document.body.style.zoom = '1';
    });
  });

  test('H) touch pointer drag updates dates', async ({ page }) => {
    await page.evaluate(() => {
      Object.defineProperty(navigator, 'maxTouchPoints', {
        configurable: true,
        value: 5,
      });
    });
    const tripId = 'trip-bob';
    const targetStart = '2024-05-13';
    await dragTripToDate(page, { tripId, targetStartDate: targetStart, steps: 5 });
    await expectTripRange(page, tripId, targetStart, addDays(targetStart, 2));
    await page.evaluate(() => {
      Object.defineProperty(navigator, 'maxTouchPoints', {
        configurable: true,
        value: 0,
      });
    });
  });

  test('I) RTL layout still drag-resizable', async ({ page }) => {
    await page.evaluate(() => {
      document.documentElement.dir = 'rtl';
      document.body.setAttribute('data-rtl-test', '1');
    });
    const tripId = 'trip-alice';
    await dragTripToDate(page, { tripId, targetStartDate: '2024-05-07' });
    await expectTripRange(page, tripId, '2024-05-07', '2024-05-09');
  });

  test('J) virtualization guard keeps grid stable during drag', async ({ page }) => {
    const tripId = 'trip-carla';
    const before = await page.evaluate(() => {
      const app = (window as any).calendarAppInstance;
      window.__virtualizationSamples = [];
      window.__virtualizationProbe = (payload: any) => {
        window.__virtualizationSamples.push(payload);
      };
      return {
        length: app.visibleDays.length,
        cellCount: app.gridEl.querySelectorAll('.day-cell').length,
      };
    });
    await dragTripToDate(page, {
      tripId,
      targetStartDate: '2024-05-19',
      steps: 6,
    });
    const probeResults = await page.evaluate(() => {
      const samples = window.__virtualizationSamples || [];
      delete window.__virtualizationProbe;
      delete window.__virtualizationSamples;
      return samples;
    });
    expect(probeResults.length).toBeGreaterThan(0);
    for (const sample of probeResults) {
      expect(sample.visibleLength).toBe(before.length);
      expect(sample.cellCount).toBe(before.cellCount);
    }
    await expectTripRange(page, tripId, '2024-05-19', '2024-05-23');
  });
});

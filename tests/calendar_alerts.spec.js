'use strict';

const { test, expect } = require('@playwright/test');

const CALENDAR_PATH = '/calendar';
const ADMIN_PASSWORD = process.env.CALENDAR_QA_PASSWORD || 'admin123';
const DEFAULT_HEIGHT = 900;

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

function createTripForEmployee(employee, { startOffset = -30, endOffset = -24, country = 'France' } = {}) {
  const startIso = isoFromOffset(startOffset);
  const endIso = isoFromOffset(endOffset);
  const travelDays = inclusiveDayCount(startIso, endIso);
  const timestamp = new Date().toISOString();

  return {
    id: Number(`${employee.id}${Math.abs(startOffset)}`),
    employee_id: employee.id,
    employee_name: employee.name,
    country,
    entry_date: startIso,
    exit_date: endIso,
    start_date: startIso,
    end_date: endIso,
    travel_days: travelDays,
    purpose: '',
    job_ref: '',
    created_at: timestamp,
    updated_at: timestamp,
  };
}

function buildAlertsMock({ totalEmployees = 10 } = {}) {
  const baseAlerts = [
    {
      id: 801,
      employee_id: 301,
      name: 'Yara Yellow',
      risk_level: 'YELLOW',
      days_used: 76,
      days_remaining: 14,
      message: 'Warning: Yara Yellow has 76/90 days used (14 left)'
    },
    {
      id: 802,
      employee_id: 302,
      name: 'Omar Orange',
      risk_level: 'ORANGE',
      days_used: 86,
      days_remaining: 4,
      message: 'Warning: Omar Orange has 86/90 days used (4 left)'
    },
    {
      id: 803,
      employee_id: 303,
      name: 'Riya Red',
      risk_level: 'RED',
      days_used: 92,
      days_remaining: -2,
      message: 'Warning: Riya Red has 92/90 days used (2 over limit)'
    }
  ];

  const employees = baseAlerts.map((alert, index) => ({
    id: alert.employee_id,
    name: alert.name,
    active: true,
    priority: index,
  }));

  while (employees.length < totalEmployees) {
    const id = 400 + employees.length;
    employees.push({
      id,
      name: `Employee ${id}`,
      active: true,
      priority: employees.length,
    });
  }

  const trips = employees.map((employee, index) => {
    const startOffset = -14 - (index % 6);
    const endOffset = startOffset + 4;
    return createTripForEmployee(employee, { startOffset, endOffset, country: index % 2 === 0 ? 'France' : 'Germany' });
  });

  let alerts = baseAlerts.map((alert) => ({
    id: alert.id,
    employee_id: alert.employee_id,
    employee_name: alert.name,
    risk_level: alert.risk_level,
    message: alert.message,
    created_at: new Date().toISOString(),
    email_sent: 0,
    days_used: alert.days_used,
    days_remaining: alert.days_remaining,
  }));
  let nextAlertId = alerts.reduce((max, item) => Math.max(max, item.id), 0) + 1;

  function serializeAlerts() {
    return alerts
      .slice()
      .sort((a, b) => {
        const priority = { RED: 3, ORANGE: 2, YELLOW: 1 };
        return (priority[b.risk_level] || 0) - (priority[a.risk_level] || 0);
      })
      .map((alert) => ({ ...alert }));
  }

  return {
    getPayload() {
      return {
        generated_at: new Date().toISOString(),
        employees: employees
          .slice()
          .sort((a, b) => a.priority - b.priority)
          .map(({ id, name, active }) => ({ id, name, active })),
        trips: trips.map((trip) => ({ ...trip })),
        alerts: serializeAlerts(),
      };
    },
    resolveAlert(alertId) {
      alerts = alerts.filter((alert) => alert.id !== alertId);
    },
    updateAlert(employeeId, update) {
      alerts = alerts.filter((alert) => alert.employee_id !== employeeId);
      if (update) {
        alerts.push({
          id: nextAlertId += 1,
          employee_id: employeeId,
          employee_name: employees.find((emp) => emp.id === employeeId)?.name || `Employee ${employeeId}`,
          created_at: new Date().toISOString(),
          email_sent: 0,
          days_used: update.days_used,
          days_remaining: update.days_remaining,
          message: update.message,
          risk_level: update.risk_level,
        });
      }
    },
    getAlerts() {
      return serializeAlerts();
    },
  };
}

async function ensureAuthenticated(page) {
  const probe = await page.request.get('/calendar', { failOnStatusCode: false });
  if (probe.status() === 200) {
    const body = await probe.text();
    if (!/Login - EU Trip Tracker/i.test(body)) {
      return;
    }
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

async function bootstrapAlertsCalendar(page, options = {}) {
  const { viewport, totalEmployees = 10 } = options;
  const api = buildAlertsMock({ totalEmployees });

  await ensureAuthenticated(page);

  await page.route('**/api/trips', async (route) => {
    if (route.request().method() !== 'GET') {
      await route.continue();
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(api.getPayload()),
    });
  });

  await page.route('**/api/alerts/*/resolve', async (route) => {
    const url = new URL(route.request().url());
    const id = Number.parseInt(url.pathname.split('/').pop(), 10);
    api.resolveAlert(id);
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ success: true }),
    });
  });

  if (viewport) {
    await page.setViewportSize({ width: viewport.width, height: viewport.height ?? DEFAULT_HEIGHT });
  }

  await page.goto(CALENDAR_PATH, { waitUntil: 'networkidle' });
  await expect(page.locator('#calendar')).toBeVisible();
  await expect(page.locator('.calendar-employee-alert')).toHaveCount(api.getAlerts().length);

  return {
    api,
    async reload() {
      await page.evaluate(() => {
        const root = document.getElementById('calendar');
        const controller = root && root.__calendarController;
        if (controller) {
          controller.loadData({ force: true, centerOnToday: false });
        }
      });
      await page.waitForFunction(() => {
        const el = document.querySelector('#calendar-loading');
        return el ? el.hidden : true;
      }, { timeout: 5000 });
    },
  };
}

test.afterEach(async ({ page }) => {
  await page.close();
});

test.describe('Calendar alerts panel', () => {
  test('displays risk icons for yellow, orange, and red thresholds', async ({ page }) => {
    await bootstrapAlertsCalendar(page);

    const yellowIcon = page.locator('.calendar-employee-item[data-employee-id="301"] .calendar-employee-alert');
    const orangeIcon = page.locator('.calendar-employee-item[data-employee-id="302"] .calendar-employee-alert');
    const redIcon = page.locator('.calendar-employee-item[data-employee-id="303"] .calendar-employee-alert');

    await expect(yellowIcon).toHaveClass(/calendar-employee-alert--yellow/);
    await expect(orangeIcon).toHaveClass(/calendar-employee-alert--orange/);
    await expect(redIcon).toHaveClass(/calendar-employee-alert--red/);

    const panelItems = page.locator('.calendar-alerts-item');
    await expect(panelItems).toHaveCount(3);
  });

  test('shows tooltip and resolves alerts from the panel', async ({ page }) => {
    await bootstrapAlertsCalendar(page);

    const redIcon = page.locator('.calendar-employee-item[data-employee-id="303"] .calendar-employee-alert');
    await redIcon.hover();
    const tooltip = page.locator('.calendar-tooltip');
    await expect(tooltip).toHaveClass(/calendar-tooltip--visible/);
    await expect(tooltip).toContainText('Critical risk');

    const resolveButton = page.locator('.calendar-alerts-item[data-employee-id="303"] button[data-action="resolve-alert"]');
    await expect(resolveButton).toBeVisible();

    const resolveResponse = page.waitForResponse((response) => {
      return response.url().includes('/api/alerts/') && response.request().method() === 'POST';
    });
    await resolveButton.click();
    const response = await resolveResponse;
    expect(response.ok()).toBeTruthy();

    await expect(page.locator('.calendar-alerts-item[data-employee-id="303"]')).toHaveCount(0);
    await expect(page.locator('.calendar-employee-item[data-employee-id="303"] .calendar-employee-alert')).toHaveCount(0);
  });

  test('refreshes alerts when risk drops below threshold', async ({ page }) => {
    const { api, reload } = await bootstrapAlertsCalendar(page);

    api.updateAlert(301, null); // remove yellow alert entirely
    await reload();

    await expect(page.locator('.calendar-employee-item[data-employee-id="301"] .calendar-employee-alert')).toHaveCount(0);
    await expect(page.locator('.calendar-alerts-filter[data-alert-filter="all"] .calendar-alerts-filter-count')).toHaveText('2');
  });

  test('maintains frame budget during heavy render', async ({ page }) => {
    await bootstrapAlertsCalendar(page, { totalEmployees: 32, viewport: { width: 1400, height: 920 } });

    const duration = await page.evaluate(() => {
      const controller = document.getElementById('calendar').__calendarController;
      if (!controller) return 0;
      controller.renderRows();
      const start = performance.now();
      return new Promise((resolve) => {
        const checkComplete = () => {
          if (!controller.state.isRendering) {
            resolve(performance.now() - start);
          } else {
            requestAnimationFrame(checkComplete);
          }
        };
        requestAnimationFrame(checkComplete);
      });
    });

    expect(duration).toBeLessThan(48); // ~3 frames @ 60 FPS
  });
});

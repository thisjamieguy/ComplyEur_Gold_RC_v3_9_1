'use strict';

const { expect } = require('@playwright/test');

const CALENDAR_PATH = '/calendar';
const ADMIN_PASSWORD = process.env.CALENDAR_QA_PASSWORD || 'admin123';

async function navigateToCalendar(page, { waitSelector = '.calendar-trip' } = {}) {
  await page.goto(CALENDAR_PATH, { waitUntil: 'networkidle' });

  const passwordField = page.locator('input[name="password"], #password');
  if (await passwordField.count()) {
    await passwordField.fill(ADMIN_PASSWORD);
    const submit = page.locator('button[type="submit"], #loginBtn, button:has-text("Login"), button:has-text("Log in")');
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'networkidle' }),
      submit.first().click(),
    ]);
    await page.goto(CALENDAR_PATH, { waitUntil: 'networkidle' });
  }

  await expect(page.locator(waitSelector).first()).toBeVisible({ timeout: 10000 });
}

module.exports = {
  CALENDAR_PATH,
  ADMIN_PASSWORD,
  navigateToCalendar,
};


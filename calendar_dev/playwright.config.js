// @ts-check
const { defineConfig, devices } = require('@playwright/test');
const path = require('path');

module.exports = defineConfig({
  testDir: path.join(__dirname, 'tests'),
  timeout: 120 * 1000,
  expect: {
    timeout: 5 * 1000,
  },
  forbidOnly: !!process.env.CI,
  fullyParallel: false,
  workers: 1,
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
  ],
  outputDir: path.join(__dirname, 'playwright-test-results'),
  use: {
    baseURL: 'http://127.0.0.1:4173',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 15 * 1000,
    navigationTimeout: 20 * 1000,
    viewport: { width: 1400, height: 900 },
    headless: true,
  },
  projects: [
    {
      name: 'Chromium',
      use: {
        ...devices['Desktop Chrome'],
        channel: 'chrome',
        launchOptions: {
          args: ['--disable-crash-reporter', '--no-crashpad'],
          chromiumSandbox: false,
        },
      },
    },
    {
      name: 'WebKit',
      use: { ...devices['Desktop Safari'] },
    },
  ],
  webServer: {
    command: 'python3 -m http.server 4173 --directory dev',
    url: 'http://127.0.0.1:4173/calendar_dev.html',
    reuseExistingServer: !process.env.CI,
    stdout: 'pipe',
    stderr: 'pipe',
  },
});

const { defineConfig } = require('@playwright/test');

const host = process.env.E2E_HOST ?? process.env.HOST ?? '127.0.0.1';
const port = Number(process.env.E2E_PORT ?? process.env.PORT ?? '5001');
const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? `http://${host}:${port}`;

// Check if login state file exists
const path = require('path');
const fs = require('fs');
const projectRoot = process.cwd();
const statePath = path.join(projectRoot, 'tests', 'auth', 'state.json');
const storageState = fs.existsSync(statePath) ? statePath : undefined;

module.exports = defineConfig({
  testDir: './tests',
  testMatch: /.*\.spec\.js/,
  timeout: 30000,
  expect: {
    timeout: 5000,
  },
  reporter: [
    ['list'],
    ['html', { outputFolder: 'tests/results/html-report', open: 'never' }],
  ],
  use: {
    baseURL,
    storageState,
    headless: true,
    viewport: { width: 1280, height: 900 },
    ignoreHTTPSErrors: true,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  outputDir: 'tests/results/artifacts',
  retries: process.env.CI ? 1 : 0,
});


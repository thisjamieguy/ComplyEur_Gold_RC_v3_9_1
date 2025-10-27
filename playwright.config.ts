import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: 'tests/e2e',
  use: {
    baseURL: 'http://127.0.0.1:5000',
    headless: false,
    channel: 'chrome',
  },
  retries: 0,
  timeout: 30000,
});



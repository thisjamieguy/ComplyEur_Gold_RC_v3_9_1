import path from 'path';
import { defineConfig } from '@playwright/test';

const projectRoot = process.cwd();
const host = process.env.E2E_HOST ?? process.env.HOST ?? '127.0.0.1';
const port = Number(process.env.E2E_PORT ?? process.env.PORT ?? '5001');
const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? `http://${host}:${port}`;
const defaultPython = process.platform === 'win32'
  ? path.join(projectRoot, 'venv', 'Scripts', 'python.exe')
  : path.join(projectRoot, 'venv', 'bin', 'python');
const pythonInterpreter = process.env.PLAYWRIGHT_PYTHON ?? defaultPython;
const runLocalScript = process.env.PLAYWRIGHT_APP_ENTRY ?? path.join(projectRoot, 'run_local.py');
const webServerCommand = process.env.PLAYWRIGHT_SERVER_COMMAND ?? `"${pythonInterpreter}" "${runLocalScript}"`;

export default defineConfig({
  testDir: 'tests/e2e',
  timeout: 30_000,
  expect: {
    timeout: 5_000,
  },
  retries: process.env.CI ? 1 : 0,
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
  ],
  use: {
    baseURL,
    headless: !!process.env.CI,
    browserName: 'chromium',
    viewport: { width: 1440, height: 900 },
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  webServer: [
    {
      command: webServerCommand,
      url: `${baseURL}/healthz`,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        HOST: host,
        PORT: String(port),
        FLASK_DEBUG: 'false',
        PYTHONUNBUFFERED: '1',
      },
    },
  ],
});



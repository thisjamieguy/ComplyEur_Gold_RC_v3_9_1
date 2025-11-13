/**
 * Playwright Configuration for ComplyEur Full-Site UI Testing
 * 
 * This configuration sets up comprehensive UI testing including:
 * - Headless browser mode for CI/CD
 * - Screenshot and video capture on failure
 * - Console and network logging
 * - Retry logic for flaky tests
 */

module.exports = {
  testDir: './tests',
  timeout: 30000,
  retries: 2,
  workers: 1, // Run tests sequentially to avoid conflicts
  
  use: {
    baseURL: 'http://localhost:5001',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
    
    // Capture all console messages
    launchOptions: {
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
      ],
    },
  },

  projects: [
    {
      name: 'chromium',
      use: {
        browserName: 'chromium',
        viewport: { width: 1920, height: 1080 },
        ignoreHTTPSErrors: true,
      },
    },
  ],

  reporter: [
    ['list'],
    ['html', { outputFolder: 'reports/playwright-report', open: 'never' }],
    ['json', { outputFile: 'reports/test-results.json' }],
  ],

  outputDir: 'screenshots',
};


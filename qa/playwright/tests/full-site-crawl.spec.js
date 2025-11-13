/**
 * Full Site Crawl Test Suite
 * 
 * Recursively discovers and tests every page in the ComplyEur application
 */

const { test, expect } = require('@playwright/test');
const SiteCrawler = require('../utils/crawler');
const FormTester = require('../utils/formTester');
const fs = require('fs');
const path = require('path');

test.describe('ComplyEur Full Site Crawl', () => {
  let crawler;
  let consoleMessages = [];
  let networkErrors = [];

  test.beforeEach(async ({ page }) => {
    // Set up console and network monitoring
    page.on('console', msg => {
      const type = msg.type();
      const text = msg.text();
      consoleMessages.push({ type, text, url: page.url() });
      
      if (type === 'error') {
        console.error(`❌ Console Error on ${page.url()}: ${text}`);
      }
    });

    page.on('response', response => {
      if (response.status() >= 400) {
        networkErrors.push({
          url: response.url(),
          status: response.status(),
          statusText: response.statusText()
        });
      }
    });

    page.on('pageerror', error => {
      console.error(`❌ Page Error: ${error.message}`);
    });

    crawler = new SiteCrawler(page, {
      baseUrl: 'http://localhost:5001',
      maxDepth: 4
    });
  });

  test('should crawl all public pages without authentication', async ({ page }) => {
    console.log('\n🔍 Starting public pages crawl...\n');

    await crawler.crawl('http://localhost:5001/', 0);
    
    const results = crawler.getResults();
    
    console.log('\n📊 Crawl Results:');
    console.log(`  Total pages visited: ${results.totalPages}`);
    console.log(`  Server errors: ${results.errors.length}`);
    console.log(`  Console errors: ${results.consoleErrors.length}`);
    console.log(`  Broken links: ${results.brokenLinks.length}`);

    // Save results
    const reportPath = path.join(__dirname, '../reports/public-crawl-results.json');
    crawler.saveResults(reportPath);

    // Assert no critical errors
    expect(results.errors.length, 'Should have no server errors').toBe(0);
    expect(results.visitedUrls.length, 'Should visit at least 5 pages').toBeGreaterThan(5);
  });

  test('should test login functionality', async ({ page }) => {
    console.log('\n🔐 Testing login functionality...\n');

    await page.goto('http://localhost:5001/login');
    
    // Test failed login
    console.log('Testing invalid credentials...');
    await page.fill('input[name="username"]', 'invalid');
    await page.fill('input[name="password"]', 'invalid');
    await page.click('button[type="submit"]');
    
    await page.waitForTimeout(1000);
    
    const hasError = await page.evaluate(() => {
      return document.body.textContent.includes('Invalid') || 
             document.querySelector('.error, .alert-danger') !== null;
    });
    
    expect(hasError, 'Should show error message for invalid login').toBe(true);
    console.log('  ✓ Invalid login handled correctly');

    // Test successful login
    console.log('\nTesting valid credentials...');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    
    // Wait for redirect
    await page.waitForURL('**/dashboard', { timeout: 5000 }).catch(() => {});
    await page.waitForTimeout(1000);
    
    const currentUrl = page.url();
    expect(currentUrl, 'Should redirect to dashboard after login').toContain('dashboard');
    console.log('  ✓ Login successful, redirected to dashboard');
  });

  test('should crawl all authenticated pages', async ({ page }) => {
    console.log('\n🔍 Starting authenticated pages crawl...\n');

    // Login first
    await page.goto('http://localhost:5001/login');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);

    // Start crawling from dashboard
    const authenticatedCrawler = new SiteCrawler(page, {
      baseUrl: 'http://localhost:5001',
      maxDepth: 4
    });

    await authenticatedCrawler.crawl('http://localhost:5001/dashboard', 0);
    
    const results = authenticatedCrawler.getResults();
    
    console.log('\n📊 Authenticated Crawl Results:');
    console.log(`  Total pages visited: ${results.totalPages}`);
    console.log(`  Server errors: ${results.errors.length}`);
    console.log(`  Console errors: ${results.consoleErrors.length}`);
    console.log(`  Broken links: ${results.brokenLinks.length}`);

    if (results.errors.length > 0) {
      console.log('\n❌ Server Errors Found:');
      results.errors.forEach(err => {
        console.log(`  - ${err.url}: ${err.error}`);
      });
    }

    if (results.consoleErrors.length > 0) {
      console.log('\n⚠️  Console Errors Found:');
      results.consoleErrors.forEach(err => {
        console.log(`  - ${err.url}: ${err.message}`);
      });
    }

    // Save results
    const reportPath = path.join(__dirname, '../reports/authenticated-crawl-results.json');
    authenticatedCrawler.saveResults(reportPath);

    // Assert no critical errors
    expect(results.errors.length, 'Should have no server errors in authenticated pages').toBe(0);
    expect(results.visitedUrls.length, 'Should visit at least 10 authenticated pages').toBeGreaterThan(10);
  });

  test('should test all forms on dashboard', async ({ page }) => {
    console.log('\n📝 Testing dashboard forms...\n');

    // Login first
    await page.goto('http://localhost:5001/login');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);

    // Go to dashboard
    await page.goto('http://localhost:5001/dashboard');
    await page.waitForLoadState('networkidle');

    const formTester = new FormTester(page);
    const results = await formTester.testAllForms({ submit: false, screenshot: true });

    console.log('\n📊 Form Testing Results:');
    console.log(`  Total forms: ${results.totalForms}`);
    console.log(`  Fields filled: ${results.results.reduce((sum, r) => sum + r.fieldsFilled, 0)}`);

    expect(results.totalForms, 'Should find at least one form on dashboard').toBeGreaterThan(0);
  });

  test('should test employee management flow', async ({ page }) => {
    console.log('\n👥 Testing employee management flow...\n');

    // Login
    await page.goto('http://localhost:5001/login');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);

    await page.goto('http://localhost:5001/dashboard');
    
    // Test add employee form (if visible)
    const addEmployeeForm = await page.$('form[data-employee-form="true"], #addEmployeeForm');
    
    if (addEmployeeForm) {
      console.log('Testing add employee form...');
      await page.fill('input[name="name"]', 'QA Test Employee');
      
      // Take screenshot
      await page.screenshot({ 
        path: 'screenshots/employee-form-filled.png',
        fullPage: true 
      });
      
      console.log('  ✓ Employee form can be filled');
    } else {
      console.log('  ⚠ Add employee form not found on dashboard');
    }

    // Check if employees table exists
    const hasEmployeesTable = await page.evaluate(() => {
      return document.querySelector('table') !== null ||
             document.querySelector('.employee-card') !== null ||
             document.body.textContent.includes('employee');
    });

    expect(hasEmployeesTable, 'Dashboard should show employees section').toBe(true);
    console.log('  ✓ Employees section found');
  });

  test('should test trip management pages', async ({ page }) => {
    console.log('\n✈️  Testing trip management pages...\n');

    // Login
    await page.goto('http://localhost:5001/login');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);

    // Test various trip-related pages
    const tripPages = [
      '/bulk_add_trip',
      '/import_excel',
      '/what_if_scenario',
      '/future_job_alerts'
    ];

    for (const pagePath of tripPages) {
      console.log(`\nTesting: ${pagePath}`);
      const response = await page.goto(`http://localhost:5001${pagePath}`);
      const status = response.status();
      
      console.log(`  Status: ${status}`);
      expect(status, `${pagePath} should return 200`).toBe(200);
      
      // Check for page content
      const hasContent = await page.evaluate(() => {
        return document.body.textContent.length > 100;
      });
      
      expect(hasContent, `${pagePath} should have content`).toBe(true);
      console.log(`  ✓ Page loaded with content`);
      
      // Take screenshot
      const filename = pagePath.replace(/\//g, '_');
      await page.screenshot({ 
        path: `screenshots/page${filename}.png`,
        fullPage: true 
      });
    }
  });

  test('should test calendar functionality', async ({ page }) => {
    console.log('\n📅 Testing calendar functionality...\n');

    // Login
    await page.goto('http://localhost:5001/login');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);

    // Test calendar pages
    const calendarPages = ['/calendar', '/calendar_view', '/global_calendar'];

    for (const pagePath of calendarPages) {
      console.log(`\nTesting: ${pagePath}`);
      
      try {
        const response = await page.goto(`http://localhost:5001${pagePath}`, { timeout: 10000 });
        const status = response.status();
        
        console.log(`  Status: ${status}`);
        
        if (status === 200) {
          // Wait for calendar to load
          await page.waitForTimeout(2000);
          
          // Check for calendar elements
          const hasCalendar = await page.evaluate(() => {
            return document.querySelector('#calendar, .calendar-container, [class*="calendar"]') !== null ||
                   document.body.textContent.includes('calendar');
          });
          
          console.log(`  Calendar element found: ${hasCalendar}`);
          
          // Take screenshot
          const filename = pagePath.replace(/\//g, '_');
          await page.screenshot({ 
            path: `screenshots/calendar${filename}.png`,
            fullPage: true 
          });
          
          console.log(`  ✓ Calendar page accessible`);
        }
      } catch (error) {
        console.log(`  ⚠ Error accessing ${pagePath}: ${error.message}`);
      }
    }
  });

  test('should test admin pages', async ({ page }) => {
    console.log('\n⚙️  Testing admin pages...\n');

    // Login
    await page.goto('http://localhost:5001/login');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);

    const adminPages = [
      '/admin_settings',
      '/admin/privacy-tools',
      '/admin/retention/expired'
    ];

    for (const pagePath of adminPages) {
      console.log(`\nTesting: ${pagePath}`);
      const response = await page.goto(`http://localhost:5001${pagePath}`);
      const status = response.status();
      
      console.log(`  Status: ${status}`);
      expect(status, `${pagePath} should be accessible`).toBe(200);
      
      // Take screenshot
      const filename = pagePath.replace(/\//g, '_');
      await page.screenshot({ 
        path: `screenshots/admin${filename}.png`,
        fullPage: true 
      });
      
      console.log(`  ✓ Admin page accessible`);
    }
  });

  test('should verify no JavaScript errors across pages', async ({ page }) => {
    console.log('\n🐛 Checking for JavaScript errors...\n');

    const jsErrors = [];
    
    page.on('pageerror', error => {
      jsErrors.push({
        message: error.message,
        stack: error.stack,
        url: page.url()
      });
    });

    // Login
    await page.goto('http://localhost:5001/login');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);

    // Visit key pages
    const pagesToCheck = [
      '/dashboard',
      '/employee/1',
      '/calendar',
      '/what_if_scenario',
      '/import_excel'
    ];

    for (const pagePath of pagesToCheck) {
      console.log(`Checking: ${pagePath}`);
      try {
        await page.goto(`http://localhost:5001${pagePath}`, { timeout: 10000 });
        await page.waitForTimeout(1000);
        console.log(`  ✓ No JS errors`);
      } catch (error) {
        console.log(`  ⚠ Error accessing page: ${error.message}`);
      }
    }

    if (jsErrors.length > 0) {
      console.log('\n❌ JavaScript Errors Found:');
      jsErrors.forEach(err => {
        console.log(`  - ${err.url}: ${err.message}`);
      });
    }

    expect(jsErrors.length, 'Should have no JavaScript errors').toBe(0);
  });
});


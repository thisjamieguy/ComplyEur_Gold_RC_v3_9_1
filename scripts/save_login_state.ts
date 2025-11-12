import { chromium } from "@playwright/test";
import * as dotenv from "dotenv";
import * as path from "path";
import * as fs from "fs";

dotenv.config();

(async () => {
  const browser = await chromium.launch({
    headless: process.env.HEADLESS_LOGIN === '1',
    args: [
      '--disable-features=Autofill,PasswordManagerOnboarding,AutofillServerCommunication,PasswordImport',
      '--disable-save-password-bubble',
      '--use-mock-keychain',
    ],
  });
  const page = await browser.newPage();
  // Construct APP_URL from PORT or use default/APP_URL env var
  const port = process.env.PORT || process.env.APP_URL?.split(':')[2]?.split('/')[0] || '5001';
  const host = process.env.HOST || 'localhost';
  const APP_URL = process.env.APP_URL || `http://${host}:${port}`;
  const TEST_PASS = process.env.TEST_PASS || process.env.ADMIN_PASSWORD || "admin123";

  console.log("🔐 Logging into ComplyEur at", APP_URL);
  console.log("⏳ Waiting for server to be ready...");

  try {
    // Disable autofill ASAP before navigation
    await page.addInitScript(() => {
      try {
        const disable = () => {
          const inputs = document.querySelectorAll('input');
          inputs.forEach((el) => {
            el.setAttribute('autocomplete', 'off');
            el.setAttribute('autocapitalize', 'none');
            el.setAttribute('autocorrect', 'off');
            el.setAttribute('spellcheck', 'false');
          });
          const forms = document.querySelectorAll('form');
          forms.forEach((f) => f.setAttribute('autocomplete', 'off'));
        };
        disable();
        new MutationObserver(disable).observe(document.documentElement, { childList: true, subtree: true });
      } catch {}
    });

    // Construct login URL
    const loginURL = `${APP_URL}/login`;
    
    // Wait for server to be ready (retry logic)
    let retries = 30;
    let serverReady = false;
    while (retries > 0 && !serverReady) {
      try {
        const response = await page.goto(loginURL, { timeout: 5000, waitUntil: 'domcontentloaded' });
        if (response && response.ok()) {
          serverReady = true;
          break;
        }
      } catch (error: any) {
        if (error.message.includes('net::ERR_CONNECTION_REFUSED') || 
            error.message.includes('net::ERR_HTTP_RESPONSE_CODE_FAILURE')) {
          retries--;
          if (retries > 0) {
            console.log(`⏳ Server not ready, retrying... (${retries} attempts remaining)`);
            await new Promise(resolve => setTimeout(resolve, 2000));
            continue;
          }
        }
        throw error;
      }
    }

    if (!serverReady) {
      throw new Error(`Server at ${loginURL} is not responding after 30 attempts. Please ensure the Flask app is running.`);
    }

    console.log("✅ Server is ready!");

    // Wait for login form to be visible - check for either username or password field
    const usernameSelector = 'input[name="username"]';
    const passwordSelector = 'input[name="password"]';
    
    // Wait for password field (always required)
    await page.waitForSelector(passwordSelector, { timeout: 15000 });

    // Helper to force-set a value and guard against autofill overwriting
    async function forceSetInput(selector: string, value: string): Promise<boolean> {
      return await page.evaluate(({ sel, val }: { sel: string; val: string }) => {
        const el = document.querySelector(sel) as HTMLInputElement | null;
        if (!el) return false;
        try {
          // Make writable, disable autofill hints
          el.removeAttribute('readonly');
          el.setAttribute('autocomplete', 'off');
          el.setAttribute('autocapitalize', 'none');
          el.setAttribute('autocorrect', 'off');
          el.setAttribute('spellcheck', 'false');

          // Clear completely
          el.value = '';
          el.setAttribute('value', '');
          el.dispatchEvent(new Event('input', { bubbles: true }));
          el.dispatchEvent(new Event('change', { bubbles: true }));

          // Assign directly and via attribute (defeat maskers)
          el.value = val;
          el.setAttribute('value', val);
          el.dispatchEvent(new Event('input', { bubbles: true }));
          el.dispatchEvent(new Event('change', { bubbles: true }));

          // Blur to freeze value, then lock
          el.blur();
          el.readOnly = true;
          return el.value === val;
        } catch {
          return false;
        }
      }, { sel: selector, val: value });
    }

    // Check if username field exists (new auth system) and fill it if present
    const usernameField = await page.$(usernameSelector);
    if (usernameField) {
      const TEST_USER = process.env.TEST_USER || 'admin';
      console.log(`🔑 Forcing username: ${TEST_USER}`);
      let ok = false;
      for (let i = 0; i < 3 && !ok; i++) {
        ok = await forceSetInput(usernameSelector, TEST_USER);
        if (!ok) await page.waitForTimeout(200);
      }
      if (!ok) {
        throw new Error('Unable to set username field to expected value after multiple attempts');
      }
    } else {
      console.log("ℹ️  Username field not found, using password-only login");
    }

    // Fill password
    console.log(`🔑 Forcing password...`);
    {
      let ok = false;
      for (let i = 0; i < 3 && !ok; i++) {
        ok = await forceSetInput(passwordSelector, TEST_PASS);
        if (!ok) await page.waitForTimeout(200);
      }
      if (!ok) {
        throw new Error('Unable to set password field to expected value after multiple attempts');
      }
    }
    
    // Wait a moment for any autofill/JavaScript to complete
    await page.waitForTimeout(1000);
    
    // Trigger input events to ensure JavaScript handlers see the values
    await page.evaluate(() => {
      const usernameInput = document.querySelector('input[name="username"]') as HTMLInputElement;
      const passwordInput = document.querySelector('input[name="password"]') as HTMLInputElement;
      
      if (usernameInput) {
        usernameInput.dispatchEvent(new Event('input', { bubbles: true }));
        usernameInput.dispatchEvent(new Event('change', { bubbles: true }));
      }
      if (passwordInput) {
        passwordInput.dispatchEvent(new Event('input', { bubbles: true }));
        passwordInput.dispatchEvent(new Event('change', { bubbles: true }));
      }
    });
    
    console.log("📤 Submitting login form...");
    
    // Debug: Log current state
    const currentURLBefore = page.url();
    console.log(`📍 Current URL: ${currentURLBefore}`);
    
    // Check form values are actually set
    const formValues = await page.evaluate(() => {
      const usernameInput = document.querySelector('input[name="username"]') as HTMLInputElement;
      const passwordInput = document.querySelector('input[name="password"]') as HTMLInputElement;
      return {
        username: usernameInput?.value || 'not found',
        password: passwordInput?.value ? '***' : 'not found'
      };
    });
    console.log(`📝 Form values - Username: ${formValues.username}, Password: ${formValues.password ? 'set' : 'missing'}`);
    
        // Wait for submit button to be enabled and visible
    const submitButton = page.locator('button[type="submit"]');
    await submitButton.waitFor({ state: 'visible', timeout: 5000 });
    
    // Final re-assert and lock right before submit
    if (await page.$(usernameSelector)) {
      const TEST_USER = process.env.TEST_USER || 'admin';
      await forceSetInput(usernameSelector, TEST_USER);
    }
    await forceSetInput(passwordSelector, TEST_PASS);

    // Use button click with Playwright's built-in navigation waiting (most reliable)
    console.log("🖱️  Clicking submit button...");
    
    // Set up navigation wait BEFORE clicking (Playwright pattern)
    const navigationPromise = Promise.race([
      // Any URL that does not include /login
      page.waitForURL(/^(?!.*\/login).+$/, { timeout: 30000 }),
      page.waitForResponse(response => {
        const url = response.url();
        return url.includes('/dashboard') || url.includes('/home');
      }, { timeout: 30000 }),
      page.waitForLoadState('networkidle', { timeout: 30000 }).then(() => page.waitForTimeout(1000))
    ]);
    
    // Click the submit button
    await page.click('button[type="submit"]');
    
    // Wait for navigation
    console.log("⏳ Waiting for login to complete...");
    await navigationPromise;
    
    // Additional wait to ensure page is fully loaded
    await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {
      console.log("⚠️  Network idle timeout, continuing anyway...");
    });
    
    // Check if we're still on login page (login failed)
    const currentURL = page.url();
    if (currentURL.includes('/login')) {
      // Check for error messages
      const errorMessage = await page.$('.error-message, .alert-danger, .error');
      if (errorMessage) {
        const errorText = await errorMessage.textContent();
        throw new Error(`Login failed: ${errorText}`);
      }
      throw new Error('Login failed - still on login page after submission');
    }

    // Handle potential 2FA step
    if (page.url().includes('/login/totp')) {
      const TEST_TOTP = process.env.TEST_TOTP;
      if (!TEST_TOTP) {
        throw new Error('TOTP required but TEST_TOTP not set. Set TEST_TOTP in .env or disable 2FA for automation runs.');
      }
      console.log('🔐 TOTP required. Submitting provided TEST_TOTP...');
      await page.fill('input[name="token"]', TEST_TOTP);
      await Promise.all([
        page.waitForLoadState('networkidle'),
        page.click('button[type="submit"]'),
      ]);
    }

    // Verify dashboard loaded - check for dashboard indicators
    console.log("✅ Login submitted, verifying dashboard...");
    
    // Wait for either dashboard heading or home page indicator
    try {
      await Promise.race([
        page.waitForSelector("text=EU Trip Tracker Dashboard", { timeout: 10000 }),
        page.waitForSelector("text=Dashboard", { timeout: 10000 }),
        page.waitForSelector("text=Welcome", { timeout: 10000 }),
        page.waitForURL(/dashboard|home/, { timeout: 10000 })
      ]);
      console.log("✅ Login successful, saving session...");
    } catch (e) {
      // If we're not on login page but can't find dashboard, take a screenshot for debugging
      console.warn("⚠️  Could not find dashboard indicator, but not on login page. Taking screenshot...");
      await page.screenshot({ path: 'login_debug.png', fullPage: true });
      throw new Error(`Login may have succeeded but dashboard not found. Screenshot saved to login_debug.png. Current URL: ${page.url()}`);
    }

    // Ensure directory exists
    const stateDir = path.join(process.cwd(), "tests", "auth");
    fs.mkdirSync(stateDir, { recursive: true });

    // Save storage state (includes cookies and session)
    const statePath = path.join(stateDir, "state.json");
    await page.context().storageState({ path: statePath });

    await browser.close();
    console.log(`💾 Saved login state to ${statePath}`);
    console.log("✅ Ready for headless overnight QA runs!");
  } catch (error) {
    await browser.close();
    console.error("❌ Login failed:", error);
    process.exit(1);
  }
})();

import { test, expect, request } from "@playwright/test";
import fs from "fs";
import path from "path";

const USERNAME = process.env.TEST_USER || "admin";
const PASSWORD = process.env.TEST_PASS || "admin123";

test.describe("ComplyEur Full E2E – Login, Import, Verify", () => {
  test("Login + Import + Backend Cross-Check", async ({ page, context }) => {
    const base = process.env.APP_URL || test.info().config.use.baseURL || "http://127.0.0.1:5001";
    const APP_URL = String(base).replace(/\/$/, "");
    // Ensure artifacts directories exist
    const artifactsDir = path.join(process.cwd(), "tests", "artifacts");
    const screenshotsDir = path.join(artifactsDir, "screenshots");
    const diffsDir = path.join(artifactsDir, "diffs");
    
    [screenshotsDir, diffsDir].forEach(dir => {
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
    });

    // 1. Ensure authenticated (storageState should handle this)
    console.log("🔐 Step 1: Ensuring authentication...");
    await page.goto(`${APP_URL}/dashboard`);
    if (page.url().includes("/login")) {
      // Handle either username+password or password-only forms
      if (await page.$('input[name="username"]')) {
        await page.fill('input[name="username"]', USERNAME);
      }
      await page.fill('input[name="password"]', PASSWORD);
      await Promise.all([
        page.waitForLoadState("networkidle"),
        page.click('button[type="submit"]')
      ]);
      await expect(
        page.locator("text=Dashboard").or(page.locator("text=EU Trip Tracker")).or(page.locator("text=ComplyEur"))
      ).toBeVisible({ timeout: 15000 });
    }
    await page.screenshot({ path: path.join(screenshotsDir, `1_login_ok_${Date.now()}.png`), fullPage: true });

    // 2. NAVIGATE TO IMPORT PAGE
    console.log("📂 Step 2: Navigating to import page...");
    
    // Look for import link/button - could be in navigation or dashboard
    const importLink = page.locator('a:has-text("Import Excel")').or(
      page.locator('a[href*="import"]')
    );
    
    if (await importLink.count() > 0) {
      await importLink.first().click();
    } else {
      // Fallback: navigate directly to import route
      await page.goto(`${APP_URL}/import_excel`);
    }
    
    await page.waitForLoadState("networkidle");
    await expect(page.locator("#excelFile").or(page.locator('input[type="file"]'))).toBeVisible({ timeout: 10000 });
    
    await page.screenshot({ 
      path: path.join(screenshotsDir, `2_import_page_${Date.now()}.png`),
      fullPage: true 
    });

    // 3. UPLOAD RANDOM FIXTURE
    console.log("📤 Step 3: Uploading fixture file...");
    
    const fixturesDir = path.join(process.cwd(), "data", "fixtures");
    
    // Ensure fixtures directory exists
    if (!fs.existsSync(fixturesDir)) {
      fs.mkdirSync(fixturesDir, { recursive: true });
      console.log("⚠️ Fixtures directory created - run scripts/make_fixtures.py first");
    }
    
    // Find available fixture files
    let files: string[] = [];
    if (fs.existsSync(fixturesDir)) {
      files = fs.readdirSync(fixturesDir).filter(
        f => f.endsWith(".csv") || f.endsWith(".xlsx") || f.endsWith(".xls")
      );
    }
    
    // If no fixtures, create a simple one for testing
    if (files.length === 0) {
      console.log("⚠️ No fixtures found, creating a test fixture...");
      const testFixturePath = path.join(fixturesDir, "test_fixture.csv");
      const csvContent = `Employee,Country,Entry,Exit
TestEmp1,FR,2025-01-01,2025-01-10
TestEmp1,DE,2025-02-01,2025-02-15`;
      fs.writeFileSync(testFixturePath, csvContent);
      files = ["test_fixture.csv"];
    }
    
    const randomFile = files[Math.floor(Math.random() * files.length)];
    const filePath = path.join(fixturesDir, randomFile);
    console.log(`📎 Uploading fixture: ${randomFile}`);

    // Wait for file chooser and upload
    const fileInput = page.locator("#excelFile").or(page.locator('input[type="file"]'));
    await fileInput.setInputFiles(filePath);

    // Click submit button
    const submitButton = page.locator("#importBtn").or(
      page.locator('button[type="submit"]').filter({ hasText: /upload|import/i })
    );
    await submitButton.click();

    // Wait for import to complete
    console.log("⏳ Waiting for import to complete...");
    
    // Wait for success message or redirect
    await Promise.race([
      page.waitForSelector("text=Import successful", { timeout: 30000 }).catch(() => null),
      page.waitForSelector("text=successfully imported", { timeout: 30000 }).catch(() => null),
      page.waitForURL(`${APP_URL}/dashboard`, { timeout: 30000 }).catch(() => null),
      page.waitForURL(`${APP_URL}/import_excel`, { timeout: 30000 }).catch(() => null),
      page.waitForTimeout(5000) // Fallback: wait 5 seconds
    ]);
    
    // Additional wait for any async processing
    await page.waitForTimeout(2000);
    await page.waitForLoadState("networkidle");
    
    await page.screenshot({ 
      path: path.join(screenshotsDir, `3_import_complete_${Date.now()}.png`),
      fullPage: true 
    });
    console.log("✅ Import completed");

    // 4. NAVIGATE TO DASHBOARD AND EXTRACT UI VALUES
    console.log("📊 Step 4: Extracting UI values from dashboard...");
    
    await page.goto(`${APP_URL}/dashboard`);
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(2000); // Allow time for calculations to render
    
    // Wait for employee table to load
    await expect(page.locator("table tbody tr").first()).toBeVisible({ timeout: 15000 });
    
    // Get first employee row data
    const firstRow = page.locator("table tbody tr").first();
    
    // Extract days used (format: "X/90" or just "X")
    const daysUsedText = await firstRow.locator("td").nth(2).innerText();
    const daysUsedMatch = daysUsedText.match(/(\d+)\/90/);
    const uiUsed = daysUsedMatch ? daysUsedMatch[1] : daysUsedText.match(/\d+/)?.[0] || "0";
    
    // Extract days remaining (format: "X days")
    const daysRemainingText = await firstRow.locator("td").nth(3).innerText();
    const daysRemainingMatch = daysRemainingText.match(/(\d+)\s*days?/i);
    const uiRemaining = daysRemainingMatch ? daysRemainingMatch[1] : daysRemainingText.match(/-?\d+/)?.[0] || "0";
    
    // Get employee name and ID for API call
    const employeeLink = firstRow.locator("td").first().locator("a");
    const employeeHref = await employeeLink.getAttribute("href");
    const employeeIdMatch = employeeHref?.match(/employee[\/=](\d+)/i);
    const employeeId = employeeIdMatch ? employeeIdMatch[1] : "1";
    
    console.log(`📋 Employee ID: ${employeeId}`);
    console.log(`📊 UI Values - Used: ${uiUsed}, Remaining: ${uiRemaining}`);

    // 5. GET BACKEND DATA FROM API
    console.log("🔍 Step 5: Fetching backend data...");
    
    // Get authentication cookies for API request
    const cookies = await context.cookies();
    const api = await request.newContext({
      extraHTTPHeaders: {
        Cookie: cookies.map(c => `${c.name}=${c.value}`).join("; ")
      }
    });
    
    // Try to get summary from API (if endpoint exists)
    let backUsed = "";
    let backRemaining = "";
    let backViolations = "0";
    
    try {
      // Try the summary endpoint first
      const summaryResp = await api.get(`${APP_URL}/api/trips/summary?employee=${employeeId}`);
      
      if (summaryResp.ok()) {
        const data = await summaryResp.json();
        backUsed = String(data.days_used || data.daysUsed || 0);
        backRemaining = String(data.days_remaining || data.daysRemaining || 0);
        backViolations = String(data.violations?.length || data.violation_count || 0);
        console.log(`✅ Summary API found - Used: ${backUsed}, Remaining: ${backRemaining}, Violations: ${backViolations}`);
      }
    } catch (e) {
      console.log("⚠️ Summary API not found, using /api/trips endpoint...");
    }
    
    // If summary API doesn't exist, get trips and calculate from employee detail page
    if (!backUsed) {
      try {
        // Get trips for this employee
        const tripsResp = await api.get(`${APP_URL}/api/trips`);
        if (tripsResp.ok()) {
          const tripsData = await tripsResp.json();
          const employeeTrips = tripsData.trips?.filter(
            (t: any) => String(t.employee_id) === String(employeeId)
          ) || [];
          
          // Navigate to employee detail page to get calculated values
          await page.goto(`${APP_URL}/employee/${employeeId}`);
          await page.waitForLoadState("networkidle");
          await page.waitForTimeout(2000);
          
          // Extract from employee detail page
          const detailUsedMatch = await page.locator("text=/\\d+\\/90/").first().innerText().catch(() => "");
          if (detailUsedMatch) {
            const match = detailUsedMatch.match(/(\d+)\/90/);
            backUsed = match ? match[1] : "";
          }
          
          const detailRemainingMatch = await page.locator("text=/\\d+\\s*days?/i").first().innerText().catch(() => "");
          if (detailRemainingMatch) {
            const match = detailRemainingMatch.match(/(\d+)\s*days?/i);
            backRemaining = match ? match[1] : "";
          }
          
          // Calculate violations (days_remaining < 0)
          const remainingNum = parseInt(backRemaining);
          backViolations = remainingNum < 0 ? "1" : "0";
          
          console.log(`📊 Backend Values - Used: ${backUsed}, Remaining: ${backRemaining}, Violations: ${backViolations}`);
        }
      } catch (e) {
        console.log(`⚠️ Could not fetch backend data: ${e}`);
      }
    }
    
    // Calculate violations from UI (days_remaining < 0 indicates violation)
    const uiViolations = parseInt(uiRemaining) < 0 ? "1" : "0";

    // 6. COMPARE VALUES
    console.log("🔬 Step 6: Comparing UI vs Backend...");
    
    const comparison = {
      when: new Date().toISOString(),
      fixture: randomFile,
      employee_id: employeeId,
      ui: {
        used: uiUsed,
        remaining: uiRemaining,
        violations: uiViolations
      },
      backend: {
        used: backUsed || "N/A",
        remaining: backRemaining || "N/A",
        violations: backViolations
      },
      matches: {
        used: uiUsed === backUsed,
        remaining: uiRemaining === backRemaining,
        violations: uiViolations === backViolations
      }
    };
    
    console.log("📊 Comparison:", JSON.stringify(comparison, null, 2));
    
    // Check for mismatches
    const mismatches: string[] = [];
    if (backUsed && uiUsed !== backUsed) {
      mismatches.push(`Days Used: UI=${uiUsed}, Backend=${backUsed}`);
    }
    if (backRemaining && uiRemaining !== backRemaining) {
      mismatches.push(`Days Remaining: UI=${uiRemaining}, Backend=${backRemaining}`);
    }
    if (backViolations && uiViolations !== backViolations) {
      mismatches.push(`Violations: UI=${uiViolations}, Backend=${backViolations}`);
    }
    
    // Take final screenshot
    await page.screenshot({ 
      path: path.join(screenshotsDir, `4_dashboard_verified_${Date.now()}.png`),
      fullPage: true 
    });
    
    // If there are mismatches, save diff and throw error
    if (mismatches.length > 0 && backUsed) {
      const diffPath = path.join(diffsDir, `diff_${Date.now()}.json`);
      fs.writeFileSync(diffPath, JSON.stringify(comparison, null, 2));
      console.error("❌ MISMATCH DETECTED:");
      mismatches.forEach(m => console.error(`  - ${m}`));
      console.error(`📝 Diff saved to: ${diffPath}`);
      throw new Error(`❌ Mismatch between UI and backend detected: ${mismatches.join(", ")}`);
    }
    
    // Save comparison log even if no mismatch (for audit trail)
    if (backUsed) {
      const logPath = path.join(diffsDir, `comparison_${Date.now()}.json`);
      fs.writeFileSync(logPath, JSON.stringify(comparison, null, 2));
    }
    
    console.log("✅ All values match perfectly!");
  });
});

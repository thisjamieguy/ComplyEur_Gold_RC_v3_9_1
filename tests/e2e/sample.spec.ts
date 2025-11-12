import { test, expect } from "@playwright/test";

test("Homepage loads", async ({ page }) => {
  await page.goto("/");
  expect(await page.title()).not.toBe("");
});

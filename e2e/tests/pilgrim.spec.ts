import { test, expect } from "@playwright/test";

// Pilgrim PWA happy path, driven with NO microphone and NO API keys — the tap-first form path
// a panicked family member would actually use at a kiosk.

const PILGRIM = process.env.SETU_PILGRIM ?? "http://localhost:5173";

test("report a lost elder via taps → success screen with a case id", async ({ page }) => {
  const failedReports: string[] = [];
  page.on("response", (r) => {
    if (r.url().includes("/api/v1/report/lost") && r.status() >= 400) {
      failedReports.push(`${r.status()} ${r.url()}`);
    }
  });

  await page.goto(PILGRIM);

  // 1. Language — Hindi (the button speaks its own name; TTS no-ops headless).
  await page.getByRole("button", { name: /हिन्दी/ }).click();
  // 1b. Triage — "someone is lost" leads to the report form.
  await page.getByRole("button", { name: /कोई खो गया है/ }).click();

  // 2. WHO — gender + age band chips.
  await page.getByRole("button", { name: /पुरुष/ }).click();
  await page.getByRole("button", { name: /61-70/ }).click();

  // 3. WHERE — a last-seen place from the first visible set.
  await page.getByRole("button", { name: /Dasak Ghat/ }).click();

  // 4. CONTACT — the required 10-digit callback number.
  await page.getByPlaceholder("9876543210").fill("9876543210");

  // 5. Submit — enabled only once phone + a descriptor are present.
  const submit = page.getByRole("button", { name: /रिपोर्ट दें/ });
  await expect(submit).toBeEnabled();
  await submit.click();

  // Success state with a non-empty case id.
  await expect(page.locator(".state-screen--success")).toBeVisible();
  await expect(page.locator(".case-id strong")).not.toBeEmpty();

  expect(failedReports, failedReports.join("\n")).toEqual([]);
});

test("submit stays disabled until a callback number is entered", async ({ page }) => {
  await page.goto(PILGRIM);
  await page.getByRole("button", { name: /हिन्दी/ }).click();
  // 1b. Triage — "someone is lost" leads to the report form.
  await page.getByRole("button", { name: /कोई खो गया है/ }).click();
  await page.getByRole("button", { name: /पुरुष/ }).click();
  // No phone yet → submit disabled.
  await expect(page.getByRole("button", { name: /रिपोर्ट दें/ })).toBeDisabled();
});

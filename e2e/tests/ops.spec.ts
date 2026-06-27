import { test, expect } from "@playwright/test";

// Ops dashboard — loads the seeded case queue from the real backend and renders the map.
// Scoped to the data-critical /ops/cases call so it is robust to headless WebGL/basemap.

const OPS = process.env.SETU_OPS ?? "http://localhost:5174";

test("dashboard loads seeded cases and the map renders", async ({ page }) => {
  const failedCases: string[] = [];
  page.on("response", (r) => {
    if (r.url().includes("/api/v1/ops/cases") && r.status() >= 400) {
      failedCases.push(`${r.status()} ${r.url()}`);
    }
  });

  await page.goto(OPS);
  await expect(page.getByRole("heading", { name: /Officials Dashboard/ })).toBeVisible();

  // Cases tab — seeded found-persons appear as rows.
  await page.getByRole("button", { name: /Cases/ }).click();
  await expect(page.locator("tbody tr").first()).toBeVisible();
  expect(await page.locator("tbody tr").count()).toBeGreaterThan(0);

  // The /ops/cases fetch must not have failed.
  expect(failedCases, failedCases.join("\n")).toEqual([]);

  // Map tab — the legend always renders even if WebGL/basemap is unavailable.
  await page.getByRole("button", { name: /Map/ }).click();
  await expect(page.locator(".legend")).toBeVisible();
});

test("a minor case surfaces in the private staff-alerts panel", async ({ page }) => {
  await page.goto(OPS);
  await page.getByRole("button", { name: /Cases/ }).click();
  // The seed includes one minor (e2e-found-003) → derived alerts panel is shown.
  await expect(page.locator(".alerts")).toBeVisible();
  await expect(page.locator(".alerts")).toContainText(/staff alerts/i);
  // Minor rows get the distinct class + 👶 indicator.
  await expect(page.locator("tbody tr.minor").first()).toBeVisible();
});

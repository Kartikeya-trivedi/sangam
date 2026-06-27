const { chromium } = require("@playwright/test");
(async () => {
  const dir = process.argv[2];
  const b = await chromium.launch();
  // ---- pilgrim (mobile viewport) ----
  const p = await b.newPage({ viewport: { width: 414, height: 896 } });
  await p.goto("http://localhost:5173");
  await p.waitForTimeout(800);
  await p.screenshot({ path: dir + "/pilgrim-1-landing.png" });
  await p.getByRole("button", { name: /हिन्दी/ }).click().catch(() => {});
  await p.waitForTimeout(500);
  await p.getByRole("button", { name: /पुरुष/ }).click().catch(() => {});
  await p.getByRole("button", { name: /71-80/ }).click().catch(() => {});
  await p.getByPlaceholder("9876543210").fill("9876543210").catch(() => {});
  await p.screenshot({ path: dir + "/pilgrim-2-form.png", fullPage: true });
  await p.getByRole("button", { name: /रिपोर्ट दें/ }).click().catch(() => {});
  await p.waitForTimeout(5000);
  await p.screenshot({ path: dir + "/pilgrim-3-results.png", fullPage: true });
  // ---- ops (desktop) ----
  const o = await b.newPage({ viewport: { width: 1280, height: 900 } });
  await o.goto("http://localhost:5174");
  await o.waitForTimeout(1000);
  await o.screenshot({ path: dir + "/ops-1-map.png" });
  await o.getByRole("button", { name: /Cases/ }).click().catch(() => {});
  await o.waitForTimeout(800);
  await o.screenshot({ path: dir + "/ops-2-cases.png", fullPage: true });
  await b.close();
  console.log("screenshots written to", dir);
})().catch((e) => { console.error(e); process.exit(1); });

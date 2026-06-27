const { chromium } = require("@playwright/test");
(async () => {
  const dir = process.argv[2];
  const b = await chromium.launch();
  const ctx = await b.newContext({
    viewport: { width: 414, height: 896 },
    geolocation: { latitude: 19.9975, longitude: 73.7898 },
    permissions: ["geolocation"],
  });
  const p = await ctx.newPage();
  await p.goto("http://localhost:5173");
  await p.waitForTimeout(1500);
  await p.screenshot({ path: dir + "/v2-1-language.png" });
  await p.getByRole("button", { name: /हिन्दी/ }).click().catch(()=>{});
  await p.waitForTimeout(2200);
  await p.screenshot({ path: dir + "/v2-2-intent.png", fullPage: true });
  await p.getByRole("button", { name: /मैं खुद खो गया/ }).click().catch(()=>{});
  await p.waitForTimeout(1800);
  await p.screenshot({ path: dir + "/v2-4-selflost.png", fullPage: true });
  await b.close();
  console.log("done");
})().catch((e)=>{console.error(e);process.exit(1);});

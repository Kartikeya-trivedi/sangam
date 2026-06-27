const { chromium } = require("@playwright/test");
(async () => {
  const dir = process.argv[2];
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 414, height: 760 },
    geolocation: { latitude: 19.9975, longitude: 73.7898 }, permissions: ["geolocation"] });
  const p = await ctx.newPage();
  await p.goto("http://localhost:5173");
  await p.waitForTimeout(1200);
  await p.getByRole("button", { name: /English/ }).click().catch(()=>{});
  await p.waitForTimeout(2200);
  await p.screenshot({ path: dir + "/nopill-intent.png" });
  await b.close(); console.log("done");
})().catch((e)=>{console.error(e);process.exit(1);});

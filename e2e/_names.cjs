const { chromium } = require("@playwright/test");
(async () => {
  const dir = process.argv[2];
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1300, height: 900 } });
  await p.goto("http://localhost:5174");
  await p.waitForTimeout(13000);  // let Sahayak run a named case
  await p.screenshot({ path: dir + "/names-sahayak.png" });
  await p.getByRole("button", { name: /Cases/ }).click().catch(()=>{});
  await p.waitForTimeout(1500);
  await p.screenshot({ path: dir + "/names-cases.png", fullPage: true });
  await b.close(); console.log("done");
})().catch((e)=>{console.error(e);process.exit(1);});

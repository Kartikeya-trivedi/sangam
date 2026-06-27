const { chromium } = require("@playwright/test");
(async () => {
  const dir = process.argv[2];
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 900 }, deviceScaleFactor: 2 });
  await p.goto("file:///C:/claude/setu/docs/how-it-works.html");
  await p.evaluate(() => document.querySelectorAll(".reveal").forEach((e) => e.classList.add("in")));
  await p.waitForTimeout(1800); // fonts
  await p.screenshot({ path: dir + "/howitworks-full.png", fullPage: true });
  await p.setViewportSize({ width: 1080, height: 1000 });
  await p.screenshot({ path: dir + "/howitworks-top.png" });
  await b.close();
  console.log("done");
})().catch((e)=>{console.error(e);process.exit(1);});

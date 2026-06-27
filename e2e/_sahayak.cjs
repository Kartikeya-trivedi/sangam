const { chromium } = require("@playwright/test");
(async () => {
  const dir = process.argv[2];
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1320, height: 900 } });
  const errs = [];
  p.on("console", (m) => { if (m.type() === "error") errs.push(m.text()); });
  await p.goto("http://localhost:5174");
  await p.waitForTimeout(3000);
  await p.screenshot({ path: dir + "/sahayak-early.png" });
  await p.waitForTimeout(16000); // let the agent stream finish (Claude drift + announce)
  await p.screenshot({ path: dir + "/sahayak-done.png", fullPage: true });
  console.log("console errors:", errs.slice(0, 6).join(" | ") || "none");
  await b.close();
})().catch((e) => { console.error(e); process.exit(1); });

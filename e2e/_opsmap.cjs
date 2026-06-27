const { chromium } = require("@playwright/test");
(async () => {
  const dir = process.argv[2];
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 900 } });
  const errs = [];
  p.on("console", (m) => { if (m.type() === "error") errs.push(m.text()); });
  await p.goto("http://localhost:5174");
  await p.waitForTimeout(5500); // let Google Maps tiles load
  await p.screenshot({ path: dir + "/ops-gmap.png" });
  console.log("console errors:", errs.slice(0, 6).join(" | ") || "none");
  await b.close();
})().catch((e) => { console.error(e); process.exit(1); });

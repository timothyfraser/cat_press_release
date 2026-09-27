// fig/src/render_figure_app_v2.cjs -- render Figure 2 (annotated REPORTER interface).
//
//   node fig/src/render_figure_app_v2.cjs      ->  fig/figure_app_v2.png
//
// figure_app_v2.html lays the numbered callouts over figure_app_v2_crop.png, a
// screenshot of the live REPORTER Standard Report form
// (https://cat-apps.com/reporter?tab=standard, Tompkins County NY, 2020, CO2
// Equivalent, vehicle type, bar chart, Word). In that screenshot the neighbouring
// "AI REPORT" tab -- a separate, AI-written mode that this paper does not study --
// is painted over with the page background so the figure shows only the
// rule-based Standard Report.
//
// Needs Node 18+ and Playwright (npm install -g playwright) with a Chromium build.
const path = require("node:path");
const fs = require("node:fs");
const { createRequire } = require("node:module");
const { execSync } = require("node:child_process");
const r = createRequire(__filename);
const { chromium } = r(r.resolve("playwright", { paths: [execSync("npm root -g").toString().trim()] }));

const here = __dirname;
const out = path.join(here, "..", "figure_app_v2.png");
(async () => {
  const exe = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome";   // cloud container; else Playwright's own
  const b = await chromium.launch(fs.existsSync(exe) ? { executablePath: exe } : {});
  const p = await b.newPage({ viewport: { width: 1145, height: 700 }, deviceScaleFactor: 2 });
  await p.goto("file://" + path.join(here, "figure_app_v2.html"), { waitUntil: "networkidle" });
  const box = await p.evaluate(() => {
    const r = document.body.firstElementChild.getBoundingClientRect();
    return { w: Math.ceil(r.right), h: Math.ceil(r.bottom) };
  });
  await p.setViewportSize({ width: Math.max(box.w, 1145), height: box.h });
  await p.screenshot({ path: out, fullPage: true });
  await b.close();
  console.log("wrote " + out);
})();

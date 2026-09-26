// time_reporter.mjs — drive the live CAT REPORTER page in headless
// Chromium and time one press release per county. Called by
// benchmark_reporter.R, which draws the sample and summarizes the result.
//
//   node time_reporter.mjs <sample.csv> <out.csv>
//
// For each row (geoid,year) of sample.csv:
//   1. load the REPORTER page deep-linked to that county, year, CO2e, and the
//      press release's default breakdown (vehicle type, donut chart)  [untimed]
//   2. click "Generate press release" and time until the .docx download
//      completes. That span covers everything a staffer waits for: reading the
//      county's emissions, computing the statistics, writing the sentences,
//      drawing the chart, and assembling and downloading the Word file.
//
// No credentials: the REPORTER page is public and its API is keyless.

import { createRequire } from "node:module";
import { execSync } from "node:child_process";
// playwright is resolved from the global npm root so the paper repo needs no node_modules.
const require = createRequire(import.meta.url);
const { chromium } = require(require.resolve("playwright", { paths: [execSync("npm root -g").toString().trim()] }));
import { readFileSync, writeFileSync, statSync } from "node:fs";

const [, , samplePath, outPath] = process.argv;
const BASE = process.env.REPORTER_PAGE ?? "https://connect.systems-apps.com/cat/#/reporter";
const POLLUTANT = 98;
const TIMEOUT_MS = Number(process.env.TIMEOUT_MS ?? 180_000);

const rows = readFileSync(samplePath, "utf8").trim().split("\n").slice(1)
  .map((l) => { const [geoid, year] = l.split(","); return { geoid: geoid.replace(/"/g, ""), year: Number(year) }; });

const exe = process.env.CHROMIUM_PATH ?? "/opt/pw-browsers/chromium-1194/chrome-linux/chrome";
const browser = await chromium.launch({ headless: true, ...(statExists(exe) ? { executablePath: exe } : {}) });
const context = await browser.newContext({ acceptDownloads: true });
// Suppress the first-visit onboarding tour, whose dialog covers the page, the
// same way a returning user's "Don't show again" does.
await context.addInitScript(() => {
  try { localStorage.setItem("cat-platform:tour:v1", JSON.stringify({ dismissed: true, completed: true })); } catch {}
});

const out = ["geoid,year,pollutant,load_s,generate_s,bytes,docx_ok,error,started_utc"];
for (const { geoid, year } of rows) {
  const page = await context.newPage();
  const started = new Date().toISOString();
  let load_s = "", gen_s = "", bytes = "", ok = false, err = "";
  try {
    const url = `${BASE}?tab=standard&geoid=${geoid}&year=${year}&pollutant=${POLLUTANT}&set=sourcetype&chart=donut`;
    const t0 = performance.now();
    await page.goto(url, { waitUntil: "networkidle", timeout: TIMEOUT_MS });
    const button = page.getByRole("button", { name: "Generate press release" });
    await button.waitFor({ state: "visible", timeout: TIMEOUT_MS });
    load_s = ((performance.now() - t0) / 1000).toFixed(3);

    const t1 = performance.now();
    const [download] = await Promise.all([
      page.waitForEvent("download", { timeout: TIMEOUT_MS }),
      button.click(),
    ]);
    const path = await download.path();           // resolves once the file is fully written
    gen_s = ((performance.now() - t1) / 1000).toFixed(3);
    if (process.env.SAVE_DOCX_DIR) await download.saveAs(`${process.env.SAVE_DOCX_DIR}/${geoid}-${year}.docx`); // optional audit copy
    const buf = readFileSync(path);
    bytes = String(buf.length);
    ok = buf.length > 4 && buf[0] === 0x50 && buf[1] === 0x4b; // .docx is a zip ("PK")
  } catch (e) {
    err = String(e?.message ?? e).split("\n")[0].replace(/[",]/g, " ").slice(0, 160);
  }
  out.push([geoid, year, POLLUTANT, load_s, gen_s, bytes, ok, `"${err}"`, started].join(","));
  process.stdout.write(`${ok ? "OK " : "ERR"} ${geoid} ${year} generate=${gen_s}s ${err}\n`);
  await page.close();
  await new Promise((r) => setTimeout(r, 1000));  // never overlap requests
}
writeFileSync(outPath, out.join("\n") + "\n");
await browser.close();

function statExists(p) { try { statSync(p); return true; } catch { return false; } }

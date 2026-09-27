# cat_press_release

Replication materials for **the CAT REPORTER**, a tool that writes a one-page,
editable press release on a US county's or state's transportation emissions in
about two seconds. This repository accompanies the paper *Automated Algorithms
for Data-Driven Press Releases on Transportation Emissions for Climate
Communication* (under review at *Technology in Society*).

Everything here is public. Nothing requires an account, a key, or a password.

---

## Try the REPORTER

**Open: <https://cat-apps.com/reporter?tab=standard>**

1. **No sign-in needed.** The page opens as a Guest. (A one-minute tour may
   pop up the first time; press *Skip*.)
2. **Stay on the STANDARD REPORT tab** ("Automated Press Release, No AI").
   That is the tool the paper describes: every sentence follows from a fixed
   rule and a published number. The neighbouring *AI REPORT* tab is a
   separate, AI-written mode that the paper does not study. The link above
   opens the Standard Report directly; the bare address
   `cat-apps.com/reporter` may open on the AI tab instead.
3. **Choose** an **Area** (type a county or state name), a **Year**, a
   **Pollutant**, a **Breakdown** (vehicle type, fuel type, regulatory class,
   or road type), a **Chart** (bar or donut), and a **Format** (Word `.docx`
   or Markdown).
4. **Click _Generate press release_.** The file downloads in about two
   seconds. It is a normal Word document: edit it, add your agency's contact
   details, and send it.

The example in the paper (Figure 1) is one click away:
<https://cat-apps.com/reporter?tab=standard&geoid=36109&year=2020&pollutant=98&set=sourcetype&chart=bar>

### Link parameters

Any combination of these can be added to the link; an invalid value is
ignored and the form falls back to its default.

| parameter | values | meaning |
|---|---|---|
| `tab` | `standard`, `ai` | which tab opens (use `standard`) |
| `geoid` | 2-digit state FIPS or 5-digit county FIPS, e.g. `36` or `36109` | the area |
| `year` | a four-digit year, 2000–2060 | the year of the estimate |
| `pollutant` | an EPA MOVES pollutant code (table below) | the pollutant |
| `set` | `sourcetype`, `fueltype`, `regclass`, `roadtype` | the breakdown: vehicle type, fuel type, regulatory class, road type |
| `chart` | `bar`, `donut` | the chart in the release |

| code | pollutant | code | pollutant |
|---|---|---|---|
| 98 | CO₂ equivalent | 100 | PM10, total |
| 2 | carbon monoxide (CO) | 106 | PM10, brake wear |
| 3 | oxides of nitrogen (NOx) | 107 | PM10, tire wear |
| 33 | nitrogen dioxide (NO₂) | 110 | PM2.5, total |
| 31 | sulfur dioxide (SO₂) | 116 | PM2.5, brake wear |
| | | 117 | PM2.5, tire wear |

### If the page stalls

The REPORTER does its work in your browser. It loads the DuckDB-WASM database
engine from `cdn.jsdelivr.net` and DuckDB's Parquet reader from
`extensions.duckdb.org`, and reads the emissions data from
`connect.systems-apps.com`. A network that blocks any of those three (some
corporate or government firewalls do) will leave the form waiting. Try another
network, or ask IT to allow them.

---

## What the REPORTER covers

- **Areas:** all 3,110 US counties and the 50 states.
- **Years:** every year from 2000 to 2060, a full 60-year span; years after the
  present are EPA MOVES projections.
- **Data:** county-level emissions estimates produced with the EPA's MOVES
  model and served from CATSERVER, the CAT project's emissions database.
  Counties that run their own MOVES scenarios through
  [Cloud MOVES](https://cat-apps.com) can publish one run per county-year as
  their official estimate; only published runs reach the REPORTER.

## How it works

1. The browser reads the county's estimates from CATSERVER (Parquet files,
   queried in the browser with DuckDB-WASM).
2. It computes each vehicle type's (or fuel type's, etc.) share of the total.
3. It writes the headline, the three bullets, and the closing paragraph from
   fixed rules: which category is largest, how far ahead it is, and so on.
   No language model is involved.
4. It draws the chart with the same chart components as the CAT
   **VISUALIZER** dashboard.
5. A small R service (Plumber + officer) assembles the editable `.docx`.

---

## What is in this repository

| path | what it is |
|---|---|
| [`benchmark_2026-09-26/`](benchmark_2026-09-26/) | **How fast is it?** Times the live REPORTER on 100 randomly sampled US counties, click to downloaded file: mean **1.78 s** (SD 0.27, SE 0.027). The R and Node scripts, the raw per-county timings, the summary statistics, and all 116 press releases the run generated. [Its README](benchmark_2026-09-26/README.md) has the full method. |
| [`figures/`](figures/) | **The paper's Figures 1 and 2**, with the code that builds them from the REPORTER's real output. [Its README](figures/README.md) explains each. |
| `press_release_v1.zip` | **The first version** of the REPORTER (2024), an R Markdown document behind a Shiny dashboard, as described in the paper's first submission. See [below](#the-first-version-2024). |

## Reproduce the benchmark

```bash
cd benchmark_2026-09-26
# needs R (httr2, dplyr, purrr, readr, tibble, nanoparquet)
# and Node 18+ with Playwright (npm install -g playwright) and a Chromium build
N_COUNTIES=5 Rscript benchmark_reporter.R     # quick check: 5 counties
Rscript benchmark_reporter.R                  # the full run: 100 counties, seed 20260925
```

The same seed draws the same counties. Timings vary with the network and the
server's load, so a rerun will land near, not exactly on, 1.78 s.

## Reproduce the figures

```bash
cd figures
python3 fig/src/build_figure_press_release_v2.py   # Figure 1 -> fig/figure_press_release_v2.png
node    fig/src/render_figure_app_v2.cjs           # Figure 2 -> fig/figure_app_v2.png
```

Figure 1 needs Python 3 with Pillow, LibreOffice (`soffice`), Poppler
(`pdftoppm`, `pdftotext`), R with ggplot2, dplyr and ragg, and Node with
Playwright. Figure 2 needs only Node with Playwright.

---

## The first version (2024)

`press_release_v1.zip` holds the workflow the first REPORTER used to render a
press release with R Markdown:

- `press_release_v1/report.Rmd`: the main file.
  - It relies on the CAT project's internal `catviz` R package to fetch data
    (`procure_data`, `procure_p`, `procure_cov`, wrappers for the CAT API).
  - It also uses `catviz` functions such as `tabulate_stat()` and
    `visualize_donut()` to draw charts in the style of the CAT VISUALIZER.
- `press_release_v1/report.docx`: an example output.

The method is the same in the current version: the same statistics, the same
sentence rules, and the same one-page layout. What changed is where each step
runs, which is why a release now takes about two seconds instead of about ten.

---

## Contact

Dr. Tim Fraser, Systems Engineering, Cornell University: <tmf77@cornell.edu>

# REPORTER benchmark, 26 September 2026

How long does the CAT REPORTER take to produce a one-page press release on a
county's transportation emissions? This folder holds the script that measured
it, the raw timings, the summary statistics, and every press release the run
generated.

## Result

100 randomly sampled US counties, timed on the live production REPORTER.

| statistic | seconds |
|---|---|
| mean | 1.780 |
| standard deviation | 0.270 |
| standard error (SD / √100) | 0.027 |
| median | 1.70 |
| minimum | 1.506 |
| maximum | 3.135 |

The 100 counties span 34 states and all 14 sampled years (1990, and
every fifth year from 2000 to 2060). Reaching 100 complete press releases took
103 draws. The three that did not count:

| draw | area | year | what happened |
|---|---|---|---|
| 7 | 72105 (Puerto Rico) | 2055 | no download: Puerto Rico is not in CATSERVER |
| 78 | 72111 (Puerto Rico) | 2020 | no download: Puerto Rico is not in CATSERVER |
| 101 | 35017 (Grant County, NM) | 2040 | a file downloaded, but CATSERVER has no 2040 estimate for this county, so the release carried no chart and no statistics |

## What is timed

For each county, the script opens the REPORTER page in headless Chromium,
deep-linked to that county and year, CO₂ equivalent, and the press release's
default breakdown (emissions by vehicle type, donut chart). It clicks
**Generate press release** and times the span from that click until the Word
file has finished downloading. That span covers everything a staffer waits
for:

1. reading the county's emissions from CATSERVER (in the browser, from Parquet
   objects),
2. computing the statistics,
3. writing the sentences,
4. drawing the chart,
5. assembling and downloading the `.docx`.

Loading the page is recorded (`load_s`) but not counted: a staffer loads the
page once. Counties run one at a time, one second apart.

A draw counts only if the downloaded file is a **complete** press release: the
chart is embedded and the bullets carry at least one percentage. Anything else
is logged with its reason and replaced by the next draw.

## Files

| file | contents |
|---|---|
| `benchmark_reporter.R` | entry point: draws the sample, runs the timer, audits every file, computes the statistics |
| `time_reporter.mjs` | the browser timer, called by the R script |
| `results/reporter_benchmark_20260926T121741Z_sample.csv` | the 120 draws (100 plus 20 spares), in order |
| `results/reporter_benchmark_20260926T121741Z.csv` | one row per draw: `load_s`, `generate_s`, file size, whether a file downloaded, whether it was complete, and the reason if not |
| `results/reporter_benchmark_20260926T121741Z_summary.csv` | the statistics in the table above |
| `results/reporter_benchmark_20260926T121741Z_env.txt` | seed, page URL, client R and Node versions, OS |
| `results/reporter_benchmark_20260926T121741Z_docx.zip` | every press release the run generated, named `<geoid>-<year>.docx` |

The timer runs all 120 draws; only the first 100 complete releases enter the
statistics (draws 1–103). The zip holds 116 files: 117 draws downloaded a file,
and the file for draw 120, an unused spare, was lost when the run's temporary
folder was cleared. The script now keeps every file in `results/` by default.

## Reproduce it

```bash
# needs: R (httr2, dplyr, purrr, readr, tibble, nanoparquet),
#        Node 18+ with `npm install -g playwright` and a Chromium build
Rscript benchmark_reporter.R                    # 100 counties, seed 20260925
N_COUNTIES=5 Rscript benchmark_reporter.R       # quick smoke test
```

Options (environment variables): `N_COUNTIES` (default 100), `BENCH_SEED`
(20260925), `OVERSAMPLE` (20 spare draws), `TIMEOUT_MS` (180000 per county),
`REPORTER_PAGE`, `PUBLIC_BASE`, `SAVE_DOCX_DIR`.

The page must be able to reach `connect.systems-apps.com`, `cdn.jsdelivr.net`
(the DuckDB-WASM engine) and `extensions.duckdb.org` (DuckDB's Parquet reader).
Run it when nothing else is loading the same server. A test run made while
another script was querying the server measured about 16 s per release instead
of about 2 s.

The same seed draws the same counties. The timings will differ from run to
run, because they depend on the network and on the server's load at the time.

## Secrets

None. The REPORTER page is public and its API needs no key. The scripts read no
credentials, send none, and print nothing sensitive.

## Provenance note

The published scripts differ from the copies that ran in two ways, neither of
which touches what is timed or how the statistics are computed:

1. they find their own folder, so they run from this repo as well as from the
   paper's repo;
2. they keep the `.docx` files in `results/` by default, where the run kept
   them in R's temporary folder.

The second change was made while the run was in progress. As a result, the
running script failed to parse its last few lines, after it had already
written the results and the summary. Every statistic above was then recomputed
independently from the raw CSV and the saved `.docx` files, and all of them
match.

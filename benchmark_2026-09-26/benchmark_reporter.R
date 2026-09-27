# bench/benchmark_reporter.R
# Benchmark: how long the CAT REPORTER takes to produce a one-page press release
# for randomly sampled US counties, timed on the live production page.
#
#   Rscript benchmark_reporter.R                  # 100 counties (default)
#   N_COUNTIES=5 Rscript benchmark_reporter.R     # smoke test
# (run it by its path from anywhere; outputs land in results/ next to it)
#
# Steps
#   1. sample   draw counties from the CAT area catalog (seeded) and a year for
#               each from 14 sampled years (1990 and every fifth year, 2000-2060)
#   2. time     bench/time_reporter.mjs drives the REPORTER page in headless
#               Chromium: for each county it clicks "Generate press release" and
#               times until the .docx download completes. That span is everything
#               a staffer waits for: reading the county's emissions (in the
#               browser, from CATSERVER's Parquet objects), computing the
#               statistics, writing the sentences, drawing the chart, and
#               assembling and downloading the Word file.
#   3. summarize mean, SD, SE (= SD / sqrt(n)), median, min, max over complete
#               press releases (chart embedded, statistics present)
#
# Why a browser: in the current REPORTER the data step runs in the user's
# browser (DuckDB-WASM over Parquet objects), so the API alone cannot reproduce
# what a staffer runs. R draws the sample and computes every statistic.
#
# Needs: R (httr2, dplyr, purrr, readr, tibble, nanoparquet), Node 18+, and the
# `playwright` npm package installed globally with a Chromium build. The page
# loads DuckDB-WASM from cdn.jsdelivr.net, so that host must be reachable.
#
# Secrets: none. The REPORTER page is public and its API is keyless; this
# script reads no key, sends no credentials, and prints nothing sensitive.
#
# Output (results/ next to this script):
#   reporter_benchmark_<stamp>_sample.csv    the drawn sample, in order
#   reporter_benchmark_<stamp>.csv           one row per attempt
#   reporter_benchmark_<stamp>_summary.csv   the statistics the paper reports
#   reporter_benchmark_<stamp>_env.txt       what ran, where (no hostnames)
#   reporter_benchmark_<stamp>_docx/         every press release the run generated,
#                                            named <geoid>-<year>.docx

suppressPackageStartupMessages({
  library(httr2)
  library(dplyr)
  library(purrr)
  library(readr)
  library(tibble)
  library(nanoparquet)
})

# ---- settings -------------------------------------------------------------
public_base = Sys.getenv("PUBLIC_BASE", "https://connect.systems-apps.com/cat-public")
n_counties  = as.integer(Sys.getenv("N_COUNTIES", "100"))
seed        = as.integer(Sys.getenv("BENCH_SEED", "20260925"))
oversample  = as.integer(Sys.getenv("OVERSAMPLE", "20"))   # spare draws, used only if a county fails
years       = c(1990L, seq(2000L, 2060L, by = 5L))         # 14 sampled years: 1990 and every fifth year, 2000-2060
# Paths are relative to this script's own folder, so it runs unchanged from the
# paper repo (bench/) or the public replication repo (benchmark_2026-09-26/).
script_arg  = grep("^--file=", commandArgs(FALSE), value = TRUE)
bench_dir   = if (length(script_arg)) dirname(normalizePath(sub("^--file=", "", script_arg))) else getwd()
out_dir     = file.path(bench_dir, "results")
stamp       = format(Sys.time(), "%Y%m%dT%H%M%SZ", tz = "UTC")
path_of     = function(suffix) file.path(out_dir, paste0("reporter_benchmark_", stamp, suffix))
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

# ---- 1. sample --------------------------------------------------------------
areas_path = tempfile(fileext = ".parquet")
request(paste0(public_base, "/objects/lookup/areas.parquet")) |>
  req_timeout(120) |>
  req_perform(path = areas_path)
counties = read_parquet(areas_path) |>
  as_tibble() |>
  filter(level == "county", grepl("^[0-9]{5}$", geoid)) |>
  distinct(geoid) |>
  pull(geoid)
message("📋 sampling frame: ", length(counties), " counties")

set.seed(seed)
n_draw = min(length(counties), n_counties + oversample)
sample_tbl = tibble(geoid = sample(counties, n_draw),
                    year  = sample(years, n_draw, replace = TRUE))
write_csv(sample_tbl, path_of("_sample.csv"))

# ---- 2. time ----------------------------------------------------------------
# The timer runs every drawn county in order; step 3 keeps the first n_counties
# successes, so a county that fails is reported and replaced, never dropped.
timer = file.path(bench_dir, "time_reporter.mjs")
# Every generated press release is kept, so the sample can be audited and published.
docx_dir = Sys.getenv("SAVE_DOCX_DIR", path_of("_docx"))
dir.create(docx_dir, recursive = TRUE, showWarnings = FALSE)
status = system2("node", c(timer, path_of("_sample.csv"), path_of(".csv")),
                 env = paste0("SAVE_DOCX_DIR=", docx_dir))
if (status != 0) stop("❌ the browser timer exited with status ", status)

# A download only counts if it is a complete press release: the vehicle-type
# chart is embedded (two logos + the chart = 3 images) and the bullets carry at
# least one percentage. A county-year CATSERVER has no estimate for downloads a
# release with neither, so it is recorded as a failure and replaced.
complete_release = function(path) {
  if (!file.exists(path)) return(FALSE)
  n_media = sum(grepl("^word/media/", unzip(path, list = TRUE)$Name))
  xml = paste(readLines(unz(path, "word/document.xml"), warn = FALSE), collapse = "")
  n_media >= 3 && grepl("[0-9]%", xml)
}
runs = read_csv(path_of(".csv"), col_types = cols(geoid = "c", error = "c", .default = col_guess())) |>
  mutate(draw = row_number(),
         complete = map2_lgl(geoid, year, \(g, y) complete_release(file.path(docx_dir, paste0(g, "-", y, ".docx")))),
         ok = docx_ok & complete,
         reason = case_when(ok ~ NA_character_,
                            docx_ok ~ "downloaded, but no chart or statistics (no estimate for this county-year)",
                            TRUE ~ "no download (area not in CATSERVER, or timeout)"))
write_csv(runs, path_of(".csv"))
good = runs |>
  filter(ok) |>
  slice_head(n = n_counties)
used = runs |> filter(draw <= max(good$draw, 0L))

# ---- 3. summarize -------------------------------------------------------------
describe = function(x) tibble(n = length(x), mean = mean(x), sd = sd(x),
                              se = sd(x) / sqrt(length(x)), median = median(x),
                              min = min(x), max = max(x))
summary_tbl = describe(good$generate_s) |>
  mutate(stage = "click to downloaded .docx (s)",
         attempts = nrow(used), failures = sum(!used$ok)) |>
  relocate(stage)
write_csv(summary_tbl, path_of("_summary.csv"))

si = Sys.info()
writeLines(c(
  paste("run_utc:", stamp),
  paste("page:", Sys.getenv("REPORTER_PAGE", "https://connect.systems-apps.com/cat/#/reporter")),
  paste("seed:", seed, "| n_counties:", n_counties, "| pollutant: 98 (CO2e) | breakdown: vehicle type, donut"),
  paste("client:", R.version.string, "|", si[["sysname"]], si[["release"]], si[["machine"]]),
  paste("node:", system2("node", "--version", stdout = TRUE))
), path_of("_env.txt"))

print(summary_tbl, width = Inf)
if (nrow(good) < n_counties) warning("⚠️ only ", nrow(good), " of ", n_counties, " counties succeeded")
message("💾 wrote ", path_of("*"))

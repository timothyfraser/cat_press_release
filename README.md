# cat_press_release
Public data sharing of basic software design behind REPORTER v1 Press Release for Climate Action in Transportation.

---

This zipfile contains the basic workflow necessary for rendering a Press Release using the REPORTER software with RMarkdown.

Some key considerations:
- `press_release_v1.zip/report.Rmd`: main file
   - relies on proprietary `catviz` R package to perform key functions like `procure_data`, `procure_p`, `procure_cov`. These are all wrappers for accessing the CAT API securely.
   - relies on proprietary `catviz` R package functions like `tabulate_stat()` and `visualize_donut()` to generate visualizations in the style of the CAT VISUALIZER.
- `press_release_v1.zip/report.docx`: example output


---

## Benchmark (September 2026)

`benchmark_2026-09-26/` times the current production REPORTER on 100 randomly
sampled US counties, from the click on **Generate press release** to the
downloaded Word file: mean 1.78 s (SD 0.27, SE 0.027). The folder has the R and
Node scripts that ran it, the raw per-county timings, the summary statistics,
and a zip of every press release the run generated. See its README.

---

For questions, reach out to Dr. Tim Fraser <tmf77@cornell.edu>, Systems Engineering @ Cornell University

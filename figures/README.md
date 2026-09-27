# Figures 1 and 2

The paper's two figures of the REPORTER, and the code that builds them. Both
are built from the live REPORTER's real output for the paper's running
example: **Tompkins County, NY, 2020, CO₂ equivalent, broken down by vehicle
type, bar chart**
(<https://cat-apps.com/reporter?tab=standard&geoid=36109&year=2020&pollutant=98&set=sourcetype&chart=bar>).

```bash
cd figures
python3 fig/src/build_figure_press_release_v2.py   # Figure 1
node    fig/src/render_figure_app_v2.cjs           # Figure 2
```

## Figure 1: an example press release, annotated

`fig/figure_press_release_v2.png`

| file | role |
|---|---|
| `fig/src/press_release_tompkins_2020.docx` | the press release exactly as the REPORTER downloaded it, September 2026 |
| `fig/src/chart_tompkins_2020_print.R` | redraws the release's chart at print size (ggplot2) |
| `fig/src/chart_tompkins_2020_print.png` | that chart |
| `fig/src/build_figure_press_release_v2.py` | renders the page and adds the bracket labels (it writes a temporary `figure_press_release_v2.html` beside itself, which git ignores) |

What the build does:

1. **Renders the `.docx` to an image** with LibreOffice. One render-only fix is
   applied first: line spacing gets an explicit `lineRule="auto"`, which is
   Word's own default, because LibreOffice otherwise clips inline images to one
   line of text. The words on the page are the REPORTER's output, untouched.
2. **Redraws the chart at print size.** The REPORTER draws its chart for a
   letter-size Word page; shrunk to journal width, its labels become
   unreadable. The R script redraws it from the release's own values (light
   trucks 48.8%, cars and bikes 27.7%, heavy trucks 11.0%, combo trucks 10.7%,
   buses 1.9%) and its own colours, and the build widens the chart column to
   fit. The paper's caption says so. Pass `--as-generated` to skip this and
   render the file exactly as downloaded.
3. **Adds the bracket labels** (Logos, Headline, Hook, ...), placed from the
   positions of the words on the rendered page.

The contact block at the bottom ("Department Name, Organization Name, ...") is
the REPORTER's own template text, for the agency to fill in.

## Figure 2: the REPORTER interface, annotated

`fig/figure_app_v2.png`

| file | role |
|---|---|
| `fig/src/figure_app_v2_crop.png` | a screenshot of the Standard Report form, September 2026 |
| `fig/src/figure_app_v2.html` | lays the numbered callouts (1–7) and the headline over it |
| `fig/src/render_figure_app_v2.cjs` | renders the HTML to the PNG |

In the screenshot, the neighbouring **AI REPORT** tab is painted over with the
page background. It is a separate, AI-written mode that the paper does not
study, and leaving it in the figure invited readers to assume the press release
itself is AI-generated. Nothing else in the screenshot is altered.

## Rebuilding

A rebuild reproduces both figures. Figure 2 comes out pixel-identical. Figure 1
can differ from the committed PNG only in the anti-aliasing of the bracket
labels' text (in a test rebuild, 0.14% of pixels, none visibly), which depends
on the fonts installed on the machine.

#!/usr/bin/env python3
"""Build Figure 1 (annotated press release) from the REPORTER's real output.

    python3 fig/src/build_figure_press_release_v2.py [DOCX_OR_PDF] [OUT_PNG]

DOCX_OR_PDF  the press release as downloaded from the REPORTER
             (default fig/src/press_release_tompkins_2020.docx), or a PDF of it
OUT_PNG      default fig/figure_press_release_v2.png

A .docx is rendered to PDF with LibreOffice. One render-only normalisation is
applied first: every <w:spacing w:line="240"/> gets an explicit
w:lineRule="auto". That IS the OOXML default (ECMA-376 17.3.1.33), which Word
applies; LibreOffice instead treats a missing lineRule as "exact" and clips each
inline image to one text line, which hides the chart and crops the logos. The
page's words are the product's own output, untouched.

Print layout (Tim, 2026-09-27; stated in the figure caption): the REPORTER's
browser chart is 1920 x 1200 px (1.6:1), so at journal size its labels are tiny and
it leaves a tall empty gap beside the bullets. For the figure the chart is redrawn at
print size by fig/src/chart_tompkins_2020_print.R (ggplot2, the REPORTER's own
server-side chart engine) from the release's exact values and colours, and the two
columns are resized to 3.4 in (chart) and 3.0 in (bullets) so both fill the same
height. Pass --as-generated to render the file exactly as downloaded.
"""
import html, os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
args = [a for a in sys.argv[1:] if not a.startswith("--")]
src = args[0] if len(args) > 0 else os.path.join(HERE, "press_release_tompkins_2020.docx")
out = args[1] if len(args) > 1 else os.path.join(REPO, "fig", "figure_press_release_v2.png")
DPI = 200
tmp = tempfile.mkdtemp()


PRINT_LAYOUT = "--as-generated" not in sys.argv
CHART_W_EMU = int(3.4 * 914400)


def find_chart(docx):
    """(media path, print-size chart PNG bytes, width/height, original cx) for the chart."""
    import io, zipfile
    from PIL import Image
    z = zipfile.ZipFile(docx)
    xml = z.read("word/document.xml").decode("utf-8")
    rels = z.read("word/_rels/document.xml.rels").decode("utf-8")
    best = max(re.finditer(r'<wp:extent cx="(\d+)" cy="(\d+)"/>.*?r:embed="([^"]+)"', xml, re.S),
               key=lambda m: int(m.group(1)))
    target = re.search(r'Id="%s"[^>]*Target="([^"]+)"' % best.group(3), rels).group(1)
    chart = os.path.join(HERE, "chart_tompkins_2020_print.png")
    if not os.path.exists(chart):
        subprocess.run(["Rscript", os.path.join(HERE, "chart_tompkins_2020_print.R")], cwd=REPO, check=True)
    data = open(chart, "rb").read()
    w, h = Image.open(io.BytesIO(data)).size
    return "word/" + target, data, w / h, best.group(1)


def print_layout_xml(xml):
    """Side by side as the REPORTER sets it, with columns sized to the print chart."""
    xml = re.sub(r'<w:cols w:num="2".*?</w:cols>',
                 '<w:cols w:num="2" w:sep="1" w:space="144" w:equalWidth="0">'
                 '<w:col w:w="4896" w:space="144"/><w:col w:w="4320"/></w:cols>', xml, flags=re.S)
    cy = int(CHART_W_EMU / chart_aspect)
    i = xml.index('cx="%s"' % chart_cx)
    p0 = max(xml.rfind("<w:p>", 0, i), xml.rfind("<w:p ", 0, i)); p1 = xml.index("</w:p>", i)
    para = re.sub(r'(<wp:extent|<a:ext) cx="%s" cy="\d+"' % chart_cx, r'\1 cx="%d" cy="%d"' % (CHART_W_EMU, cy), xml[p0:p1])
    xml = xml[:p0] + para + xml[p1:]
    # a little air above the conclusion paragraph
    k = xml.index("In conclusion")
    q0 = max(xml.rfind("<w:p>", 0, k), xml.rfind("<w:p ", 0, k))
    q = re.sub(r'<w:spacing w:after="(\d+)" w:before="0"', r'<w:spacing w:after="\1" w:before="160"', xml[q0:k], count=1)
    return xml[:q0] + q + xml[k:]


def docx_to_pdf(docx):
    """Render a .docx to PDF with LibreOffice after making lineRule explicit."""
    import zipfile
    global chart_media, trimmed_chart, chart_aspect, chart_cx
    if PRINT_LAYOUT:
        chart_media, trimmed_chart, chart_aspect, chart_cx = find_chart(docx)
    fixed = os.path.join(tmp, "release.docx")
    with zipfile.ZipFile(docx) as zin, zipfile.ZipFile(fixed, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                xml = data.decode("utf-8")
                xml = re.sub(r'(<w:spacing\b(?![^>]*w:lineRule)[^>]*\bw:line="\d+")', r'\1 w:lineRule="auto"', xml)
                if PRINT_LAYOUT:
                    xml = print_layout_xml(xml)
                data = xml.encode("utf-8")
            elif PRINT_LAYOUT and item.filename == chart_media:
                data = trimmed_chart
            zout.writestr(item, data)
    env = dict(os.environ, HOME=tmp)  # private LibreOffice profile
    subprocess.run(["soffice", "--headless", "--norestore", "--convert-to", "pdf", "--outdir", tmp, fixed],
                   check=True, capture_output=True, env=env, timeout=180)
    return os.path.join(tmp, "release.pdf")


pdf = docx_to_pdf(src) if src.lower().endswith(".docx") else src
npages = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout).group(1))
if npages != 1:
    sys.exit("the press release renders to %d pages; it must fit on one" % npages)

# 1. page image
subprocess.run(["pdftoppm", "-r", str(DPI), "-png", "-singlefile", "-f", "1", "-l", "1", pdf,
                os.path.join(tmp, "page")], check=True)
page_png = os.path.join(tmp, "page.png")

# 2. word boxes (PDF points) -> lines
bbox = subprocess.run(["pdftotext", "-bbox", "-f", "1", "-l", "1", pdf, "-"],
                      capture_output=True, text=True, check=True).stdout
pw, ph = map(float, re.search(r'<page width="([\d.]+)" height="([\d.]+)"', bbox).groups())
words = [(float(a), float(b), float(c), float(d), html.unescape(w)) for a, b, c, d, w in
         re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>', bbox)]
text = " ".join(w[4] for w in words)


def y_of(pattern, which="top", after=0.0):
    """y (points) of the first word run matching `pattern` at or below `after`."""
    toks = pattern.split()
    for i in range(len(words) - len(toks) + 1):
        if words[i][1] < after:
            continue
        if all(words[i + k][4].startswith(t) for k, t in enumerate(toks)):
            return words[i][1] if which == "top" else words[i + len(toks) - 1][3]
    sys.exit("anchor not found in the PDF text: %r" % pattern)


def last_y_before(limit):
    return max(w[3] for w in words if w[3] <= limit)


head_top = y_of("Carbon Emissions")

hook_top = y_of("New Research")
b1_top = y_of("1.", after=hook_top)
hook_bottom = y_of("sustainable environment", which="bottom", after=hook_top)
concl_top = y_of("In conclusion")
contact_top = y_of("Contact Information")
bottom = max(w[3] for w in words)
bullet2_top = y_of("2.", after=b1_top)
b2_tag_bottom = y_of("Still a Concern", which="bottom", after=bullet2_top) if "Still a Concern" in text else bullet2_top + 12
b3_top = y_of("3.", after=bullet2_top)

spans = [  # (label, top, bottom, anchor_top?)
    ("Logos", max(head_top - 55, 20), head_top - 4, False),
    ("Headline", head_top, y_of("Made with") - 2, False),
    ("Hook", hook_top, hook_bottom, False),
    ("3 Bullet Points<br>+ Chart", hook_bottom + 6, last_y_before(concl_top - 2), True),
    ("Interpretation<br>Paragraph", concl_top, last_y_before(contact_top - 2), False),
    ("Agency Contact<br>Information", contact_top, bottom, False),
]
sub = [("<i>Eg. Bullet 2:</i>", None, None), ("Bullet Tagline", bullet2_top, b2_tag_bottom),
       ("Statistics in Text", b2_tag_bottom, b3_top - 4)]

# 3. HTML overlay (page scaled to 700 px wide; labels in a 360 px right column)
W_PAGE = 700
k = W_PAGE / pw
T0 = max(0.0, head_top - 75)        # crop the empty top margin above the logos
H_PAGE = (min(ph, bottom + 32) - T0) * k   # ...and the empty page below the contact block
items = []
spans = [(l, t - T0, b - T0, a) for l, t, b, a in spans]
sub = [sub[0]] + [(l, t - T0, b - T0) for l, t, b in sub[1:]]
for label, t, b, at_top in spans:
    ly = f'top:{t*k:.0f}px;transform:none' if at_top else f'top:{(t+b)/2*k:.0f}px'
    items.append(f'<div class="br" style="top:{t*k:.0f}px;height:{max((b-t)*k,14):.0f}px"></div>'
                 f'<div class="lb" style="{ly}">{label}</div>')
for label, t, b in sub[1:]:
    items.append(f'<div class="br sm" style="top:{t*k:.0f}px;height:{max((b-t)*k,10):.0f}px"></div>'
                 f'<div class="lb sm" style="top:{(t+b)/2*k:.0f}px">{label}</div>')
if True:
    items.append(f'<div class="lb note" style="top:{(sub[1][1]*k)-26:.0f}px">{sub[0][0]}</div>')
doc = f"""<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@500;700&display=swap" rel="stylesheet">
<style>
 body{{margin:0;background:#fff;font-family:Inter,Arial,sans-serif}}
 .wrap{{position:relative;width:{W_PAGE+380}px;height:{H_PAGE+4:.0f}px;padding:16px}}
 .pgbox{{position:absolute;left:16px;top:16px;width:{W_PAGE}px;height:{H_PAGE:.0f}px;overflow:hidden;border:1px solid #222}}
 .pg{{display:block;width:{W_PAGE}px;margin-top:-{T0*k:.0f}px}}
 .col{{position:absolute;left:{W_PAGE+40}px;top:16px;width:340px;height:{H_PAGE:.0f}px}}
 .br{{position:absolute;left:0;width:10px;border:2px solid #111;border-left:none}}
 .br.sm{{left:18px;width:7px}}
 .lb{{position:absolute;left:26px;transform:translateY(-50%);font-weight:700;font-size:25px;line-height:1.1;color:#111}}
 .lb.sm{{left:34px;font-size:21px}}
 .lb.note{{left:34px;font-size:17px;font-weight:500;transform:none}}
</style></head><body><div class="wrap">
<div class="pgbox"><img class="pg" src="file://{page_png}"></div>
<div class="col">{''.join(items)}</div></div></body></html>"""
html_path = os.path.join(HERE, "figure_press_release_v2.html")
open(html_path, "w").write(doc)

# 4. render
js = f"""
const {{createRequire}} = require("node:module"); const {{execSync}} = require("node:child_process");
const r = createRequire(__filename);
const {{ chromium }} = r(r.resolve("playwright", {{ paths: [execSync("npm root -g").toString().trim()] }}));
(async () => {{
  const exe = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome";
  const b = await chromium.launch(require("fs").existsSync(exe) ? {{ executablePath: exe }} : {{}});
  const p = await b.newPage({{ viewport: {{ width: {W_PAGE+412}, height: {int(H_PAGE)+40} }}, deviceScaleFactor: 2 }});
  await p.goto("file://{html_path}", {{ waitUntil: "networkidle" }});
  await p.locator(".wrap").screenshot({{ path: "{out}" }});
  await b.close();
}})();
"""
js_path = os.path.join(tmp, "render.cjs")
open(js_path, "w").write(js)
subprocess.run(["node", js_path], check=True)
print("wrote", out)

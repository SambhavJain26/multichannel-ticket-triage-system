# HTML recreation of the earlier square brief

Open `square-brief-original.html` in a browser. It is an editable HTML/CSS recreation of the four-page `output/pdf/maintenance-triage-square-brief.pdf`, not a wrapper around page images. Copy, cards, icons, links, and connectors remain DOM/SVG elements. Its shared icon script and local Geist/Manrope fonts are loaded from this repository; no internet connection is required. The separately named export is `output/pdf/maintenance-triage-square-brief-html-recreation.pdf`.

The fixed 864px square pages preserve the PDF's 9-inch proportions. For print, the stylesheet declares four 9-inch square pages with no margins. The layout is fixed to match the source, so a narrow phone browser can scroll horizontally rather than reflowing the process diagrams.

To render and check all four pages from the repository root:

```powershell
node concept-brief/scripts/render-original-html.cjs
```

The checker saves temporary PNGs under `tmp/pdfs/original-html/`, rejects content extending past a page, the footer, or its containing card, and exports the new PDF. The original PDF and the newer `square-brief.html`/CSS/PDF are unchanged. The export was verified as four 648pt-square pages with its booking link; all four Poppler renders were visually reviewed.

The spacing pass tightened that check: visible text must clear its card edges by at least 12 CSS pixels, the comparison key must clear its enclosing panel, and matching lane/card tops must align. It increased research-note insets, rebalanced comparison rows and key spacing, gave the responsibility rail a safer bottom margin, aligned the outer integration cards, equalized the central stack gaps, and increased text clearance in the integration and operations cards. `ui-ux-foundations` guided the consistent insets and alignment; the high-end design skill's nested-frame principle was retained selectively, without importing website motion into a PDF.

The page-two decision highlight now begins beside the process rail rather than covering it. All numbered-circle centers coincide with the rail center. The renderer asserts both the circle-to-line alignment and the highlight's clearance from the circle, title, and manager badge.

## Personalize one prospect

Copy `concept-brief/prospect-data.template.json` to a new JSON file for the lead. Fill the required `slug`, `company`, `decisionMaker`, one to three short `research.reviewed` source labels, and a short `research.note` based on verified facts. Keep source URLs or research notes in `research.evidence`; this field is for your records and is **not printed** in the PDF. Avoid claims about the prospect's process that your research does not support.

Fill the optional `systems` and `routes` fields only when confirmed. A blank optional value leaves its bracketed placeholder in the PDF so an unknown PMS, approval channel, API route, or hosting choice is not presented as fact. Keep the research note under 260 characters and source labels short enough to fit their panel. The exporter checks for missing required data, page overflow, text clearance, and CTA validity.

From the repository root, run:

```powershell
node concept-brief/scripts/render-original-html.cjs --data path/to/prospect.json
```

This writes `output/pdf/<slug>-maintenance-triage-brief.pdf`. To choose another distinct PDF path, add `--output path/to/brief.pdf`. The reusable HTML and placeholder PDF are not overwritten by a prospect export. Running the command without `--data` regenerates only the placeholder template PDF. `concept-brief/fixtures/prospect-data.qa.json` contains fictional test data for renderer checks; do not send its output to a prospect.

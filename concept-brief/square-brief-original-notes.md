# HTML recreation of the earlier square brief

Open `square-brief-original.html` in a browser. It is an editable HTML/CSS recreation of the four-page `output/pdf/maintenance-triage-square-brief.pdf`, not a wrapper around page images. Copy, cards, icons, links, and connectors remain DOM/SVG elements. Its shared icon script and local Geist/Manrope fonts are loaded from this repository; no internet connection is required. The separately named export is `output/pdf/maintenance-triage-square-brief-html-recreation.pdf`.

The fixed 864px square pages preserve the PDF's 9-inch proportions. For print, the stylesheet declares four 9-inch square pages with no margins. The layout is fixed to match the source, so a narrow phone browser can scroll horizontally rather than reflowing the process diagrams.

To render and check all four pages from the repository root:

```powershell
node concept-brief/scripts/render-original-html.cjs
```

The checker saves temporary PNGs under `tmp/pdfs/original-html/`, rejects content extending past a page, the footer, or its containing card, and exports the new PDF. The original PDF and the newer `square-brief.html`/CSS/PDF are unchanged. The export was verified as four 648pt-square pages with its booking link; all four Poppler renders were visually reviewed.

The spacing pass tightened that check: visible text must clear its card edges by at least 12 CSS pixels, the comparison key must clear its enclosing panel, and matching lane/card tops must align. It increased research-note insets, rebalanced comparison rows and key spacing, gave the responsibility rail a safer bottom margin, aligned the outer integration cards, equalized the central stack gaps, and increased text clearance in the integration and operations cards. `ui-ux-foundations` guided the consistent insets and alignment; the high-end design skill's nested-frame principle was retained selectively, without importing website motion into a PDF.

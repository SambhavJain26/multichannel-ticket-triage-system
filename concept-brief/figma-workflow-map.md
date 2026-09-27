# Prospect workflow map

Editable source: https://www.figma.com/design/o0OBwdcDGsqv3oinTTG4Om

Final PDF: `output/pdf/maintenance-triage-workflow-map.pdf`.

Four A4 landscape pages cover business outcomes, end-to-end workflow, systems integration, and staged implementation. This is a generic prospect handout, with no invented company facts, customer results, delivery dates, pricing, or universal connector guarantees. It is separate from the existing three-page prospect briefs.

## Figma frames in reading order

1. `4:2` - A clearer path from report to repair.
2. `4:55` - Follow one maintenance request.
3. `4:122` - How it connects to your business.
4. `4:194` - Start small. Expand on evidence.

`figma-workflow-map.js` is the editable authoring recipe for a fresh Figma Design file. For later changes in the existing file, edit the named frames rather than rerunning it and duplicating pages. Fonts are Geist and Manrope. Pages use neutral existing systems, forest preparation, amber human gates and red exceptions.

Export each frame with Figma `download_assets` using PDF format; save exports as `tmp/pdfs/figma-page-1.pdf` through `figma-page-4.pdf`. Run `scripts/assemble-prospect-workflow-map.py` with a Python runtime containing pypdf. It merges and scales the genuine Figma exports without redrawing them, retains searchable text and the booking link, and checks the core content. Render the resulting PDF with Poppler and visually inspect all pages after edits. Temporary export URLs are secrets and must not enter Git.

## Evidence and scope

Content is based on `progress-notes.md`, `build-plan.md`, `maintenance-triage-demo-build-plan.md`, `02-maintenance-triage.md`, `foundation-2-maintenance-operations.md`, and the production blueprint, how-it-works, build-description, build-technical-notes and operating-guide documents under `docs/`.

The production blueprint governs the proposed connected business process. Current progress and Stage 9 documentation govern what the demo can be said to demonstrate. The handout explicitly reserves PMS integration, verified identity, production controls and broader safety testing for implementation. Its 1,000-request / three-minute / 50-hour example is hypothetical arithmetic, not a measured result or an industry benchmark.

The blueprint's old Excalidraw recommendation is superseded for this deliverable by the user's explicit Figma request. The full technical reference is condensed into six business steps and contextual branches for prospect readability. No workflow or production service is changed.

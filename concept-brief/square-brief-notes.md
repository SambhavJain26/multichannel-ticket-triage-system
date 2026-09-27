# Square production brief

Build with `python concept-brief/scripts/build-square-brief.py` using a Python environment with `reportlab` and `fonttools`. The bundled Codex Python environment was used for the verified export. Variable font sources and OFL licenses are in `assets/fonts`; static instances are generated under ignored `tmp/pdfs/square-fonts`.

Output: `output/pdf/maintenance-triage-square-brief.pdf`. Four 648 x 648 point pages. Preserve earlier versions under dated `output/pdf/archive` folders before replacing the output. Do not modify the portrait template or sent prospect PDFs as a side effect.

## Content authority

`docs/production-maintenance-triage-blueprint.md` controls the operating model. This brief describes the proposed production scope, not a demo, completed client deployment, or guaranteed result.

- Page 1: sections 1, 3, and 4 - five-step current/system comparison, researched relevance placeholders, business value, and retained staff authority.
- Page 2: sections 3, 7, and 8 - all eight lifecycle stages through closure, verified identity, follow-up questions, separate escalate-only rules, human and owner approvals, confirmed outbound state, vendor progress, and status behaviour. The general workflow takes priority over the optional leak example.
- Page 3: sections 4, 5, and 6 - controlled integrations, isolated approved hosting, operational state versus PMS business records. n8n, PostgreSQL, and OpenAI are proposed implementation choices, not mandatory blueprint vendors. Queue state can live in PostgreSQL; runtime queue implementation is a detailed engineering choice.
- Page 4: sections 1, 8, and 9 - daily operations, authority, exceptions, access controls, monitoring, reconciliation, tested recovery, and mechanism-to-outcome statements. Lifecycle completion stays on page 2.

## Design references

Reviewed all three rendered pages of `output/pdf/maintenance-triage-prospect-brief.pdf` and the portfolio's `src/index.css`, `Hero.tsx`, `Methodology.tsx`, and `OutcomeBand.tsx`. Adopted Geist display headings, Manrope body text, warm stone background, terracotta brand emphasis, nested rounded frames, thin icons, and dark anchor panels. Green denotes added preparation or confirmed operational movement; existing client tools remain neutral. No gradients.

## Current reference audit

See `square-brief-design-audit.md` for page-specific findings, reference principles, changes and verification. The latest connection map supersedes the historical numbered-key layout below: methods now sit beside each endpoint, with separate payload arrows in a wide corridor. The incoming PDF and builder are archived under `square-20260928-reference-audit`.

## QA

Render with Poppler and inspect every page. Confirm exactly four square pages, no overflow or line collisions, distinct AI/fixed-policy display, no AI-to-vendor connection, working CTA, and no demo language. Only use verified facts when replacing personalization placeholders. Keep template placeholders visible until a specific prospect is selected.

## 2026-09-28 redesign

Previous PDF and exact builder preserved together in `output/pdf/archive/square-20260928-redesign/`. Portrait sources, sent prospect PDFs, and unrelated working-tree edits are outside this task.

Compact shared headers; 22pt Geist titles; 13-15pt sections; 11pt main copy and 10pt diagram/support labels. Metadata is 8-9pt. No font shrinking on overflow: Paragraph height assertions catch exceeded text budgets. Page 3 uses a numbered connection key to retain readable route labels without crowding arrow corridors. Connections describe a proposed implementation; account access and write permissions remain confirmation fields.

Run `python concept-brief/scripts/validate-square-brief.py` after building. It checks page dimensions/count, embedded used fonts, CTA annotation, text boundaries, key capability terms, and archive existence. Visual inspection remains required for connectors and reading order. Poppler is available; `pdffonts` and PyMuPDF are not, so font/link checks use pypdf and text geometry uses pdfplumber.

### Reference and frontend-skill pass

Re-rendered and reviewed all three pages of `maintenance-triage-prospect-brief.pdf` at the user's request. Preserved its inset research card, rounded surfaces, small topic pills, terracotta headline emphasis, dark branch rail, and dark service header; did not inherit its oversized gaps or smaller text. The existing portrait artifact is unchanged.

Applied `design-taste-frontend` for audit-first brand preservation and component consistency, `high-end-visual-design` for selective nested framing, and `ui-ux-foundations` for hierarchy, meaningful color, text contrast, and diagram spacing. Design read: operational solution brief for property-management decision-makers, warm architectural style. Dials: variance 4, motion 1 (static PDF), density 5. These are design heuristics, not a change to ReportLab. Website-only motion, breakpoints, image requirements, and library defaults do not apply; user-approved two semantic accents, dark panels, and four-page content take precedence.

Final checks: every page inspected at 648px (72 dpi, point-for-pixel) and 1100px desktop renders. Corrected intake path crossing, connector label clearance, and a divider close to body text. Structural validation passes: four 648pt square pages, three embedded used typefaces, valid meeting URL annotation, text within page margins, required feature families, and preserved archive. The archived PDF's Git blob hash equals the pre-edit HEAD PDF hash.

## 2026-09-28 full design pass

Archived the incoming PDF and builder under `output/pdf/archive/square-20260928-design-polish/` before editing. Applied the existing design-taste-frontend, high-end-visual-design, and ui-ux-foundations guidance to the document's static surfaces. The four-page structure and production authority remain unchanged.

- Matched card padding, rounded icon tiles, heading positions, and comparison text starts across both lanes. Reused ten licensed Lucide icon definitions from the portfolio dependency, rendered as vectors through ReportLab's existing SVG-path support. No new runtime dependency or rendering framework.
- Right-aligned the recipient consistently with the page margin; adjusted research-panel padding; centered workflow numbers on their shared rail.
- Clarified connection labels and gave each system a consistent icon/header treatment. Human review now explicitly applies at any stage, removing the misleading edge from only the execution stage.
- Rebuilt page 4 as two concise daily-operation/authority panels, one unified controls-and-recovery section, and a single business-outcome paragraph. The closing panel is now 92pt deep (previously 43pt), with a 38pt meeting button, separate explanatory line, and readable 10pt contact details. Shortened copy within its blocks to retain padding without reducing body size.
- Kept diagram labels at 10pt, main copy at 11pt, semantic green for automation, neutral existing tools, and terracotta for decision/brand emphasis. Reviewed final renders at desktop and native page size; the existing validator checks fonts, links, page dimensions, required capabilities, and text boundaries.
- Checked representative text contrast: white on terracotta 4.57:1; green on light green 6.30:1; muted text on warm paper 6.64:1; peach and muted light text on dark panels exceed 9:1. These are visual contrast checks, not a claim of a fully tagged accessible PDF.
- Final spacing review also applied `redesign-existing-projects`: retained the established brand and ReportLab stack, audited wrapping and shared alignments, and removed page-two dividers that crowded the inter-step gaps. The process rail and distinct approval panel retain the reading order. Re-inspected all four final desktop renders after the interrupted session resumed.

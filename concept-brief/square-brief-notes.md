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

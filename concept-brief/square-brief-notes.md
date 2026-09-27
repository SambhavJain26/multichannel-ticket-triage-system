# Square production brief

Build with `python concept-brief/scripts/build-square-brief.py` using a Python environment with `reportlab` and `fonttools`. The bundled Codex Python environment was used for the verified export. Variable font sources and OFL licenses are in `assets/fonts`; static instances are generated under ignored `tmp/pdfs/square-fonts`.

Output: `output/pdf/maintenance-triage-square-brief.pdf`. Four 648 x 648 point pages. Preserve earlier versions under dated `output/pdf/archive` folders before replacing the output. Do not modify the portrait template or sent prospect PDFs as a side effect.

## Content authority

`docs/production-maintenance-triage-blueprint.md` controls the operating model. This brief describes the proposed production scope, not a demo, completed client deployment, or guaranteed result.

- Page 1: sections 1, 3, and 4 - business impact, preparation functions, existing systems and staff authority.
- Page 2: sections 2, 7, and 8 - leak example, verified identity, follow-up questions, separate escalate-only rules, human approval, confirmed outbound state.
- Page 3: sections 4, 5, and 6 - controlled integrations, isolated approved hosting, operational state versus PMS business records. n8n, PostgreSQL, and OpenAI are proposed implementation choices, not mandatory blueprint vendors. Queue state can live in PostgreSQL; runtime queue implementation is a detailed engineering choice.
- Page 4: sections 8 and 9 - vendor response, confirmed appointment, progress, human verification/closure, exceptions, access controls, monitoring, reconciliation, and recovery.

## Design references

Reviewed all three rendered pages of `output/pdf/maintenance-triage-prospect-brief.pdf` and the portfolio's `src/index.css`, `Hero.tsx`, `Methodology.tsx`, and `OutcomeBand.tsx`. Adopted Geist display headings, Manrope body text, warm stone background, terracotta brand emphasis, nested rounded frames, thin icons, and dark anchor panels. Green denotes added preparation or confirmed operational movement; existing client tools remain neutral. No gradients.

## QA

Render with Poppler and inspect every page. Confirm exactly four square pages, no overflow or line collisions, distinct AI/fixed-policy display, no AI-to-vendor connection, working CTA, and no demo language. Only use verified facts when replacing personalization placeholders. Keep template placeholders visible until a specific prospect is selected.

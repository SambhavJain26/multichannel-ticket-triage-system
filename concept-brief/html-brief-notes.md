# HTML/CSS production brief

## Editable source and output

- `square-brief.html`: all four pages and prospect placeholders.
- `square-brief.css`: shared tokens, layouts and print styles.
- `square-brief-icons.js`: local licensed Lucide geometry from the portfolio; no network dependency.
- `scripts/render-square-brief.cjs`: Edge/Chromium export and DOM layout checks.
- Output: `../output/pdf/maintenance-triage-html-brief.pdf`.

Open the HTML directly in a browser. It displays the same fixed square pages used for print; this is not a responsive website. The small-screen view deliberately permits horizontal scrolling rather than scaling the text down. No React build, server or personalization generator is required.

Run from the repository root:

```powershell
node concept-brief/scripts/render-square-brief.cjs
& 'C:/Users/jains/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' concept-brief/scripts/validate-html-brief.py
pdftoppm -scale-to 1100 -png output/pdf/maintenance-triage-html-brief.pdf tmp/pdfs/html-square/final
```

The exporter first tries local Playwright, then the bundled Codex runtime. `BRIEF_PLAYWRIGHT_PATH` and `BRIEF_BROWSER` can override the package path and Chromium channel. It waits for local fonts before printing. It checks four 864px pages, footer clearance, page bounds and content containment in key cards; human visual inspection remains required. PDF geometry is 648pt square because browser CSS uses 96px per inch and PDF uses 72pt.

## Preservation

The earlier ReportLab PDF remains at `output/pdf/maintenance-triage-square-brief.pdf`, byte-for-byte unchanged. Its builder remains unchanged too. An exact snapshot of both is also in `output/pdf/archive/square-20260928-html-rebuild/`. The new exporter writes only the differently named HTML brief. Portrait and sent-prospect PDFs are not touched.

## Design reference and decisions

Reviewed the live `https://sambhavbuilds.com` website, its `src/index.css`, `Methodology.tsx` and `OutcomeBand.tsx`, and the portrait `maintenance-triage-prospect-brief.pdf` reference.

Applied `design-taste-frontend` and `high-end-visual-design` selectively to a static document: Geist/Manrope typography, warm paper, dark research/authority panels, inset rounded framing, thin licensed icons, consistent spacing, a connected process spine and a pill meeting link with a nested arrow. The user's no-gradient, compact-title and informative-document requirements override website-only motion, hero, imagery and oversized-spacing prescriptions. This is a print-first native CSS design, not a claim to use a UI framework.

- Page 1: inset research panel, two matched vertical lanes, neutral retained tools, terracotta reduced manual preparation, green added automation. Business value follows the comparison.
- Page 2: one continuous eight-stage process, with a separate fixed-rule treatment and a distinct human-approval panel. Actor labels and the right rail distinguish AI, workflow and staff. Exceptions are explained next to the flow.
- Page 3: central hosting/n8n/PostgreSQL boundary; short shared connector branches, local payloads and editable methods. AI stays external and has no direct action path. PMS ownership and access caveats remain explicit.
- Page 4: daily work and human authority form a single top group. Controls, outcomes and a separately padded CTA follow. Contact details and icons have real container padding.

## Content authority and coverage

Authority: `docs/production-maintenance-triage-blueprint.md`. Cross-check: `docs/how-the-system-works.md` and the existing production capability checklist. Demo-specific limitations, schedules and fixed channels are not imported. The PDF describes a proposed production build, not a deployed client integration or verified client result.

| Capability family | Page |
| --- | --- |
| Existing channels, verified context, duplicate/reply linking and incident grouping | 1, 2, 3 |
| Original reports/files, acknowledgment, language/access/pets interpretation | 2 |
| Fixed escalate-only safety rules; alerts bypass clarification | 2 |
| Focused approved follow-ups, retained facts, reassessment, vague-opening handling | 1, 2 |
| PMS/vendor drafts and trade/coverage/hours/compliance checks | 1, 2 |
| Manager choices, owner approval, human commitments and closure | 2, 4 |
| Once-only approved execution, successful-send boundary and factual status | 2, 4 |
| Vendor replies/quotes, agreed appointments, delays, progress and completion | 2 |
| n8n, OpenAI API, PostgreSQL, approved hosting, connectors, queue/retry state | 3 |
| PMS business record; manager/vendor/owner/reporting routes and limited-write fallback | 3 |
| Daily priority view, quiet hours, unanswered emergency checks, overdue/delay reporting | 4 |
| Human-owned uncertainty/sensitive/identity/language/no-vendor/failed cases | 2, 4 |
| AI fallback, retries, stale approvals, reconciliation and visible failures | 4 |
| Role access, MFA, encryption, managed credentials, retention | 4 |
| Intake/full-path monitoring, tested backup restore, controlled changes and rollback | 4 |
| Business value without promised savings or invented deployment evidence | 1, 4 |

Detailed engineering controls stay in the blueprint. Bracketed values require verified research and account-permission confirmation. No capability claim is evidence of a client deployment.

## Verification

Rendered all four PDF pages with Poppler and visually inspected them at 1100px; also reviewed browser renders at native 864px. Corrected the initial page-1/page-4 overflow, page-2 footer collision, and page-3 endpoint alignment before delivery. The final gate checks page geometry, embedded fonts, booking/email links, text bounds, key capability terms, and exact preservation of the earlier PDF/builder. Tagged Chromium output is provided; this is not a claim of PDF/UA certification.

Chromium embeds these variable fonts as Type 3 glyph programs (`CharProcs`) with Unicode maps, rather than a `FontFile2` stream. Validation checks both supported embedding forms. Common ligatures are disabled on all elements because the font shorthand can reset inherited ligature settings, and some variable-font ligatures otherwise extract as private-use characters. PDFMiner emits a font-bounding-box warning for Chromium's Type 3 descriptors; rendered inspection and DOM containment checks supplement its text-bound checks.

## Phone-readability pass (2026-09-28)

The previous square PDF was the copy and type-scale reference, while the newer HTML/CSS composition was retained. It uses 22pt page titles, approximately 13pt process headings, 11pt primary copy, 10pt diagram copy and 8pt metadata. All four pages were edited to be shorter than the older PDF, without removing the approved follow-up, fixed-rule, human-approval, confirmed-send or connection-route boundaries. Page 3 keeps the tool map and moves connection methods to a compact list below it so the diagram labels can stay readable.

The incoming HTML/CSS/PDF are preserved under `output/pdf/archive/html-brief-20260928-before-phone-pass/`. The older `maintenance-triage-square-brief.pdf` remains unchanged. Re-exported four 648pt-square pages; inspected every Poppler render at 750px phone-style width and passed the HTML PDF validator, including footer/card containment, embedded fonts, link, text bounds and preservation checks. A PDF at 750px still benefits from landscape phone viewing or pinch zoom for the denser connection diagram; this pass does not claim mobile-native reflow.

# Reference-based design audit - 2026-09-28

Scope: four-page square production template. Reference: all three rendered pages of `output/pdf/maintenance-triage-prospect-brief.pdf`. Incoming PDF and exact builder preserved in `output/pdf/archive/square-20260928-reference-audit/`.

## Applied guidance

The redesign-existing-projects skill's scan/diagnose/fix sequence guided this pass. The previously read design-taste-frontend, high-end-visual-design and ui-ux-foundations skills inform hierarchy, optical alignment, bounded reading widths, selective nested frames and consistent spacing. The PDF skill requires rendered inspection, not just text extraction. Website motion, gradients, framework changes and decorative images are inappropriate here. The user's semantic green/terracotta palette and approved portfolio icons take precedence over generic skill defaults.

## Findings and changes

| Page | Specific finding | Reference principle | Applied change |
| --- | --- | --- | --- |
| 1 | Cards and legend appeared as unrelated objects; no shared comparison boundary. | Group two lanes without losing individual steps. | One rounded comparison surface; aligned rows; neutral existing systems; inset legend; business value outside the comparison. |
| 2 | Main panel started close to its first step; exception prose was dense; panel bottoms differed. | Continuous numbered rail, emphasized approval checkpoint, distinct exception rail. | Adjusted first-step position and copy; 11pt clarification/owner branch copy; matched panel bottoms; separate fixed rules and all eight stages retained. |
| 3 | Spokes squeezed labels into 45-53pt corridors and required a detached method key. | Separate the proposed service from existing systems with labeled communication. | Seven connection rows with a 154pt routing corridor; endpoint responsibilities and methods; separate payload/direction arrows. All connections pass through n8n. OpenAI stays outside hosting, without a vendor action path. PostgreSQL state remains distinct from PMS business records. |
| 4 | Recovery prose lacked scan points and competed with outcomes. | Short grouped sections and a reserved closing panel. | Two recovery subheadings, concise control copy, clearer outcome mechanisms. Preserved the 92pt CTA frame and 38pt clickable button. |

## Verification

- Reviewed all three reference renders at 900px and revised pages at desktop and native page size.
- Corrected comparison-legend padding and workflow/exception panel bottom alignment after first render.
- Connection methods and arrow labels: 10pt. Workflow and daily-operation main copy: 11pt. Supporting controls: 10pt.
- Automated checks cover four 648pt square pages, embedded used fonts, meeting URL, text margins, capability terms and archive.
- Production authority unchanged: eight stages, safety bypass, clarification/owner loops, human exceptions, named proposed stack, route placeholders, daily oversight, recovery and authority remain represented. No access claim, savings promise or demo restriction added.
- Portrait reference, sent prospect PDFs and unrelated working-tree edits are outside scope.

Remaining trade-off: page 2 is denser than the reference because it contains eight lifecycle stages, not five. Readable copy and continuous flow take precedence over decorative cards or dropping behaviour.

## 2026-09-28 central-map revision

The row map made the exchanges readable but gave its many parallel arrows more visual weight than the actual system. Compared a radial spoke map, the row map, and a grouped three-zone architecture against the page's main question: what already exists, what is added, and what talks to what. The grouped version keeps the central service legible while reducing long connector lines.

- Left: existing resident channels and the proposed external OpenAI API, explicitly distinguished.
- Centre: a client AWS or approved-cloud placeholder enclosing n8n, fixed rules, conversation/delivery handling, and PostgreSQL. The PMS remains the business record.
- Right: existing PMS, manager, vendor, owner, and reporting tools. A short shared junction connects each tool to the central workflow; each card states the payload and proposed route.
- Bottom: editable intake, PMS, vendor, and manager connection fields plus permissions, hosting, AI-data, and delivery-result checks.

This replaces the page-3 finding and row-map solution in the historical table above. The previous PDF and exact builder are archived under `output/pdf/archive/square-20260928-central-map/`. The new page was inspected at 1200px and native 648px after correcting a wrapped centre heading and crowded route notes. The long parallel-arrow pattern is no longer used.

## 2026-09-28 role and copy pass

Page 2 previously described the work but left automatic preparation and human authority implicit in several steps. It now labels the responsible actor at every stage and uses a concise role key. AI makes recommendations and drafts; fixed rules can only raise urgency; the workflow links, asks, checks, sends after approval, and tracks delivery; the manager decides; staff verify and close. The side rail no longer repeats each exception branch in long prose.

Page 3 had inconsistent external card padding and divider use. All external cards now share one icon, heading, body, corner, and border treatment. Proposed connection methods moved to one compact key. Both grouped connection paths meet the n8n header, preventing a visual suggestion that AI reaches PostgreSQL or business tools directly. Card copy states direction without rows of arrows. The n8n header and resident title were shortened after rendered checks showed collisions.

Every page received a text pass using syntax-polish guidance: shorter concrete sentences, retained conditional language for prospective integrations, and no added client evidence or promised savings. The controls, lifecycle, and full capability families remain represented. Incoming PDF and builder are archived under `output/pdf/archive/square-20260928-role-clarity/`.

## 2026-09-28 padding correction

Three screenshot-reported defects were measured and corrected:

- Page 1: the left comparison icons started 1pt inside their cards, while the right icons had 9pt. Both sides now use 9pt inset; their text starts 8pt after the icon and ends 10pt before the card edge.
- Page 3: external-card body text started 3pt before a 26pt icon tile ended. The cards now use a 22pt icon tile and put left-card body text 7pt below it; right-card body text starts 4pt below it. Card text remains within its bottom padding.
- Page 4: contact details sat about 5pt above the dark panel's inner edge and 11pt from its left edge. The line was moved up and right to roughly 10pt bottom and 19pt left padding. The CTA button was inset to balance the right side and its clickable area was moved with it.

The incoming PDF and exact builder are preserved under `output/pdf/archive/square-20260928-padding-fix/`. All four pages were regenerated; pages 1, 3, and 4 were inspected at 1200px after the changes, and the structural PDF validator passed.

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

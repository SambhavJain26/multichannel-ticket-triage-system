# Build retrospective: maintenance request triage

Revised: 2026-10-20. Status: rendered draft for review; not published or queued.

Review PDF: `carousel-kit/out/technical-retrospective-maintenance-triage.pdf`.
Editable HTML: `carousel-kit/technical-retrospective-maintenance-triage.html`.
Build: `node carousel-kit/scripts/build-technical-retrospective.cjs`.
Verify: `python carousel-kit/scripts/verify-technical-retrospective.py`.

## Editorial direction

- Problem-first retrospective for property-management decision makers and buyers, with enough concrete decisions and debugging to show hiring readers how I work.
- No prominent stack list, code, schema, node counts, or internal database status labels. Explain decisions through their operational consequences. Keep the two real defects and specific checks; avoid vague AI claims.
- Eleven short slides: problem, workflow, responsibilities, safety boundary, two bugs, fallbacks, lesson, verification, and next steps. Use varied plain-language diagrams and comparisons.
- Preserve cream ruled paper, Switzer, restrained Zodiak, and meaning-led blue and yellow annotations. Either color works for every annotation shape.
- Public wording omits demo, synthetic data, and no-client or no-deployment labels. Internal evidence remains below. No invented business results, classifier benchmarks, or completed future safeguards.

## LinkedIn caption

> A resident reporting a squeaky door might mark it as an emergency. A resident with an understated gas leak might apologize for the inconvenience.
>
> Maintenance requests arrive at all hours, messy, incomplete, and unpredictably phrased. If property teams rely entirely on manual triage, dangerous repairs get delayed in crowded inboxes. But if automation dispatches contractors on a hunch, managers face expensive callouts for minor issues.
>
> I built a maintenance triage workflow designed around that reality: clarify missing details with the resident, separate genuine hazards from routine requests, and bring ready-to-send dispatches to a property manager for approval.
>
> The system has a clear boundary. AI handles the heavy reading, extracts symptoms, identifies trades, and drafts dispatch emails. The manager stays in full control: they verify the issue and authorize every contractor callout. Furthermore, deterministic safety rules can only escalate. If an email describes gas odor, sparking wires, or flooding, the workflow immediately flags it as an emergency. Software is never permitted to down-rank a hazard.
>
> Two real failures taught me more than the happy path.
>
> The first was an email loop. When a manager approved a repair, the system sent a dispatch email to the contractor. Because that outgoing message landed in the shared mailbox, the intake trigger read it as a brand-new maintenance request and opened a second ticket. Adding explicit system tags to outbound email subjects stopped the intake trigger from reading its own output.
>
> The second was handling follow-ups. When a tenant messaged asking when their repair would be completed, the system treated the question as another maintenance issue, opening another ticket and generating a duplicate manager alert. I added an upfront intent check that recognizes status queries, pulls open tickets for that resident, and returns a factual progress summary without creating a new repair or paging staff.
>
> Those two fixes reinforced a key lesson: building reliable automation is less about extracting keywords and more about accounting for what happens when messages overlap, buttons get tapped twice, or tenants ask a follow-up question.
>
> I checked those behaviors alongside understated safety hazards, routine complaints marked urgent, and sensitive requests. Next, I would add guided photo uploads for ambiguous leaks and integrate two-way contractor schedule updates directly into property records.
>
> The goal is simple: ensure genuine emergencies get immediate attention while keeping managers firmly in control of who gets dispatched.

## Carousel copy

### Slide 1

**Title:** Maintenance triage that puts safety first

**Body:** What I built to triage maintenance requests safely, the two failure loops that broke, and what I learned.

**Footer:** Build retrospective · Maintenance request triage

### Slide 2

**Title:** Real emergencies don't label themselves

**Body:** Tenants describe problems in different ways. A squeaky door gets marked urgent, while a gas leak arrives in an apology.

**Footer:** The problem · Urgency is rarely what the subject line says

### Slide 3

**Title:** From messy intake to reviewed dispatch

**Body:** I built a workflow that gathers missing details, separates genuine hazards from routine repairs, and presents ready-to-approve dispatches to a manager.

**Footer:** The workflow · Structured intake, human dispatch

### Slide 4

**Title:** AI advises. The manager authorizes.

**Body:** AI handles the heavy reading, symptom extraction, and draft wording. The property manager verifies the repair and authorizes every contractor dispatch.

**Footer:** The boundary · No contractor dispatch without human approval

### Slide 5

**Title:** Safety rules can escalate, never down-rank

**Body:** If a message mentions a gas smell or flooding, deterministic rules force an immediate emergency alert. The automation cannot downgrade a safety risk.

**Footer:** Architectural decision · Escalation only, never down-grading

### Slide 6

**Title:** The system emailed itself

**Body:** Outbound contractor emails landed in the same inbox and triggered new maintenance tickets. Adding system tags to outgoing email subjects stopped the loop permanently.

**Footer:** Bug 1 · Stop outbound dispatches re-entering intake

### Slide 7

**Title:** A status question became a new repair

**Body:** When a tenant asked when their repair would finish, the system opened another ticket. An upfront status check now returns existing progress instead.

**Footer:** Bug 2 · Separate status inquiries from new requests

### Slide 8

**Title:** Uncertainty needs a person

**Body:** Disability accommodations, legal questions, and vague complaints bypass automated drafting. If the model fails or times out, the request is flagged for staff.

**Footer:** The fallback · Sensitive requests bypass automated drafting

### Slide 9

**Title:** Edge cases are the real build

**Body:** The hardest part of maintenance triage is not extracting symptoms. It is protecting the workflow against feedback loops, duplicate button clicks, and ambiguous wording.

**Footer:** What I learned · Design for the failure modes

### Slide 10

**Title:** I checked the awkward cases

**Body:** I checked understated safety hazards, routine issues marked urgent, duplicate approvals, and follow-up status queries to ensure predictable behavior.

**Footer:** Verification · Specific checks of workflow behavior

### Slide 11

**Title:** What I'd improve next

**Body:** Next, I would add guided photo uploads for ambiguous leaks and two-way contractor arrival tracking, reducing unnecessary callouts even further.

**Footer:** Next steps · Proposed improvements

## Internal evidence mapping

| Slides | Evidence | Boundary |
|---|---|---|
| 1-3 | Stage 4 core triage sub-workflow (`workflows/maintenance-triage-core.json`), intake routers, and project problem definition | Built to surface and prioritize maintenance issues; no operational cost reduction claimed |
| 4 | Stage 6 manager approval (`workflows/maintenance-triage-manager-desk.json`), vendor candidate keyboards, and explicit operator authorization | Every vendor contact individually authorized by property manager; AI suggests and drafts only |
| 5 | Stage 4 deterministic safety overrides in SQL and code nodes (`db/postgres/003-stage-4-support.sql`) | Hard post-model escalation rules for gas, floods, and electrical hazards; cannot downgrade |
| 6 | August 13 progress notes: vendor emails re-entering IMAP as `MR-0014`/`MR-0015` and triggering repeated manager approvals | Fixed by enforcing `[MT-SYSTEM]` prefix on all outbound mail and ignoring that prefix in IMAP triggers |
| 7 | August 13 progress notes: "When will all these issues be resolved?" parsed as `MR-0013`; execution 1315 fix | Fixed by adding upfront resolution/status intent detection that queries open tickets and skips triage |
| 8 | Stage 4 human-only routing for disability accommodations and legal issues; continue-on-fail error routes | Sensitive categories suppress automated drafts; timeouts and parsing failures route to manual staff review |
| 9 | August 13 & 16 progress notes: preliminary vague bathroom buffering, sequence collision guards, and idempotency | System reliability requires defense against repeat clicks, stale buttons, and ambiguous phrasing |
| 10 | Rehearsal logs in `tmp/stage-3/`, Stage 8 five-run rehearsal (`scripts/run-stage-8-rehearsal.ps1`), and Stage 9 execution 1315 | Verified synthetic test runs: gas escalation, squeaky door routine, duplicate approval ignored, status query handled |
| 11 | Proposed production blueprint (`docs/production-maintenance-triage-blueprint.md`) and future improvements | Structured tenant photo capture, two-way contractor ETA updates, and PMS/accounting integration are proposed |

Keep this appendix, evidence provenance, and local paths outside the PDF.

# Product Marketing Context

**Document version:** v1
**Last updated:** 2026-08-04

## Product Overview
**One-liner:** A demo-depth advisory AI triage layer for inbound residential property-management maintenance requests — classifies urgency and trade, drafts replies for human approval, and alerts the manager on emergencies.

**What it does:** Reads inbound maintenance messages from a monitored mailbox, a web form, and batch-imported prospect samples. Classifies urgency (EMERGENCY / URGENT / ROUTINE) and trade, then applies deterministic, escalate-only safety-keyword rules on top of the model so a life-safety case is never left to the model alone. Drafts a tenant reply and a vendor note. Posts everything to a priority-ordered board. Alerts the manager by Telegram on emergencies with an approve/hold/not-emergency button gate. Sends the approved reply by email only after a human taps approve. Never writes to the client's PMS, never dispatches a vendor, never auto-replies.

**Product category:** Custom AI automation for residential property-management maintenance triage — not a category of software the client shops for by name; it's built into their existing inbox and workflow.

**Product type:** Custom-built automation delivered and run inside the client's own infrastructure (self-hosted n8n + Postgres, eventually on a client-owned VPS). Not a multi-tenant SaaS product — there is nothing to log into, no seats, no subscription in the software sense, and no second customer sharing the same instance. See Brand Voice for the language rules that protect this distinction.

**Business model:** One-time setup fee plus a flat monthly fee. $800–1,500 setup / $250–450 per month (source: `02-maintenance-triage.md`). First two clients discounted to $500 setup / $200 per month.

## Target Audience
**Target companies:** US residential property management companies, ideally 200–600 doors (150 doors is the hard floor below which volume doesn't justify it). Works regardless of which PMS they run, since the product doesn't integrate with any of them. Staff of 3–15, with 1–2 people handling maintenance intake.

**Decision-makers:** Owner/principal signs. Ops manager is the day-to-day champion and user.

**Primary use case:** Sorting the flood of unstructured inbound maintenance messages (email, text, portal, voicemail-shaped text) so a true emergency is never missed and a trivial issue is never dispatched at emergency rates.

**Jobs to be done:**
- Read and classify every inbound maintenance message correctly (urgency + trade) without a human doing that dozens of times a day across four other things.
- Surface true emergencies immediately, even outside business hours, without crying wolf on trivial issues.
- Draft a tenant acknowledgment and a vendor note so the manager isn't starting from a blank page on every ticket.

**Use cases:**
- An after-hours emergency (gas smell, burst pipe) is triaged and alerted the moment it lands, not discovered Monday morning.
- A rambling, multi-complaint message where the real issue (a dripping ceiling) is buried in sentence nine gets condensed to a plain, correctly-prioritized summary.
- A tenant marks a trivial issue (a squeaky door) "URGENT!!!" and it correctly stays at the bottom of the board.
- A Spanish-language message gets a tenant reply drafted in Spanish and a vendor note in English.
- A fair-housing / disability-accommodation request is routed to a human with no auto-draft generated at all.

## Personas
| Persona | Cares about | Challenge | Value we promise |
|---------|-------------|-----------|------------------|
| Owner / principal (signs) | Retention, cost, liability | Non-renewal driven by slow response (~$4,000 turnover cost per unit); emergency call-out rates paid on non-emergencies | "Slow maintenance response is the number one reason tenants don't renew, and each turnover runs you about $4,000. This makes sure nothing sits, and stops you paying emergency rates for a running toilet." |
| Ops manager (champion, daily user) | Not carrying the inbox in their head at night | Checking their phone at 10pm "just in case"; missing something in an unstructured inbox while doing four other jobs | "This reads everything as it lands, sorts it, and only wakes you for the ones that genuinely can't wait." |

## Problems & Pain Points
**Core problem:** Maintenance requests arrive unstructured — email, text, portal, voicemail-shaped text — with no urgency field, and the tenant's own sense of how serious their problem is unreliable in both directions. A human currently reads and classifies every one, dozens of times a day. Triage is invisible work: it appears on no report, nobody is thanked for correctly calling something routine, and it's the first thing to degrade under pressure — exactly when volume is highest and when after-hours coverage (76% of the week) is thinnest.

**Why alternatives fall short:**
- PMS maintenance modules (e.g. Buildium) are ticketing only: storing, assigning, and tracking a request a human already read and categorized. None of them reads an unstructured 11pm email and decides it's an emergency.
- Answering services ($300–800/month) can't assess urgency, so protocol says dispatch — producing a $340 weekend emergency call-out for a $60 flapper valve.
- Category leaders that do offer AI triage (Property Meld, Latchel, Vendoroo) require moving the whole maintenance workflow into their platform, charge per door, and are moving toward removing the human from dispatch entirely.

**What it costs them:** Under-response — a $150 repair becomes a $12,000 water-damage claim, plus possible habitability legal exposure and a lost renewal (~$4,000 per turnover). Over-response — emergency call-out rates (1.5–2x standard) on trivial issues, the owner questioning the manager's judgment, vendor goodwill burned on non-urgent calls.

**Emotional tension:** The ops manager checking their phone before bed "just in case." 38% of owners name maintenance their top source of stress. The fear of the one message that got missed and became a legal or financial incident.

## Competitive Landscape
**Direct:** Property Meld (~$1.60–2.00/door/month, the SMB/mid-market AI-triage default), Latchel (~$25/unit/month outsourced coordination, often resident-paid), Vendoroo (~$3/door, agentic dispatch) — all require migrating the maintenance workflow into their platform, price per door, and are moving toward removing the human from the loop.

**Secondary:** Answering services — take a message but can't assess urgency, so protocol forces dispatch on nearly everything.

**Indirect:** Doing nothing, or the ops manager's own memory and phone at 11pm — the real, most common competitor at this segment. Most 150–600 door shops have bought none of the category leaders above.

**How each falls short:** Category leaders demand a platform migration and per-door pricing while trending toward full auto-dispatch. Answering services and doing-nothing provide zero triage intelligence at all.

## Differentiation
**Key differentiators:**
- Zero PMS or platform migration — forwarding turns on and off, back to today in five minutes.
- Advisory-only by structural design, not policy: no code path exists from an inbound message to a tenant without a human tap.
- Flat fee, not per-door.
- Tuned to the client's own vocabulary, unit naming, and escalation list on a phone call, not filed as a feature request.

**How we do it differently:** The model reads and classifies; a separate deterministic, escalate-only safety-rules layer decides whether to override it upward. The model never gets the final say on a life-safety case, and nothing drafted ever sends without a human approving it first.

**Why that's better:** The category is racing toward auto-dispatch. For the owner who specifically doesn't want AI talking to their tenants, this is structurally the only option going the other direction.

**Why customers choose us:** No migration, no PMS upgrade required, they keep the tenant relationship (nothing here ever talks to a tenant unsupervised), flat pricing regardless of door count, and configuration changes happen on a phone call.

## Objections
| Objection | Response |
|-----------|----------|
| "What if it misses an emergency?" | It can't hide one — nothing gets filtered out. Everything still reaches the manager exactly as it does today. It only ever adds information, never removes it. |
| "[Our PMS] already handles maintenance." | It handles the work order once a human has decided what it is. This is the step before that: reading the message and working out whether it's an emergency. Most PMS vendors even publish guidance recommending automated routing for gas smells and water leaks — they just don't ship it. |
| "We're not comfortable with AI talking to tenants." | Nothing sends without a human clicking approve. It drafts; a person decides. |
| "How is this different from an answering service?" | An answering service takes a message and passes it on — it can't assess it, so protocol says dispatch, which is why trivial issues get billed at emergency rates. This reads and classifies, for a fraction of the cost. |

**Anti-persona:** Under 150 doors. Already has a dedicated 24/7 maintenance coordinator. Tenants submit exclusively through a working structured portal with a mandatory urgency field. Wants full auto-dispatch with no human in the loop — decline this engagement; it's a different product with different liability and needs a provider with insurance and a track record.

## Switching Dynamics
**Push:** The after-hours coverage gap (76% of the week uncovered by default), a recent water-damage claim, a bad review mentioning slow maintenance, an ops manager visibly at capacity, a growing portfolio outgrowing informal handling.

**Pull:** Watching a real message get triaged and alerted live in a demo. The zero-migration promise. Flat pricing. The advisory-only safety story landing as reassurance rather than a limitation.

**Habit:** An existing answering-service contract. "Our coordinator handles it, she's great" (until she's out). A structured portal already in place that tenants bypass anyway.

**Anxiety:** AI talking to tenants without oversight. Whether it will miss a real emergency. Whether something legally consequential (habitability) can be trusted to an automated read. Where tenant message data lives and who can see it.

## Customer Language
**How they describe the problem (verbatim, from documented discovery language — not yet from real client interviews):**
- "I check my phone before bed just in case."
- "It goes in the portal and we deal with it Monday."
- "We had a flood last year that we found out about late."
- "Our coordinator handles it, she's great." (until she's asked what happens when the coordinator is on holiday)

**How they describe us:** Not yet documented — no real client or prospect has used this yet. Fill this in after the first live demo calls; do not invent quotes here.

**Words to use:** "sorts and drafts, you decide," advisory, response target (never "deadline"), triage nurse for your inbox.

**Words to avoid:** "handles your maintenance requests automatically," "it will never miss an emergency," "replaces your answering service" (say instead: does the part an answering service can't), "maintenance management system," my platform / my tool / my product / the app, users, sign up, subscribers.

**Glossary:**
| Term | Meaning |
|------|---------|
| EMERGENCY / URGENT / ROUTINE | The three model-assigned priority levels; response targets configured per client, not legal deadlines |
| NEEDS_REVIEW | A system-only state — the model cannot output it. Forced by a bad/failed model call, low confidence with a safety signal, or a low-information message |
| Human-only | An accommodation or legal-sensitive request; drafting is skipped entirely and a human must decide |
| Override / safety signal | A deterministic keyword rule raising priority above what the model returned; can only escalate, never downgrade |
| Response target | An operational target set in config, explicitly not a legal deadline |
| Advisory-only | The system classifies, drafts, and notifies; it never dispatches, suppresses, auto-closes, or auto-replies |

## Brand Voice
**Tone:** Understated, incident-report register, first person, plain declaratives, no hype vocabulary.

**Style:** Direct. Names the responsible workflow or mechanism rather than saying "the system." Short sentences. Real numbers over adjectives. At most one em dash per document, zero preferred.

**Personality:** Careful, honest about limitations, safety-first, non-salesy.

## Proof Points
**Metrics:** Six-fixture live-demo gate (`docs/stage-3-scorecard.md`, `docs/stage-8-operator-cheat-sheet.md`): 6/6 priority match, 0 under-escalations, 0 over-escalations, 0 missed safety signals, ~10.9s average classification-plus-draft latency, ~$0.003 total OpenAI cost across the 6-fixture run. Estimated production infrastructure cost ~$8/month at 300 doors / ~250 requests a month. **Do not cite a percentage across the full 30-fixture set — that harness run failed and is deferred per `progress-notes.md`.**

**Customers:** None yet — pre-first-client demo build.

**Testimonials:** None yet.

**Value themes:**
| Theme | Proof |
|-------|-------|
| Nothing sits unseen overnight | EMERGENCY always alerts regardless of quiet hours (Alert Dispatch policy) |
| Emergencies surface immediately, even after hours | The safety-rules layer runs independent of quiet-hours suppression |
| Stops paying emergency rates for non-emergencies | Deterministic downgrades for a squeaky door or a contained, bucketed ceiling drip |
| Nothing sent without a human tap | The approval double-guard and human-only refusal are enforced in the database `WHERE` clause of the approval query, not by convention |

## Goals
**Business goal:** Land the first paying client from this build.

**Conversion action:** Get the prospect to forward roughly 20 anonymized real maintenance emails for a free "here's your own week, sorted" follow-up report, leading to a paid single-inbox pilot.

**Current metrics:** Pre-launch. Six-fixture demo gate passed; no live client data yet.

## Changelog
*Newest first. One line per revision: what changed and why.*
- v1 (2026-08-04) — Initial context, auto-drafted from `02-maintenance-triage.md`, `foundation-2-maintenance-operations.md`, `AGENTS.md`, and `maintenance-triage-demo-build-plan.md`. No real client language yet — Customer Language and Proof Points sections flag gaps that need real prospect calls, not invention.

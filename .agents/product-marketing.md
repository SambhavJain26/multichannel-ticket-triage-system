# Product Marketing Context

**Document version:** v2
**Last updated:** 2026-08-13

## Product Overview
**One-liner:** A demo-depth advisory AI triage layer for inbound residential property-management maintenance requests — it classifies urgency and trade, collects the missing details from the resident, proposes matching vendors, and makes the manager the approval point for any vendor contact.

**What it does:** Accepts maintenance requests from three channels — a monitored Gmail mailbox, a web form, and a tenant Telegram bot. Classifies urgency (EMERGENCY / URGENT / ROUTINE) and trade, then applies deterministic, escalate-only safety rules on top of the model so a life-safety case is never left to the model alone. Where the request is too vague to act on, it keeps asking the resident focused follow-up questions until the required details exist, rather than handing a half-formed request to a person. It writes durable state to Postgres, mirrors a manager-facing workspace into Airtable, matches up to three active vendors on property and trade, and sends the manager a Telegram message containing the request summary and a drafted vendor email. Selecting a vendor sends that one email. Hold sends nothing. After a successful send, the resident is told a provider has been contacted.

**What it never does:** Write to the client's PMS. Select or dispatch a vendor on its own. Send a vendor email without an explicit manager tap. Invent an arrival time or an ETA. Close a request. Decide that a request does not matter.

**What it may do without asking:** Message the resident within a bounded set — acknowledge receipt, ask deterministic clarification questions for reported missing fields, answer a status question truthfully across their open requests, and confirm that a provider has been contacted once a manager-approved send has succeeded. This is a real change from v1: the system does talk to the resident on its own, but only inside that fixed set, and never with anything requiring management judgment.

**Product category:** Custom AI automation for residential property-management maintenance triage — not a category the client shops for by name; it is built into the mailbox and workflow they already have.

**Product type:** Custom-built automation delivered and run inside the client's own infrastructure (self-hosted n8n + Postgres + Airtable, eventually on a client-owned VPS). Not a multi-tenant SaaS product — nothing to log into, no seats, no subscription in the software sense, no second customer sharing the instance. See Brand Voice for the language rules protecting this distinction.

**Business model:** One-time setup fee plus a flat monthly fee. $800–1,500 setup / $250–450 per month (source: `02-maintenance-triage.md`). First two clients discounted to $500 setup / $200 per month. Flat, not per-door — this is a live differentiator, since every named competitor prices per unit.

**Current state:** Stage 9, published for a local demo. Pre-first-client. No PMS integration, no verified resident identity, no vendor appointment integration, no production hosting. The tenant Telegram bot currently serves one configured demo resident, analogous to a dedicated SMS number.

## Target Audience
**Target companies:** US residential property management companies, ideally 200–600 doors (150 is the hard floor below which request volume does not justify it). Works regardless of PMS, since it does not integrate with any of them. Staff of 3–15, with 1–2 people handling maintenance intake.

**Decision-makers:** Owner/principal signs. Ops manager or maintenance coordinator is the day-to-day champion and user.

**Primary use case:** Sorting unstructured inbound maintenance messages (email, text, portal-forwarded, voicemail-shaped) so a true emergency is never missed and a trivial issue is never dispatched at emergency rates.

**Jobs to be done:**
- Read and classify every inbound message correctly (urgency + trade) without a human doing it dozens of times a day across four other jobs.
- Surface true emergencies immediately, including outside business hours, without crying wolf on trivia.
- Get a vague request to the point of being actionable before it reaches the manager's desk.
- Put a drafted vendor email and a matched vendor in front of the manager so they are approving, not composing.

**Use cases:**
- An after-hours emergency (gas smell, burst pipe) is triaged and alerted the moment it lands, not discovered Monday.
- A rambling multi-complaint message with the real issue buried in sentence nine is condensed to a plain, correctly prioritized summary.
- A resident marks a trivial issue "URGENT!!!" and it correctly stays routine.
- A vague report ("the door is broken") gets follow-up questions until it can be classified, instead of escalating half-formed.
- A resident asks "when will all this be fixed?" and receives one truthful consolidated status across their open requests, with no new request created and no invented ETA.
- A Spanish-language message is classified correctly with the resident reply drafted in Spanish.
- A fair-housing / disability-accommodation request is routed to a human with no draft generated at all.

## Personas
| Persona | Cares about | Challenge | Value we promise |
|---------|-------------|-----------|------------------|
| Owner / principal (signs) | Retention, cost, liability | Non-renewal driven by slow response (~$4,000 turnover cost per unit); emergency call-out rates paid on non-emergencies | "Slow maintenance response is the number one reason tenants don't renew, and each turnover runs you about $4,000. This makes sure nothing sits, and stops you paying emergency rates for a running toilet." |
| Ops manager / coordinator (champion, daily user) | Not carrying the inbox in their head at night | Checking their phone at 10pm "just in case"; missing something in an unstructured inbox while doing four other jobs; being handed requests too vague to act on | "This reads everything as it lands, sorts it, chases the details out of the resident, and only wakes you for what genuinely can't wait." |

## Problems & Pain Points
**Core problem:** Maintenance requests arrive unstructured, with no reliable urgency field, and the resident's own sense of severity is unreliable in both directions. A human currently reads and classifies every one. Triage is invisible work: it appears on no report, nobody is thanked for correctly calling something routine, and it degrades first under pressure — exactly when volume is highest and after-hours coverage (76% of the week) is thinnest.

**Why alternatives fall short:**
- PMS maintenance modules (Buildium, AppFolio, Rentvine) are ticketing: storing, assigning and tracking a request a human already read and categorized. The classification step is what is still manual.
- Answering services ($300–800/month) cannot assess urgency, so protocol says dispatch — producing a $340 weekend call-out for a $60 flapper valve.
- The AI-triage category (Property Meld, Latchel, Vendoroo) requires moving the maintenance workflow into their platform, prices per door, and is actively moving toward removing the human from dispatch.

**What it costs them:** Under-response — a $150 repair becomes a $12,000 water-damage claim, plus habitability exposure and a lost renewal (~$4,000 per turnover). Over-response — emergency call-out rates at 1.5–2x standard on trivia, the owner questioning the manager's judgment, vendor goodwill burned.

**Emotional tension:** The ops manager checking their phone before bed "just in case." 38% of owners name maintenance their top source of stress. The fear of the one message that got missed.

## Competitive Landscape
**Direct — the AI triage category, and the direction it is moving:**

| Competitor | Pricing | Position |
|---|---|---|
| Property Meld | ~$1.60/unit/month Core, ~$2.00 Ops | The SMB/mid-market default. Marketed as agentic AI that triages and dispatches on its own |
| Latchel | ~$25/unit/month managed, commonly resident-paid at $15–18/month inside a resident benefits package | AI call center answering every call; advertises "23% solved at intake" and **"48% of emergencies de-escalated"** |
| Vendoroo | From ~$3/door/month | End-to-end AI coordination; trained on 2M+ work orders; carries an explicit **"If the AI makes an error, we will pay for it"** guarantee |

**Two researched facts that define our position (2026-08-13):**

1. **Latchel advertises de-escalating emergencies as a feature.** Our safety-rules layer is structurally escalate-only: it can raise a priority above what the model returned and can never lower it. Two products, opposite directions on the same decision. This is the sharpest available contrast and it is factual, not a smear — de-escalation with a staffed human call center behind it is a legitimate design, just not this one.
2. **Vendoroo's answer to the liability question is an indemnity, not a human.** That is a real answer, and a company with insurance and a track record can make it. It is worth naming honestly rather than pretending autonomy has no answer. Ours is a different answer: the decision never leaves the manager.

**Secondary:** Answering services — take a message, cannot assess urgency, so protocol forces dispatch.

**Indirect:** Doing nothing, or the ops manager's memory and phone at 11pm. This is the real, most common competitor at this segment; most 150–600 door shops have bought none of the above.

## Differentiation
**Key differentiators:**
- Zero PMS or platform migration — forwarding turns on and off, back to today in five minutes.
- Advisory by structure, not policy: no code path exists from an inbound message to a vendor without a manager tap.
- Escalate-only safety rules. The rules layer can raise a priority and can never lower one.
- One-send-only is enforced in the database, not by convention — a unique constraint on the vendor-send claim means a double tap cannot produce a second plumber.
- Flat fee, not per-door.
- Tuned to the client's vocabulary, unit naming and escalation list on a phone call, not filed as a feature request.

**How we do it differently:** The model reads and classifies; a separate deterministic layer decides whether to override it upward. The model never has the final say on a life-safety case, and no vendor is contacted without a person choosing them.

**Why that's better:** The category is racing toward auto-dispatch, and at least one competitor markets automatic emergency de-escalation. For the owner who specifically does not want AI making the call on their residents, this is structurally the option going the other direction.

## Objections
| Objection | Response |
|-----------|----------|
| "What if it misses an emergency?" | Nothing is filtered out. Everything still reaches the manager exactly as it does today. It only ever adds information, never removes it — and the rules layer can only push priority up, never down. |
| "[Our PMS] already handles maintenance." | It handles the work order once a human has decided what it is. This is the step before: reading the message and working out whether it is an emergency. Most PMS vendors publish guidance recommending automated routing for gas smells and water leaks. They just don't ship it. |
| "We're not comfortable with AI talking to residents." | It acknowledges, asks for missing details, and answers status questions with facts. It never gives an ETA, never picks a vendor, and never sends a vendor anything without you tapping a button. |
| "How is this different from an answering service?" | An answering service takes a message and passes it on — it can't assess, so protocol says dispatch, which is why trivia gets billed at emergency rates. This reads and classifies, for a fraction of the cost. |
| "Why not the ones that do the whole thing automatically?" | Those are real products and some carry a guarantee to pay for their own errors. If you want the human out of dispatch, buy one of those. This is built for the operator who wants the opposite. |

**Anti-persona:** Under 150 doors. Already has a dedicated 24/7 maintenance coordinator. Residents submit exclusively through a working structured portal with a mandatory urgency field. Wants full auto-dispatch with no human in the loop — decline; that is a different product with different liability, and the honest move is to name the competitors who do it.

## Switching Dynamics
**Push:** The after-hours coverage gap, a recent water-damage claim, a bad review mentioning slow maintenance, an ops manager at capacity, a portfolio outgrowing informal handling.

**Pull:** Watching a real message get triaged and alerted live. Zero migration. Flat pricing. The advisory story landing as reassurance rather than a limitation.

**Habit:** An existing answering-service contract. "Our coordinator handles it, she's great" (until she's out). A portal residents bypass anyway.

**Anxiety:** AI talking to residents unsupervised. Whether it misses a real emergency. Whether something legally consequential (habitability) can be trusted to an automated read. Where resident message data lives.

## Customer Language
See `docs/build-2-content-strategy/customer-language.md` for the full vocabulary reference, sourcing caveats, and copy rules.

**How they describe the problem (from documented discovery language — not yet from real client interviews):**
- "I check my phone before bed just in case."
- "It goes in the portal and we deal with it Monday."
- "We had a flood last year that we found out about late."
- "Our coordinator handles it, she's great."

**How they describe us:** Not yet documented. No real client or prospect has used this. Fill in after the first live demo calls; do not invent quotes.

**Words to use:** "sorts and drafts, you decide," advisory, response target (never "deadline"), triage, work order, doors, resident, after-hours, on-call.

**Words to avoid:** "handles your maintenance requests automatically," "it will never miss an emergency," "replaces your answering service" (say: does the part an answering service can't), "maintenance management system," my platform / my tool / my product / the app, users, sign up, subscribers, streamline, seamless, end-to-end.

**Glossary:**
| Term | Meaning |
|------|---------|
| EMERGENCY / URGENT / ROUTINE | The three assigned priority levels; response targets are configured per client, not legal deadlines |
| NEEDS_REVIEW | A system-only state the model cannot output. Forced by a failed model call, low confidence with a safety signal, or an unreadable message |
| NEEDS_VENDOR_ASSIGNMENT | No active vendor matches the property and trade. Manager sees Hold only; no vendor email is possible |
| Human-only | An accommodation or legal-sensitive request. Drafting is skipped entirely and a person must decide |
| Override / safety signal | A deterministic keyword rule raising priority above what the model returned. Escalate-only, never downgrade |
| missing_info | The mapped fields still needed to classify a request. While any remain, the resident keeps getting focused questions and the manager is not interrupted |
| Vendor candidate | An active Airtable vendor matching the request's property and trade. Up to three, ordered by priority |
| Response target | An operational target set in config, explicitly not a legal deadline |
| Advisory-only | Classifies, drafts, asks, and notifies. Never dispatches, suppresses, auto-closes, or contacts a vendor without a manager tap |

## Brand Voice
**Tone:** Understated, incident-report register, first person, plain declaratives, no hype vocabulary.

**Style:** Direct. Names the responsible workflow or mechanism rather than "the system." Short sentences with varied length. Real numbers over adjectives. At most one em dash per document, zero preferred.

**Personality:** Careful, honest about limitations, safety-first, non-salesy.

## Proof Points
**Metrics (`docs/stage-3-scorecard.md`, `docs/build-description.md`):**
- Six-fixture live-demo gate: 6/6 priority match, 0 under-escalations, 0 over-escalations, 0 missed safety signals.
- Stage 8/9 rehearsal: 5 clean runs x 6 fixtures = 30/30 expected priorities, with zero real Telegram or SMTP sends in fixture mode.
- ~10.9s average classification-plus-draft latency. ~$0.003 total OpenAI cost across the 6-fixture run.
- One-send-only: unique constraint on the vendor-send claim; a repeated approval tap cannot produce a second send.

**The mandatory honesty constraint:** **Do not cite an accuracy percentage across the full 30-fixture set.** That harness run failed — 15.6% exact match, 6 under-escalations, 4 over-escalations, 10 missed safety signals — and is deferred per `progress-notes.md`. The passing figures above come from six fixtures selected for the demo. Any claim of broad or production-grade accuracy is unsupported. This constraint is not a weakness to hide; post 8 of the content plan is built on it.

**Customers:** None yet — pre-first-client demo build.

**Testimonials:** None yet.

**Value themes:**
| Theme | Proof |
|-------|-------|
| Nothing sits unseen overnight | EMERGENCY alerts regardless of quiet hours |
| Emergencies surface immediately, even after hours | The safety-rules layer runs independent of quiet-hours suppression |
| Stops paying emergency rates for non-emergencies | Deterministic boundaries for a squeaky hinge, a bucketed ceiling drip, a standalone fan |
| The manager is never handed a half-formed request | Clarification continues while any mapped `missing_info` field remains |
| No vendor is contacted without a person choosing them | Manager Telegram selection is the only path to SMTP; Hold sends nothing |
| A double tap cannot send twice | Unique constraint on `vendor_send_attempts`, enforced in the database |
| It never invents an ETA | Status replies state only where the request actually is |

## Goals
**Business goal:** Land the first paying client from this build.

**Conversion action:** Get the prospect to forward roughly 20 anonymized real maintenance messages for a free "here's your own week, sorted" report, leading to a paid single-inbox pilot.

**Current metrics:** Pre-launch. Six-fixture demo gate passed; no live client data.

## Changelog
*Newest first. One line per revision: what changed and why.*
- v2 (2026-08-13) — Rewritten for Stage 9. v1 described the Stage 8 build and was stale in ways that would have poisoned every draft: it referenced the read-only board (replaced by Airtable), email tenant replies (replaced by the tenant Telegram conversation), and "never auto-replies" (the system now does message residents inside a bounded set). Added vendor matching and manager vendor approval, the clarification loop, status handling, one-send-only, `NEEDS_VENDOR_ASSIGNMENT` and `missing_info`. Competitive landscape rebuilt on fresh research, including Latchel's advertised emergency de-escalation and Vendoroo's error indemnity, which together define the positioning contrast. Promoted the 30-fixture failure from a footnote to a named constraint.
- v1 (2026-08-04) — Initial context, auto-drafted from `02-maintenance-triage.md`, `foundation-2-maintenance-operations.md`, `AGENTS.md`, and `maintenance-triage-demo-build-plan.md`. No real client language yet.

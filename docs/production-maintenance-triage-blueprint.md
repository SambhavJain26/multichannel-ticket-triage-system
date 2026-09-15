# Production Maintenance Request Triage Blueprint

# 1 Business impact at scale

## A Monday morning across a large portfolio

At 7:06 on a Monday morning, a regional property management company is responsible for 12,000 homes across 85 properties. Residents reported 146 issues between Friday evening and Monday morning. They arrived through the resident portal, email, text messages, and voicemail transcripts from the after-hours line.

The first maintenance coordinator has not yet opened the shared inbox. Even so, the production system has already processed the weekend workload. It has linked each report to a resident, lease, property, and unit where the source data supports that match. It has separated new issues from replies and duplicate messages. It has grouped six reports about the same burst pipe into one property incident. It has asked 19 residents for a missing access detail or a clearer description. It has identified the requests most likely to involve immediate safety or habitability risk and has alerted the on-call manager according to the company's policy.

The on-call manager was interrupted twice during the weekend. One alert concerned a possible gas odor. The other concerned active water flowing through a ceiling near electrical fixtures. Routine messages, status questions, and incomplete reports did not create phone alerts. They remained visible and continued moving through the appropriate background process.

When the office opens, the maintenance team sees the same work inside the tools it already uses. The property management system contains the work orders that were approved for creation. The resident communication timeline contains the acknowledgments and clarification messages. The manager's normal alert channel shows the two after-hours decisions and who handled them. The work list is ordered by the company's priority rules, with exceptions and breached response targets shown first.

The coordinator does not start by reading 146 messages from top to bottom. The coordinator starts with a prepared operating list:

- 2 emergency incidents already acknowledged by the on-call manager
- 31 urgent requests ready for a human decision or assignment
- 74 routine requests with complete information
- 19 resident conversations still waiting for specific details
- 7 legal, accommodation, identity, or other sensitive cases reserved for human review
- 13 duplicate, follow-up, vendor, or non-request messages attached to the correct records

No item disappeared because the AI was unavailable, a vendor email failed, a resident sent the same message twice, or an integration timed out. Each item has an owner, status, next action, and history.

## How small savings accumulate

The value is created in small increments. One message may take only a few minutes to read, interpret, look up, summarize, route, and acknowledge. At portfolio scale, those minutes become a recurring staffing requirement.

The following illustration uses planning assumptions, not promised results. A 12,000-unit portfolio receiving 3.3 maintenance requests per unit per year would handle about 39,600 requests annually, or 3,300 per month. If the system removes an average of four minutes of reading, rekeying, lookup, and first-response preparation from each request, it returns about 220 staff hours per month. That is roughly 1.3 full-time equivalents at 173 working hours per month. The company may use that capacity to absorb growth, reduce overtime, improve follow-up, or spend more time on vendor performance and resident service. It should not treat the illustration as a headcount guarantee until its own baseline is measured.

| Portfolio size | Illustrative requests per month | Minutes removed per request | Capacity returned per month |
|---|---:|---:|---:|
| 2,000 units | 550 | 4 | 37 hours |
| 5,000 units | 1,375 | 4 | 92 hours |
| 12,000 units | 3,300 | 4 | 220 hours |
| 25,000 units | 6,875 | 4 | 458 hours |

The larger gain comes from consistency. A person working through a crowded inbox has to remember which resident is waiting, which owner approval is outstanding, which vendor has not responded, and which issue is becoming more serious. The production system records those states and checks them on a schedule. The business gets fewer unowned handoffs, faster awareness of dangerous conditions, cleaner resident communication, and a common process across offices and properties.

## Business outcomes the system is designed to improve

The production system should be measured against observable operating outcomes:

- less coordinator time spent reading, summarizing, copying, and chasing basic details
- shorter time from resident report to an informed human decision
- fewer emergencies sitting unseen outside office hours
- fewer routine items sent at after-hours rates because an answering service could not assess them
- fewer repeated calls from residents asking whether anyone received the request
- fewer duplicate work orders and repeated vendor emails
- clearer ownership of approvals, vendor selection, access coordination, and exceptions
- a consistent record of what the system suggested and what a person decided
- better visibility across properties without requiring managers to maintain parallel spreadsheets
- more portfolio capacity without adding staff in direct proportion to request volume

The system does not guarantee repair quality, vendor availability, resident renewal, or legal compliance. It improves the information and handoffs that influence those outcomes.

## What this blueprint covers

This document explains how a production maintenance request triage system would operate inside an established residential property management company. It is written for owners, executives, and operations leaders. It is also the source for a complete workflow map that can be presented when the live system is not available.

The production system is an operating layer around the company's existing maintenance process. It receives the same messages the company receives today, identifies what requires attention first, obtains missing details, prepares work for the maintenance team, and records every handoff. It does not replace the property management system, remove employees from important decisions, or send a vendor into a resident's home without an authorized person approving that action.

The scope is maintenance request intake and coordination. Renewals, inspections, leasing, and accounting may use the resulting maintenance history, but they are not automated by this workflow.

# 2 Real world production example

## The request

At 10:42 p.m., a resident texts the number already listed in the resident portal:

> Sorry to bother you. There is water under the kitchen sink again and now it is spreading toward the dishwasher. I turned the tap off but it is still coming out. Dog is in the unit. I can let someone in.

The resident is already known because the text arrives from a phone number verified against the active lease. The message enters the resident communication service and is copied to the automation. The resident does not download a new application or learn a new process.

## The background work

Within seconds, the system performs several separate jobs:

1. It checks whether the text belongs to an open conversation or repeats a recent message.
2. It retrieves the property and unit from the property management system using the verified resident identity.
3. It preserves the resident's exact words and creates an auditable intake record.
4. It uses AI to summarize the symptom, identify the likely trade, note access permission and the dog, and recommend a priority.
5. It runs fixed safety and business rules after the AI. The words about spreading water and continued flow satisfy the company's water escalation policy. Rules may raise the priority but cannot lower it.
6. It checks the property's vendor roster, coverage hours, trade, insurance eligibility, and manager preferences.
7. It prepares a resident acknowledgment, an internal summary, and a vendor work description. It does not send the vendor work description.

## The human decision

The on-call manager receives one alert in the company's normal mobile channel. It shows the resident, property, unit, original words, system summary, reason for escalation, access notes, pet warning, and the available plumbing vendors. The manager can open the corresponding PMS record for the full history.

The manager chooses the approved after-hours plumber. That decision creates or updates the PMS work order, sends the vendor request through the company's existing vendor channel, and records who approved it. A second manager tapping the same action cannot send a duplicate because the database permits only one dispatch claim for that incident.

The resident is told that the request has been received immediately. The resident is told that a provider has been contacted only after the vendor message succeeds. The system does not promise an arrival time. If the vendor later accepts a time through the PMS or approved scheduling system, that confirmed time can be relayed using the company's normal communication process.

## The exception

Suppose the vendor email service fails. The request remains open. The manager sees a failed dispatch state and receives a retry or manual-action prompt. The resident does not receive a false message saying that help is on the way. The failed action is placed in an exception queue, retried according to policy, and escalated to the operations team if retries expire.

By morning, the coordinator sees the complete record in the PMS: original report, classification, safety rule, manager approval, attempted vendor contact, successful retry, resident messages, and current owner. Nothing depends on remembering what happened in a private text thread.

# 3 What the production system does

## The operating promise

The production system converts unstructured maintenance communication into prepared, visible work while preserving human control over material decisions.

It performs eight business functions continuously:

1. **Capture** maintenance messages from approved channels.
2. **Identify** the resident, property, unit, conversation, and related work order where possible.
3. **Interpret** the message into structured maintenance information.
4. **Protect** the process with fixed safety, legal, data, and approval rules.
5. **Clarify** missing operational details through bounded resident questions.
6. **Prepare** acknowledgments, work-order notes, vendor descriptions, and manager choices.
7. **Coordinate** approved updates across the PMS, communication channels, vendors, and staff.
8. **Monitor** ownership, deadlines, failures, aging work, and silent integration problems.

## Information processed for each request

The system may process the following information when it is already available through an authorized business source:

- resident identity and verified contact channel
- property, building, unit, active lease, and preferred language
- the resident's message, subject, attachments, and conversation history
- issue symptoms, location within the home, onset, severity, and whether the condition is changing
- safety signals such as gas, smoke, active flooding, sewage, loss of heat or water, electrical danger, security failure, or structural concern
- access permission, pets, mobility constraints relevant to entry, and preferred contact method
- open work orders that may represent the same issue
- vendor trade, property coverage, hours, priority, compliance status, and contact route
- company response targets, quiet hours, spending authority, and escalation contacts
- human decisions, approvals, corrections, and completion evidence

The system should not ingest payment card data, bank information, screening files, identification documents, or full lease documents unless a separate approved use case requires them. Sensitive content that appears unexpectedly must follow the company's retention and access policy.

## Actions that may happen automatically

Production policy determines which actions are enabled. A conservative starting configuration allows the system to:

- create an intake record and attach the original message
- match a verified resident to a property and unit
- detect duplicates and attach follow-ups to an existing request
- classify priority and trade
- apply fixed escalation rules
- request specific missing details from a verified resident
- acknowledge that a report was received
- create a draft work order or an actual PMS work order in an unassigned review state
- propose eligible vendors without contacting them
- notify the responsible employee according to priority and quiet-hour policy
- update statuses after confirmed events
- answer factual status questions using recorded state
- schedule reminders, aging checks, escalation checks, and operational digests
- retry failed technical actions and place exhausted failures in an exception queue

## Actions reserved for people

The production design keeps the following decisions with authorized employees unless the company adopts a separately approved policy:

- deciding whether to dispatch a vendor
- selecting the specific vendor
- approving spend above the applicable authority limit
- deciding accommodation, discrimination, legal-threat, insurance, or liability matters
- changing an emergency classification downward
- committing to an appointment, completion time, reimbursement, rent credit, or legal position
- closing a work order where completion needs verification
- changing safety rules, response targets, vendor eligibility, or communication policy

## Status model

A visible status model prevents ambiguity between receipt, decision, dispatch, and completion.

| Status | Business meaning | Typical owner |
|---|---|---|
| Received | The company has the original report | Automation |
| Needs details | The system is waiting for specific resident information | Resident with coordinator oversight |
| Needs review | The system cannot safely prepare the next action | Assigned employee |
| Ready for decision | Information is complete and a human action is required | Maintenance coordinator or manager |
| Awaiting owner approval | Spend or scope requires property-owner approval | Property manager |
| Vendor approved | An employee selected a vendor and authorized contact | Manager |
| Vendor contact pending | The outbound action is queued or retrying | Automation with exception owner |
| Vendor contacted | The vendor message was confirmed as sent | Coordinator |
| Appointment proposed | A time has been proposed but not confirmed | Vendor or coordinator |
| Appointment confirmed | The agreed time is recorded in an authoritative system | Coordinator or PMS |
| In progress | The vendor has accepted or started the job | Vendor coordinator |
| Waiting on resident | Entry, information, or confirmation is required | Resident with coordinator oversight |
| Waiting on vendor | Quote, acceptance, update, or invoice is required | Vendor coordinator |
| Work reported complete | Completion was reported but may need verification | Vendor or coordinator |
| Closed | The company accepted completion and sent final communication | Authorized employee |
| Exception | A technical or business action failed and needs attention | Named exception owner |

# 4 How the system integrates with the existing property management business

## The overlay principle

The company should not have to replace its property management system or ask employees to work from a new automation dashboard. The production system sits behind the current channels and systems. It listens for authorized business events, prepares the next step, and writes the result back to the place employees already use.

The property management system remains the authoritative place for properties, units, residents, leases, work orders, and final maintenance status. The automation database remains the authoritative place for processing history, idempotency, retries, model output, and audit events. The two have different jobs and are synchronized through controlled integrations.

## What this looks like to employees

**Residents** continue using the portal, email address, text number, or phone line the company already advertises.

**Maintenance coordinators** continue using the PMS work-order list and the shared communication history. Prepared fields, summaries, recommended priorities, and exception flags appear there as notes, custom fields, tags, tasks, or linked records.

**Property managers** receive approvals through the company's existing collaboration or mobile channel, such as Microsoft Teams, Slack, an approved messaging service, SMS, or the PMS mobile application. Each alert links to the PMS record.

**Vendors** continue receiving work through the existing vendor portal, PMS assignment, email, or dispatch service. The automation does not require a vendor to adopt another portal unless the company chooses one.

**Owners** continue approving costs through the existing owner portal, email approval process, or PMS workflow. The automation can prepare and route the request, but it does not redefine the authority in the management agreement.

**Executives** view service metrics through the reporting platform already used by the business. The automation contributes clean event data rather than creating a separate executive dashboard by default.

## Integration patterns by starting point

| Current business setup | Production connection | Employee experience |
|---|---|---|
| PMS with mature APIs and webhooks | Two-way integration for residents, units, work orders, notes, tasks, and statuses | Work appears and updates inside the PMS |
| PMS with export access but limited write access | Scheduled roster sync plus email or portal-event intake; prepared work returned as tasks, emails, or controlled imports | Staff use the PMS and shared inbox; some creation remains manual |
| Shared mailbox as primary intake | Secure mailbox connection reads new maintenance mail and writes outcomes back to the PMS or task system | Residents and staff keep using email |
| Resident portal sends notification emails | The system extracts the resident's request from the notification and links it to the PMS record | No resident behavior change |
| Existing SMS or communications platform | The provider forwards verified inbound and delivery events to the automation | Residents keep using the same number |
| Existing call center or VoIP system | Voicemail transcripts and call dispositions enter the same intake flow | After-hours staff keep their current phone process |
| Existing Teams or Slack operations channel | Approvals and exception alerts appear as interactive messages | Managers act in a familiar mobile application |
| Existing BI platform | Event and status data is published to the warehouse or reporting layer | Executives use existing reports |

## Production onboarding without disruption

Implementation should proceed in controlled operating stages.

### Discovery and process mapping

The company identifies its current intake channels, PMS, work-order stages, vendor rules, approval limits, on-call policy, response targets, sensitive-case policy, and escalation roster. Existing practice is documented before the automation is configured.

### Read only shadow operation

The system receives a copy of real requests, classifies them, and records what it would have done. It sends no resident or vendor messages and creates no operational work orders. The company compares system recommendations with actual staff decisions.

### Assisted intake

The system may acknowledge receipt, ask approved clarification questions, and prepare PMS records. Vendor contact and material resident communication remain fully manual. Staff corrections are measured.

### Controlled approvals

Interactive manager approvals are enabled for selected properties, trades, and hours. Idempotency, rollback, delivery confirmation, and exception handling are tested with real business users.

### Portfolio rollout

The company expands by property group after accuracy, staffing, vendor coverage, resident experience, and failure handling meet agreed thresholds. A forwarding rule, webhook subscription, or feature flag provides a documented rollback path.

## Data ownership and rollback

The client should own the production hosting account, communication accounts, domains, phone numbers, and third-party credentials wherever practical. Turning off inbound forwarding or integration subscriptions returns the company to its prior workflow. The PMS and original communication channels continue operating even if the automation is unavailable.

# 5 Major components and why they exist

## Component responsibilities

| Component | Why it exists | Receives | Sends | Communicates with |
|---|---|---|---|---|
| Residents and authorized reporters | Originate maintenance requests and provide clarification | Questions, acknowledgments, factual status updates | Portal forms, email, text, calls, attachments | Communication platform and PMS portal |
| Property management system | Holds the business record for residents, properties, leases, work orders, assignments, and final status | New or updated work orders, notes, tags, tasks, status events | Resident and unit data, open work orders, owner rules, vendor assignments | Integration layer, staff, owner and vendor portals |
| Communication services | Preserve the channels the company already uses | Outbound acknowledgments, questions, approved updates | Inbound messages, delivery receipts, replies, voicemail transcripts | Residents, integration layer, PMS timeline |
| Integration and orchestration platform | Coordinates the sequence and routes each event to the correct service | New-message events, PMS events, approvals, schedules, delivery results | Tasks to AI, rules, database, PMS, communication services, and monitoring | Every major system through authenticated connectors |
| Identity and context service | Establishes who is speaking and which property or unit is involved | Verified phone or email, portal session, resident and lease data | Trusted resident, property, unit, language, and permissions context | PMS, communication platform, triage process |
| Message preparation service | Removes signatures and quoted history while preserving evidence | Raw messages and attachments | Clean text, message hash, thread identifiers, attachment metadata | Triage process and audit store |
| AI classification service | Converts unstructured language into a structured maintenance interpretation | Clean message plus limited trusted context | Summary, recommended priority, trade, missing details, language, confidence, sensitive-case indicators | Orchestration platform and policy engine |
| AI drafting service | Prepares concise business communication for approved uses | Structured request, company tone, confirmed facts | Resident acknowledgment draft, internal note, vendor description, clarification wording | Orchestration platform and approval workflow |
| Deterministic policy and safety engine | Enforces rules that must not depend on model judgment | Clean text, AI output, company policy, time, property context | Final routing priority, required human review, notification class, blocked actions | Orchestration, database, alerting |
| Operational database | Keeps processing state and the complete event history | Intake, AI output, rules, approvals, deliveries, errors, timestamps | Current state, audit trail, retry state, idempotency decisions | Orchestration, reporting, monitoring, PMS sync |
| Work queue and retry service | Absorbs bursts and prevents temporary outages from losing work | Units of processing work and failed external actions | Ordered retries, dead-letter exceptions, load controls | Orchestration, external services, monitoring |
| Vendor directory and eligibility rules | Prevents suggestions that ignore trade, property, hours, or compliance | PMS vendor roster, coverage, trade, compliance, priority | Eligible candidate list with reasons | Triage process, manager approval, PMS |
| Manager approval channel | Places time-sensitive decisions in a tool managers already monitor | Prepared decision, original wording, context, choices | Approve, hold, downgrade request, assign manually, escalate | Authorized employees, orchestration, PMS |
| Owner approval channel | Applies management-agreement spending authority | Scope summary, quote, property, approval requirement | Approve, reject, request information | Property manager, PMS, orchestration |
| Vendor communication channel | Delivers only authorized work requests and captures delivery or response | Approved vendor instruction | Delivery status, acceptance, quote, proposed appointment | Vendor, PMS, orchestration |
| Reporting and service management | Shows volume, response times, aging, exceptions, corrections, and vendor outcomes | Event and status data | Operations views, digests, trend reports | Executives, coordinators, monitoring |
| Monitoring and alerting | Detects silent failures and degraded service | Health checks, queue depth, failure rate, last-ingested time, canary results | Operator incidents and escalations | Operations support, orchestration, hosting |
| Security and secrets management | Limits access and protects credentials and sensitive data | User identities, service credentials, policies | Authorized tokens, access decisions, audit logs | Every connected service |
| Backup and recovery services | Restores operations after infrastructure or data loss | Encrypted database and configuration backups | Tested restoration points | Database, hosting, operations support |

## Production hosting

The automation should run in an isolated, client-owned or contractually approved production environment in the required data region. The environment includes the orchestration service, operational database, work queue, encrypted backup process, centralized logs, monitoring, and a secure public integration endpoint.

The public endpoint accepts only signed events from approved systems. The database is not exposed publicly. Secrets are held in a credential vault or the orchestration platform's encrypted credential store. Each client environment is isolated to limit cross-client risk and simplify data ownership.

## The property management system as the business record

The production system should not create a competing source of truth. The PMS remains authoritative for final work-order state. The automation may keep a richer technical event history, but business-facing status must be synchronized back to the PMS. When the two disagree, a reconciliation process flags the difference instead of silently overwriting a human change.

## Communication channels

The company may use different channels by portfolio. Portal, email, SMS, and voice transcripts should all enter a shared intake contract. Outbound messages should use the company's own domain, phone number, and templates. Email must be authenticated and monitored for bounces. SMS requires the company's approved provider, consent process, registration, and opt-out handling. The system records delivery status rather than assuming that a successful send request means the resident received the message.

## Operational database and audit trail

The automation database stores the original event, processing state, model version, model output, rules applied, human decisions, delivery results, retries, and timestamps. It supplies three protections that a simple workflow cannot:

- idempotency so the same inbound event or approval cannot create duplicate work
- recovery so interrupted actions can resume from known state
- accountability so the company can reconstruct what happened and why

## Work queue and dead letter handling

At production volume, a morning surge or provider outage cannot be handled as one long chain of immediate calls. A work queue separates receipt from processing. The system acknowledges receipt of the event, processes it within the agreed target, and retries temporary failures with increasing delays. An action that exhausts retries enters a dead-letter queue with a named human owner. It does not disappear into a technical log.

# 6 How the components communicate

## Business event exchange

The production system is event driven. Each meaningful change becomes a named business event with a unique identifier. Systems exchange references and confirmed facts instead of copying uncontrolled free text wherever possible.

| Event | Source | Primary consumers | Result |
|---|---|---|---|
| Maintenance report received | PMS portal, email, SMS, call platform | Orchestration and operational database | Intake record and processing job |
| Resident identity verified | PMS or communication platform | Context service and orchestration | Trusted resident and unit context |
| Request interpreted | AI service | Policy engine and database | Structured recommendation preserved with model version |
| Policy applied | Safety and policy engine | Orchestration, PMS sync, alerting | Final routing class and permitted actions |
| Clarification requested | Orchestration | Communication service and PMS timeline | Resident receives a bounded question |
| Clarification received | Communication service | Orchestration and request record | Existing request is updated and reassessed |
| Manager decision required | Orchestration | Approval channel and PMS task list | Authorized employee receives prepared choices |
| Manager decision recorded | Approval channel | Database, PMS, vendor communication | Approved action is claimed once |
| Owner approval required | PMS or spending rules | Owner approval channel | Work pauses with visible owner and due time |
| Vendor contact attempted | Orchestration | Vendor channel and database | Delivery is attempted and tracked |
| Vendor contact confirmed | Vendor channel | PMS, resident communication, database | Status changes to vendor contacted |
| Vendor response received | PMS portal, email, vendor platform | Orchestration and coordinator task list | Quote, acceptance, or schedule enters the work order |
| Work completed reported | Vendor or PMS | Coordinator and resident communication | Verification or closure task is created |
| Request closed | Authorized employee in PMS | Reporting, resident communication, database | Final state and close message are recorded |
| Processing failed | Any integration | Retry service and monitoring | Retry, exception ownership, and escalation |

## Communication rules

Every integration follows the same operating rules:

- Each inbound event has a unique source identifier.
- Each action has an idempotency key so retrying cannot duplicate the business outcome.
- The receiving system returns a confirmed result, not merely a request accepted response, where the provider supports it.
- Status changes include the actor, source, time, and prior state.
- Human changes in the PMS are preserved and reconciled.
- Sensitive data is minimized to what the receiving component needs.
- Failures are visible to an operator and to the business owner of the task.
- Resident-facing statements rely only on confirmed state.

## Source of truth by information type

| Information | Authoritative source | Production rule |
|---|---|---|
| Resident, property, unit, lease | PMS | Automation reads and caches only what it needs |
| Original resident communication | Communication platform or PMS timeline | Automation stores an audit copy under retention policy |
| Final work-order status and assignment | PMS | Automation writes confirmed changes and reconciles differences |
| Processing, retries, idempotency, model output | Operational database | Never inferred from the PMS alone |
| Vendor eligibility and authority | PMS or approved vendor master | Suggestions use current approved records only |
| Human approval | Approval record plus PMS audit | Must identify the authorized person and exact action |
| Delivery state | Sending provider | Sent, delivered, bounced, and failed remain distinct |
| Business reporting | PMS and analytics platform | Automation publishes normalized event data |

# 7 Human involvement and AI boundaries

## What AI is used for

AI is useful where residents communicate in ordinary language and fixed forms cannot capture the meaning reliably. It is responsible for:

- summarizing the reported symptom in plain language
- identifying likely urgency and trade
- extracting details such as room, fixture, onset, access, and pets
- distinguishing a new issue from a likely follow-up when thread data is incomplete
- recognizing the language used by the resident
- detecting uncertainty, missing information, and potentially sensitive language
- drafting short acknowledgments, clarification wording, internal summaries, and vendor descriptions from confirmed facts

AI output is a recommendation with a recorded model version and confidence indicator. It is not the business decision.

## What AI is not allowed to do

AI does not:

- suppress or delete a request
- lower a priority created by a fixed safety rule
- select and contact a vendor without an authorized approval
- approve spend or interpret a management agreement
- decide a disability accommodation, discrimination concern, legal threat, insurance claim, or liability position
- promise an appointment, repair date, reimbursement, legal deadline, or outcome
- close a work order without the company's required evidence
- change its own rules or retrain itself from corrections

## Deterministic boundaries

Fixed policy runs after AI interpretation. Safety patterns, company escalation rules, notification policy, spending authority, quiet hours, vendor eligibility, data restrictions, and approval requirements are enforced as explicit conditions. The AI cannot talk its way around them.

For safety, the rule layer is escalate only. It may raise a request to emergency or force human review. It may not reduce urgency. A human downgrade requires an identified employee, reason, and audit event.

## Uncertainty and incomplete information

The system does not turn uncertainty into confident action. It follows a defined order:

1. Ask the verified resident for specific missing operational details when the question is safe and approved.
2. Preserve the request and set a visible waiting state.
3. Reassess when the reply arrives.
4. Send the request to a person if the detail cannot be obtained, the message remains unclear, or the topic is sensitive.

A general opening such as “there is a problem in my bathroom” can be buffered briefly while the system asks for the symptom. It should not create a vendor approval before an actual issue is described. Once a concrete issue exists, the system creates a durable request even if other details remain missing.

## Sensitive and high risk cases

Accommodation requests, discrimination allegations, legal threats, rent-withholding statements, insurance claims, injury reports, and ambiguous safety cases go to trained staff. The system may identify and route the issue, but it should not draft a substantive response unless legal and operations leaders have approved a narrow template for that category.

## Human roles

| Role | Decisions and responsibilities |
|---|---|
| Resident | Reports the issue, answers clarification, confirms access, receives factual updates |
| Maintenance coordinator | Reviews prepared requests, resolves exceptions, coordinates access, monitors vendors, verifies completion |
| On call manager | Responds to emergency alerts and authorizes after-hours action |
| Property manager | Applies property and owner context, obtains owner approval, handles sensitive cases |
| Regional operations leader | Owns policy, service targets, staffing, escalation design, and exception performance |
| Property owner | Approves work above authority limits where the management agreement requires it |
| Vendor | Accepts work, proposes schedule, reports progress and completion |
| System operator | Maintains integrations, monitors health, restores failed service, and reviews technical exceptions |
| Compliance or legal reviewer | Defines sensitive-case policy and reviews escalated matters |

## Governance and improvement

Corrections become review data, not automatic training. Operations leaders review disagreements by category, especially missed and unnecessary escalations. A policy or prompt change is tested against an approved fixture set and recent anonymized examples before release. The company records who approved the change and can roll back to the prior version.

# 8 End to end workflow

## Flow A New resident maintenance request

1. A resident reports a problem through the current portal, email address, text number, or phone line.
2. The source system records the message and emits a signed event or exposes it through an approved mailbox connection.
3. The orchestration platform writes a receipt record before calling any external intelligence service.
4. Identity and context are resolved from the portal session, verified phone, email, lease data, or a human review path.
5. Message preparation removes quoted history and signatures, preserves attachments, calculates a duplicate key, and identifies reply headers.
6. Duplicate and thread checks determine whether to create a request, append a message, or group the report into an existing incident.
7. If the message is only a greeting or lacks any concrete symptom, the system asks for the symptom and keeps preliminary conversation state.
8. The AI classification service returns structured fields, confidence, and sensitive-case indicators.
9. Fixed safety and policy rules determine the final routing class and permitted actions.
10. The request is written to the operational database and synchronized to the PMS as an intake record, note, task, or work order according to rollout mode.
11. If safe clarification is required, the system asks the resident and sets Needs details. The manager remains unalerted unless the message includes a safety condition or policy requires review.
12. If the request is sensitive, unreadable, identity-ambiguous, or inconsistent, it is assigned to a human with the reason shown.
13. If information is complete, the system prepares the internal summary, resident acknowledgment, vendor description, and eligible vendor list.
14. Notification policy determines whether to alert immediately, send silently, place a PMS task, or include the item in the next digest.
15. The authorized employee reviews the original message, recommendation, applied rules, property context, and available actions.
16. The employee may hold, edit, reclassify, assign manually, seek owner approval, or select a vendor.
17. The selected action is claimed once in the operational database and synchronized to the PMS.
18. If owner approval is required, the work enters Awaiting owner approval with a due time and owner-facing request. No vendor is contacted until approval or an authorized emergency exception is recorded.
19. If vendor contact is approved, the system sends through the existing PMS vendor channel, portal, or authenticated email service.
20. On confirmed send, the PMS and operational database move to Vendor contacted. Only then may the resident receive that factual update.
21. Vendor replies, quotes, acceptance, and proposed times attach to the same work order and create coordinator tasks where needed.
22. A confirmed appointment may be sent to the resident. A proposed time is not described as confirmed.
23. Progress checks follow the company's cadence. Missing vendor responses, access blocks, owner delays, and response-target breaches remain visible with an owner.
24. When work is reported complete, the system creates the required verification step. Depending on company policy, this may be vendor evidence, coordinator review, resident confirmation, or inspection.
25. An authorized employee closes the work order in the PMS. The resident receives the approved completion message, and the event history is retained under policy.

## Flow B Resident follow up or status question

1. A resident replies in the same channel or asks when an issue will be completed.
2. Thread identifiers, verified identity, and open-request context are checked before any new-ticket logic.
3. A progress question produces a factual response from recorded status and creates no new maintenance request.
4. New symptoms or worsening conditions attach to the existing request and trigger reassessment.
5. A genuinely separate issue creates a new request with a link to the same resident and property.
6. The PMS communication timeline and operational audit both record the exchange.

## Flow C Multiple reports about one property incident

1. Several residents report water, smoke, power, or access problems within a defined property and time window.
2. The system creates or identifies a parent incident and links individual resident reports to it.
3. Safety evaluation still occurs for every message.
4. The on-call manager receives one incident alert with the number of affected units and the most serious evidence, rather than one phone alert per resident.
5. Individual resident records remain separate for communication and access needs.
6. Incident status changes can update all linked requests while preserving resident-specific messages.

## Flow D Scheduled operational controls

1. A frequent unanswered-emergency check looks for emergency requests without a recorded acknowledgment, regardless of whether the first alert succeeded.
2. Aging checks mark urgent and routine work as overdue according to company targets. Age alone never creates an emergency phone alert.
3. The daily digest summarizes open emergencies, breached targets, overdue work, unowned exceptions, owner approvals, vendor delays, and prior-day volume.
4. A heartbeat checks recent intake, queue processing, PMS synchronization, and communication delivery. It alerts the system operator when expected activity stops.
5. A canary request periodically tests the complete path in a non-customer test context.

# 9 Exceptions and edge cases

## Exception handling matrix

| Exception | System response | Human owner | What remains visible |
|---|---|---|---|
| AI timeout or invalid output | Store request, apply fixed safety rules, set Needs review, retry within policy | Maintenance coordinator for the request; system operator for repeated failures | Original message, failed step, rules result, retry state |
| Repeated AI failures | Enter reduced mode, stop unnecessary AI calls, continue intake and safety checks, send one operator incident | System operator | All requests plus degraded-service status |
| PMS unavailable | Keep durable intake and queue PMS updates for retry | System operator and maintenance coordinator | Exception list and unsynchronized state |
| Communication provider unavailable | Queue outbound action, retry, do not claim delivery | System operator; coordinator if time sensitive | Message state such as queued, failed, bounced |
| Vendor message fails | Keep Vendor contact pending or Failed, alert manager, do not tell resident vendor was contacted | Maintenance coordinator | Selected vendor, attempts, error, next action |
| Duplicate inbound event | Attach technical receipt to existing record and take no duplicate business action | None unless conflict exists | Duplicate link and original request |
| Two managers approve | First valid approval claims the action; later attempts receive Already handled | None | Both attempts and successful actor |
| Resident identity cannot be verified | Do not reveal property or work-order information; request verification or route to staff | Resident services or property manager | Unverified conversation and assigned task |
| Message names no concrete problem | Ask for a symptom and create no vendor decision | Resident | Preliminary conversation state |
| Important details remain missing | Continue bounded clarification or assign to staff | Resident then coordinator | Missing fields, questions, response history |
| Prompt injection or hostile text | Treat message as resident content, validate structured output, apply fixed rules | Coordinator if ambiguous | Original text and flagged interpretation issue |
| Legal or accommodation language | Block substantive automated response and vendor approval where inappropriate | Property manager or compliance reviewer | Sensitive-case flag and assigned owner |
| Resident reports worsening condition | Append to request and reassess priority immediately | On-call manager if escalated | Before and after priority with reason |
| One incident creates many reports | Group alert by property and time while preserving each resident record | On-call manager | Parent incident and linked requests |
| No eligible vendor | Set Needs vendor assignment and present no vendor action | Maintenance coordinator | Eligibility filters and missing coverage reason |
| Vendor compliance expires | Remove vendor from automated suggestions and assign manual review | Vendor manager | Compliance reason and alternative candidates |
| Owner does not answer | Keep Awaiting owner approval, remind and escalate according to agreement | Property manager | Approval age, reminders, emergency exception if used |
| Resident asks for ETA | Answer only with recorded confirmed status; create no ticket | None unless request is stalled | Status response linked to open work |
| Attachment cannot be read | Preserve file metadata, quarantine if unsafe, request description or review | Coordinator or security operator | Attachment state and original message |
| Unsupported language | Preserve request, use approved translation path or human review | Coordinator | Language flag and untranslated original |
| Data mismatch between PMS and automation | Stop destructive overwrite and create reconciliation task | System operator or data steward | Both values, last update, source system |
| Old approval link is used | Reject because action token is expired, revoked, or belongs to a completed action | None | Rejected attempt in audit log |
| Backup restore is required | Restore isolated environment, replay queued events, reconcile PMS state | System operator | Recovery record and reconciliation report |

## Preventing silent loss

The production design uses several independent controls:

- The original channel keeps its own copy of the resident report.
- The automation records receipt before interpretation.
- Work is queued before external processing.
- Each request has a current owner and next action.
- Retries have limits and exhausted work becomes a business-visible exception.
- Unanswered emergencies are selected by priority and missing acknowledgment, not by whether an alert-send status was recorded.
- A heartbeat detects when expected intake or synchronization becomes quiet.
- A periodic canary proves that the complete path still works.
- Daily reconciliation compares PMS work orders with automation state.
- Backups are encrypted and restoration is tested on a schedule.

## Security privacy and control requirements

A production deployment requires least-privilege access, multi-factor authentication for users, single sign-on where available, encrypted connections, encryption at rest, managed secrets, per-role permissions, tamper-evident audit history, configurable retention, attachment deletion, incident response, and tested termination deletion.

Resident message text sent to an AI service must follow the client-approved data-handling policy and current provider terms. Only the minimum context needed for the task should be transmitted. A production agreement should define hosting region, subprocessors, access, retention, deletion, uptime expectations, support responsibility, and the advisory human-approval boundary.

# 10 Complete production workflow map reference

## Diagram purpose

The Excalidraw map should let a prospect follow one maintenance request from resident report through completion while also seeing the controls that keep work visible. The map should show business systems first and technical support systems second. Low-level code, database queries, and individual automation nodes should not appear.

## Recommended swimlanes

Create the workflow from left to right with these horizontal lanes:

1. Resident and authorized reporter
2. Existing communication channels
3. Existing property management system
4. Production automation layer
5. AI and fixed policy controls
6. Property management team and owner
7. Vendor and field service
8. Operational control and monitoring

Place authoritative data stores below the lanes and connect them with dashed lines. Place exception handling along the bottom so every failure path ends with a visible owner.

## Visual legend

| Visual | Meaning |
|---|---|
| Rounded rectangle | Business event or process |
| Diamond | Decision or policy gate |
| Person icon | Human actor |
| Application frame | Existing business system |
| Cylinder | Authoritative data store |
| Solid arrow | Normal business flow |
| Dashed arrow | Data lookup, synchronization, monitoring, or audit copy |
| Red border | Safety or emergency path |
| Amber border | Human review, missing information, or waiting state |
| Blue border | Automated preparation or synchronization |
| Green border | Confirmed external action or completed state |
| Gray border | Supporting system or non-urgent path |

## Actors

| ID | Actor | Role on the map |
|---|---|---|
| A1 | Resident | Reports issue, answers questions, receives updates |
| A2 | Maintenance coordinator | Reviews prepared work, resolves exceptions, coordinates progress |
| A3 | On call manager | Handles immediate safety decisions and after-hours approvals |
| A4 | Property manager | Applies property, owner, spending, and sensitive-case context |
| A5 | Property owner | Approves work above authority where required |
| A6 | Vendor | Accepts, schedules, performs, and reports work |
| A7 | System operator | Maintains uptime, integrations, retries, and recovery |
| A8 | Compliance or legal reviewer | Handles accommodation, legal, discrimination, and liability cases |

## Major systems

| ID | System | Label to display | Key inputs | Key outputs |
|---|---|---|---|---|
| S1 | Resident portal | Existing Resident Portal | Authenticated submissions, attachments | Request event, resident identity |
| S2 | Email service | Existing Maintenance Mailbox | Email and replies | Messages, delivery and bounce results |
| S3 | SMS communications | Existing Resident Text Number | Verified texts and opt-out events | Messages and delivery results |
| S4 | Call or VoIP service | Existing After Hours Line | Calls and transcripts | Transcript and call disposition |
| S5 | PMS | Property Management System | Resident, lease, property, work order, owner and vendor data | Work orders, tasks, notes, assignments, final status |
| S6 | Manager collaboration tool | Existing Manager Alert Channel | Prepared alerts and decisions | Approve, hold, assign, reclassify |
| S7 | Owner approval tool | Existing Owner Approval Process | Scope, quote, authority context | Approval or rejection |
| S8 | Vendor system | Existing Vendor Channel | Approved work request | Delivery, acceptance, quote, schedule, completion |
| S9 | Analytics platform | Existing Operations Reporting | Normalized events and status | Dashboards, digests, trends |
| S10 | Automation platform | Production Orchestration | Business events and schedules | Coordinated actions across systems |
| S11 | Operational database | Automation State and Audit | Receipts, processing, decisions, failures | State, idempotency, history, retry context |
| S12 | Work queue | Queue and Retry Control | Processing jobs and failed actions | Ordered work, retry, dead-letter exception |
| S13 | AI service | AI Language Interpretation | Clean message and limited context | Structured classification and drafts |
| S14 | Policy engine | Fixed Safety and Business Rules | AI output, message, company policy | Final route, blocked actions, notification class |
| S15 | Monitoring | Health Monitoring and Recovery | Health, queue, latency, failure and canary events | Operator alerts and incident records |
| S16 | Security services | Identity Secrets and Access Control | User and service identity | Authentication, authorization, audit access |
| S17 | Backup service | Encrypted Backup and Restore | Database and configuration snapshots | Tested recovery points |

## Inputs

| ID | Input | Origin |
|---|---|---|
| I1 | Portal maintenance submission | S1 |
| I2 | Maintenance email or reply | S2 |
| I3 | Resident text message | S3 |
| I4 | Voicemail transcript or call disposition | S4 |
| I5 | Resident property unit and lease context | S5 |
| I6 | Open work orders and conversation history | S5 and communication systems |
| I7 | Company priority response quiet-hour and escalation policy | Operations leadership |
| I8 | Vendor eligibility coverage and contact data | S5 or approved vendor master |
| I9 | Spending authority and owner approval rules | S5 and management agreement configuration |
| I10 | Manager owner vendor and operator decisions | A2 through A7 |
| I11 | Delivery acceptance quote schedule and completion events | S2 S3 S8 |

## Core process nodes

| ID | Process | Lane | Output |
|---|---|---|---|
| P1 | Resident reports maintenance issue | Resident | New channel event |
| P2 | Capture signed event and preserve original | Automation | Durable receipt |
| P3 | Verify identity and load property context | PMS and Automation | Trusted or unverified context |
| P4 | Normalize message and preserve attachments | Automation | Clean text and metadata |
| P5 | Check duplicate thread and open incident | Automation | New request or linked update |
| P6 | Buffer preliminary message if no symptom exists | Automation | Clarification before ticket |
| P7 | Interpret language priority trade and missing details | AI | Structured recommendation |
| P8 | Apply fixed safety legal and business rules | Policy | Final route and permitted actions |
| P9 | Record request model result rules and status | Database | Auditable request state |
| P10 | Synchronize intake to PMS | PMS and Automation | PMS record task note or draft work order |
| P11 | Ask resident for approved missing details | Communication | Clarification message |
| P12 | Reassess reply in same request | Automation | Updated prepared request |
| P13 | Prepare resident internal and vendor wording | AI and Automation | Draft communication package |
| P14 | Match eligible vendors | Automation and PMS | Zero to several candidates |
| P15 | Apply notification policy | Policy | Immediate silent task or digest route |
| P16 | Present manager decision | Manager channel | Human action request |
| P17 | Record hold edit reclassify assign or vendor choice | Automation | Claimed human decision |
| P18 | Obtain owner approval when required | PMS and Owner | Approved rejected or waiting state |
| P19 | Send approved vendor request | Vendor channel | Delivery attempt |
| P20 | Confirm delivery before resident update | Automation | Vendor contacted or exception |
| P21 | Send factual resident status update | Communication | Recorded outbound message |
| P22 | Receive vendor acceptance quote or proposed time | Vendor and PMS | Coordinator task or updated work order |
| P23 | Confirm appointment using authoritative state | PMS and Communication | Confirmed schedule update |
| P24 | Track work progress ownership and response targets | PMS and Automation | Reminders and exceptions |
| P25 | Record completion report and request verification | PMS and Automation | Verification task |
| P26 | Human verifies and closes work order | PM team and PMS | Closed request |
| P27 | Send final resident communication | Communication | Closure message |
| P28 | Publish operational metrics | Reporting | Executive and operations views |

## Decision gateways

| ID | Decision | Yes path | No path |
|---|---|---|---|
| D1 | Identity verified | Load trusted context | Do not disclose status and assign verification |
| D2 | Duplicate follow up or shared incident | Link to existing record and reassess | Create new request |
| D3 | Concrete maintenance symptom present | Continue triage | Buffer and ask for symptom |
| D4 | AI result usable | Apply policy to recommendation | Apply safety rules and Needs review |
| D5 | Safety signal or mandatory escalation | Emergency or human review route | Continue recommended priority |
| D6 | Sensitive legal accommodation or liability case | Block substantive automation and assign trained human | Continue operational preparation |
| D7 | Required details complete | Prepare manager decision | Ask resident or assign human |
| D8 | Immediate alert permitted by notification policy | Alert on-call role | Silent task or digest |
| D9 | Eligible vendor found | Show approved candidates | Needs vendor assignment |
| D10 | Spend within manager authority or emergency exception | Continue to vendor choice | Obtain owner approval |
| D11 | Human approves vendor contact | Claim action once and send | Hold edit reclassify or manual route |
| D12 | Vendor message confirmed sent | Mark contacted and update resident | Retry and create visible exception |
| D13 | Appointment confirmed in authoritative system | Notify resident | Keep proposed or waiting state |
| D14 | Completion evidence accepted | Close and notify | Return to coordinator or vendor |

## Outputs

| ID | Output | Destination |
|---|---|---|
| O1 | Durable intake record | S11 |
| O2 | Prepared or created PMS work order | S5 |
| O3 | Resident receipt or clarification | S1 S2 or S3 |
| O4 | Human review task | S5 or S6 |
| O5 | Emergency alert | S6 |
| O6 | Owner approval request | S7 |
| O7 | Approved vendor request | S8 |
| O8 | Vendor delivery failure exception | S5 S6 and S12 |
| O9 | Factual resident status update | Resident channel and PMS timeline |
| O10 | Confirmed appointment update | Resident channel and S5 |
| O11 | Progress reminder or escalation | S5 or S6 |
| O12 | Closed work order and resident close message | S5 and resident channel |
| O13 | Audit history | S11 |
| O14 | Daily digest and executive metrics | S9 |
| O15 | Technical incident alert | S15 to A7 |

## Exception nodes

| ID | Exception node | Route |
|---|---|---|
| E1 | Unverified resident | Resident services verification task |
| E2 | Unreadable or low confidence request | Human review with original message |
| E3 | Missing operational detail | Resident clarification then reassessment |
| E4 | Sensitive case | Property manager or compliance review |
| E5 | AI degraded mode | Fixed rules continue and operator incident opens |
| E6 | PMS synchronization failed | Queue retry and reconciliation task |
| E7 | No eligible vendor | Manual vendor assignment |
| E8 | Owner approval overdue | Property manager reminder and escalation |
| E9 | Vendor contact failed | Retry then coordinator exception without resident claim |
| E10 | Vendor has not responded | Coordinator reminder or alternative-vendor decision |
| E11 | Appointment or access conflict | Coordinator task and resident/vendor communication |
| E12 | Completion disputed or unverified | Reopen or inspection path |
| E13 | Intake has gone silent | Operator heartbeat incident |
| E14 | Duplicate approval or stale action | Reject safely and preserve audit event |
| E15 | Data mismatch | Reconciliation task without silent overwrite |

## Primary connector list

Use these arrows as the main left-to-right story:

1. A1 to P1 through S1 S2 S3 or S4
2. P1 to P2 to O1
3. P2 to P3 with lookup to S5
4. P3 through D1 to P4
5. P4 to P5 through D2
6. P5 through D3 to P7
7. P7 to P8 through D4 D5 and D6
8. P8 to P9 to P10
9. P9 through D7 to either P11 P12 or P13
10. P13 to P14 through D9
11. P14 to P15 through D8
12. P15 to P16 to P17
13. P17 through D10 and P18 when owner approval applies
14. P17 or P18 through D11 to P19
15. P19 through D12 to P20 and P21
16. S8 to P22 to P23 through D13
17. P23 to P24 to P25
18. P25 through D14 to P26 and P27
19. P9 P17 P20 P24 and P26 to P28 by dashed reporting arrows
20. Every process and external system to S15 and S11 by dashed monitoring and audit arrows

## Exception connector list

Use red or amber downward arrows from each relevant gateway:

- D1 to E1
- D3 to P6 and P11
- D4 to E2 and E5
- D6 to E4
- D7 to E3
- D9 to E7
- D10 to P18 and E8 when overdue
- D11 duplicate or stale action to E14
- D12 failure to E9
- P10 failure to E6
- P22 no response to E10
- P23 access or schedule conflict to E11
- D14 rejected completion to E12
- Monitoring silence condition to E13
- Reconciliation difference to E15

Every exception node must connect to a named human role, a visible system record, and a return path. No exception should end at a technical log.

## Meeting narrative for the completed map

Present the map in four passes.

First, trace the resident's familiar path into the company's existing portal, email, text, or phone system. Emphasize that no new employee application is required.

Second, follow the background preparation through identity, duplicate checks, AI interpretation, fixed policy, clarification, and PMS update. Separate the AI recommendation from the fixed rules visually.

Third, stop at the human decision. Show that vendor selection, owner approval, sensitive cases, and downward emergency changes remain with authorized people. Then follow only a confirmed action to the vendor and resident.

Fourth, trace the dashed controls underneath the workflow: audit history, retries, dead-letter ownership, reconciliation, heartbeat, canary, backups, and reporting. This is what turns a demonstration into an operating system the company can depend on.

## Production success measures

The prospect and implementation team should agree on baseline and target measures before launch:

- intake volume by channel and property
- time from report to recorded receipt
- time from report to informed human decision
- emergency acknowledgment time
- missed and unnecessary escalations reviewed separately
- percentage of requests requiring clarification
- clarification response rate and usefulness
- duplicate work-order rate
- vendor match acceptance rate
- vendor contact failure and retry rate
- time waiting on resident vendor owner and staff
- response-target breach rate
- unowned exception age
- resident repeat-contact rate before first meaningful update
- staff minutes spent on intake and first response
- system availability queue delay and synchronization lag
- number of sensitive cases correctly reserved for human review

The production case should be based on the company's measured baseline and pilot results. The scale arithmetic in this document explains the opportunity; it does not replace that measurement.

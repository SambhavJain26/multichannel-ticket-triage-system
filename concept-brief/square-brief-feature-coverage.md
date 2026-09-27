# Production brief capability coverage

Authority: `docs/production-maintenance-triage-blueprint.md`. Cross-check: `docs/how-the-system-works.md`, `docs/build-description.md`, and `02-maintenance-triage.md`.

The latter three contain demo-specific and historical constraints. Do not import fixed demo schedules, Telegram onboarding, vendor-count limits, pricing, older age-escalation rules, unsupported competitor claims, or the absence of PMS integration into a proposed production brief. The user's explicit scope is production.

This is a prospect brief, not an exhaustive implementation specification. The following maps buyer-facing capability families to visible pages. Low-level security, event contracts, all exception variants, and configuration details remain in the controlling blueprint; they are summarized, not claimed to be reproduced verbatim.

| Capability | PDF page | Blueprint section |
|---|---|---|
| Portal/email/SMS/phone transcript intake | 1, 3 | 3-6 |
| Preserve original and attachment history | 1, 2 | 3, 8 |
| Verified resident/property/unit context | 1, 2 | 3, 8 |
| Duplicate/reply linking and shared incident grouping | 1, 2 | 8 A-C |
| Vague messages get clarification, not vendor tasks | 2 | 7, 8 |
| Urgency/trade/access/pets interpretation | 1, 2 | 3, 7 |
| Approved language support and human fallback | 1, 4 | 3, 9 |
| Separate, escalate-only fixed rules | 1, 2, 3 | 7 |
| Receipt acknowledgment and bounded missing-detail follow-up | 1, 2 | 3, 7 |
| Preserve known details and reassess replies | 2 | 7, 8 |
| Draft PMS notes and vendor instructions | 1, 2, 3 | 3, 5 |
| Vendor eligibility: trade, coverage, hours, compliance | 2 | 2, 5 |
| Emergency alerts versus quiet routine tasks | 2 | 6-8 |
| Hold/edit/assign/vendor choice/owner approval | 2, 4 | 7, 8 |
| Approved send, duplicate/stale approval protection | 2, 4 | 6, 9 |
| Truthful status replies; no new ticket or invented ETA | 1, 2 | 8 B |
| Existing PMS/manager/vendor channels and prospect-specific routes | 3 | 4-6 |
| Limited-write fallback, owner routing, reporting feed | 3 | 4 |
| Named stack, hosting, state/queue/retry/audit, AI boundary | 3 | 5-7 |
| Vendor replies, confirmed schedule, progress, verification/closure | 1, 4 | 8 A |
| Unanswered-emergency checks and daily delay digests | 4 | 8 D |
| No age-only emergency escalation | 4 | 8 D |
| Sensitive, unreadable, identity, language, no-vendor review | 4 | 9 |
| AI failure, PMS/channel retry and owned exceptions | 4 | 9 |
| Reconciliation without silent overwrites | 4 | 6, 9 |
| Silent-intake monitoring, full-path checks, tested recovery | 4 | 9 |
| Privacy, encrypted data, credential control, MFA/roles | 4 | 9 |
| Staff-approved tested changes, no self-training, rollback/support | 4 | 4, 7, 9 |

## Personalization connection fields

For each prospect, replace the square-bracket routes with the specific product and confirmed connection method. Public research alone may not establish account entitlements. Mark unconfirmed permissions as such.

- Intake: channel/provider, event or secure-mailbox route, reply method.
- PMS: API/partner entitlement or export route, readable records, allowed writes, fallback if blocked.
- Manager: app integration and authenticated approval callback, or secure review link. Add owner approval route.
- Vendor: PMS API, supported portal route, or authenticated email service; capture replies and delivery results.
- Reporting and hosting: named destination and connection, client-approved environment.

Do not present a list of alternative routes as if all have been implemented or verified for a prospect.

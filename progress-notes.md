# Maintenance Request Triage - Progress Notes

Read this file first at the start of every session.

## Current Status

Planning complete. No implementation code, workflow JSON, Docker files, schemas, scripts, prompts, or fixtures have been created yet.

The staged plan is saved in `build-plan.md`.

## Stage Progress

| Stage | Name | Status | Notes |
|---|---|---|---|
| 1 | Local Environment, Accounts, and Runtime Setup | Not started | Default decision changed: local Docker first; tunnel only for Telegram/public webhook tests; VPS/Caddy production-only. |
| 2 | Data Model, Config, and Fixture Corpus | Not started | No schema or fixtures created yet. |
| 3 | OpenAI Model Contract and Accuracy Harness | Not started | Must verify current model string and accepted parameters live. |
| 4 | Core Triage Sub-Workflow | Not started | Depends on stages 2-3. |
| 5 | Board and Detail View | Not started | Depends on stored tickets/events. |
| 6 | Alerts, Approval Gate, and Outbound Email | Not started | Depends on core workflow and credentials. |
| 7 | Ingestion Paths and Follow-Up Importer | Not started | Depends on core workflow; importer supports the sales follow-up ask. |
| 8 | Digest, Aging, Heartbeat, and Demo Hardening | Not started | Final reliability and demo-readiness pass. |

## Planning Decisions Already Made

- Build is demo-depth, not production.
- Architecture is email/form/fixture in, local n8n orchestration, local Postgres storage, OpenAI strict JSON calls, Telegram manager alerts via tunnel when callback testing is needed, SMTP approved replies, and server-rendered board.
- No PMS integration in the demo.
- Advisory-only is non-negotiable: no dispatch, no suppress, no auto-close, no auto-reply without human approval.
- Age-based routine escalation becomes `OVERDUE` board/digest status only. It does not create an emergency phone alert.
- Deterministic safety rules are escalate-only and run after the model.
- `NEEDS_REVIEW` is a system state, not a model output.
- Accommodation/legal-sensitive requests skip draft generation and require human handling.
- Competitor-aware positioning is required; do not claim nobody else does maintenance AI triage.
- Default setup is local-first. VPS and Caddy are reserved for production deployment.
- Use a tunnel for Telegram callback testing and temporary public board access.
- Use n8n's built-in OpenAI node for workflow model calls if the installed version supports Text -> Generate a Model Response with JSON Schema output and the needed model/reasoning settings. Keep HTTP Request as fallback and use direct API calls in the standalone harness.
- Do not use n8n AI Agent/LangChain agent loops for the triage classifier.
- Default model is `gpt-5-nano`. Fallback model is `gpt-5.6-luna` if nano misses safety cases, under-escalates too often, has unstable schema output, or produces weak drafts. Use standard pricing for live workflow estimates; batch pricing is only relevant for offline batch harness/report runs.
- Early approved outbound replies should go to controlled test inboxes until the approval gate and double-approve guard are verified.

## Open Questions Before Stage 1

- Which domain/mailbox should be used for the demo?
- Which tunnel should be used for Telegram testing: Cloudflare Tunnel, ngrok, or another option?

## Deviations From Original Plan

- One planning refinement after rechecking `maintenance-triage-demo-build-plan.md`: Stage 8 now explicitly includes demo collateral and rehearsed claims, including accuracy/cost numbers, failure recovery lines, data-handling answer, competitor-aware positioning, and the "what not to claim" list.
- User corrected deployment approach: demo build is local-first; VPS and Caddy are production-only; tunnel is used for Telegram/public webhook testing.
- Research correction: current n8n OpenAI node V2 supports Responses API and JSON Schema output, so the workflow default is the built-in OpenAI node when available, not HTTP Request. HTTP Request remains fallback and direct API remains useful for the standalone harness.
- `AGENTS.md` was rewritten using lessons from a similar local n8n AI automation project, adapted for maintenance triage: read order, local service rules, n8n workflow gotchas, fixture expectations, security rules, and completion/documentation discipline.
- User requested a durable rule to commit and push after every completed task. `AGENTS.md` now requires committing and pushing to `main` after task completion, while still avoiding secrets/local data/generated temp output.

## Verification Log

No verification has been run yet.

## Outstanding Risks To Recheck During Build

- Current OpenAI model IDs, prices, and accepted API parameters may change; Stage 3 must verify live.
- Gmail App Password availability may not hold for the selected mailbox type.
- Tunnel reliability and URL stability must be verified before Telegram callback testing.
- n8n production hosting has licensing nuance; production should use a client-owned VPS unless n8n confirms another arrangement in writing.
- Email deliverability from demo and production domains must be handled explicitly before showing tenant replies.

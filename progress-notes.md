# Maintenance Request Triage - Progress Notes

Read this file first at the start of every session.

## Current Status

Stage 2 data foundation is implemented and verified. Docker Compose runs local n8n, Postgres, and GreenMail. The `triage` Postgres schema, config seed, and 30-fixture corpus exist. Stage 3 prompt/schema artifacts and the standalone OpenAI harness are implemented for the revised demo gate: six live-demo fixtures, one run, priority/safety acceptance. No workflow JSON, board, or n8n triage logic has been created yet.

The staged plan is saved in `build-plan.md`.

## Stage Progress

| Stage | Name | Status | Notes |
|---|---|---|---|
| 1 | Local Environment, Accounts, and Runtime Setup | Implemented | Local Docker runtime verified with n8n, Postgres, GreenMail, and Cloudflare Tunnel quick URL. OpenAI, Telegram, Postgres, IMAP, and SMTP credentials exist in n8n. Real demo mailbox/domain is deferred until outbound demo rehearsal. |
| 2 | Data Model, Config, and Fixture Corpus | Implemented | App tables live under dedicated `triage` schema. Seven config rows seeded. Thirty text fixtures with matching expected JSON files validate successfully. |
| 3 | OpenAI Model Contract and Accuracy Harness | Implemented for demo gate | Responses API probe passed for `gpt-5-nano` and `gpt-5.6-luna`. Reduced live-demo harness passed with 6/6 priority matches, zero under-escalations, zero over-escalations, and zero missed safety signals. Full 30-fixture x 3-run hardening failed and is deferred. |
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

- Resolved for Stage 1: use GreenMail as the local IMAP/SMTP simulator. Real demo mailbox/domain is deferred until outbound demo rehearsal.
- Resolved for Stage 1: use Cloudflare Tunnel quick tunnels for temporary HTTPS callback testing.

## Deviations From Original Plan

- One planning refinement after rechecking `maintenance-triage-demo-build-plan.md`: Stage 8 now explicitly includes demo collateral and rehearsed claims, including accuracy/cost numbers, failure recovery lines, data-handling answer, competitor-aware positioning, and the "what not to claim" list.
- User corrected deployment approach: demo build is local-first; VPS and Caddy are production-only; tunnel is used for Telegram/public webhook testing.
- Research correction: current n8n OpenAI node V2 supports Responses API and JSON Schema output, so the workflow default is the built-in OpenAI node when available, not HTTP Request. HTTP Request remains fallback and direct API remains useful for the standalone harness.
- `AGENTS.md` was rewritten using lessons from a similar local n8n AI automation project, adapted for maintenance triage: read order, local service rules, n8n workflow gotchas, fixture expectations, security rules, and completion/documentation discipline.
- User requested a durable rule to commit and push after every completed task. `AGENTS.md` now requires committing and pushing to `main` after task completion, while still avoiding secrets/local data/generated temp output.

## Verification Log

- 2026-07-31: `docker compose config` passes after `.env` is present.
- 2026-07-31: `.\scripts\start-local.ps1` created ignored `.env` from `.env.example` and started `n8n`, `postgres`, and `greenmail`.
- 2026-07-31: `.\scripts\validate-stage-1.ps1` passed. Verified Postgres readiness, n8n HTTP 200, loopback bindings for n8n on 5678 and Postgres on 5432, and GreenMail SMTP/IMAP send/fetch.
- 2026-07-31: Cloudflare quick tunnel started successfully for `http://localhost:5678` and issued a `trycloudflare.com` HTTPS URL. The test tunnel was stopped after verification.
- 2026-07-31: Initial Stage 1 verification used local GreenMail IMAP/SMTP values because no real demo mailbox/domain was selected. Real mailbox setup remains deferred until outbound demo rehearsal.
- 2026-07-31: User created `maintenance-triage-openai` and `maintenance-triage-telegram-bot` credentials in n8n. Added and ran `.\scripts\import-local-n8n-credentials.ps1`, which imported `maintenance-triage-postgres-local`, `maintenance-triage-greenmail-imap-local`, and `maintenance-triage-greenmail-smtp-local` through n8n's `import:credentials` CLI. Verified all five `maintenance-triage-*` credentials exist and are owned by the personal n8n project.
- 2026-07-31: Added Stage 2 SQL and scripts. Ran `.\scripts\apply-stage-2.ps1 -Reset`; it dropped/recreated only the `triage` schema, created `triage.tickets`, `triage.events`, `triage.config`, and `triage.feedback`, created required indexes, and seeded seven config keys.
- 2026-07-31: Added 30 synthetic fixture text files and 30 matching expected JSON labels. Ran `python .\scripts\validate-stage-2.py`; it validated all fixtures and confirmed six live-demo fixtures.
- 2026-07-31: Ran `.\scripts\validate-stage-2.ps1`; it verified Docker services, four `triage` tables, eight required indexes, seven config keys, and full fixture corpus coverage.
- 2026-07-31: Added Stage 3 prompt/schema artifacts and `scripts/run-stage-3-harness.py` with `probe`, `classify`, `draft`, and `harness` subcommands. Ran `python -m py_compile scripts\run-stage-3-harness.py scripts\validate-stage-2.py`, `python .\scripts\validate-stage-2.py`, `.\scripts\validate-stage-2.ps1`, and `python .\scripts\run-stage-3-harness.py --help`; all passed.
- 2026-07-31: Ran `python .\scripts\run-stage-3-harness.py probe`; `gpt-5-nano` and `gpt-5.6-luna` both accepted strict Responses API JSON Schema requests with `reasoning: low`. Saved `fixtures/known-good-request.json` without secrets.
- 2026-07-31: Initial `gpt-5-nano` full harness run over 30 fixtures x 3 runs took about 14m47s and failed the production-style gate: 15.6% exact match, 6 under-escalations, 4 over-escalations, and 10 missed safety signals. User revised Stage 3 target to demo-depth happy-flow testing rather than thorough production-style coverage.
- 2026-07-31: Added `harness --live-only`, `--fixture-id`, and `--fixture-slug` selection options. Tightened prompt guidance for tenant urgency vs trivial issues, expanded the deterministic flood rule for "pipe under sink burst" wording, and refined draft lint to avoid false positives on tenant-provided onset dates.
- 2026-07-31: Ran `python .\scripts\run-stage-3-harness.py harness --live-only --runs 1`; it passed the revised demo gate with 6/6 priority matches, 0 under-escalations, 0 over-escalations, 0 missed safety signals, and estimated API cost `$0.003130`. Saved `docs/stage-3-scorecard.md`.

## Outstanding Risks To Recheck During Build

- Current OpenAI model IDs, prices, and accepted API parameters may change; Stage 3 must verify live.
- The accidentally exposed OpenAI API key should be rotated before further work or screen sharing.
- Full-corpus Stage 3 hardening is not demo-blocking but remains weak: the 30-fixture x 3-run nano harness had under-escalations and missed safety signals. Revisit before claiming broad accuracy or moving toward production.
- Gmail App Password availability may not hold for the selected mailbox type.
- Tunnel reliability and URL stability must be verified before Telegram callback testing.
- n8n production hosting has licensing nuance; production should use a client-owned VPS unless n8n confirms another arrangement in writing.
- Email deliverability from demo and production domains must be handled explicitly before showing tenant replies.

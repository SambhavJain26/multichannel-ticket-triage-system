# Repository Guidelines

This repository is the planning and implementation workspace for a local n8n maintenance request triage demo. Treat it as an automation project, not a compiled app. Core behavior will live in n8n workflow exports, Postgres schema/state, fixtures, prompts, and small helper scripts.

## Read Order And Authority

Read these files before changing scope or implementation details:

1. `progress-notes.md` - current status, decisions, deviations, and open items.
2. `build-plan.md` - staged implementation plan to follow across sessions.
3. `maintenance-triage-demo-build-plan.md` - detailed controlling demo spec.
4. `02-maintenance-triage.md` - validated problem and product framing.
5. `foundation-2-maintenance-operations.md` - domain background only.

If documents conflict, prefer the newest explicit decision in `progress-notes.md`, then update stale docs instead of guessing. Current controlling decisions: local-first demo build, VPS/Caddy production-only, `gpt-5-nano` default model, `gpt-5.6-luna` fallback, built-in n8n OpenAI node preferred, HTTP Request only as fallback.

## Project Structure

Current files are documentation-only. Expected implementation directories:

- `workflows/` or `n8n-workflows/` - importable n8n workflow JSON exports.
- `db/postgres/` - schema, migrations, seed SQL, reset SQL.
- `scripts/` - local setup, import, reset, validation, and fixture helpers.
- `fixtures/` - synthetic tenant messages, emails, attachments, and expected outputs.
- `prompts/` - classification and drafting prompts/schemas if kept outside workflows.
- `docs/` - runbooks, demo notes, failure scripts, production caveats.
- `tmp/` and `data/` - generated local artifacts only; keep ignored once created.

Use lowercase hyphenated filenames. Use `snake_case` for database columns and JSON fields unless an external API requires otherwise.

## Local Services And Commands

There is no runnable stack yet. Until scripts exist, use:

- `rg --files` - list repository files.
- `Get-Content -Raw <file>` - read docs/scripts without truncation.
- `Get-Content -Raw <file>.json | ConvertFrom-Json | Out-Null` - validate workflow JSON once exports exist.
- `docker images` - check local images before adding or pulling new ones.
- `docker compose config` - validate Compose once `docker-compose.yml` exists.
- `docker compose ps` - inspect local service status.
- `docker compose logs n8n` - inspect n8n startup/import/runtime failures.

Expected local services after Stage 1: n8n at `http://localhost:5678` and Postgres on `127.0.0.1:5432`. Use a temporary HTTPS tunnel, such as Cloudflare Tunnel or ngrok, only for Telegram callback testing or temporary public board access. Do not provision VPS or Caddy for the demo.

Do not assume Docker images, accounts, API keys, mailbox app passwords, tunnel credentials, Telegram bots, or n8n credentials already exist. Document missing prerequisites before depending on them.

## Architecture Rules

- n8n orchestrates the workflow; Postgres is durable automation state.
- Do not use n8n Data Tables for core state.
- IMAP email intake is the default demo path; form and fixture ingestion feed the same triage core.
- SMTP sends tenant acknowledgments only after explicit human approval.
- Telegram is the manager alert and approval-button channel.
- Use n8n OpenAI node V2 by default for classification and drafting if it supports JSON Schema output, selected model, reasoning settings, raw output, and error behavior.
- Use direct OpenAI API calls in the standalone harness.
- Use HTTP Request for OpenAI workflow calls only if the built-in OpenAI node cannot expose the required contract.
- Do not use n8n AI Agent or LangChain agent loops for triage.
- The product is advisory-only: never dispatch, suppress, auto-close, or auto-reply without a human action.
- Age creates `OVERDUE` board/digest status only. It must not trigger emergency phone alerts.

## n8n Workflow Rules

Prefer editable workflow JSON exports over manual-only UI changes. Name every node descriptively; never leave default names like `Code`, `If`, `Set`, or `HTTP Request`.

Use n8n credentials by name only. Never hardcode OpenAI keys, Telegram tokens, mailbox passwords, bearer tokens, OAuth secrets, or tunnel credentials in workflow JSON. When importing workflows locally, resolve n8n credential IDs from their names at import time; do not hand-edit workflow JSON with IDs or secrets.

Known n8n gotchas to account for:

- Active webhooks may use the active workflow snapshot, not the editor draft.
- Imported Webhook nodes in local n8n `2.29.10` need a fixed top-level `webhookId` when the production URL must be a clean path such as `/webhook/board`; otherwise n8n may register a workflow/node-prefixed path.
- After importing and publishing a new active webhook workflow, restart n8n or otherwise reload active workflows before testing the production `/webhook/...` URL.
- Respond to Webhook `options.responseCode` expressions may not be reliable in local n8n `2.29.10`; prefer separate Respond nodes with literal status codes when 404/200 behavior is important.
- Imported workflow `id` values must fit n8n's database limit of 36 characters. Keep generated IDs short even when workflow names are descriptive.
- Strict IF nodes require expressions that evaluate to booleans. Do not rely on JavaScript truthy strings such as a draft body; wrap them with `Boolean(...)` in Code nodes before routing.
- After import or activation, verify with a real execution, database row, or validation script.
- Code nodes may be sandboxed; do not assume `process.env` exists.
- Optional Postgres update/cleanup nodes need `alwaysOutputData` if downstream nodes must continue after zero rows.
- Postgres nodes that update then reselect rows must return every field later expressions use.
- A Postgres lookup replaces its input item with the query result. When a later route needs trigger fields such as Telegram `text`, `message_id`, or route flags, add a Code node immediately after the lookup to reattach the normalized trigger context before routing or executing a sub-workflow.
- Airtable single- and multi-select fields must omit missing values rather than receive empty strings. Airtable may otherwise attempt to create an empty select option and reject the record write. Keep manager review and vendor approval distinct: `NEEDS_REVIEW`, incomplete, and human-only tickets notify the manager with Hold only and must never expose a vendor-send callback.
- Do not treat the clarification-round count or a provisional `NEEDS_REVIEW` result as a reason to stop a tenant conversation while mapped `missing_info` fields remain. Keep asking deterministic clarification prompts until the request is sufficiently detailed; reserve manager review for human-only/sensitive cases or requests that remain review-only after those fields are resolved.
- Postgres nodes must also preserve control fields such as `test_mode`, `msg_id`, and source outcome when downstream dispatch depends on them. Do not assume n8n will carry pre-query JSON through a Postgres node.
- Execute Sub-workflow nodes may produce no downstream items when the called workflow exits through multiple routed branches. For ingestion connectors, treat the core workflow as a database-writing side effect and reselect tickets by stable identifiers such as `msg_id` before post-processing.
- After an Execute Sub-workflow node, its output may be empty even with `alwaysOutputData`. Preserve a common normalized context node before the call, then reselect durable ticket state using that common node's `msg_id`. Do not reach back to mutually exclusive intake branches with `$("Node Name").all()`: local n8n can surface an unexecuted branch as a non-catchable expression error.
- Publishing a live Gmail IMAP trigger against an inbox with unrelated unread mail can ingest those messages immediately. Use a dedicated mailbox or clear/archive unrelated unread mail before publishing live triggers.
- Form Trigger submissions can render fields as `field-0`; normalize form payloads before SQL or AI steps.
- Imported Form Trigger workflows in local n8n `2.29.10` may register under a workflow/node-prefixed form path rather than the clean configured path. Query `webhook_entity` or test the registered `/form/...` path after import.
- Form Trigger node names must also avoid spaces in local n8n `2.29.10`; a space is persisted as `%20` and then requires `%2520` in the live URL. Use a compact node name such as `TenantIntakeForm` for a usable form path.
- Form Trigger v2.5+ does not use the older `defineForm`/`jsonOutput` shape. Use `formFields: { values: [...] }` with an explicit `fieldName` for each item, then verify the rendered form contains all inputs before testing submission.
- AI structured output may be wrapped under `output`; downstream expressions should handle wrapped and direct JSON shapes.
- Form Trigger workflows should use the Form completion step, not Respond to Webhook.
- One-off `n8n execute` commands can collide with the running task broker on port `5679`. Stop the n8n service before CLI execution and restart it afterward when using this local Compose setup.
- Telegram callback webhooks require a reachable HTTPS tunnel during local testing. Import callback workflows freely, but publish/activate Telegram Trigger workflows only after real chat IDs and `N8N_WEBHOOK_URL` are set.
- Telegram inline keyboard URL buttons require valid public HTTP(S) URLs. For live local Telegram tests, set `triage.config.board.public_base_url` to the current HTTPS tunnel URL before sending real alerts.
- Telegram Trigger node names should avoid spaces in local n8n `2.29.10`; space-bearing trigger names can register webhook paths that do not match Telegram's configured callback path.
- Telegram inline keyboards should be represented as explicit fixed-collection rows/buttons in the Telegram node. Do not pass the whole `inlineKeyboard` object as a single expression; it can send a plain text message with no buttons.
- Airtable's public API can create typed tables and fields but cannot delete or convert an existing table schema. Its schema endpoint also cannot create native `createdTime`/`lastModifiedTime` fields. For the local demo typed-table rebuild, delete only the four known Stage 9 demo tables in Airtable's UI first when replacing text-only tables, then run the guarded bootstrap/replay scripts. The helper resumes an interrupted typed rebuild and writes Postgres-backed `Created At`/`Last Synced` date-time fields instead. Never apply that procedure to a client or production base.
- Telegram `answerQuery` responses do not preserve the upstream approval/context payload. Reattach the approval result before downstream edit-message or audit nodes need chat/message IDs.
- Alert recording must never regress handled tickets. Successful re-alerts can update alert metadata, but `ACKED`, `ACK_SENT`, and `HELD` statuses must not be overwritten back to `ALERTED`.
- Board and detail pages are manager-facing by default. Render model outputs, rule outcomes, and event details in plain language first; keep raw JSON only behind collapsed technical audit controls.
- Repeated live-model rehearsal may expose small `gpt-5-nano` variance on demo boundary cases. Prefer narrow deterministic post-model boundaries for known maintenance semantics, and document every boundary in `progress-notes.md`.

## Testing And Verification

Each stage in `build-plan.md` must be independently verified before moving on. Record completed checks, failures, and deviations in `progress-notes.md`.

The fixture harness is the main safety gate. It must report schema validity, confusion matrix, over-escalations, under-escalations, safety-signal misses, latency, token usage, and cost.

Minimum maintenance fixture scenarios:

- understated gas smell.
- active flood or burst pipe with missing unit.
- tenant-marked urgent but routine issue.
- buried leak detail in a rambling message.
- Spanish maintenance message.
- accommodation/legal-sensitive request with no draft.
- negated safety keyword trap.
- garbage input forcing `NEEDS_REVIEW`.
- prompt injection attempt.
- tenant reply threading.
- auto-responder loop bait.
- voicemail-transcript-shaped text.

`gpt-5-nano` is the default model. Run `gpt-5.6-luna` as fallback if nano misses safety cases, under-escalates too often, has unstable schema output, or produces weak drafts.

## Security And Configuration

Never commit `.env`, n8n credential exports containing secrets, real tenant data, real client emails, API keys, Telegram tokens, mailbox passwords, tunnel credentials, or production workflow exports containing secrets. Keep examples placeholder-only.

Build reset paths for local demo data only. Never run destructive reset/delete scripts against a client mailbox, client database, or production workflow.

Stage 8 clean snapshots are intended for local clean demo state. Data-only dumps of populated threaded tickets can warn on the self-referential ticket foreign key; test restore before relying on any populated snapshot.

Data-only snapshots do not include `triage.ticket_ref_seq`. Any restore that repopulates `triage.tickets` must realign the sequence to the highest restored `MR-xxxx` reference before new ingestion. The core allocator uses `triage.next_ticket_ref()` as a second guard and skips existing references if a local sequence is stale.

## Commit And Completion Guidelines

Use short imperative commits, for example `docs: update triage workflow guidance` or `feat: add fixture harness`.

Before every final response, decide whether the task exposed a durable mistake, blocker, workaround, command, gotcha, or best practice. If yes, update `AGENTS.md` or the relevant plan document first. Use `progress-notes.md` for stage status, deviations, verification results, and outstanding work. For documentation-only planning edits, do not auto-commit unless the user asks.

After every completed task, commit and push the changes to `main`. If push fails because no remote or authentication is configured, report that clearly and include the local commit hash if a commit was created. Do not commit secrets, local data, generated temp output, or n8n credential exports.

Pull requests should summarize the stage affected, verification performed, credential/manual steps, and any deviation from `build-plan.md`.

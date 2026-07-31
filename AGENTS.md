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

Use n8n credentials by name only. Never hardcode OpenAI keys, Telegram tokens, mailbox passwords, bearer tokens, OAuth secrets, or tunnel credentials in workflow JSON.

Known n8n gotchas to account for:

- Active webhooks may use the active workflow snapshot, not the editor draft.
- After import or activation, verify with a real execution, database row, or validation script.
- Code nodes may be sandboxed; do not assume `process.env` exists.
- Optional Postgres update/cleanup nodes need `alwaysOutputData` if downstream nodes must continue after zero rows.
- Postgres nodes that update then reselect rows must return every field later expressions use.
- Form Trigger submissions can render fields as `field-0`; normalize form payloads before SQL or AI steps.
- AI structured output may be wrapped under `output`; downstream expressions should handle wrapped and direct JSON shapes.
- Form Trigger workflows should use the Form completion step, not Respond to Webhook.
- Telegram callback webhooks require a reachable HTTPS tunnel during local testing.

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

## Commit And Completion Guidelines

Use short imperative commits, for example `docs: update triage workflow guidance` or `feat: add fixture harness`.

Before every final response, decide whether the task exposed a durable mistake, blocker, workaround, command, gotcha, or best practice. If yes, update `AGENTS.md` or the relevant plan document first. Use `progress-notes.md` for stage status, deviations, verification results, and outstanding work. For documentation-only planning edits, do not auto-commit unless the user asks.

After every completed task, commit and push the changes to `main`. If push fails because no remote or authentication is configured, report that clearly and include the local commit hash if a commit was created. Do not commit secrets, local data, generated temp output, or n8n credential exports.

Pull requests should summarize the stage affected, verification performed, credential/manual steps, and any deviation from `build-plan.md`.

# Stage 8 Operator Cheat Sheet

## Current Measured Demo Gate

- Model: `gpt-5-nano`
- Harness: six live-demo fixtures, five clean n8n runs
- Priority stability: 30/30 expected priorities across five clean runs
- Real Telegram sends during fixture rehearsal: 0
- Under-escalations: 0
- Over-escalations: 0
- Safety signals missed: 0
- Expected safety overrides: 2 per run
- Roster display and board HTTP 200: passed each run
- Live smoke: Gmail accepted one digest email; operator Telegram heartbeat sent once and immediate repeat was suppressed
- Stage 3 one-run scorecard: average classification-plus-draft latency 10895.3 ms; estimated API cost `$0.003130`

Be explicit: the full 30-fixture hardening run is not production-clean yet. Do not quote broad production accuracy from the six-fixture demo gate.

## What To Say

- Advisory-only: "It does not dispatch vendors, close tickets, or send tenant replies by itself. It sorts and drafts; a human still decides."
- Failure mode: "If the model cannot read something, the request lands as NEEDS_REVIEW. Nothing disappears."
- Safety rules: "Gas/flood/sewage/security-style signals are caught by deterministic rules after the model. That layer is not the AI."
- Competitors: "Property Meld, Latchel and others do versions of this. This demo is the smaller layer that sits on top of the inbox and keeps the human in control."
- Data handling: "For this demo, data stays in local n8n/Postgres plus the configured mailbox/OpenAI calls. Production would run on a client-owned VPS and authenticated client domain."

## What Not To Claim

- Do not claim it creates work orders in a PMS.
- Do not claim it dispatches vendors.
- Do not claim replies are automatic.
- Do not claim it catches every emergency.
- Do not claim legal compliance.
- Do not claim photo interpretation or voicemail transcription in this build.
- Do not claim nobody else does maintenance AI triage.
- Do not claim production-grade uptime from the local demo.

## If It Gets Something Wrong

Say it first:

> "That's wrong, and I'd rather you see it now than in month two. I'm saving it as a test case and I'll follow up with the fix."

Then add the message to the fixture corpus after the call and rerun the harness.

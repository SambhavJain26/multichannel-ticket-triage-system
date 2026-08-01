# Stage 8 Failure Rehearsal Notes

Rehearse these before a live call. The point is not to pretend the demo cannot fail; it is to show that failures are visible and recoverable.

## OpenAI Slow Or Failing

Expected behavior: ticket becomes `NEEDS_REVIEW` instead of disappearing.

Line:

> "That's the failure mode I want. When it can't read something, it says so loudly instead of quietly dropping it."

## Telegram Does Not Deliver

Expected behavior: ticket still exists on the board; alert event records failure if Telegram was attempted.

Line:

> "The alert is the second channel, not the source of truth. The ticket is still on the board."

## Board Link Fails

Expected behavior: check token/tunnel URL; tickets and alerts are still in Postgres/n8n.

Line:

> "The display link is down. The request is still stored, and I can show the execution trace."

## Postgres Or Board Down

Expected behavior: local demo is impaired; do not troubleshoot live for more than 20 seconds.

Line:

> "I'm not going to burn your time debugging live. I have the fallback recording, and I'll send you a live link tonight where you can test it yourself."

## Wrong Classification

Expected behavior: acknowledge the miss, save it as a fixture, follow up.

Line:

> "That's wrong. I want that in the test set because this is exactly how the system gets safer."

## Double Approve

Expected behavior: exactly one tenant email is sent; the second approval returns already handled.

Rehearsal check:

```powershell
.\scripts\validate-stage-6.ps1
```

## Recording Checklist

Record manually after Stage 8 validation passes:

1. Clean board.
2. Fire fixture workflow.
3. Show cards appearing.
4. Open gas ticket detail.
5. Show Telegram alert shape.
6. Show approve path on a controlled test message.
7. Open accommodation request and show no draft.
8. End on the board and the "nothing auto-sends" line.

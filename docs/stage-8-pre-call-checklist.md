# Stage 8 Pre-Call Checklist

Run this five minutes before a prospect call.

1. Restore clean local state:

```powershell
.\scripts\restore-stage-8-demo-snapshot.ps1 -Name clean
```

2. Confirm n8n and Postgres are up:

```powershell
docker compose ps
```

3. Confirm the board opens with the local token and shows an empty state.

4. Confirm the current Cloudflare Tunnel URL is set as `triage.config.board.public_base_url` if using real Telegram buttons.

5. Confirm Telegram alert path with one controlled smoke test, or keep alerts going to your phone and show that path on camera.

6. Confirm the live form URL:

```text
http://localhost:5678/form/mt-form-ingest-stage-7/tenantreportform/report-issue
```

7. Confirm the fallback recording plays offline.

8. Close unrelated inbox/browser tabs. Keep n8n executions, board, Telegram, and this checklist ready.

9. During the call, use fixture-first demo flow unless the prospect asks to type their own issue.

10. After the call, reset local state again if real Gmail/Telegram smoke tests created tickets.

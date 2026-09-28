# Maintenance triage prospect brief

The current reusable brief is [`square-brief-original.html`](square-brief-original.html), styled by [`square-brief-original.css`](square-brief-original.css). Its current PDF is `../output/pdf/maintenance-triage-square-brief-html-recreation.pdf`. These are the only HTML, CSS, and PDF brief versions kept in this workspace.

To personalize it, copy `prospect-data.template.json`, enter verified prospect information, then run from the repository root:

```powershell
node concept-brief/scripts/render-original-html.cjs --data path/to/prospect.json
```

The renderer writes `output/pdf/<slug>-maintenance-triage-brief.pdf` and checks all four square pages for overflow, spacing, alignment, and the meeting link. Running it without `--data` refreshes the reusable placeholder PDF. See [`square-brief-original-notes.md`](square-brief-original-notes.md) for the data fields and limitations. Keep unknown integration routes as placeholders until the prospect confirms them.

Older generated PDFs, HTML versions, and paired CSS were removed from the working tree. They were moved to the Windows Recycle Bin on 2026-09-28; tracked versions also remain recoverable through Git history.

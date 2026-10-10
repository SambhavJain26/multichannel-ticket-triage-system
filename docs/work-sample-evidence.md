# Work sample evidence and verification

## Scope

The public work sample covers the five current main workflows: Tenant Intake,
Triage Engine, Tenant Telegram, Manager Desk and Operations. Demo Tools is an
inactive fixture helper. The application canvases were tidied with n8n's actual
Tidy Up control and the resulting positions were retained in
`workflows/canvas-layouts.json` and the editable exports.

The fresh demonstration on 2026-10-10 used the configured synthetic Demo Tenant,
Maple Court, Unit 2B and synthetic vendor names. OpenAI, Telegram, Airtable and
Gmail were live services through controlled demo accounts. The form ran in test
mode. Approved vendor SMTP delivery went to the controlled demo mailbox, not a
real contractor. The displayed core executions did not use the mock classifier.
Existing operational state was inspected and preserved; no reset was performed.

## Connected executions

| Execution | Observed behavior | Durable or visible output |
| --- | --- | --- |
| 1518 | New conversation prompt after buffer clearing | Telegram received the nonempty prompt |
| 1519 | Vague bathroom opening buffered | Ticket count stayed at six; no manager or Airtable request |
| 1520 / 1521 | Concrete faucet symptom triaged | MR-0007, URGENT / PLUMBING, access permission missing |
| 1522 / 1523 / 1524 | Tenant clarification re-triaged and merged | Original MR-0007 completed; manager vendor draft and button |
| 1526 / 1527 / 1528 | Actual form submitted | MR-0009, ROUTINE / APPLIANCE; receipt and pairing email |
| 1529 | Operator exercised the authorized vendor button | One SENT attempt, actual received Gmail email, tenant provider update, Airtable selected vendor |
| 1533 | Tenant asked when repair would occur | Consolidated factual reply; nine existing ticket rows unchanged; no core or manager call |
| 1534 | Scheduled conversation sync | Two MR-0007 status entries appended and marked synced |
| 1535 / 1536 | Same vendor button pressed again | `already_handled`; five-node stop before SMTP; still one SENT attempt |

Clarification uses an internal child result for re-triage and closes that child
after merging into the original reference. The public journey keeps MR-0007;
it does not assert that clarification creates no internal audit row. MR-0009
remains AWAITING_VENDOR with no selected vendor or vendor dispatch.

## Mirror accuracy

All six visible request references, priorities, sources, trades and conversation
links were compared with Postgres. Unrelated mailbox traffic was excluded.
Four newly appended conversation records had blank Airtable primary labels;
their names were repaired from authoritative message rows. The Operations
builder now supplies the primary Conversation label on every future append.
The fresh scheduled status sync verified that repair without using the obsolete
environment-file Airtable token. The user refreshed the named n8n credential.

## Runtime repairs

- Preserve `message_text` through the Postgres query that clears the preliminary
  conversation buffer. The initial `/new` rehearsal had a Telegram empty-message
  error despite a green workflow execution; the corrected execution delivered
  the prompt successfully.
- Preserve stable Telegram Trigger webhook UUIDs across CLI imports. After
  publication/restart, real callbacks reached the intended tenant and manager
  workflows.
- Apply the actual editor layout to workflow generation. The changes to canvas
  positions did not change workflow connections.

The shared mailbox IMAP intake was left inactive to avoid ingesting unrelated
unread mail. Form evidence used the real manual test execution. Daily notification
and operator heartbeat were disabled in the demonstrated configuration; the
public sample describes them as configured lanes, not delivered outcomes.
The emergency query selects open EMERGENCY requests awaiting vendor handling
and older than fifteen minutes. It does not promote old routine or urgent work.

## PDF review and privacy

- Rebuilt 37 landscape Letter pages using the reference's Geist/Manrope fonts,
  green/ink palette, spacing and footer design.
- Each main workflow has a full canvas and enlarged actual sections. Clipped
  route details were replaced with separate native router/output crops. Drafting
  received its own page. Operations was recaptured clear of editor controls.
- Inspected every page individually at 100 dpi (1100 by 850 pixels). Final
  minor corrections were re-rendered; unchanged pages were compared by pixel
  hash with the reviewed renders.
- Telegram sidebars and unrelated contacts were removed. Form and email contact
  values were flattened out of the source crop. No original private capture is
  embedded in the PDF.
- Structural validation checks geometry, authored text size and bounds, the
  requested footer and page numbers, prohibited text/metadata, annotations,
  attachments, active content and pixel identity of embedded public images.
- Windows OCR recognized text in 43 of 44 sanitized images. The small full
  engine overview was additionally reviewed in enlarged analysis tiles; OCR
  could not recognize that topology view. Readable branch images accompany it.
- No public links, attachments, private contact paths, tokens or raw evidence
  are included. Fixture accuracy from earlier historical mock rehearsals is
  not presented as current live-model accuracy.

Raw screenshots, execution payloads, database backup and review renders remain
in ignored local storage. The tracked public PNG assets are flattened crops.
`prepare-work-sample-images.py`, `build-work-sample.py` and
`validate-work-sample.py` provide the preparation, build and structural checks.
Windows Runtime OCR required Windows PowerShell rather than PowerShell 7 on
this host; its raw results stay in ignored storage.

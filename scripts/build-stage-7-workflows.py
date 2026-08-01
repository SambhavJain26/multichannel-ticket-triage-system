#!/usr/bin/env python3
import json
import pathlib
import textwrap


ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / "workflows"
FIXTURES = ROOT / "fixtures"

CORE_ID = "maintenance-triage-core-stage-4"
ALERT_ID = "mt-alert-dispatch-stage-6"
POST_INGEST_ID = "mt-post-ingest-stage-7"
EMAIL_INGEST_ID = "mt-email-ingest-stage-7"
FORM_INGEST_ID = "mt-form-ingest-stage-7"
FIXTURE_FIRE_ID = "mt-fixture-fire-stage-7"
IMPORT_BRIDGE_ID = "mt-import-bridge-stage-7"


def node(name, node_type, type_version, position, parameters=None, credentials=None):
    data = {
        "parameters": parameters or {},
        "id": name.lower().replace(" ", "-"),
        "name": name,
        "type": node_type,
        "typeVersion": type_version,
        "position": position,
    }
    if credentials:
        data["credentials"] = credentials
    return data


def code_node(name, position, js_code):
    return node(
        name,
        "n8n-nodes-base.code",
        2,
        position,
        {
            "mode": "runOnceForAllItems",
            "language": "javaScript",
            "jsCode": textwrap.dedent(js_code).strip(),
        },
    )


def pg_node(name, position, query, replacements_expr, always_output=False):
    parameters = {
        "resource": "database",
        "operation": "executeQuery",
        "query": textwrap.dedent(query).strip(),
        "options": {"queryReplacement": replacements_expr},
    }
    if always_output:
        parameters["options"]["alwaysOutputData"] = True
    return node(
        name,
        "n8n-nodes-base.postgres",
        2.6,
        position,
        parameters,
        credentials={
            "postgres": {
                "id": "stage1PgLocal",
                "name": "maintenance-triage-postgres-local",
            }
        },
    )


def if_node(name, position, left_expr, right_value=True, operation="true"):
    return node(
        name,
        "n8n-nodes-base.if",
        2.2,
        position,
        {
            "conditions": {
                "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict"},
                "conditions": [
                    {
                        "id": name.lower().replace(" ", "-") + "-condition",
                        "leftValue": left_expr,
                        "rightValue": right_value,
                        "operator": {"type": "boolean", "operation": operation, "singleValue": True},
                    }
                ],
                "combinator": "and",
            },
        },
    )


def execute_workflow_node(name, position, workflow_id, always_output=False):
    data = node(
        name,
        "n8n-nodes-base.executeWorkflow",
        1,
        position,
        {
            "source": "database",
            "workflowId": workflow_id,
            "mode": "each",
            "options": {"waitForSubWorkflow": True},
        },
    )
    if always_output:
        data["alwaysOutputData"] = True
    return data


def read_write_node(name, position):
    data = node(
        name,
        "n8n-nodes-base.readWriteFile",
        1.1,
        position,
        {
            "operation": "write",
            "fileName": "={{ $json.attachment_path }}",
            "dataPropertyName": "data",
            "options": {},
        },
    )
    data["continueOnFail"] = True
    return data


def respond_json_node(name, position, status_code):
    return node(
        name,
        "n8n-nodes-base.respondToWebhook",
        1.5,
        position,
        {
            "respondWith": "json",
            "responseBody": "={{ $json }}",
            "options": {
                "responseCode": status_code,
                "responseHeaders": {
                    "entries": [
                        {"name": "Cache-Control", "value": "no-store"},
                    ]
                },
            },
        },
    )


def workflow_base(workflow_id, name, nodes, connections):
    return {
        "id": workflow_id,
        "name": name,
        "active": False,
        "nodes": nodes,
        "connections": connections,
        "settings": {"executionOrder": "v1"},
        "staticData": None,
        "pinData": {},
        "meta": {"stage": 7, "generatedBy": "scripts/build-stage-7-workflows.py"},
        "versionId": "stage-7-generated",
        "triggerCount": 0,
        "tags": [],
    }


UNIT_MATCH_QUERY = r"""
WITH input_values AS (
  SELECT
    NULLIF($1::text, '')::bigint AS ticket_id,
    NULLIF($2::text, '') AS source_outcome,
    NULLIF($3::text, '') AS msg_id
),
target AS (
  SELECT t.*
  FROM triage.tickets t
  JOIN input_values i ON i.ticket_id = t.id OR (i.ticket_id IS NULL AND i.msg_id IS NOT NULL AND t.msg_id = i.msg_id)
),
norm AS (
  SELECT
    t.*,
    lower(regexp_replace(coalesce(t.unit_identifier, ''), '[^a-zA-Z0-9]+', '', 'g')) AS unit_norm,
    lower(coalesce(t.subject, '') || ' ' || coalesce(t.body_clean, '') || ' ' || coalesce(t.body_raw, '')) AS haystack
  FROM target t
),
exact_matches AS (
  SELECT
    u.*,
    (position(lower(u.property_name) in n.haystack) > 0) AS property_hint
  FROM triage.units u
  CROSS JOIN norm n
  WHERE u.active
    AND n.unit_norm <> ''
    AND lower(regexp_replace(u.unit_label, '[^a-zA-Z0-9]+', '', 'g')) = n.unit_norm
),
selected_exact AS (
  SELECT *
  FROM exact_matches
  WHERE property_hint OR NOT EXISTS (SELECT 1 FROM exact_matches WHERE property_hint)
),
near_match AS (
  SELECT u.*
  FROM triage.units u
  CROSS JOIN norm n
  WHERE u.active
    AND n.unit_norm <> ''
    AND NOT EXISTS (SELECT 1 FROM selected_exact)
  ORDER BY
    CASE
      WHEN regexp_replace(lower(u.unit_label), '[^0-9]+', '', 'g') <> ''
       AND regexp_replace(lower(u.unit_label), '[^0-9]+', '', 'g') = regexp_replace(n.unit_norm, '[^0-9]+', '', 'g')
      THEN 0 ELSE 1
    END,
    abs(length(regexp_replace(lower(u.unit_label), '[^a-zA-Z0-9]+', '', 'g')) - length(n.unit_norm)),
    u.property_name,
    u.unit_label
  LIMIT 1
),
decision AS (
  SELECT
    n.id AS ticket_id,
    CASE
      WHEN n.unit_norm = '' THEN 'NOT_STATED'
      WHEN (SELECT count(*) FROM selected_exact) = 1 THEN 'EXACT'
      WHEN (SELECT count(*) FROM selected_exact) > 1 THEN 'AMBIGUOUS'
      WHEN EXISTS (SELECT 1 FROM near_match) THEN 'NEAR_MISS'
      ELSE 'NOT_FOUND'
    END AS unit_match_status,
    CASE WHEN (SELECT count(*) FROM selected_exact) = 1 THEN (SELECT id FROM selected_exact LIMIT 1) ELSE NULL END AS matched_unit_id,
    CASE
      WHEN n.unit_norm = '' THEN 'UNIT NOT STATED'
      WHEN (SELECT count(*) FROM selected_exact) = 1 THEN (SELECT unit_label || ' - ' || property_name FROM selected_exact LIMIT 1)
      WHEN (SELECT count(*) FROM selected_exact) > 1 THEN coalesce(n.unit_identifier, 'Unit') || ' matches multiple properties'
      WHEN EXISTS (SELECT 1 FROM near_match) THEN coalesce(n.unit_identifier, 'Unit') || ' not found; closest ' || (SELECT unit_label || ' - ' || property_name FROM near_match LIMIT 1)
      ELSE coalesce(n.unit_identifier, 'Unit') || ' not found in roster'
    END AS unit_match_display,
    CASE
      WHEN n.unit_norm = '' THEN 'No unit was stated in the message.'
      WHEN (SELECT count(*) FROM selected_exact) = 1 THEN 'Unit matched the demo roster.'
      WHEN (SELECT count(*) FROM selected_exact) > 1 THEN 'Same unit label exists at more than one property and no clear property hint resolved it.'
      WHEN EXISTS (SELECT 1 FROM near_match) THEN 'No exact roster match; showing the nearest demo unit label.'
      ELSE 'No matching demo unit was found.'
    END AS unit_match_reason
  FROM norm n
),
updated AS (
  UPDATE triage.tickets t
  SET
    unit_match_status = d.unit_match_status,
    matched_unit_id = d.matched_unit_id,
    unit_match_display = d.unit_match_display,
    unit_match_reason = d.unit_match_reason
  FROM decision d
  WHERE t.id = d.ticket_id
  RETURNING t.*
),
event_insert AS (
  INSERT INTO triage.events (ticket_id, actor, action, detail)
  SELECT
    u.id,
    'system',
    'unit_matched',
    jsonb_build_object(
      'status', u.unit_match_status,
      'display', u.unit_match_display,
      'reason', u.unit_match_reason,
      'matched_unit_id', u.matched_unit_id
    )
  FROM updated u
  RETURNING id
)
SELECT
  u.id AS ticket_id,
  u.ref,
  u.priority,
  u.status,
  u.unit_match_status,
  u.unit_match_display,
  (SELECT source_outcome FROM input_values) AS source_outcome,
  ((SELECT source_outcome FROM input_values) = 'created') AS should_dispatch_alert
FROM updated u;
"""


def build_post_ingest():
    prepare_alert_js = r"""
    return $input.all().map((item) => ({
      json: {
        ...item.json,
        test_mode: item.json.test_mode || {}
      }
    }));
    """
    result_js = "return $input.all().map(item => ({ json: item.json }));"
    nodes = [
        node("Post Ingest Input", "n8n-nodes-base.executeWorkflowTrigger", 1.2, [-780, 0], {"inputSource": "passthrough", "returnOutput": "allRuns"}),
        pg_node("Postgres Match Unit Roster", [-540, 0], UNIT_MATCH_QUERY, "={{ [$json.ticket_id || $json.id || '', $json.outcome || 'created', $json.msg_id || ''] }}"),
        code_node("Prepare Alert Dispatch Input", [-300, 0], prepare_alert_js),
        if_node("Should Dispatch Alert", [-60, 0], "={{ Boolean($json.should_dispatch_alert) }}"),
        execute_workflow_node("Execute Alert Dispatch", [180, -100], ALERT_ID),
        code_node("Return Post Ingest Result", [420, 0], result_js),
    ]
    connections = {
        "Post Ingest Input": {"main": [[{"node": "Postgres Match Unit Roster", "type": "main", "index": 0}]]},
        "Postgres Match Unit Roster": {"main": [[{"node": "Prepare Alert Dispatch Input", "type": "main", "index": 0}]]},
        "Prepare Alert Dispatch Input": {"main": [[{"node": "Should Dispatch Alert", "type": "main", "index": 0}]]},
        "Should Dispatch Alert": {
            "main": [
                [{"node": "Execute Alert Dispatch", "type": "main", "index": 0}],
                [{"node": "Return Post Ingest Result", "type": "main", "index": 0}],
            ]
        },
        "Execute Alert Dispatch": {"main": [[{"node": "Return Post Ingest Result", "type": "main", "index": 0}]]},
    }
    return workflow_base(POST_INGEST_ID, "Maintenance Triage Post Ingest", nodes, connections)


def post_ingest_items_js(source_node_name, default_test_mode=None):
    test_mode = json.dumps(default_test_mode) if default_test_mode is not None else "null"
    return f"""
    const defaultTestMode = __DEFAULT_TEST_MODE__;
    const contexts = $("__SOURCE__").all();
    return contexts.map((item) => ({{
      json: {{
        msg_id: item.json.msg_id || "",
        outcome: "created",
        test_mode: item.json.test_mode || defaultTestMode || undefined
      }}
    }}));
    """.replace("__SOURCE__", source_node_name).replace("__DEFAULT_TEST_MODE__", test_mode)


ATTACHMENT_PREP_JS = r"""
function safeName(value, fallback) {
  const raw = String(value || fallback || "attachment.bin");
  const cleaned = raw.replace(/[^a-zA-Z0-9._-]+/g, "-").replace(/^-+|-+$/g, "");
  return (cleaned || "attachment.bin").slice(0, 100);
}
function headerValue(headers, name) {
  if (!headers) return null;
  const lower = name.toLowerCase();
  if (Array.isArray(headers)) {
    const hit = headers.find((h) => String(h.name || "").toLowerCase() === lower);
    return hit?.value || null;
  }
  for (const [key, value] of Object.entries(headers)) {
    if (key.toLowerCase() === lower) return Array.isArray(value) ? value.join(" ") : String(value);
  }
  return null;
}
function firstAddress(value) {
  if (!value) return "";
  if (typeof value === "string") {
    const match = value.match(/<([^>]+)>/);
    return (match ? match[1] : value).trim();
  }
  if (Array.isArray(value.value) && value.value[0]?.address) return value.value[0].address;
  if (value.address) return value.address;
  if (Array.isArray(value) && value[0]) return firstAddress(value[0]);
  return "";
}
function stripHtml(value) {
  return String(value || "")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/\s+/g, " ")
    .trim();
}
function payloadFromEmail(item, index) {
  const j = item.json || {};
  const headers = j.headers || j.headerLines || {};
  const receivedAt = j.date || j.receivedDate || j.internalDate || new Date().toISOString();
  const body = j.text || j.textPlain || j.body || stripHtml(j.html || j.textHtml || j.raw || "");
  const msgId = j.messageId || j.messageID || headerValue(headers, "message-id") || `<email-${Date.now()}-${index}@maintenance-triage.local>`;
  const refs = j.references || headerValue(headers, "references") || "";
  return {
    source: "email",
    from_address: firstAddress(j.from || j.sender || j.replyTo),
    subject: j.subject || "(no subject)",
    body_raw: body || "(empty email body)",
    received_at: receivedAt,
    attachment_paths: [],
    msg_id: msgId,
    in_reply_to: j.inReplyTo || headerValue(headers, "in-reply-to") || null,
    refs,
  };
}
const out = [];
for (const [index, item] of $input.all().entries()) {
  const core_payload = payloadFromEmail(item, index);
  const ingestion_id = `email-${Date.now()}-${index}`;
  const binary = item.binary || {};
  const keys = Object.keys(binary).filter((key) => key.startsWith("attachment_") || key === "data");
  if (keys.length === 0) {
    out.push({ json: { ingestion_id, has_attachment: false, core_payload } });
    continue;
  }
  keys.forEach((key, attachmentIndex) => {
    const meta = binary[key] || {};
    const fileName = safeName(meta.fileName, `attachment-${attachmentIndex}.bin`);
    out.push({
      json: {
        ingestion_id,
        has_attachment: true,
        attachment_path: `/data/attachments/${ingestion_id}-${attachmentIndex}-${fileName}`,
        core_payload,
      },
      binary: { data: meta },
    });
  });
}
return out;
"""


FORM_PREP_JS = r"""
function safeName(value, fallback) {
  const raw = String(value || fallback || "attachment.bin");
  const cleaned = raw.replace(/[^a-zA-Z0-9._-]+/g, "-").replace(/^-+|-+$/g, "");
  return (cleaned || "attachment.bin").slice(0, 100);
}
function field(obj, labels) {
  for (const label of labels) {
    if (obj[label] !== undefined && obj[label] !== null && String(obj[label]).trim() !== "") return String(obj[label]).trim();
  }
  return "";
}
const out = [];
for (const [index, item] of $input.all().entries()) {
  const j = item.json || {};
  const name = field(j, ["Name", "name", "field-0"]);
  const unit = field(j, ["Unit", "unit", "field-1"]);
  const contact = field(j, ["Phone or email", "Contact", "contact", "field-2"]);
  const issue = field(j, ["What's wrong?", "What is wrong?", "Issue", "issue", "field-3"]);
  const entry = field(j, ["Can we enter if you're not home?", "Entry permission", "entry_permission", "field-4"]);
  const core_payload = {
    source: "form",
    from_address: contact || null,
    subject: unit ? `Form report - ${unit}` : "Form report",
    body_raw: [`Tenant: ${name || "Not stated"}`, `Unit: ${unit || "Not stated"}`, `Contact: ${contact || "Not stated"}`, `Entry permission: ${entry || "Not stated"}`, "", issue || "(empty form issue)"].join("\n"),
    received_at: new Date().toISOString(),
    attachment_paths: [],
    msg_id: `<form-${Date.now()}-${index}@maintenance-triage.local>`,
    in_reply_to: null,
    refs: null,
  };
  const ingestion_id = `form-${Date.now()}-${index}`;
  const binary = item.binary || {};
  const keys = Object.keys(binary);
  if (keys.length === 0) {
    out.push({ json: { ingestion_id, has_attachment: false, core_payload } });
    continue;
  }
  keys.forEach((key, attachmentIndex) => {
    const meta = binary[key] || {};
    const fileName = safeName(meta.fileName, `form-photo-${attachmentIndex}.bin`);
    out.push({
      json: {
        ingestion_id,
        has_attachment: true,
        attachment_path: `/data/attachments/${ingestion_id}-${attachmentIndex}-${fileName}`,
        core_payload,
      },
      binary: { data: meta },
    });
  });
}
return out;
"""


BUILD_CORE_PAYLOAD_JS = r"""
const groups = new Map();
for (const item of $input.all()) {
  const j = item.json || {};
  if (!groups.has(j.ingestion_id)) {
    groups.set(j.ingestion_id, { ...j.core_payload, attachment_paths: [] });
  }
  const payload = groups.get(j.ingestion_id);
  const path = j.fileName || j.attachment_path;
  const writeFailed = Boolean(j.error);
  if (j.has_attachment && path && !writeFailed) payload.attachment_paths.push(path);
}
return [...groups.values()].map((json) => ({ json }));
"""


def build_email_ingest():
    nodes = [
        node(
            "Demo Mailbox IMAP Trigger",
            "n8n-nodes-base.emailReadImap",
            2.1,
            [-1040, 0],
            {
                "mailbox": "INBOX",
                "postProcessAction": "read",
                "format": "resolved",
                "dataPropertyAttachmentsPrefixName": "attachment_",
                "options": {"trackLastMessageId": True, "customEmailConfig": '["UNSEEN"]'},
            },
            credentials={"imap": {"id": "stage7DemoImapDomain", "name": "maintenance-triage-demo-imap-domain"}},
        ),
        code_node("Prepare Email Core Payload", [-800, 0], ATTACHMENT_PREP_JS),
        if_node("Has Email Attachment", [-560, 0], "={{ Boolean($json.has_attachment) }}"),
        read_write_node("Write Email Attachment", [-320, -120]),
        code_node("Build Email Core Payload", [-80, 0], BUILD_CORE_PAYLOAD_JS),
        execute_workflow_node("Execute Core Workflow", [180, 0], CORE_ID, always_output=True),
        code_node("Prepare Email Post Ingest Items", [440, 0], post_ingest_items_js("Build Email Core Payload")),
        execute_workflow_node("Execute Post Ingest", [700, 0], POST_INGEST_ID),
    ]
    connections = {
        "Demo Mailbox IMAP Trigger": {"main": [[{"node": "Prepare Email Core Payload", "type": "main", "index": 0}]]},
        "Prepare Email Core Payload": {"main": [[{"node": "Has Email Attachment", "type": "main", "index": 0}]]},
        "Has Email Attachment": {
            "main": [
                [{"node": "Write Email Attachment", "type": "main", "index": 0}],
                [{"node": "Build Email Core Payload", "type": "main", "index": 0}],
            ]
        },
        "Write Email Attachment": {"main": [[{"node": "Build Email Core Payload", "type": "main", "index": 0}]]},
        "Build Email Core Payload": {"main": [[{"node": "Execute Core Workflow", "type": "main", "index": 0}]]},
        "Execute Core Workflow": {"main": [[{"node": "Prepare Email Post Ingest Items", "type": "main", "index": 0}]]},
        "Prepare Email Post Ingest Items": {"main": [[{"node": "Execute Post Ingest", "type": "main", "index": 0}]]},
    }
    return workflow_base(EMAIL_INGEST_ID, "Maintenance Triage Email Ingest", nodes, connections)


def build_form_ingest():
    form_fields = [
        {"fieldLabel": "Name", "requiredField": True},
        {"fieldLabel": "Unit", "requiredField": False},
        {"fieldLabel": "Phone or email", "fieldType": "email", "requiredField": True},
        {"fieldLabel": "What's wrong?", "fieldType": "textarea", "requiredField": True},
        {
            "fieldLabel": "Can we enter if you're not home?",
            "fieldType": "dropdown",
            "fieldOptions": {"values": [{"option": "Yes"}, {"option": "No"}, {"option": "Call first"}]},
            "requiredField": False,
        },
        {"fieldLabel": "Photo", "fieldType": "file", "multipleFiles": True, "acceptFileTypes": ".jpg,.jpeg,.png,.webp,.heic"},
    ]
    nodes = [
        node(
            "TenantReportForm",
            "n8n-nodes-base.formTrigger",
            2.6,
            [-1120, 0],
            {
                "authentication": "none",
                "formTitle": "Report a Maintenance Issue",
                "formDescription": "Submit a maintenance issue for demo triage.",
                "defineForm": "json",
                "jsonOutput": json.dumps(form_fields),
                "responseMode": "lastNode",
                "options": {"path": "report-issue", "buttonLabel": "Submit"},
            },
        ),
        code_node("Prepare Form Core Payload", [-880, 0], FORM_PREP_JS),
        if_node("Has Form Attachment", [-640, 0], "={{ Boolean($json.has_attachment) }}"),
        read_write_node("Write Form Attachment", [-400, -120]),
        code_node("Build Form Core Payload", [-160, 0], BUILD_CORE_PAYLOAD_JS),
        execute_workflow_node("Execute Core Workflow", [100, 0], CORE_ID, always_output=True),
        code_node("Prepare Form Post Ingest Items", [360, 0], post_ingest_items_js("Build Form Core Payload")),
        execute_workflow_node("Execute Post Ingest", [620, 0], POST_INGEST_ID),
        node(
            "Show Reference Completion",
            "n8n-nodes-base.form",
            2.5,
            [880, 0],
            {
                "operation": "completion",
                "respondWith": "text",
                "completionTitle": "Request received",
                "completionMessage": "={{ 'Reference: ' + ($json.ref || 'pending review') }}",
                "options": {"formTitle": "Maintenance request"},
            },
        ),
    ]
    connections = {
        "TenantReportForm": {"main": [[{"node": "Prepare Form Core Payload", "type": "main", "index": 0}]]},
        "Prepare Form Core Payload": {"main": [[{"node": "Has Form Attachment", "type": "main", "index": 0}]]},
        "Has Form Attachment": {
            "main": [
                [{"node": "Write Form Attachment", "type": "main", "index": 0}],
                [{"node": "Build Form Core Payload", "type": "main", "index": 0}],
            ]
        },
        "Write Form Attachment": {"main": [[{"node": "Build Form Core Payload", "type": "main", "index": 0}]]},
        "Build Form Core Payload": {"main": [[{"node": "Execute Core Workflow", "type": "main", "index": 0}]]},
        "Execute Core Workflow": {"main": [[{"node": "Prepare Form Post Ingest Items", "type": "main", "index": 0}]]},
        "Prepare Form Post Ingest Items": {"main": [[{"node": "Execute Post Ingest", "type": "main", "index": 0}]]},
        "Execute Post Ingest": {"main": [[{"node": "Show Reference Completion", "type": "main", "index": 0}]]},
    }
    return workflow_base(FORM_INGEST_ID, "Maintenance Triage Form Ingest", nodes, connections)


def fixture_payload(stem: str, offset_minutes: int) -> dict:
    text = (FIXTURES / f"{stem}.txt").read_text(encoding="utf-8").strip()
    return {
        "source": "fixture",
        "from_address": f"{stem}@fixture.example",
        "subject": stem,
        "body_raw": text,
        "received_at": f"2026-08-01T12:{offset_minutes:02d}:00Z",
        "attachment_paths": [],
        "msg_id": f"<stage7-{stem}@fixture.example>",
        "in_reply_to": None,
        "refs": None,
    }


def build_fixture_fire():
    live_stems = [
        "01-understated-gas",
        "02-panicked-burst-pipe-no-unit",
        "03-urgent-squeaky-door",
        "04-buried-lede",
        "05-spanish-no-hot-water",
        "06-accommodation-request",
    ]
    cases = [fixture_payload(stem, i * 2) for i, stem in enumerate(live_stems)]
    load_js = f"return {json.dumps([{'json': c} for c in cases], indent=2)};"
    nodes = [
        node("Manual Start", "n8n-nodes-base.manualTrigger", 1, [-720, 0]),
        code_node("Load Stage 7 Demo Fixtures", [-480, 0], load_js),
        node("Demo Stagger", "n8n-nodes-base.wait", 1.1, [-240, 0], {"amount": 2, "unit": "seconds"}),
        execute_workflow_node("Execute Core Workflow", [20, 0], CORE_ID, always_output=True),
        code_node("Prepare Fixture Post Ingest Items", [280, 0], post_ingest_items_js("Load Stage 7 Demo Fixtures", {"mock_telegram": True, "force_business_hours": True})),
        execute_workflow_node("Execute Post Ingest", [540, 0], POST_INGEST_ID),
    ]
    connections = {
        "Manual Start": {"main": [[{"node": "Load Stage 7 Demo Fixtures", "type": "main", "index": 0}]]},
        "Load Stage 7 Demo Fixtures": {"main": [[{"node": "Demo Stagger", "type": "main", "index": 0}]]},
        "Demo Stagger": {"main": [[{"node": "Execute Core Workflow", "type": "main", "index": 0}]]},
        "Execute Core Workflow": {"main": [[{"node": "Prepare Fixture Post Ingest Items", "type": "main", "index": 0}]]},
        "Prepare Fixture Post Ingest Items": {"main": [[{"node": "Execute Post Ingest", "type": "main", "index": 0}]]},
    }
    return workflow_base(FIXTURE_FIRE_ID, "Maintenance Triage Fixture Fire", nodes, connections)


def build_import_bridge():
    validate_query = r"""
    WITH cfg AS (
      SELECT coalesce((SELECT value FROM triage.config WHERE key = 'ingestion'), '{}'::jsonb) AS ingestion
    )
    SELECT
      coalesce(NULLIF($1::text, '') = ingestion->>'import_token', false) AS authorized,
      NULLIF($2::text, '')::jsonb AS payload
    FROM cfg;
    """
    normalize_js = r"""
    const out = [];
    for (const item of $input.all()) {
      const payload = typeof item.json.payload === "string" ? JSON.parse(item.json.payload) : item.json.payload;
      out.push({
        json: {
          source: "import",
          from_address: payload.from_address || null,
          subject: payload.subject || "(no subject)",
          body_raw: payload.body_raw || "(empty imported message)",
          received_at: payload.received_at || new Date().toISOString(),
          attachment_paths: Array.isArray(payload.attachment_paths) ? payload.attachment_paths : [],
          msg_id: payload.msg_id || `<import-${Date.now()}@maintenance-triage.local>`,
          in_reply_to: payload.in_reply_to || null,
          refs: payload.refs || null,
          import_batch_id: payload.import_batch_id || null,
          import_item_id: payload.import_item_id || null,
          test_mode: payload.test_mode || { mock_telegram: true, force_business_hours: true },
        }
      });
    }
    return out;
    """
    attach_response_js = r"""
    return $input.all().map((item) => ({
      json: {
        ok: true,
        ticket_id: item.json.ticket_id || item.json.id || null,
        ref: item.json.ref || null,
        priority: item.json.priority || null,
        outcome: item.json.outcome || item.json.source_outcome || null,
      }
    }));
    """
    unauthorized_js = "return [{ json: { ok: false, error: 'not_found' } }];"
    nodes = [
        node(
            "Batch Import Webhook",
            "n8n-nodes-base.webhook",
            2,
            [-980, 0],
            {"path": "stage-7-import", "httpMethod": "POST", "responseMode": "responseNode", "options": {}},
        ),
        pg_node("Postgres Validate Import Token", [-740, 0], validate_query, "={{ [$json.headers?.['x-import-token'] || $json.query?.t || '', JSON.stringify($json.body || $json)] }}"),
        if_node("Is Authorized Import", [-500, 0], "={{ Boolean($json.authorized) }}"),
        code_node("Normalize Import Payload", [-260, -100], normalize_js),
        execute_workflow_node("Execute Core Workflow", [0, -100], CORE_ID, always_output=True),
        code_node("Prepare Import Post Ingest Items", [260, -100], post_ingest_items_js("Normalize Import Payload")),
        execute_workflow_node("Execute Post Ingest", [520, -100], POST_INGEST_ID),
        code_node("Prepare Import Response", [780, -100], attach_response_js),
        respond_json_node("Respond Import OK", [1040, -100], 200),
        code_node("Prepare Import Not Found", [-260, 140], unauthorized_js),
        respond_json_node("Respond Import Not Found", [0, 140], 404),
    ]
    nodes[0]["webhookId"] = "stage-7-import"
    connections = {
        "Batch Import Webhook": {"main": [[{"node": "Postgres Validate Import Token", "type": "main", "index": 0}]]},
        "Postgres Validate Import Token": {"main": [[{"node": "Is Authorized Import", "type": "main", "index": 0}]]},
        "Is Authorized Import": {
            "main": [
                [{"node": "Normalize Import Payload", "type": "main", "index": 0}],
                [{"node": "Prepare Import Not Found", "type": "main", "index": 0}],
            ]
        },
        "Normalize Import Payload": {"main": [[{"node": "Execute Core Workflow", "type": "main", "index": 0}]]},
        "Execute Core Workflow": {"main": [[{"node": "Prepare Import Post Ingest Items", "type": "main", "index": 0}]]},
        "Prepare Import Post Ingest Items": {"main": [[{"node": "Execute Post Ingest", "type": "main", "index": 0}]]},
        "Execute Post Ingest": {"main": [[{"node": "Prepare Import Response", "type": "main", "index": 0}]]},
        "Prepare Import Response": {"main": [[{"node": "Respond Import OK", "type": "main", "index": 0}]]},
        "Prepare Import Not Found": {"main": [[{"node": "Respond Import Not Found", "type": "main", "index": 0}]]},
    }
    return workflow_base(IMPORT_BRIDGE_ID, "Maintenance Triage Import Bridge", nodes, connections)


def main():
    WORKFLOWS.mkdir(exist_ok=True)
    workflows = [
        ("maintenance-triage-post-ingest.json", build_post_ingest()),
        ("maintenance-triage-email-ingest.json", build_email_ingest()),
        ("maintenance-triage-form-ingest.json", build_form_ingest()),
        ("maintenance-triage-fixture-fire.json", build_fixture_fire()),
        ("maintenance-triage-import-bridge.json", build_import_bridge()),
    ]
    for filename, workflow in workflows:
        path = WORKFLOWS / filename
        path.write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()

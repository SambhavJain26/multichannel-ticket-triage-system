#!/usr/bin/env python3
import json
import pathlib
import textwrap


ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / "workflows"
FIXTURES = ROOT / "fixtures"

ENGINE_ID = "maintenance-triage-core-stage-4"
INTAKE_ID = "mt-tenant-intake-stage-9"
TENANT_ID = "mt-tenant-telegram-stage-9"
MANAGER_ID = "mt-manager-desk-stage-9"
OPS_ID = "mt-operations-stage-9"
TOOLS_ID = "mt-demo-tools-stage-9"


def node(name, node_type, type_version, position, parameters=None, credentials=None):
    value = {
        "parameters": parameters or {},
        "id": name.lower().replace(" ", "-"),
        "name": name,
        "type": node_type,
        "typeVersion": type_version,
        "position": position,
    }
    if credentials:
        value["credentials"] = credentials
    return value


def code(name, position, js):
    return node(name, "n8n-nodes-base.code", 2, position, {
        "mode": "runOnceForAllItems", "language": "javaScript", "jsCode": textwrap.dedent(js).strip()
    })


def pg(name, position, query, replacements="={{ [] }}", always_output=False):
    result = node(name, "n8n-nodes-base.postgres", 2.6, position, {
        "resource": "database", "operation": "executeQuery", "query": textwrap.dedent(query).strip(),
        "options": {"queryReplacement": replacements},
    }, {"postgres": {"id": "stage1PgLocal", "name": "maintenance-triage-postgres-local"}})
    if always_output:
        result["alwaysOutputData"] = True
    return result


def if_node(name, position, expression):
    return node(name, "n8n-nodes-base.if", 2.2, position, {
        "conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict"}, "conditions": [{
            "id": name.lower().replace(" ", "-") + "-condition", "leftValue": expression, "rightValue": True,
            "operator": {"type": "boolean", "operation": "true", "singleValue": True},
        }], "combinator": "and"}
    })


def switch(name, position, values):
    return node(name, "n8n-nodes-base.switch", 3.2, position, {
        "mode": "rules", "rules": {"values": [{"conditions": {"conditions": [{
            "leftValue": "={{ $json.route }}", "rightValue": value,
            "operator": {"type": "string", "operation": "equals"},
        }], "combinator": "and"}} for value in values]}, "options": {}
    })


def execute(name, position, workflow_id, always_output=False):
    result = node(name, "n8n-nodes-base.executeWorkflow", 1, position, {
        "source": "database", "workflowId": workflow_id, "mode": "each", "options": {"waitForSubWorkflow": True},
    })
    if always_output:
        result["alwaysOutputData"] = True
    return result


def email(name, position):
    result = node(name, "n8n-nodes-base.emailSend", 2.1, position, {
        "fromEmail": "={{ $json.from_email }}", "toEmail": "={{ $json.to_email }}",
        "subject": "={{ $json.email_subject }}", "emailFormat": "text", "text": "={{ $json.email_body }}",
        "options": {"appendAttribution": False, "replyTo": "={{ $json.from_email }}"},
    }, {"smtp": {"id": "stage7DemoSmtpDomain", "name": "maintenance-triage-demo-smtp-domain"}})
    result["continueOnFail"] = True
    return result


def telegram(name, position, credential, vendor_button_count=None):
    params = {
        "resource": "message", "operation": "sendMessage", "chatId": "={{ $json.chat_id }}",
        "text": "={{ $json.message_text }}",
        "additionalFields": {"appendAttribution": False, "disable_web_page_preview": True, "parse_mode": "HTML"},
    }
    if vendor_button_count is not None:
        params["replyMarkup"] = "inlineKeyboard"
        rows = []
        for index in range(vendor_button_count):
            rows.append({"row": {"buttons": [{
                "text": f"={{{{ $json.vendor_{index + 1}_label }}}}",
                "additionalFields": {"callback_data": f"={{{{ $json.vendor_{index + 1}_callback }}}}"},
            }]}})
        rows.append({"row": {"buttons": [{
            "text": "Hold", "additionalFields": {"callback_data": "={{ 'vendor:' + $json.ticket_id + ':hold' }}"}
        }]}})
        params["inlineKeyboard"] = {"rows": rows}
    result = node(name, "n8n-nodes-base.telegram", 1.2, position, params, {"telegramApi": credential})
    result["continueOnFail"] = True
    return result


def airtable(name, position, method, url, body=""):
    params = {
        "method": method, "url": url, "authentication": "predefinedCredentialType", "nodeCredentialType": "airtableTokenApi",
        "options": {"response": {"response": {"fullResponse": True, "neverError": True, "responseFormat": "json"}}},
    }
    if body:
        params.update({"sendBody": True, "contentType": "json", "specifyBody": "json", "jsonBody": body})
    result = node(name, "n8n-nodes-base.httpRequest", 4.4, position, params,
                  {"airtableTokenApi": {"id": "stage9Airtable", "name": "maintenance-triage-airtable"}})
    result["continueOnFail"] = True
    return result


def workflow(workflow_id, name, nodes, connections):
    return {
        "id": workflow_id, "name": name, "active": False, "nodes": nodes, "connections": connections,
        "settings": {"executionOrder": "v1"}, "staticData": None, "pinData": {},
        "meta": {"stage": 9, "generatedBy": "scripts/build-stage-9-workflows.py"},
        "versionId": "stage-9-generated", "triggerCount": 0, "tags": [],
    }


EMAIL_NORMALIZE = r"""
function header(headers, name) {
  const lower = name.toLowerCase();
  for (const [key, value] of Object.entries(headers || {})) if (key.toLowerCase() === lower) return Array.isArray(value) ? value.join(" ") : String(value);
  return "";
}
function address(value) {
  const raw = String(value || ""); const match = raw.match(/<([^>]+)>/); return (match ? match[1] : raw).trim();
}
return $input.all().flatMap((item, index) => {
  const j = item.json || {}; const subject = String(j.subject || "(no subject)");
  if (/^\[MT-SYSTEM\]/i.test(subject)) return [];
  const body = j.text || j.textPlain || j.body || j.html || "(empty email body)";
  return [{json: {source: "email", from_address: address(j.from || j.sender || j.replyTo), subject, body_raw: body,
    received_at: j.date || new Date().toISOString(), attachment_paths: [],
    msg_id: j.messageId || header(j.headers, "message-id") || `<email-${Date.now()}-${index}@maintenance-triage.local>`,
    in_reply_to: j.inReplyTo || header(j.headers, "in-reply-to") || null, refs: j.references || header(j.headers, "references") || null}}];
});
"""


FORM_NORMALIZE = r"""
function field(j, names) { for (const name of names) if (j[name] !== undefined && String(j[name]).trim()) return String(j[name]).trim(); return ""; }
return $input.all().map((item, index) => {
  const j = item.json || {}; const name = field(j, ["Name", "name", "field-0"]); const unit = field(j, ["Unit", "unit", "field-1"]);
  const property = field(j, ["Property", "property", "field-2"]); const email = field(j, ["Email", "email", "field-3"]); const issue = field(j, ["What's wrong?", "Issue", "issue", "field-4"]);
  const entry = field(j, ["Can we enter if you're not home?", "entry_permission", "field-5"]);
  return {json: {source: "form", from_address: email, subject: unit ? `Form report - ${unit}` : "Form report",
    body_raw: [`Tenant: ${name || "Not stated"}`, `Property: ${property || "Not stated"}`, `Unit: ${unit || "Not stated"}`, `Contact: ${email}`, `Entry permission: ${entry || "Not stated"}`, "", issue || "(empty form issue)"].join("\n"),
    received_at: new Date().toISOString(), attachment_paths: [], msg_id: `<form-${Date.now()}-${index}@maintenance-triage.local>`, in_reply_to: null, refs: null}};
});
"""


def build_intake():
    pairing_query = r"""
WITH input_values AS (SELECT NULLIF($1::text, '') AS msg_id, NULLIF($2::text, '') AS source),
ticket AS (
  SELECT t.* FROM triage.tickets t, input_values i WHERE t.msg_id = i.msg_id AND t.source = i.source ORDER BY t.id DESC LIMIT 1
), pair AS (
  INSERT INTO triage.tenant_pairing_tokens (ticket_id, tenant_email)
  SELECT id, coalesce(from_address, tenant_contact) FROM ticket
  WHERE coalesce(from_address, tenant_contact) IS NOT NULL
  RETURNING ticket_id, token, expires_at
)
SELECT t.id AS ticket_id, t.ref, t.source, t.from_address, t.priority, t.missing_info, t.human_only,
       p.token, p.expires_at, cfg.value AS tenant_telegram, mail.value AS system_mail
FROM ticket t LEFT JOIN pair p ON p.ticket_id = t.id
CROSS JOIN (SELECT value FROM triage.config WHERE key = 'tenant_telegram') cfg
CROSS JOIN (SELECT value FROM triage.config WHERE key = 'system_mail') mail;
"""
    prepare_email = r"""
function json(value, fallback) { try { return typeof value === "string" ? JSON.parse(value) : (value || fallback); } catch (_) { return fallback; } }
return $input.all().map((item) => {
  const j = item.json; const bot = json(j.tenant_telegram, {}); const mail = json(j.system_mail, {}); const username = String(bot.bot_username || "");
  const link = username && !username.startsWith("PLACEHOLDER") && j.token ? `https://t.me/${username}?start=${j.token}` : "";
  return {json: {...j, should_send: Boolean(j.from_address && link), chat_link: link,
    from_email: "Demo Maintenance Desk <sambhavn8n@gmail.com>", to_email: j.from_address,
    email_subject: mail.onboarding_subject || "[MT-SYSTEM] Continue your maintenance request in Telegram",
    email_body: `Your maintenance request ${j.ref} was received. Continue updates in Telegram: ${link}\n\nThis link is for the demo and expires ${j.expires_at || "soon"}.`}};
});
"""
    record_onboarding = r"""
INSERT INTO triage.ticket_messages (ticket_id, channel, direction, intent, body, external_message_id, delivery_state, detail)
VALUES ($1::bigint, 'email', 'outbound', 'pairing', $2::text, NULLIF($3::text, ''), CASE WHEN NULLIF($4::text, '') IS NULL THEN 'SENT' ELSE 'FAILED' END, jsonb_build_object('link', $5::text))
RETURNING ticket_id;
"""
    nodes = [
        node("Demo Mailbox IMAP Trigger", "n8n-nodes-base.emailReadImap", 2.1, [-1000, -180], {"mailbox": "INBOX", "postProcessAction": "read", "format": "resolved", "options": {"trackLastMessageId": True, "customEmailConfig": '["UNSEEN"]'}}, {"imap": {"id": "stage7DemoImapDomain", "name": "maintenance-triage-demo-imap-domain"}}),
        node("TenantIntakeForm", "n8n-nodes-base.formTrigger", 2.6, [-1000, 180], {"authentication": "none", "formTitle": "Report a Maintenance Issue", "formDescription": "You will receive a Telegram link for updates.", "formFields": {"values": [{"fieldName":"name","fieldLabel":"Name","fieldType":"text","requiredField":True},{"fieldName":"unit","fieldLabel":"Unit","fieldType":"text","requiredField":False},{"fieldName":"property","fieldLabel":"Property","fieldType":"dropdown","fieldOptions":{"values":[{"option":"Maple Court"},{"option":"Oak Terrace"},{"option":"Pine House"}]},"requiredField":True},{"fieldName":"email","fieldLabel":"Email","fieldType":"email","requiredField":True},{"fieldName":"issue","fieldLabel":"What's wrong?","fieldType":"textarea","requiredField":True},{"fieldName":"entry_permission","fieldLabel":"Can we enter if you're not home?","fieldType":"dropdown","fieldOptions":{"values":[{"option":"Yes"},{"option":"No"},{"option":"Call first"}]},"requiredField":False}]}, "responseMode": "lastNode", "options": {"path": "report-issue", "buttonLabel": "Submit"}}),
        code("Normalize Email Intake", [-760, -180], EMAIL_NORMALIZE), code("Normalize Form Intake", [-760, 180], FORM_NORMALIZE),
        code("Preserve Intake Context", [-520, 0], """return $input.all().map(item => ({json: item.json}));"""),
        execute("Execute Triage Engine", [-300, 0], ENGINE_ID, True),
        code("Prepare Pairing Lookup", [-60, 0], """return $(\"Preserve Intake Context\").all().map(item => ({json: {msg_id: item.json.msg_id, source: item.json.source}}));"""),
        pg("Postgres Create Pairing Token", [-20, 0], pairing_query, "={{ [$json.msg_id, $json.source] }}"),
        execute("Execute Manager Desk", [220, -140], MANAGER_ID),
        code("Prepare Onboarding Email", [220, 80], prepare_email), if_node("Should Send Onboarding Email", [460, 80], "={{ Boolean($json.should_send) }}"),
        email("SMTP Send Telegram Onboarding", [700, -20]),
        code("Attach Onboarding Result", [920, -20], """const ctx = $(\"Prepare Onboarding Email\").all().filter(i => i.json.should_send); return $input.all().map((item, i) => ({json: {...ctx[i].json, email_error: item.json.error || \"\", message_id: item.json.messageId || item.json.message_id || \"\"}}));"""),
        pg("Postgres Record Onboarding Email", [1140, -20], record_onboarding, "={{ [$json.ticket_id, $json.email_body, $json.message_id || '', $json.email_error || '', $json.chat_link] }}"),
        node("Show Form Completion", "n8n-nodes-base.form", 2.5, [1360, 140], {"operation": "completion", "respondWith": "text", "completionTitle": "Request received", "completionMessage": "={{ 'Check your email for the Telegram link to continue request ' + ($json.ref || '') }}", "options": {"formTitle": "Maintenance request"}}),
    ]
    connections = {
        "Demo Mailbox IMAP Trigger": {"main": [[{"node":"Normalize Email Intake","type":"main","index":0}]]},
        "TenantIntakeForm": {"main": [[{"node":"Normalize Form Intake","type":"main","index":0}]]},
        "Normalize Email Intake": {"main": [[{"node":"Preserve Intake Context","type":"main","index":0}]]},
        "Normalize Form Intake": {"main": [[{"node":"Preserve Intake Context","type":"main","index":0}]]},
        "Preserve Intake Context": {"main": [[{"node":"Execute Triage Engine","type":"main","index":0}]]},
        "Execute Triage Engine": {"main": [[{"node":"Prepare Pairing Lookup","type":"main","index":0}]]},
        "Prepare Pairing Lookup": {"main": [[{"node":"Postgres Create Pairing Token","type":"main","index":0}]]},
        "Postgres Create Pairing Token": {"main": [[{"node":"Execute Manager Desk","type":"main","index":0},{"node":"Prepare Onboarding Email","type":"main","index":0}]]},
        "Prepare Onboarding Email": {"main": [[{"node":"Should Send Onboarding Email","type":"main","index":0}]]},
        "Should Send Onboarding Email": {"main": [[{"node":"SMTP Send Telegram Onboarding","type":"main","index":0}], [{"node":"Show Form Completion","type":"main","index":0}]]},
        "SMTP Send Telegram Onboarding": {"main": [[{"node":"Attach Onboarding Result","type":"main","index":0}]]},
        "Attach Onboarding Result": {"main": [[{"node":"Postgres Record Onboarding Email","type":"main","index":0}]]},
        "Postgres Record Onboarding Email": {"main": [[{"node":"Show Form Completion","type":"main","index":0}]]},
    }
    return workflow(INTAKE_ID, "Maintenance Tenant Intake", nodes, connections)


def build_tenant_telegram():
    record_telegram_delivery = r"""
INSERT INTO triage.ticket_messages (ticket_id, channel, direction, intent, body, external_message_id, delivery_state, detail)
VALUES ($1::bigint, 'telegram', 'outbound', $2::text, $3::text, NULLIF($4::text, ''), CASE WHEN NULLIF($5::text, '') IS NULL THEN 'SENT' ELSE 'FAILED' END, jsonb_build_object('error', NULLIF($5::text, '')))
ON CONFLICT (channel, direction, external_message_id) DO UPDATE SET delivery_state = EXCLUDED.delivery_state, detail = EXCLUDED.detail
RETURNING id;
"""
    claim_pair = r"""
WITH input_values AS (SELECT $1::text AS token, $2::text AS chat_id, NULLIF($3::text, '') AS user_id, NULLIF($4::text, '') AS username),
claimed AS (
  UPDATE triage.tenant_pairing_tokens p SET consumed_at = now(), consumed_chat_id = i.chat_id
  FROM input_values i WHERE p.token = i.token AND p.consumed_at IS NULL AND p.expires_at > now() RETURNING p.ticket_id, p.tenant_email
), chat AS (
  INSERT INTO triage.tenant_chats (telegram_chat_id, telegram_user_id, telegram_username, tenant_email, active_ticket_id)
  SELECT i.chat_id, i.user_id, i.username, c.tenant_email, c.ticket_id FROM claimed c CROSS JOIN input_values i
  ON CONFLICT (telegram_chat_id) DO UPDATE SET active_ticket_id = EXCLUDED.active_ticket_id, tenant_email = EXCLUDED.tenant_email, updated_at = now()
  RETURNING *
)
UPDATE triage.tickets t SET tenant_chat_id = c.telegram_chat_id FROM chat c WHERE t.id = c.active_ticket_id
RETURNING t.id AS ticket_id, t.ref, t.priority, t.missing_info, t.human_only, t.vendor_status, c.telegram_chat_id AS chat_id;
"""
    load_chat = r"""
SELECT c.telegram_chat_id AS chat_id, c.active_ticket_id, to_jsonb(t) AS ticket
FROM triage.tenant_chats c LEFT JOIN triage.tickets t ON t.id = c.active_ticket_id
WHERE c.telegram_chat_id = $1::text;
"""
    new_ticket = r"""
WITH input_values AS (SELECT $1::text AS chat_id, $2::text AS msg_id), ticket AS (
  SELECT * FROM triage.tickets WHERE msg_id = (SELECT msg_id FROM input_values) ORDER BY id DESC LIMIT 1
), upsert_chat AS (
  INSERT INTO triage.tenant_chats (telegram_chat_id, active_ticket_id) SELECT chat_id, id FROM input_values CROSS JOIN ticket
  ON CONFLICT (telegram_chat_id) DO UPDATE SET active_ticket_id = EXCLUDED.active_ticket_id, updated_at = now() RETURNING *
), linked AS (UPDATE triage.tickets SET tenant_chat_id = (SELECT telegram_chat_id FROM upsert_chat) WHERE id = (SELECT id FROM ticket) RETURNING *)
INSERT INTO triage.ticket_messages (ticket_id, channel, direction, intent, body, external_message_id, delivery_state)
SELECT id, 'telegram', 'inbound', 'request', body_clean, msg_id, 'RECORDED' FROM linked
ON CONFLICT (channel, direction, external_message_id) DO NOTHING
RETURNING ticket_id, (SELECT ref FROM linked) AS ref, (SELECT priority FROM linked) AS priority, (SELECT missing_info FROM linked) AS missing_info, (SELECT human_only FROM linked) AS human_only, (SELECT vendor_status FROM linked) AS vendor_status, (SELECT tenant_chat_id FROM linked) AS chat_id;
"""
    start_message = r"""
function parse(v, fallback) { try { return typeof v === "string" ? JSON.parse(v) : (v || fallback); } catch (_) { return fallback; } }
function questions(missing) { const q = {UNIT:"Which unit and property is this for?", PROPERTY:"Which property is this at?", CONTACT:"What is the best contact number?", ACCESS_PERMISSION:"Can maintenance enter if you are away?", ISSUE_DETAIL:"Please describe what is happening, where it is happening, and whether it is getting worse.", ONSET_TIME:"When did this start?"}; return (parse(missing, []) || []).filter(x => q[x]).slice(0,3).map(x => q[x]); }
return $input.all().map((item) => { const j = item.json; const qs = questions(j.missing_info); const text = j.human_only ? `Request ${j.ref} was received. A manager needs to review it and will update you here.` : (qs.length ? `Request ${j.ref} was received. ${qs.join(" ")}` : `Request ${j.ref} was received. We will keep you updated here.`); return {json: {...j, message_text: text, intent: qs.length ? "clarification" : "receipt"}}; });
"""
    status_message = r"""
return $input.all().map(item => { const j = item.json; const t = typeof j.ticket === "string" ? JSON.parse(j.ticket) : j.ticket; const sent = t?.vendor_status === "SENT"; return {json: {chat_id: j.chat_id, ticket_id: t?.id, intent: "status", message_text: sent ? "We have contacted a maintenance provider. We will update you when we have an arrival time." : "Your request has been escalated to the manager. We will update you here when there is more information."}}; });
"""
    merge_clarification = r"""
WITH input_values AS (SELECT $1::bigint AS original_ticket_id, NULLIF($2::text, '') AS child_msg_id, $3::text AS chat_id, $4::text AS body, $5::text AS external_message_id),
child AS (SELECT * FROM triage.tickets WHERE msg_id = (SELECT child_msg_id FROM input_values) ORDER BY id DESC LIMIT 1),
merged AS (
  UPDATE triage.tickets t SET
    model_json = c.model_json, model_priority = c.model_priority, model_name = c.model_name, model_latency_ms = c.model_latency_ms,
    prompt_tokens = t.prompt_tokens + c.prompt_tokens, completion_tokens = t.completion_tokens + c.completion_tokens,
    is_maintenance_request = c.is_maintenance_request, request_type = c.request_type, priority = CASE WHEN t.clarification_round + 1 >= 2 AND jsonb_array_length(c.missing_info) > 0 THEN 'NEEDS_REVIEW' ELSE c.priority END,
    priority_reason = c.priority_reason, override_applied = c.override_applied, override_reason = c.override_reason, human_only = c.human_only,
    trade = c.trade, unit_identifier = coalesce(c.unit_identifier, t.unit_identifier), issue_summary = c.issue_summary,
    habitability_flag = c.habitability_flag, habitability_reason = c.habitability_reason, safety_signals = c.safety_signals,
    access_notes = c.access_notes, accommodation_or_legal_flag = c.accommodation_or_legal_flag, accommodation_or_legal_reason = c.accommodation_or_legal_reason,
    missing_info = c.missing_info, confidence = c.confidence, ambiguity_note = c.ambiguity_note, language = c.language,
    draft_subject = c.draft_subject, draft_body = c.draft_body, vendor_note = c.vendor_note, clarifying_qs = c.clarifying_qs,
    clarification_round = t.clarification_round + 1, vendor_status = 'NOT_STARTED', status = 'NEW'
  FROM child c WHERE t.id = (SELECT original_ticket_id FROM input_values) RETURNING t.*
), child_closed AS (UPDATE triage.tickets SET status='CLOSED', closed_at=now(), thread_root_id=(SELECT original_ticket_id FROM input_values) WHERE id=(SELECT id FROM child)),
message AS (INSERT INTO triage.ticket_messages(ticket_id,channel,direction,intent,body,external_message_id,delivery_state)
  SELECT original_ticket_id,'telegram','inbound','clarification_answer',body,external_message_id,'RECORDED' FROM input_values ON CONFLICT (channel,direction,external_message_id) DO NOTHING),
event AS (INSERT INTO triage.events(ticket_id,actor,action,detail) SELECT id,'system','tenant_clarification_retriaged',jsonb_build_object('round',clarification_round) FROM merged)
SELECT id AS ticket_id, ref, priority, missing_info, human_only, vendor_status, clarification_round, tenant_chat_id AS chat_id FROM merged;
"""
    clarification_response = r"""
function parse(v, fallback) { try { return typeof v === 'string' ? JSON.parse(v) : (v || fallback); } catch (_) { return fallback; } }
function questions(missing) { const q={UNIT:'Which unit and property is this for?',PROPERTY:'Which property is this at?',CONTACT:'What is the best contact number?',ACCESS_PERMISSION:'Can maintenance enter if you are away?',ISSUE_DETAIL:'Please describe what is happening, where it is happening, and whether it is getting worse.',ONSET_TIME:'When did this start?'}; return (parse(missing,[]) || []).filter(x=>q[x]).slice(0,3).map(x=>q[x]); }
return $input.all().map(item=>{const j=item.json; const qs=questions(j.missing_info); const hasClarificationPrompt=qs.length>0; const readyForVendor=!hasClarificationPrompt && !j.human_only && j.priority!=='NEEDS_REVIEW'; const needsManager=!hasClarificationPrompt && !readyForVendor; const text=readyForVendor?`Thank you. Your request ${j.ref} is now being reviewed for the right maintenance provider.`:(needsManager?`Thank you. A manager needs to review request ${j.ref} and will update you here.`:`Thank you. ${qs.join(' ')}`); return {json:{...j,should_notify_manager:readyForVendor || needsManager,message_text:text}};});
"""
    normalize = r"""
return $input.all().map((item) => { const u = item.json.message || item.json; const text = String(u.text || "").trim(); const match = text.match(/^\/start\s+([a-zA-Z0-9_-]+)$/); return {json: {chat_id: String(u.chat?.id || ""), user_id: String(u.from?.id || ""), username: u.from?.username || "", text, message_id: String(u.message_id || ""), pairing_token: match?.[1] || "", is_pairing: Boolean(match), is_bare_start: /^\/start$/i.test(text), is_new_command: /^\/new\b/i.test(text)}}; });
"""
    route_message = r"""
function parse(v) { try { return typeof v === "string" ? JSON.parse(v) : v; } catch (_) { return null; } }
return $input.all().map((item) => { const j = item.json; const ticket = parse(j.ticket); const status = /\b(when|what time|how soon).{0,30}\b(arrive|coming|help|someone)\b/i.test(j.text); let route = "new"; if (j.is_bare_start) route = "welcome"; else if (j.is_new_command) route = "new_command"; else if (ticket && status) route = "status"; else if (ticket && Array.isArray(ticket.missing_info) && ticket.missing_info.length) route = "clarification"; return {json: {...j, ticket, route}}; });
"""
    nodes = [
        node("TenantTelegramTrigger", "n8n-nodes-base.telegramTrigger", 1.3, [-1020, 0], {"updates": ["message"], "additionalFields": {}}, {"telegramApi": {"id":"stage9TenantTelegram", "name":"maintenance-triage-tenant-telegram-bot"}}),
        code("Normalize Tenant Telegram Event", [-800,0], normalize), if_node("Is Pairing Start", [-580,-100], "={{ $json.is_pairing }}"),
        pg("Postgres Claim Pairing Token", [-360,-180], claim_pair, "={{ [$json.pairing_token, $json.chat_id, $json.user_id, $json.username] }}"), code("Prepare Pairing Receipt", [-140,-180], start_message), telegram("Telegram Send Pairing Receipt", [80,-180], {"id":"stage9TenantTelegram", "name":"maintenance-triage-tenant-telegram-bot"}),
        pg("Postgres Load Tenant Chat", [-580,120], load_chat, "={{ [$json.chat_id] }}", True), code("Reattach Tenant Event Context", [-360,120], """const events = $("Normalize Tenant Telegram Event").all();
return $input.all().map((item, index) => {
  const database = item.json || {};
  const event = events.find(candidate => String(candidate.json.chat_id || '') === String(database.chat_id || ''))?.json || events[index]?.json || {};
  return {json: {...event, ...database}};
});"""), code("Route Tenant Message", [-140,120], route_message), switch("Tenant Conversation Route", [80,120], ["welcome", "new", "new_command", "status", "clarification"]),
        code("Prepare Direct Telegram Welcome", [80,-120], """return $input.all().map(item => ({json:{chat_id:item.json.chat_id,message_text:'Tell us what is wrong and include your property and unit if you can.'}}));"""), telegram("Telegram Send Direct Welcome", [300,-120], {"id":"stage9TenantTelegram", "name":"maintenance-triage-tenant-telegram-bot"}),
        code("Prepare New Ticket Payload", [80,0], """return $input.all().map(item => ({json:{source:'telegram',from_address:'telegram:' + item.json.chat_id,subject:'Telegram maintenance request',body_raw:item.json.text,received_at:new Date().toISOString(),attachment_paths:[],msg_id:'<telegram-' + item.json.chat_id + '-' + item.json.message_id + '@maintenance-triage.local>',in_reply_to:null,refs:null,tenant_chat_id:item.json.chat_id}}));"""),
        execute("Execute Triage Engine For Tenant", [300,0], ENGINE_ID, True), code("Prepare New Ticket Link", [520,0], """const ctx=$(\"Prepare New Ticket Payload\").all(); return ctx.map(item=>({json:{chat_id:item.json.tenant_chat_id,msg_id:item.json.msg_id}}));"""), pg("Postgres Link New Tenant Ticket", [740,0], new_ticket, "={{ [$json.chat_id, $json.msg_id] }}"), execute("Execute Manager Desk For Tenant", [960,-60], MANAGER_ID), code("Prepare New Ticket Tenant Reply", [960,60], start_message), telegram("Telegram Send New Ticket Reply", [1180,60], {"id":"stage9TenantTelegram", "name":"maintenance-triage-tenant-telegram-bot"}),
        code("Prepare New Conversation Prompt", [80,160], """return $input.all().map(item=>({json:{chat_id:item.json.chat_id,message_text:'Tell us what is wrong and include your unit if you can.'}}));"""), telegram("Telegram Send New Conversation Prompt", [300,160], {"id":"stage9TenantTelegram", "name":"maintenance-triage-tenant-telegram-bot"}),
        code("Prepare Tenant Status Reply", [80,300], status_message), telegram("Telegram Send Status Reply", [300,300], {"id":"stage9TenantTelegram", "name":"maintenance-triage-tenant-telegram-bot"}), code("Attach Status Reply Delivery", [520,300], """const ctx=$(\"Prepare Tenant Status Reply\").all(); return $input.all().map((item,i)=>({json:{...ctx[i].json,delivery_error:item.json.error || '',delivery_external_message_id:String(item.json.message_id || item.json.messageId || `telegram:status:${ctx[i].json.ticket_id}:${Date.now()}`)}}));"""), pg("Postgres Record Status Reply", [740,300], record_telegram_delivery, "={{ [$json.ticket_id,$json.intent,$json.message_text,$json.delivery_external_message_id,$json.delivery_error] }}"),
        code("Prepare Clarification Retriage", [80,440], """return $input.all().map(item=>{const t=item.json.ticket; const msgId='<telegram-retriage-' + item.json.chat_id + '-' + item.json.message_id + '@maintenance-triage.local>'; return {json:{original_ticket_id:t.id,chat_id:item.json.chat_id,answer_text:item.json.text,external_message_id:'telegram:' + item.json.chat_id + ':' + item.json.message_id,source:'telegram',from_address:'telegram:' + item.json.chat_id,subject:'Clarification for ' + t.ref,body_raw:(t.body_raw || '') + '\\n\\nTenant clarification: ' + item.json.text,received_at:new Date().toISOString(),attachment_paths:[],msg_id:msgId,in_reply_to:null,refs:null}};});"""), execute("Execute Clarification Retriage", [300,440], ENGINE_ID, True), code("Prepare Clarification Merge", [520,440], """const ctx=$(\"Prepare Clarification Retriage\").all(); return ctx.map(item=>({json:{original_ticket_id:item.json.original_ticket_id,child_msg_id:item.json.msg_id,chat_id:item.json.chat_id,body:item.json.answer_text,external_message_id:item.json.external_message_id}}));"""), pg("Postgres Merge Clarification Result", [740,440], merge_clarification, "={{ [$json.original_ticket_id, $json.child_msg_id, $json.chat_id, $json.body, $json.external_message_id] }}"), code("Prepare Clarification Response", [960,440], clarification_response), if_node("Clarification Needs Manager", [1180,380], "={{ Boolean($json.should_notify_manager) }}"), execute("Execute Manager Desk After Clarification", [1400,320], MANAGER_ID), telegram("Telegram Send Clarification Reply", [1400,500], {"id":"stage9TenantTelegram", "name":"maintenance-triage-tenant-telegram-bot"}),
    ]
    connections = {
        "TenantTelegramTrigger":{"main":[[{"node":"Normalize Tenant Telegram Event","type":"main","index":0}]]}, "Normalize Tenant Telegram Event":{"main":[[{"node":"Is Pairing Start","type":"main","index":0}]]},
        "Is Pairing Start":{"main":[[{"node":"Postgres Claim Pairing Token","type":"main","index":0}],[{"node":"Postgres Load Tenant Chat","type":"main","index":0}]]}, "Postgres Claim Pairing Token":{"main":[[{"node":"Prepare Pairing Receipt","type":"main","index":0}]]}, "Prepare Pairing Receipt":{"main":[[{"node":"Telegram Send Pairing Receipt","type":"main","index":0}]]},
        "Postgres Load Tenant Chat":{"main":[[{"node":"Reattach Tenant Event Context","type":"main","index":0}]]}, "Reattach Tenant Event Context":{"main":[[{"node":"Route Tenant Message","type":"main","index":0}]]}, "Route Tenant Message":{"main":[[{"node":"Tenant Conversation Route","type":"main","index":0}]]},
        "Tenant Conversation Route":{"main":[[{"node":"Prepare Direct Telegram Welcome","type":"main","index":0}],[{"node":"Prepare New Ticket Payload","type":"main","index":0}],[{"node":"Prepare New Conversation Prompt","type":"main","index":0}],[{"node":"Prepare Tenant Status Reply","type":"main","index":0}],[{"node":"Prepare Clarification Retriage","type":"main","index":0}]]}, "Prepare Direct Telegram Welcome":{"main":[[{"node":"Telegram Send Direct Welcome","type":"main","index":0}]]},
        "Prepare New Ticket Payload":{"main":[[{"node":"Execute Triage Engine For Tenant","type":"main","index":0}]]}, "Execute Triage Engine For Tenant":{"main":[[{"node":"Prepare New Ticket Link","type":"main","index":0}]]}, "Prepare New Ticket Link":{"main":[[{"node":"Postgres Link New Tenant Ticket","type":"main","index":0}]]},
        "Postgres Link New Tenant Ticket":{"main":[[{"node":"Execute Manager Desk For Tenant","type":"main","index":0},{"node":"Prepare New Ticket Tenant Reply","type":"main","index":0}]]}, "Prepare New Ticket Tenant Reply":{"main":[[{"node":"Telegram Send New Ticket Reply","type":"main","index":0}]]},
        "Prepare New Conversation Prompt":{"main":[[{"node":"Telegram Send New Conversation Prompt","type":"main","index":0}]]}, "Prepare Tenant Status Reply":{"main":[[{"node":"Telegram Send Status Reply","type":"main","index":0}]]}, "Telegram Send Status Reply":{"main":[[{"node":"Attach Status Reply Delivery","type":"main","index":0}]]}, "Attach Status Reply Delivery":{"main":[[{"node":"Postgres Record Status Reply","type":"main","index":0}]]}, "Prepare Clarification Retriage":{"main":[[{"node":"Execute Clarification Retriage","type":"main","index":0}]]}, "Execute Clarification Retriage":{"main":[[{"node":"Prepare Clarification Merge","type":"main","index":0}]]}, "Prepare Clarification Merge":{"main":[[{"node":"Postgres Merge Clarification Result","type":"main","index":0}]]}, "Postgres Merge Clarification Result":{"main":[[{"node":"Prepare Clarification Response","type":"main","index":0}]]}, "Prepare Clarification Response":{"main":[[{"node":"Clarification Needs Manager","type":"main","index":0},{"node":"Telegram Send Clarification Reply","type":"main","index":0}]]}, "Clarification Needs Manager":{"main":[[{"node":"Execute Manager Desk After Clarification","type":"main","index":0}],[]]},
    }
    return workflow(TENANT_ID, "Maintenance Tenant Telegram", nodes, connections)


def build_manager_desk_legacy():
    record_tenant_delivery = r"""
INSERT INTO triage.ticket_messages (ticket_id, channel, direction, intent, body, external_message_id, delivery_state, detail)
VALUES ($1::bigint, 'telegram', 'outbound', 'vendor_dispatch', $2::text, NULLIF($3::text, ''), CASE WHEN NULLIF($4::text, '') IS NULL THEN 'SENT' ELSE 'FAILED' END, jsonb_build_object('error', NULLIF($4::text, '')))
ON CONFLICT (channel, direction, external_message_id) DO UPDATE SET delivery_state = EXCLUDED.delivery_state, detail = EXCLUDED.detail
RETURNING id;
"""
    load_ticket = r"""
WITH input_values AS (SELECT NULLIF($1::text, '')::bigint AS ticket_id), cfg AS (
  SELECT (SELECT value FROM triage.config WHERE key = 'contacts') AS contacts, (SELECT value FROM triage.config WHERE key = 'airtable') AS airtable,
         (SELECT value FROM triage.config WHERE key = 'company') AS company, (SELECT value FROM triage.config WHERE key = 'system_mail') AS system_mail
)
SELECT to_jsonb(t) AS ticket, cfg.contacts, cfg.airtable, cfg.company, cfg.system_mail,
       (SELECT airtable_record_id FROM triage.airtable_roster_links
        WHERE roster_kind = 'tenant' AND lookup_key = lower(coalesce(t.from_address, t.tenant_contact, ''))
        LIMIT 1) AS tenant_airtable_record_id
FROM triage.tickets t CROSS JOIN cfg JOIN input_values i ON t.id = i.ticket_id;
"""
    candidate_query = r"""
WITH input_values AS (SELECT $1::bigint AS ticket_id, $2::jsonb AS candidates, $3::boolean AS dispatch_eligible), removed AS (
  DELETE FROM triage.ticket_vendor_candidates WHERE ticket_id = (SELECT ticket_id FROM input_values)
), inserted AS (
  INSERT INTO triage.ticket_vendor_candidates (ticket_id, vendor_id, vendor_name, vendor_email, candidate_rank)
  SELECT i.ticket_id, c->>'id', c->>'name', c->>'email', ord::smallint FROM input_values i, jsonb_array_elements(i.candidates) WITH ORDINALITY AS x(c, ord)
  WHERE i.dispatch_eligible AND c->>'id' IS NOT NULL AND ord <= 3
  ON CONFLICT (ticket_id, vendor_id) DO UPDATE SET vendor_name = EXCLUDED.vendor_name, vendor_email = EXCLUDED.vendor_email, candidate_rank = EXCLUDED.candidate_rank
  RETURNING *
), updated AS (
  UPDATE triage.tickets SET vendor_status = CASE WHEN NOT (SELECT dispatch_eligible FROM input_values) THEN 'NOT_STARTED' WHEN EXISTS (SELECT 1 FROM inserted) THEN 'AWAITING_VENDOR' ELSE 'NEEDS_VENDOR_ASSIGNMENT' END
  WHERE id = (SELECT ticket_id FROM input_values) RETURNING *
)
SELECT (SELECT ticket_id FROM input_values) AS ticket_id, count(*)::int AS candidate_count FROM inserted;
"""
    prep_candidates = r"""
function parse(value, fallback) { try { return typeof value === 'string' ? JSON.parse(value) : (value || fallback); } catch (_) { return fallback; } }
function records(value) { const body = parse(value?.body ?? value ?? {}, {}); return Array.isArray(body?.records) ? body.records : []; }
function list(value) { return Array.isArray(value) ? value.map(String).join(',').toUpperCase() : String(value || '').toUpperCase(); }
const context = $("Postgres Load Ticket For Manager").all()[0]?.json || {};
const ticket = parse(context.ticket, {}); const cfg = parse(context.airtable, {}); const contacts = parse(context.contacts, {});
let rows = []; try { rows = records($input.all()[0]?.json); } catch (_) {}
const trade = String(ticket.trade || '').toUpperCase(); const propertyMatch = String(ticket.body_raw || '').match(/(?:^|\\n)Property:\\s*([^\\n]+)/i); const property = [ticket.unit_match_display, ticket.unit_identifier, propertyMatch?.[1]].filter(Boolean).join(' ').toUpperCase();
const candidates = rows.map(r => ({id:r.id, name:r.fields?.['Vendor Name'] || '', email:r.fields?.Email || '', active:r.fields?.Active !== false && String(r.fields?.Active || '').toLowerCase() !== 'no', trades:list(r.fields?.Trades), properties:list(r.fields?.Properties), priority:Number(r.fields?.Priority || 999)}))
  .filter(v => v.active && v.name && v.email && v.trades.includes(trade) && (!v.properties || property.includes(v.properties) || v.properties.includes(property.split(' - ')[0] || '')))
  .sort((a,b) => a.priority - b.priority).slice(0,3);
const missing = Array.isArray(ticket.missing_info) ? ticket.missing_info : [];
const eligible = Boolean(ticket.id && !ticket.human_only && ticket.priority !== 'NEEDS_REVIEW' && missing.length === 0 && ticket.source !== 'fixture' && ticket.source !== 'import');
const labels = candidates.map(v => `Send to ${v.name}`); const callbacks = candidates.map(v => `vendor:${ticket.id}:${v.id}`);
const canChoose = eligible && candidates.length > 0;
const text = canChoose ? [`VENDOR APPROVAL: ${ticket.ref}`, `Priority: ${ticket.priority}`, `Trade: ${ticket.trade || 'UNKNOWN'}`, `Unit: ${ticket.unit_match_display || ticket.unit_identifier || 'not stated'}`, `Issue: ${ticket.issue_summary || ticket.subject || 'Maintenance request'}`, '', 'Select a vendor to send this exact email:', String(ticket.vendor_note || 'No vendor note was drafted.')].join('\n') : (eligible ? `${ticket.ref}: no active vendor matches this property and trade. Assign a vendor manually; no email has been sent.` : `${ticket.ref}: manager review required. No vendor email will be sent automatically.`);
return [{json:{ticket_id:ticket.id, ticket, airtable:cfg, contacts, candidates, vendor_count:candidates.length, tenant_record_id:context.tenant_airtable_record_id || '', should_send_manager:Boolean(eligible && (contacts.primary_chat_id || contacts.operator_chat_id)), should_sync:Boolean(cfg.enabled && cfg.base_id), chat_id:contacts.primary_chat_id || contacts.operator_chat_id || '', vendor_1_label:labels[0] || '', vendor_2_label:labels[1] || '', vendor_3_label:labels[2] || '', vendor_1_callback:callbacks[0] || '', vendor_2_callback:callbacks[1] || '', vendor_3_callback:callbacks[2] || '', message_text:text}}];
"""
    claim = r"""
WITH input_values AS (SELECT $1::bigint AS ticket_id, $2::text AS vendor_id, $3::text AS actor, $4::text AS manager_chat_id, NULLIF($5::text, '')::bigint AS manager_message_id),
candidate AS (SELECT c.* FROM triage.ticket_vendor_candidates c JOIN input_values i ON c.ticket_id=i.ticket_id AND c.vendor_id=i.vendor_id),
held AS (UPDATE triage.tickets t SET vendor_status='HELD' FROM input_values i WHERE t.id=i.ticket_id AND i.vendor_id='hold' RETURNING t.*),
claim AS (INSERT INTO triage.vendor_send_attempts (ticket_id,vendor_id,vendor_name,vendor_email,manager_chat_id,manager_message_id,actor,state)
  SELECT i.ticket_id,c.vendor_id,c.vendor_name,c.vendor_email,i.manager_chat_id,i.manager_message_id,i.actor,'CLAIMED' FROM input_values i JOIN candidate c ON true WHERE i.vendor_id <> 'hold'
  ON CONFLICT (ticket_id) DO NOTHING RETURNING *),
updated AS (UPDATE triage.tickets t SET vendor_status='SENDING',selected_vendor_id=c.vendor_id,selected_vendor_name=c.vendor_name,selected_vendor_email=c.vendor_email FROM claim c WHERE t.id=c.ticket_id RETURNING t.*)
SELECT CASE WHEN EXISTS(SELECT 1 FROM held) THEN 'held' WHEN EXISTS(SELECT 1 FROM claim) THEN 'send' WHEN EXISTS(SELECT 1 FROM candidate) THEN 'already_handled' ELSE 'invalid_vendor' END AS result,
  (SELECT row_to_json(c) FROM claim c LIMIT 1) AS attempt, (SELECT to_jsonb(t) FROM updated t LIMIT 1) AS ticket;
"""
    finalize = r"""
WITH input_values AS (SELECT $1::bigint AS ticket_id, NULLIF($2::text, '') AS message_id, NULLIF($3::text, '') AS error),
updated AS (UPDATE triage.tickets t SET vendor_status=CASE WHEN i.error IS NULL THEN 'SENT' ELSE 'FAILED' END, vendor_email_message_id=i.message_id, vendor_email_sent_at=CASE WHEN i.error IS NULL THEN now() ELSE NULL END, vendor_email_error=i.error FROM input_values i WHERE t.id=i.ticket_id RETURNING t.*),
attempt AS (UPDATE triage.vendor_send_attempts a SET state=CASE WHEN i.error IS NULL THEN 'SENT' ELSE 'FAILED' END,smtp_message_id=i.message_id,error=i.error,finished_at=now() FROM input_values i WHERE a.ticket_id=i.ticket_id AND a.state='CLAIMED' RETURNING a.*),
events AS (INSERT INTO triage.events(ticket_id,actor,action,detail) SELECT id,'manager','vendor_email_sent',jsonb_build_object('vendor',selected_vendor_name,'email',selected_vendor_email) FROM updated WHERE (SELECT error FROM input_values) IS NULL UNION ALL SELECT id,'system','vendor_email_failed',jsonb_build_object('error',(SELECT error FROM input_values)) FROM updated WHERE (SELECT error FROM input_values) IS NOT NULL)
SELECT to_jsonb(u) AS ticket,
       CASE WHEN (SELECT error FROM input_values) IS NULL THEN 'sent' ELSE 'failed' END AS result,
       (SELECT value FROM triage.config WHERE key = 'airtable') AS airtable
FROM updated u;
"""
    prep_vendor_email = r"""
function parse(v) { try { return typeof v === 'string' ? JSON.parse(v) : v; } catch (_) { return null; } }
return $input.all().map(item => { const row=item.json; const attempt=parse(row.attempt); const ticket=parse(row.ticket); const should=row.result==='send' && attempt && ticket; return {json:{...row,attempt,ticket,should_send:should,chat_id:attempt?.manager_chat_id || '',from_email:'Demo Maintenance Desk <sambhavn8n@gmail.com>',to_email:attempt?.vendor_email || '',email_subject:`[MT-SYSTEM][VENDOR] ${ticket?.ref || ''} ${ticket?.trade || 'Maintenance'} request`,email_body:ticket?.vendor_note || `Maintenance request ${ticket?.ref || ''}`,message_text:'Vendor email is being sent.'}}; });
"""
    normalize_callback = r"""
return $input.all().map(item => { const q=item.json.callback_query || item.json; const parts=String(q.data || '').split(':'); return {json:{ticket_id:parts[1] || '',vendor_id:parts[2] || '',actor:q.from?.username ? `manager:${q.from.username}` : 'manager:telegram',manager_chat_id:String(q.message?.chat?.id || ''),manager_message_id:String(q.message?.message_id || ''),callback_query_id:q.id || ''}}; });
"""
    prep_post_send_airtable = r"""
function parse(v, fallback) { try { return typeof v === 'string' ? JSON.parse(v) : (v || fallback); } catch (_) { return fallback; } }
return $input.all().flatMap(item => {
  const t = parse(item.json.ticket, {}); const cfg = parse(item.json.airtable, {});
  if (!cfg.enabled || !cfg.base_id || !t.ref) return [];
  return [{json:{
    airtable_url:`https://api.airtable.com/v0/${cfg.base_id}/${encodeURIComponent(cfg.requests_table || 'Requests')}`,
    airtable_body:{performUpsert:{fieldsToMergeOn:['Reference']},records:[{fields:{
      'Reference':t.ref, 'Vendor Status':t.vendor_status || '', 'Selected Vendor':t.selected_vendor_name || '',
      'Vendor Email':t.selected_vendor_email || '', 'Telegram Chat ID':t.tenant_chat_id || ''
    }}]}
  }}];
});
"""
    nodes = [
        node("Manager Desk Input", "n8n-nodes-base.executeWorkflowTrigger", 1.2, [-1180,-180], {"inputSource":"passthrough","returnOutput":"allRuns"}),
        node("ManagerTelegramTrigger", "n8n-nodes-base.telegramTrigger", 1.3, [-1180,180], {"updates":["callback_query"],"additionalFields":{}}, {"telegramApi":{"id":"stage1TelegramLocal","name":"maintenance-triage-telegram-bot"}}),
        code("Normalize Manager Callback", [-960,180], normalize_callback), pg("Postgres Claim Vendor Send", [-740,180], claim, "={{ [$json.ticket_id, $json.vendor_id, $json.actor, $json.manager_chat_id, $json.manager_message_id] }}"), code("Prepare Vendor Email", [-520,180], prep_vendor_email), if_node("Should Send Vendor Email", [-300,180], "={{ Boolean($json.should_send) }}"), email("SMTP Send Approved Vendor Email", [-80,100]), code("Attach Vendor Email Result", [140,100], """const ctx=$(\"Prepare Vendor Email\").all().filter(i=>i.json.should_send); return $input.all().map((item,i)=>({json:{...ctx[i].json,email_error:item.json.error || '',smtp_message_id:item.json.messageId || item.json.message_id || ''}}));"""), pg("Postgres Finalize Vendor Send", [360,100], finalize, "={{ [$json.ticket?.id || $json.ticket_id, $json.smtp_message_id || '', $json.email_error || ''] }}"),
        code("Prepare Tenant Vendor Update", [580,100], """return $input.all().flatMap(item=>{const t=typeof item.json.ticket==='string'?JSON.parse(item.json.ticket):item.json.ticket; return item.json.result==='sent' && t?.tenant_chat_id?[{json:{ticket_id:t.id,chat_id:t.tenant_chat_id,message_text:'We have contacted a maintenance provider. We will update you when we have an arrival time.'}}]:[];});"""), telegram("Telegram Send Tenant Vendor Update", [800,100], {"id":"stage9TenantTelegram","name":"maintenance-triage-tenant-telegram-bot"}), code("Attach Tenant Vendor Update Delivery", [1020,100], """const ctx=$(\"Prepare Tenant Vendor Update\").all(); return $input.all().map((item,i)=>({json:{...ctx[i].json,delivery_error:item.json.error || '',delivery_external_message_id:String(item.json.message_id || item.json.messageId || `telegram:vendor-dispatch:${ctx[i].json.ticket_id}:${Date.now()}`)}}));"""), pg("Postgres Record Tenant Vendor Update", [1240,100], record_tenant_delivery, "={{ [$json.ticket_id,$json.message_text,$json.delivery_external_message_id,$json.delivery_error] }}"),
        code("Prepare Airtable Vendor Send Sync", [580,180], prep_post_send_airtable), airtable("HTTP Airtable Sync Vendor Send", [800,180], "PATCH", "={{ $json.airtable_url }}", "={{ $json.airtable_body }}"),
        pg("Postgres Load Ticket For Manager", [-960,-180], load_ticket, "={{ [$json.ticket_id || $json.id || ''] }}"), code("Prepare Airtable Vendor Lookup", [-740,-180], """const j=$input.all()[0]?.json||{}; const cfg=typeof j.airtable==='string'?JSON.parse(j.airtable):j.airtable||{}; return [{json:{...j,should_fetch:Boolean(cfg.enabled && cfg.base_id),vendor_url:`https://api.airtable.com/v0/${cfg.base_id}/${encodeURIComponent(cfg.vendors_table || 'Vendors')}`}}];"""), if_node("Should Fetch Airtable Vendors", [-520,-180], "={{ $json.should_fetch }}"), airtable("HTTP Load Airtable Vendors", [-300,-260], "GET", "={{ $json.vendor_url }}"), code("Prepare Manager Vendor Alert", [-80,-180], prep_candidates), pg("Postgres Store Vendor Candidates", [140,-180], candidate_query, "={{ [$json.ticket_id, JSON.stringify($json.candidates || [])] }}"), code("Reattach Manager Alert", [360,-180], """return $(\"Prepare Manager Vendor Alert\").all().map(item=>{const j=item.json; return {json:{...j,ticket:{...j.ticket,vendor_status:(j.candidates||[]).length?'AWAITING_VENDOR':'NEEDS_VENDOR_ASSIGNMENT'}}};});"""), if_node("Should Notify Manager", [580,-180], "={{ Boolean($json.should_send_manager) }}"), telegram("Telegram Send Vendor Approval", [800,-260], {"id":"stage1TelegramLocal","name":"maintenance-triage-telegram-bot"}, True),
        code("Prepare Airtable Request Upsert", [580,-60], """return $input.all().map(item=>{const j=item.json; const t=j.ticket||{}; const cfg=j.airtable||{}; const propertyMatch=String(t.body_raw||'').match(/(?:^|\\n)Property:\\s*([^\\n]+)/i); return {json:{...j,should_sync:Boolean(cfg.enabled&&cfg.base_id),airtable_url:`https://api.airtable.com/v0/${cfg.base_id}/${encodeURIComponent(cfg.requests_table||'Requests')}`,airtable_body:{performUpsert:{fieldsToMergeOn:['Reference']},records:[{fields:{'Reference':t.ref||'',Status:t.status||'NEW',Priority:t.priority||'',Source:t.source||'', 'Tenant Name':t.tenant_name||'', 'Tenant Email':t.from_address||t.tenant_contact||'',Property:propertyMatch?.[1]||'',Unit:t.unit_identifier||'',Trade:t.trade||'',Summary:t.issue_summary||t.subject||'', 'Missing Info':JSON.stringify(t.missing_info||[]), 'Human Only':String(Boolean(t.human_only)), 'Vendor Status':t.vendor_status||'', 'Suggested Vendors':(j.candidates||[]).map(v=>v.name).join(', '), 'Telegram Chat ID':t.tenant_chat_id||''}}]}}};});"""), if_node("Should Sync Airtable Request", [800,-60], "={{ Boolean($json.should_sync) }}"), airtable("HTTP Airtable Upsert Request", [1020,-60], "PATCH", "={{ $json.airtable_url }}", "={{ $json.airtable_body }}"), code("Attach Airtable Request Result", [1240,-60], """const ctx=$(\"Prepare Airtable Request Upsert\").all(); return $input.all().map((item,i)=>({json:{ticket_id:ctx[i]?.json.ticket?.id || '',airtable_record_id:item.json.body?.records?.[0]?.id || item.json.records?.[0]?.id || '',sync_error:item.json.error || ''}}));"""), pg("Postgres Store Airtable Request Link", [1460,-60], "UPDATE triage.tickets SET airtable_record_id=NULLIF($2::text,'') WHERE id=$1::bigint AND NULLIF($3::text,'') IS NULL RETURNING id;", "={{ [$json.ticket_id,$json.airtable_record_id || '',$json.sync_error || ''] }}"),
    ]
    connections = {
        "Manager Desk Input":{"main":[[{"node":"Postgres Load Ticket For Manager","type":"main","index":0}]]}, "ManagerTelegramTrigger":{"main":[[{"node":"Normalize Manager Callback","type":"main","index":0}]]}, "Normalize Manager Callback":{"main":[[{"node":"Postgres Claim Vendor Send","type":"main","index":0}]]}, "Prepare Vendor Email":{"main":[[{"node":"Should Send Vendor Email","type":"main","index":0}]]}, "Should Send Vendor Email":{"main":[[{"node":"SMTP Send Approved Vendor Email","type":"main","index":0}],[]]}, "SMTP Send Approved Vendor Email":{"main":[[{"node":"Attach Vendor Email Result","type":"main","index":0}]]}, "Attach Vendor Email Result":{"main":[[{"node":"Postgres Finalize Vendor Send","type":"main","index":0}]]}, "Postgres Finalize Vendor Send":{"main":[[{"node":"Prepare Tenant Vendor Update","type":"main","index":0},{"node":"Prepare Airtable Vendor Send Sync","type":"main","index":0}]]}, "Prepare Tenant Vendor Update":{"main":[[{"node":"Telegram Send Tenant Vendor Update","type":"main","index":0}]]}, "Telegram Send Tenant Vendor Update":{"main":[[{"node":"Attach Tenant Vendor Update Delivery","type":"main","index":0}]]}, "Attach Tenant Vendor Update Delivery":{"main":[[{"node":"Postgres Record Tenant Vendor Update","type":"main","index":0}]]}, "Prepare Airtable Vendor Send Sync":{"main":[[{"node":"HTTP Airtable Sync Vendor Send","type":"main","index":0}]]},
        "Postgres Load Ticket For Manager":{"main":[[{"node":"Prepare Airtable Vendor Lookup","type":"main","index":0}]]}, "Prepare Airtable Vendor Lookup":{"main":[[{"node":"Should Fetch Airtable Vendors","type":"main","index":0}]]}, "Should Fetch Airtable Vendors":{"main":[[{"node":"HTTP Load Airtable Vendors","type":"main","index":0}],[{"node":"Prepare Manager Vendor Alert","type":"main","index":0}]]}, "HTTP Load Airtable Vendors":{"main":[[{"node":"Prepare Manager Vendor Alert","type":"main","index":0}]]}, "Prepare Manager Vendor Alert":{"main":[[{"node":"Postgres Store Vendor Candidates","type":"main","index":0}]]}, "Postgres Store Vendor Candidates":{"main":[[{"node":"Reattach Manager Alert","type":"main","index":0}]]}, "Reattach Manager Alert":{"main":[[{"node":"Should Notify Manager","type":"main","index":0},{"node":"Prepare Airtable Request Upsert","type":"main","index":0}]]}, "Should Notify Manager":{"main":[[{"node":"Telegram Send Vendor Approval","type":"main","index":0}],[]]}, "Prepare Airtable Request Upsert":{"main":[[{"node":"Should Sync Airtable Request","type":"main","index":0}]]}, "Should Sync Airtable Request":{"main":[[{"node":"HTTP Airtable Upsert Request","type":"main","index":0}],[]]}, "HTTP Airtable Upsert Request":{"main":[[{"node":"Attach Airtable Request Result","type":"main","index":0}]]}, "Attach Airtable Request Result":{"main":[[{"node":"Postgres Store Airtable Request Link","type":"main","index":0}]]},
    }
    return workflow(MANAGER_ID, "Maintenance Manager Desk", nodes, connections)


def build_manager_desk():
    flow = build_manager_desk_legacy()
    nodes = flow["nodes"]
    by_name = {item["name"]: item for item in nodes}

    by_name["Postgres Load Ticket For Manager"]["parameters"]["query"] = r"""
WITH input_values AS (SELECT NULLIF($1::text, '')::bigint AS ticket_id), cfg AS (
  SELECT (SELECT value FROM triage.config WHERE key = 'contacts') AS contacts,
         (SELECT value FROM triage.config WHERE key = 'airtable') AS airtable
)
SELECT to_jsonb(t) AS ticket, cfg.contacts, cfg.airtable,
       (SELECT airtable_record_id FROM triage.airtable_roster_links
        WHERE roster_kind = 'tenant' AND lookup_key = lower(coalesce(t.from_address, t.tenant_contact, ''))
        LIMIT 1) AS tenant_airtable_record_id
FROM triage.tickets t CROSS JOIN cfg JOIN input_values i ON t.id = i.ticket_id;
""".strip()
    by_name["Prepare Manager Vendor Alert"]["parameters"]["jsCode"] = r"""
function parse(value, fallback) { try { return typeof value === 'string' ? JSON.parse(value) : (value || fallback); } catch (_) { return fallback; } }
function records(value) { const body = parse(value?.body ?? value ?? {}, {}); return Array.isArray(body?.records) ? body.records : []; }
function list(value) { return Array.isArray(value) ? value.map(String).join(',').toUpperCase() : String(value || '').toUpperCase(); }
const context = $("Postgres Load Ticket For Manager").all()[0]?.json || {};
const ticket = parse(context.ticket, {}); const cfg = parse(context.airtable, {}); const contacts = parse(context.contacts, {});
let rows = []; try { rows = records($input.all()[0]?.json); } catch (_) {}
const trade = String(ticket.trade || '').toUpperCase();
const propertyMatch = String(ticket.body_raw || '').match(/(?:^|\n)Property:\s*([^\n]+)/i);
const property = [ticket.unit_match_display, ticket.unit_identifier, propertyMatch?.[1]].filter(Boolean).join(' ').toUpperCase();
const candidates = rows.map(r => ({
  id:r.id, name:r.fields?.['Vendor Name'] || '', email:r.fields?.Email || '',
  active:r.fields?.Active !== false && String(r.fields?.Active || '').toLowerCase() !== 'no',
  trades:list(r.fields?.Trades), properties:list(r.fields?.Properties), priority:Number(r.fields?.Priority || 999)
})).filter(v => v.active && v.name && v.email && v.trades.includes(trade) && (!v.properties || property.includes(v.properties) || v.properties.includes(property.split(' - ')[0] || '')))
  .sort((a,b) => a.priority - b.priority).slice(0,3);
const missing = Array.isArray(ticket.missing_info) ? ticket.missing_info : [];
const eligible = Boolean(ticket.id && !ticket.human_only && ticket.priority !== 'NEEDS_REVIEW' && missing.length === 0 && ticket.source !== 'fixture' && ticket.source !== 'import');
const dispatchCandidates = eligible ? candidates : [];
const canChoose = dispatchCandidates.length > 0;
const reviewReason = ticket.human_only ? 'This request requires human handling.' : (missing.length ? `Missing details: ${missing.join(', ')}.` : 'The request needs manual review.');
const text = canChoose ? [
  `VENDOR APPROVAL: ${ticket.ref}`, `Priority: ${ticket.priority}`, `Trade: ${ticket.trade || 'UNKNOWN'}`,
  `Unit: ${ticket.unit_match_display || ticket.unit_identifier || 'not stated'}`,
  `Issue: ${ticket.issue_summary || ticket.subject || 'Maintenance request'}`, '',
  'Select a vendor to send this exact email:', String(ticket.vendor_note || 'No vendor note was drafted.')
].join('\n') : (eligible ? `${ticket.ref}: no active vendor matches this property and trade. Assign a vendor manually; no email has been sent.` : [`MANAGER REVIEW: ${ticket.ref}`, `Priority: ${ticket.priority}`, `Issue: ${ticket.issue_summary || ticket.subject || 'Maintenance request'}`, `Reason: ${reviewReason}`, '', 'No vendor email has been sent.'].join('\n'));
return [{json:{
  ticket_id:ticket.id, ticket, airtable:cfg, contacts, candidates:dispatchCandidates, vendor_count:canChoose ? dispatchCandidates.length : 0, vendor_dispatch_eligible:eligible,
  tenant_record_id:context.tenant_airtable_record_id || '', should_send_manager:Boolean(ticket.id && ticket.source !== 'fixture' && ticket.source !== 'import' && (contacts.primary_chat_id || contacts.operator_chat_id)),
  should_sync:Boolean(cfg.enabled && cfg.base_id), chat_id:contacts.primary_chat_id || contacts.operator_chat_id || '',
  vendor_1_label:dispatchCandidates[0] ? `Send to ${dispatchCandidates[0].name}` : '', vendor_2_label:dispatchCandidates[1] ? `Send to ${dispatchCandidates[1].name}` : '', vendor_3_label:dispatchCandidates[2] ? `Send to ${dispatchCandidates[2].name}` : '',
  vendor_1_callback:dispatchCandidates[0] ? `vendor:${ticket.id}:${dispatchCandidates[0].id}` : '', vendor_2_callback:dispatchCandidates[1] ? `vendor:${ticket.id}:${dispatchCandidates[1].id}` : '', vendor_3_callback:dispatchCandidates[2] ? `vendor:${ticket.id}:${dispatchCandidates[2].id}` : '',
  message_text:text
}}];
""".strip()
    by_name["Prepare Airtable Request Upsert"]["parameters"]["jsCode"] = r"""
return $input.all().map(item => {
  const j = item.json; const t = j.ticket || {}; const cfg = j.airtable || {};
  const propertyMatch = String(t.body_raw || '').match(/(?:^|\n)Property:\s*([^\n]+)/i);
  const fields = {
    'Reference':t.ref || '', Status:t.status || 'NEW', Priority:t.priority || 'NEEDS_REVIEW', Source:t.source || 'telegram',
    Summary:t.issue_summary || t.subject || 'Maintenance request', 'Missing Info':Array.isArray(t.missing_info) ? t.missing_info : [],
    'Human Only':Boolean(t.human_only), 'Vendor Status':t.vendor_status || 'NOT_STARTED'
  };
  const add = (name, value) => { if (value !== null && value !== undefined && String(value).trim() !== '') fields[name] = value; };
  const tenantEmail = (t.from_address || t.tenant_contact || '');
  const property = propertyMatch?.[1]?.trim();
  add('Tenant Email', tenantEmail.startsWith('telegram:') ? '' : tenantEmail);
  add('Property', property); add('Unit', t.unit_identifier); add('Trade', t.trade); add('Telegram Chat ID', t.tenant_chat_id);
  if (j.tenant_record_id) fields.Tenant = [j.tenant_record_id];
  if ((j.candidates || []).length) fields['Suggested Vendors'] = j.candidates.map(v => v.id);
  if (t.selected_vendor_id) fields['Selected Vendor'] = [t.selected_vendor_id];
  return {json:{...j, should_sync:Boolean(cfg.enabled && cfg.base_id), airtable_url:`https://api.airtable.com/v0/${cfg.base_id}/${encodeURIComponent(cfg.requests_table || 'Requests')}`, airtable_body:{performUpsert:{fieldsToMergeOn:['Reference']},records:[{fields}]}}};
});
""".strip()
    by_name["Prepare Airtable Vendor Send Sync"]["parameters"]["jsCode"] = r"""
function parse(v, fallback) { try { return typeof v === 'string' ? JSON.parse(v) : (v || fallback); } catch (_) { return fallback; } }
return $input.all().flatMap(item => {
  const t = parse(item.json.ticket, {}); const cfg = parse(item.json.airtable, {});
  if (!cfg.enabled || !cfg.base_id || !t.ref) return [];
  const fields = {'Reference':t.ref, 'Vendor Status':t.vendor_status || '', 'Telegram Chat ID':t.tenant_chat_id || ''};
  if (t.selected_vendor_id) fields['Selected Vendor'] = [t.selected_vendor_id];
  return [{json:{airtable_url:`https://api.airtable.com/v0/${cfg.base_id}/${encodeURIComponent(cfg.requests_table || 'Requests')}`, airtable_body:{performUpsert:{fieldsToMergeOn:['Reference']},records:[{fields}]}}}];
});
""".strip()

    nodes = [item for item in nodes if item["name"] not in {"Should Notify Manager", "Telegram Send Vendor Approval"}]
    for count in range(4):
        nodes.append(if_node(f"Should Send Manager Keyboard {count}", [580, -260 + count * 120], f"={{{{ Boolean($json.should_send_manager && $json.vendor_count === {count}) }}}}"))
        nodes.append(telegram(f"Telegram Send Manager Keyboard {count}", [820, -260 + count * 120], {"id":"stage1TelegramLocal", "name":"maintenance-triage-telegram-bot"}, count))
    flow["nodes"] = nodes

    connections = flow["connections"]
    by_name["Postgres Store Vendor Candidates"]["parameters"]["options"]["queryReplacement"] = "={{ [$json.ticket_id, JSON.stringify($json.candidates || []), Boolean($json.vendor_dispatch_eligible)] }}"
    by_name["Reattach Manager Alert"]["parameters"]["jsCode"] = """return $("Prepare Manager Vendor Alert").all().map(item => {
  const j = item.json;
  const vendorStatus = j.vendor_dispatch_eligible ? ((j.candidates || []).length ? 'AWAITING_VENDOR' : 'NEEDS_VENDOR_ASSIGNMENT') : 'NOT_STARTED';
  return {json:{...j,ticket:{...j.ticket,vendor_status:vendorStatus}}};
});"""
    connections["Postgres Claim Vendor Send"] = {"main":[[{"node":"Prepare Vendor Email","type":"main","index":0}]]}
    connections.pop("Should Notify Manager", None)
    connections.pop("Telegram Send Vendor Approval", None)
    connections["Reattach Manager Alert"] = {"main":[[
        {"node":"Should Send Manager Keyboard 0","type":"main","index":0},
        {"node":"Should Send Manager Keyboard 1","type":"main","index":0},
        {"node":"Should Send Manager Keyboard 2","type":"main","index":0},
        {"node":"Should Send Manager Keyboard 3","type":"main","index":0},
        {"node":"Prepare Airtable Request Upsert","type":"main","index":0},
    ]]}
    for count in range(4):
        connections[f"Should Send Manager Keyboard {count}"] = {"main":[[{"node":f"Telegram Send Manager Keyboard {count}","type":"main","index":0}],[]]}
    return flow


def build_operations():
    digest_query = "SELECT value AS digest, (SELECT value FROM triage.config WHERE key='outbound_email') AS outbound FROM triage.config WHERE key='digest';"
    heartbeat_query = "SELECT value AS heartbeat, (SELECT value FROM triage.config WHERE key='contacts') AS contacts FROM triage.config WHERE key='heartbeat';"
    conversation_query = "SELECT m.id, t.ref, t.airtable_record_id AS request_record_id, m.direction, m.channel, m.intent, m.body, m.external_message_id, m.delivery_state, m.created_at, a.value AS airtable FROM triage.ticket_messages m JOIN triage.tickets t ON t.id=m.ticket_id CROSS JOIN (SELECT value FROM triage.config WHERE key='airtable') a WHERE m.airtable_synced_at IS NULL AND t.airtable_record_id IS NOT NULL ORDER BY m.id LIMIT 25;"
    nodes = [
        node("Daily Digest Schedule", "n8n-nodes-base.scheduleTrigger", 1.2, [-720,-140], {"rule":{"interval":[{"field":"cronExpression","expression":"0 7 * * *"}]}}),
        node("Heartbeat Schedule", "n8n-nodes-base.scheduleTrigger", 1.2, [-720,20], {"rule":{"interval":[{"field":"minutes","minutesInterval":15}]}}),
        node("Emergency Escalation Schedule", "n8n-nodes-base.scheduleTrigger", 1.2, [-720,180], {"rule":{"interval":[{"field":"minutes","minutesInterval":15}]}}),
        node("Conversation Sync Schedule", "n8n-nodes-base.scheduleTrigger", 1.2, [-720,340], {"rule":{"interval":[{"field":"minutes","minutesInterval":5}]}}),
        pg("Postgres Load Digest Config", [-480,-140], digest_query), code("Prepare Digest", [-240,-140], """return $input.all().flatMap(item=>{const d=typeof item.json.digest==='string'?JSON.parse(item.json.digest):item.json.digest||{}; const o=typeof item.json.outbound==='string'?JSON.parse(item.json.outbound):item.json.outbound||{}; return d.enabled&&d.to_email?[{json:{from_email:`${o.from_name || 'Demo Maintenance Desk'} <${o.from_email || 'sambhavn8n@gmail.com'}>`,to_email:d.to_email,email_subject:(d.subject_prefix || 'Daily maintenance triage digest'),email_body:'Open maintenance requests are available in Airtable.'}}]:[];});"""), email("SMTP Send Daily Digest", [0,-140]),
        pg("Postgres Load Heartbeat Config", [-480,20], heartbeat_query), code("Prepare Heartbeat", [-240,20], """return $input.all().flatMap(item=>{const h=typeof item.json.heartbeat==='string'?JSON.parse(item.json.heartbeat):item.json.heartbeat||{}; const c=typeof item.json.contacts==='string'?JSON.parse(item.json.contacts):item.json.contacts||{}; return h.enabled&&c.operator_chat_id?[{json:{chat_id:c.operator_chat_id,message_text:'OPERATOR HEARTBEAT: maintenance intake is quiet. Check Airtable.'}}]:[];});"""), telegram("Telegram Send Operator Heartbeat", [0,20], {"id":"stage1TelegramLocal","name":"maintenance-triage-telegram-bot"}),
        pg("Postgres Select Unanswered Emergencies", [-480,180], "SELECT id AS ticket_id FROM triage.tickets WHERE priority='EMERGENCY' AND vendor_status IN ('NOT_STARTED','AWAITING_VENDOR','NEEDS_VENDOR_ASSIGNMENT') AND closed_at IS NULL AND received_at < now() - interval '15 minutes' ORDER BY received_at LIMIT 10;"), execute("Execute Manager Desk Escalation", [-240,180], MANAGER_ID),
        pg("Postgres Select Unsynced Conversations", [-480,340], conversation_query), code("Prepare Airtable Conversation Append", [-240,340], """return $input.all().flatMap(item=>{const j=item.json; const a=typeof j.airtable==='string'?JSON.parse(j.airtable):j.airtable||{}; return a.enabled&&a.base_id&&j.request_record_id?[{json:{...j,airtable_url:`https://api.airtable.com/v0/${a.base_id}/${encodeURIComponent(a.conversations_table||'Conversations')}`,airtable_body:{records:[{fields:{'Request':[j.request_record_id],'Direction':j.direction,'Channel':j.channel,'Intent':j.intent,'Body':j.body,'External Message ID':j.external_message_id||'','Delivery State':j.delivery_state,'At':j.created_at}}]}}}]:[];});"""), airtable("HTTP Airtable Append Conversation", [0,340], "POST", "={{ $json.airtable_url }}", "={{ $json.airtable_body }}"), code("Attach Conversation Sync Result", [240,340], """const ctx=$(\"Prepare Airtable Conversation Append\").all(); return $input.all().map((item,i)=>({json:{id:ctx[i].json.id,airtable_record_id:item.json.body?.records?.[0]?.id || item.json.records?.[0]?.id || '',sync_error:item.json.error || ''}}));"""), pg("Postgres Mark Conversation Synced", [480,340], "UPDATE triage.ticket_messages SET airtable_record_id=NULLIF($2::text,''), airtable_synced_at=CASE WHEN NULLIF($3::text,'') IS NULL THEN now() ELSE NULL END WHERE id=$1::bigint RETURNING id;", "={{ [$json.id,$json.airtable_record_id || '',$json.sync_error || ''] }}"),
    ]
    return workflow(OPS_ID, "Maintenance Operations", nodes, {
        "Daily Digest Schedule":{"main":[[{"node":"Postgres Load Digest Config","type":"main","index":0}]]}, "Postgres Load Digest Config":{"main":[[{"node":"Prepare Digest","type":"main","index":0}]]}, "Prepare Digest":{"main":[[{"node":"SMTP Send Daily Digest","type":"main","index":0}]]},
        "Heartbeat Schedule":{"main":[[{"node":"Postgres Load Heartbeat Config","type":"main","index":0}]]}, "Postgres Load Heartbeat Config":{"main":[[{"node":"Prepare Heartbeat","type":"main","index":0}]]}, "Prepare Heartbeat":{"main":[[{"node":"Telegram Send Operator Heartbeat","type":"main","index":0}]]},
        "Emergency Escalation Schedule":{"main":[[{"node":"Postgres Select Unanswered Emergencies","type":"main","index":0}]]}, "Postgres Select Unanswered Emergencies":{"main":[[{"node":"Execute Manager Desk Escalation","type":"main","index":0}]]},
        "Conversation Sync Schedule":{"main":[[{"node":"Postgres Select Unsynced Conversations","type":"main","index":0}]]}, "Postgres Select Unsynced Conversations":{"main":[[{"node":"Prepare Airtable Conversation Append","type":"main","index":0}]]}, "Prepare Airtable Conversation Append":{"main":[[{"node":"HTTP Airtable Append Conversation","type":"main","index":0}]]}, "HTTP Airtable Append Conversation":{"main":[[{"node":"Attach Conversation Sync Result","type":"main","index":0}]]}, "Attach Conversation Sync Result":{"main":[[{"node":"Postgres Mark Conversation Synced","type":"main","index":0}]]},
    })


def build_tools():
    fixture_names = [
        "01-understated-gas", "02-panicked-burst-pipe-no-unit", "03-urgent-squeaky-door",
        "04-buried-lede", "05-spanish-no-hot-water", "06-accommodation-request",
    ]
    payloads = [{
        "source": "fixture", "from_address": f"{name}@fixture.example", "subject": name,
        "body_raw": (FIXTURES / f"{name}.txt").read_text(encoding="utf-8").strip(),
        "received_at": "2026-08-12T12:00:00Z", "attachment_paths": [],
        "msg_id": f"<stage9-{name}@fixture.example>", "in_reply_to": None, "refs": None,
    } for name in fixture_names]
    return workflow(TOOLS_ID, "Maintenance Triage Demo Tools", [
        node("Manual Demo Tool Trigger", "n8n-nodes-base.manualTrigger", 1, [-360,0]),
        code("Load Six Safe Demo Fixtures", [-120,0], f"return {json.dumps(payloads)}.map(json => ({{json}}));"),
        execute("Execute Triage Engine For Fixtures", [120,0], ENGINE_ID, True),
        code("Finish Safe Fixture Rehearsal", [360,0], "return [{json:{message:'Six fixture requests processed without manager, vendor, or tenant sends.'}}];"),
    ], {"Manual Demo Tool Trigger":{"main":[[{"node":"Load Six Safe Demo Fixtures","type":"main","index":0}]]}, "Load Six Safe Demo Fixtures":{"main":[[{"node":"Execute Triage Engine For Fixtures","type":"main","index":0}]]}, "Execute Triage Engine For Fixtures":{"main":[[{"node":"Finish Safe Fixture Rehearsal","type":"main","index":0}]]}})


def main():
    WORKFLOWS.mkdir(exist_ok=True)
    outputs = [
        ("maintenance-triage-tenant-intake.json", build_intake()),
        ("maintenance-triage-tenant-telegram.json", build_tenant_telegram()),
        ("maintenance-triage-manager-desk.json", build_manager_desk()),
        ("maintenance-triage-operations.json", build_operations()),
        ("maintenance-triage-demo-tools.json", build_tools()),
    ]
    for filename, data in outputs:
        path = WORKFLOWS / filename
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import json
import pathlib
import textwrap


ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / "workflows"

ALERT_ID = "mt-alert-dispatch-stage-6"
APPROVAL_ID = "mt-approval-action-stage-6"
CALLBACK_ID = "mt-telegram-callback-stage-6"
ESCALATION_ID = "mt-emergency-escalation-stage-6"
DRIVER_ID = "mt-stage-6-driver"


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


def pg_node(name, position, query, replacements_expr):
    return node(
        name,
        "n8n-nodes-base.postgres",
        2.6,
        position,
        {
            "resource": "database",
            "operation": "executeQuery",
            "query": textwrap.dedent(query).strip(),
            "options": {"queryReplacement": replacements_expr},
        },
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


def execute_workflow_node(name, position, workflow_id):
    return node(
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


def telegram_node(name, position, parameters):
    data = node(
        name,
        "n8n-nodes-base.telegram",
        1.2,
        position,
        parameters,
        credentials={
            "telegramApi": {
                "id": "stage1TelegramLocal",
                "name": "maintenance-triage-telegram-bot",
            }
        },
    )
    data["continueOnFail"] = True
    return data


def email_node(name, position):
    data = node(
        name,
        "n8n-nodes-base.emailSend",
        2.1,
        position,
        {
            "fromEmail": "={{ $json.from_email }}",
            "toEmail": "={{ $json.to_email }}",
            "subject": "={{ $json.email_subject }}",
            "emailFormat": "text",
            "text": "={{ $json.email_body }}",
            "options": {"appendAttribution": False, "replyTo": "={{ $json.from_email }}"},
        },
        credentials={
            "smtp": {
                "id": "stage1GreenmailSmtpLocal",
                "name": "maintenance-triage-greenmail-smtp-local",
            }
        },
    )
    data["continueOnFail"] = True
    return data


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
        "meta": {"stage": 6, "generatedBy": "scripts/build-stage-6-workflows.py"},
        "versionId": "stage-6-generated",
        "triggerCount": 0,
        "tags": [],
    }


def build_alert_dispatch():
    load_query = r"""
    WITH input_values AS (
      SELECT
        NULLIF($1::text, '')::bigint AS ticket_id,
        coalesce(NULLIF($2::text, '')::jsonb, '{}'::jsonb) AS test_mode
    ),
    configs AS (
      SELECT
        coalesce((SELECT value FROM triage.config WHERE key = 'board'), '{}'::jsonb) AS board,
        coalesce((SELECT value FROM triage.config WHERE key = 'contacts'), '{}'::jsonb) AS contacts,
        coalesce((SELECT value FROM triage.config WHERE key = 'company'), '{}'::jsonb) AS company,
        coalesce((SELECT value FROM triage.config WHERE key = 'quiet_hours'), '{}'::jsonb) AS quiet_hours,
        coalesce((SELECT value FROM triage.config WHERE key = 'limits'), '{}'::jsonb) AS limits
    ),
    recent AS (
      SELECT count(*)::int AS alert_count
      FROM triage.events
      WHERE action IN ('telegram_alert_sent', 'telegram_alert_mocked', 'telegram_alert_grouped')
        AND at >= now() - interval '1 hour'
    )
    SELECT
      to_jsonb(t) AS ticket,
      i.test_mode,
      c.board,
      c.contacts,
      c.company,
      c.quiet_hours,
      c.limits,
      r.alert_count,
      now() AS loaded_at
    FROM input_values i
    CROSS JOIN configs c
    CROSS JOIN recent r
    LEFT JOIN triage.tickets t ON t.id = i.ticket_id;
    """

    prepare_js = r"""
    function parseJson(value, fallback) {
      if (value === null || value === undefined || value === "") return fallback;
      if (typeof value === "string") {
        try { return JSON.parse(value); } catch (error) { return fallback; }
      }
      return value;
    }
    function isPlaceholder(value) {
      return !value || String(value).startsWith("PLACEHOLDER_");
    }
    function escHtml(value) {
      return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
    }
    function truncate(value, max) {
      const text = String(value ?? "").replace(/\s+/g, " ").trim();
      return text.length <= max ? text : `${text.slice(0, max - 1)}...`;
    }
    function inQuietHours(config, testMode) {
      if (testMode.force_quiet_hours === true) return true;
      if (testMode.force_business_hours === true) return false;
      const start = String(config.start || "20:00");
      const end = String(config.end || "07:00");
      const tz = config.tz || "America/Chicago";
      const parts = new Intl.DateTimeFormat("en-US", {
        timeZone: tz,
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
      }).formatToParts(new Date());
      const hour = Number(parts.find(p => p.type === "hour")?.value || 0);
      const minute = Number(parts.find(p => p.type === "minute")?.value || 0);
      const nowMin = hour * 60 + minute;
      const [sh, sm] = start.split(":").map(Number);
      const [eh, em] = end.split(":").map(Number);
      const startMin = (sh || 0) * 60 + (sm || 0);
      const endMin = (eh || 0) * 60 + (em || 0);
      if (startMin === endMin) return false;
      return startMin < endMin
        ? nowMin >= startMin && nowMin < endMin
        : nowMin >= startMin || nowMin < endMin;
    }
    function signals(ticket) {
      const parsed = parseJson(ticket.safety_signals, []);
      return Array.isArray(parsed) ? parsed.filter(v => v && v !== "NONE").map(String) : [];
    }
    function button(label, data) {
      return { text: label, additionalFields: { callback_data: data } };
    }
    function actionButtons(ticket) {
      if (ticket.priority === "EMERGENCY") {
        return {
          rows: [
            { row: { buttons: [
              button("Approve reply", `act:${ticket.id}:approve`),
              button("Hold", `act:${ticket.id}:hold`),
            ] } },
            { row: { buttons: [
              button("Not emergency", `act:${ticket.id}:not_emergency`),
            ] } },
          ],
        };
      }
      if (ticket.priority === "URGENT") {
        return {
          rows: [
            { row: { buttons: [button("Approve reply", `act:${ticket.id}:approve`)] } },
          ],
        };
      }
      return {};
    }
    function boardLink(board, ticket) {
      const token = board?.token || "";
      if (!token) return "Board token missing";
      return `http://localhost:5678/webhook/board?t=${encodeURIComponent(token)}&ref=${encodeURIComponent(ticket.ref)}`;
    }
    function messageFor(ticket, kind, board, company) {
      const unit = ticket.unit_identifier || "UNIT NOT STATED";
      const target = ticket.sla_due_at ? new Date(ticket.sla_due_at).toLocaleString("en-US", { timeZone: company.timezone || "America/Chicago", hour: "numeric", minute: "2-digit", month: "short", day: "numeric" }) : "Not set";
      const tenant = truncate(ticket.body_clean || ticket.body_raw || "", 420);
      const override = ticket.override_applied && ticket.override_reason ? `\nOverride: ${ticket.override_reason}` : "";
      return [
        `${kind}: ${ticket.ref}`,
        `Unit: ${unit}`,
        `Summary: ${ticket.issue_summary || ticket.subject || "Maintenance request"}`,
        `Trade: ${ticket.trade || "UNKNOWN"}`,
        `Target: ${target}`,
        override.trim(),
        `Tenant words: "${tenant}"`,
        `Board: ${boardLink(board, ticket)}`,
      ].filter(Boolean).map(escHtml).join("\n");
    }

    return $input.all().map((item) => {
      const row = item.json;
      const ticket = parseJson(row.ticket, null);
      const testMode = parseJson(row.test_mode, {});
      const board = parseJson(row.board, {});
      const contacts = parseJson(row.contacts, {});
      const company = parseJson(row.company, {});
      const quiet = parseJson(row.quiet_hours, {});
      const limits = parseJson(row.limits, {});
      if (!ticket) {
        return { json: { outcome: "not_found", action: "telegram_alert_skipped", should_send_real: false, detail: { reason: "ticket_not_found" } } };
      }

      const safetySignals = signals(ticket);
      const quietNow = inQuietHours(quiet, testMode);
      const maxAlerts = Number(limits.max_alerts_per_hour || 6);
      const recentAlerts = Number(row.alert_count || 0);
      const rateLimited = (testMode.force_rate_limit === true || recentAlerts >= maxAlerts) && testMode.ignore_rate_cap !== true;
      let outcome = "skipped";
      let reason = "priority_not_alertable";
      let kind = "";
      let silent = false;
      let shouldAlert = false;

      if (ticket.priority === "EMERGENCY") {
        kind = "EMERGENCY";
        shouldAlert = true;
        reason = "emergency";
      } else if (ticket.priority === "URGENT") {
        kind = "URGENT";
        shouldAlert = !quietNow;
        silent = true;
        reason = shouldAlert ? "urgent_business_hours" : "urgent_quiet_hours_held";
      } else if (ticket.priority === "NEEDS_REVIEW") {
        kind = "NEEDS REVIEW";
        shouldAlert = !quietNow || safetySignals.length > 0;
        silent = !safetySignals.length;
        reason = shouldAlert ? (safetySignals.length ? "needs_review_safety_signal" : "needs_review_business_hours") : "needs_review_quiet_hours_held";
      }
      if (ticket.human_only && ticket.priority === "ROUTINE") {
        shouldAlert = false;
        reason = "routine_human_only_no_alert";
      }
      if (rateLimited && shouldAlert) {
        shouldAlert = false;
        outcome = "rate_limited";
        reason = "max_alerts_per_hour_reached";
      }
      if (shouldAlert) {
        outcome = testMode.mock_telegram === true ? "mocked" : "send_real";
      }
      if (testMode.force_telegram_error === true && ticket.priority === "EMERGENCY") {
        outcome = "failed";
        shouldAlert = false;
        reason = "simulated_telegram_failure";
      }

      const chatId = contacts.primary_chat_id || contacts.operator_chat_id || "";
      const canSendReal = outcome === "send_real" && !isPlaceholder(chatId);
      const text = messageFor(ticket, kind || "NOTICE", board, company);
      const inlineKeyboard = actionButtons(ticket);
      const hasButtons = inlineKeyboard.rows && inlineKeyboard.rows.length > 0;
      return {
        json: {
          ticket_id: ticket.id,
          ref: ticket.ref,
          priority: ticket.priority,
          outcome,
          action: outcome === "rate_limited" ? "telegram_alert_grouped" : (outcome === "failed" ? "telegram_alert_failed" : (outcome === "skipped" ? "telegram_alert_skipped" : (outcome === "mocked" ? "telegram_alert_mocked" : "telegram_alert_sent"))),
          reason,
          kind,
          chat_id: chatId,
          should_send_real: canSendReal,
          message_text: text,
          silent,
          reply_markup: hasButtons ? "inlineKeyboard" : "none",
          inline_keyboard: hasButtons ? inlineKeyboard : {},
          telegram_message_id: testMode.mock_message_id || null,
          alert_error: outcome === "failed" ? "simulated Telegram alert failure" : (outcome === "send_real" && isPlaceholder(chatId) ? "Telegram chat ID is not configured" : null),
          detail: {
            ref: ticket.ref,
            priority: ticket.priority,
            reason,
            quiet_hours: quietNow,
            safety_signals: safetySignals,
            silent,
            rate_limited: rateLimited,
            board_url: boardLink(board, ticket),
            mock: testMode.mock_telegram === true,
          },
        },
      };
    });
    """

    record_query = r"""
    WITH input_values AS (
      SELECT
        $1::bigint AS ticket_id,
        $2::text AS outcome,
        $3::text AS event_action,
        NULLIF($4::text, '') AS chat_id,
        NULLIF($5::text, '')::bigint AS telegram_message_id,
        NULLIF($6::text, '') AS alert_error,
        $7::jsonb AS detail
    ),
    updated AS (
      UPDATE triage.tickets t
      SET
        status = CASE WHEN i.outcome IN ('mocked', 'sent') THEN 'ALERTED' ELSE t.status END,
        alerted_at = CASE WHEN i.outcome IN ('mocked', 'sent') THEN now() ELSE t.alerted_at END,
        telegram_chat_id = CASE WHEN i.outcome IN ('mocked', 'sent') THEN i.chat_id ELSE t.telegram_chat_id END,
        telegram_msg_id = CASE WHEN i.outcome IN ('mocked', 'sent') THEN i.telegram_message_id ELSE t.telegram_msg_id END,
        last_alert_error = CASE WHEN i.outcome = 'failed' THEN i.alert_error ELSE t.last_alert_error END
      FROM input_values i
      WHERE t.id = i.ticket_id
      RETURNING t.id
    ),
    event_insert AS (
      INSERT INTO triage.events (ticket_id, actor, action, detail)
      SELECT
        i.ticket_id,
        'system',
        i.event_action,
        i.detail || jsonb_build_object('outcome', i.outcome, 'telegram_message_id', i.telegram_message_id, 'error', i.alert_error)
      FROM input_values i
      WHERE EXISTS (SELECT 1 FROM updated)
      RETURNING id
    )
    SELECT
      i.ticket_id,
      i.outcome,
      i.event_action,
      i.chat_id,
      i.telegram_message_id,
      i.alert_error
    FROM input_values i;
    """

    attach_telegram_js = r"""
    const contexts = $("Prepare Alert Action").all();
    return $input.all().map((item, index) => {
      const ctx = contexts[index].json;
      const response = item.json || {};
      const failed = Boolean(response.error);
      return {
        json: {
          ...ctx,
          outcome: failed ? "failed" : "sent",
          action: failed ? "telegram_alert_failed" : "telegram_alert_sent",
          telegram_message_id: failed ? null : (response.result?.message_id || response.message_id || null),
          alert_error: failed ? response.error : null,
        },
      };
    });
    """

    nodes = [
        node("Alert Dispatch Input", "n8n-nodes-base.executeWorkflowTrigger", 1.2, [-980, 0], {"inputSource": "passthrough", "returnOutput": "allRuns"}),
        pg_node("Postgres Load Alert Context", [-760, 0], load_query, "={{ [$json.ticket_id || $json.id || '', JSON.stringify($json.test_mode || {})] }}"),
        code_node("Prepare Alert Action", [-520, 0], prepare_js),
        if_node("Should Send Real Telegram", [-280, 0], "={{ $json.should_send_real }}"),
        telegram_node(
            "Telegram Send Alert",
            [-20, -120],
            {
                "resource": "message",
                "operation": "sendMessage",
                "chatId": "={{ $json.chat_id }}",
                "text": "={{ $json.message_text }}",
                "replyMarkup": "={{ $json.reply_markup }}",
                "inlineKeyboard": "={{ $json.inline_keyboard }}",
                "additionalFields": {
                    "appendAttribution": False,
                    "disable_notification": "={{ $json.silent }}",
                    "disable_web_page_preview": True,
                    "parse_mode": "HTML",
                },
            },
        ),
        code_node("Attach Telegram Send Result", [220, -120], attach_telegram_js),
        pg_node("Postgres Record Real Alert", [460, -120], record_query, "={{ [$json.ticket_id, $json.outcome, $json.action, $json.chat_id || '', $json.telegram_message_id || '', $json.alert_error || '', JSON.stringify($json.detail || {})] }}"),
        pg_node("Postgres Record Mock Or Skipped Alert", [0, 140], record_query, "={{ [$json.ticket_id || 0, $json.outcome, $json.action, $json.chat_id || '', $json.telegram_message_id || '', $json.alert_error || '', JSON.stringify($json.detail || {})] }}"),
    ]
    connections = {
        "Alert Dispatch Input": {"main": [[{"node": "Postgres Load Alert Context", "type": "main", "index": 0}]]},
        "Postgres Load Alert Context": {"main": [[{"node": "Prepare Alert Action", "type": "main", "index": 0}]]},
        "Prepare Alert Action": {"main": [[{"node": "Should Send Real Telegram", "type": "main", "index": 0}]]},
        "Should Send Real Telegram": {
            "main": [
                [{"node": "Telegram Send Alert", "type": "main", "index": 0}],
                [{"node": "Postgres Record Mock Or Skipped Alert", "type": "main", "index": 0}],
            ]
        },
        "Telegram Send Alert": {"main": [[{"node": "Attach Telegram Send Result", "type": "main", "index": 0}]]},
        "Attach Telegram Send Result": {"main": [[{"node": "Postgres Record Real Alert", "type": "main", "index": 0}]]},
    }
    return workflow_base(ALERT_ID, "Maintenance Triage Alert Dispatch", nodes, connections)


def build_approval_action():
    normalize_js = r"""
    function parseCallback(value) {
      const raw = String(value || "");
      const match = /^act:(\d+):(approve|hold|not_emergency)$/.exec(raw);
      if (!match) return { valid: false, ticket_id: null, action: null };
      return { valid: true, ticket_id: Number(match[1]), action: match[2] };
    }
    return $input.all().map((item) => {
      const src = item.json || {};
      const parsed = parseCallback(src.callback_data || src.data || "");
      return {
        json: {
          callback_data: src.callback_data || src.data || "",
          valid: parsed.valid,
          ticket_id: parsed.ticket_id,
          action_name: parsed.action,
          actor: src.actor || src.actor_username || src.username || "human:local",
          callback_query_id: src.callback_query_id || src.query_id || "",
          telegram_chat_id: src.telegram_chat_id || src.chat_id || "",
          telegram_message_id: src.telegram_message_id || src.message_id || "",
        },
      };
    });
    """

    action_query = r"""
    WITH input_values AS (
      SELECT
        $1::boolean AS valid,
        NULLIF($2::text, '')::bigint AS ticket_id,
        NULLIF($3::text, '') AS action_name,
        NULLIF($4::text, '') AS actor,
        NULLIF($5::text, '') AS telegram_chat_id,
        NULLIF($6::text, '')::bigint AS telegram_message_id
    ),
    cfg AS (
      SELECT
        coalesce((SELECT value FROM triage.config WHERE key = 'outbound_email'), '{}'::jsonb) AS outbound_email,
        coalesce((SELECT value FROM triage.config WHERE key = 'company'), '{}'::jsonb) AS company
    ),
    target AS (
      SELECT t.*
      FROM triage.tickets t
      JOIN input_values i ON i.ticket_id = t.id
    ),
    approve_claim AS (
      UPDATE triage.tickets t
      SET status = 'ACKED', acked_at = now(), acked_by = i.actor
      FROM input_values i
      WHERE i.valid
        AND i.action_name = 'approve'
        AND t.id = i.ticket_id
        AND t.status NOT IN ('ACKED', 'ACK_SENT')
        AND t.draft_body IS NOT NULL
        AND t.human_only = false
        AND t.priority <> 'NEEDS_REVIEW'
      RETURNING t.*
    ),
    hold_claim AS (
      UPDATE triage.tickets t
      SET status = 'HELD', acked_at = now(), acked_by = i.actor
      FROM input_values i
      WHERE i.valid
        AND i.action_name = 'hold'
        AND t.id = i.ticket_id
        AND t.status <> 'ACK_SENT'
      RETURNING t.*
    ),
    downgrade_claim AS (
      UPDATE triage.tickets t
      SET priority = 'URGENT', status = 'ACKED', acked_at = now(), acked_by = i.actor
      FROM input_values i
      WHERE i.valid
        AND i.action_name = 'not_emergency'
        AND t.id = i.ticket_id
        AND t.status <> 'ACK_SENT'
      RETURNING t.*
    ),
    feedback_insert AS (
      INSERT INTO triage.feedback (ticket_id, was, became, by_user)
      SELECT id, 'EMERGENCY', 'URGENT', (SELECT actor FROM input_values)
      FROM downgrade_claim
      WHERE priority = 'URGENT'
      RETURNING id
    ),
    event_insert AS (
      INSERT INTO triage.events (ticket_id, actor, action, detail)
      SELECT id, (SELECT actor FROM input_values), 'approval_claimed', jsonb_build_object('action', 'approve')
      FROM approve_claim
      UNION ALL
      SELECT id, (SELECT actor FROM input_values), 'held', jsonb_build_object('action', 'hold')
      FROM hold_claim
      UNION ALL
      SELECT id, (SELECT actor FROM input_values), 'not_emergency', jsonb_build_object('was', 'EMERGENCY', 'became', 'URGENT')
      FROM downgrade_claim
      RETURNING id
    ),
    final_ticket AS (
      SELECT * FROM approve_claim
      UNION ALL SELECT * FROM hold_claim
      UNION ALL SELECT * FROM downgrade_claim
      UNION ALL SELECT * FROM target WHERE NOT EXISTS (SELECT 1 FROM approve_claim) AND NOT EXISTS (SELECT 1 FROM hold_claim) AND NOT EXISTS (SELECT 1 FROM downgrade_claim)
      LIMIT 1
    )
    SELECT
      i.valid,
      i.action_name,
      i.actor,
      i.telegram_chat_id,
      i.telegram_message_id,
      to_jsonb(f) AS ticket,
      cfg.outbound_email,
      cfg.company,
      CASE
        WHEN NOT i.valid THEN 'invalid'
        WHEN NOT EXISTS (SELECT 1 FROM target) THEN 'not_found'
        WHEN i.action_name = 'approve' AND EXISTS (SELECT 1 FROM approve_claim) THEN 'send_email'
        WHEN i.action_name = 'approve' AND EXISTS (SELECT 1 FROM target WHERE status IN ('ACKED', 'ACK_SENT') OR out_msg_id IS NOT NULL) THEN 'already_handled'
        WHEN i.action_name = 'approve' THEN 'refused'
        WHEN i.action_name = 'hold' AND EXISTS (SELECT 1 FROM hold_claim) THEN 'held'
        WHEN i.action_name = 'not_emergency' AND EXISTS (SELECT 1 FROM downgrade_claim) THEN 'not_emergency'
        ELSE 'already_handled'
      END AS action_result
    FROM input_values i
    CROSS JOIN cfg
    LEFT JOIN final_ticket f ON true;
    """

    prepare_email_js = r"""
    function parseJson(value, fallback) {
      if (value === null || value === undefined || value === "") return fallback;
      if (typeof value === "string") {
        try { return JSON.parse(value); } catch (error) { return fallback; }
      }
      return value;
    }
    function emailFor(ticket, outbound, company) {
      const fromName = outbound.from_name || company.from_name || "Demo Maintenance Desk";
      const fromEmail = outbound.from_email || "maintenance@example.test";
      const toEmail = outbound.mode === "test_only"
        ? (outbound.test_to || "maintenance@example.test")
        : (ticket.tenant_contact || outbound.test_to || "maintenance@example.test");
      return {
        from_email: `${fromName} <${fromEmail}>`,
        to_email: toEmail,
        email_subject: `[${ticket.ref}] ${ticket.draft_subject || "Maintenance request received"}`,
        email_body: ticket.draft_body,
      };
    }
    return $input.all().map((item) => {
      const row = item.json;
      const ticket = parseJson(row.ticket, null);
      const outbound = parseJson(row.outbound_email, {});
      const company = parseJson(row.company, {});
      const result = row.action_result;
      const canEmail = result === "send_email" && Boolean(ticket && ticket.draft_body);
      const email = canEmail ? emailFor(ticket, outbound, company) : {};
      let answer = "Action recorded.";
      if (result === "send_email") answer = "Sending approved reply.";
      if (result === "already_handled") answer = "Already sent or already being handled.";
      if (result === "refused") answer = "No draft can be sent for this ticket.";
      if (result === "held") answer = "Held. No email sent.";
      if (result === "not_emergency") answer = "Changed to urgent. No email sent.";
      if (result === "invalid") answer = "Invalid action.";
      if (result === "not_found") answer = "Ticket not found.";
      return {
        json: {
          ...row,
          ticket,
          should_send_email: canEmail,
          answer_text: answer,
          edit_text: ticket ? `${ticket.ref}: ${answer}` : answer,
          ...email,
        },
      };
    });
    """

    attach_email_js = r"""
    const contexts = $("Prepare Email Payload").all().filter(item => item.json.should_send_email);
    return $input.all().map((item, index) => {
      const ctx = contexts[index].json;
      const response = item.json || {};
      const error = response.error || null;
      return {
        json: {
          ...ctx,
          email_error: error,
          out_msg_id: error ? null : (response.messageId || response.message_id || response.response || null),
        },
      };
    });
    """

    no_email_js = r"""
    return $input.all()
      .filter(item => !item.json.should_send_email)
      .map(item => ({ json: item.json }));
    """

    finalize_query = r"""
    WITH input_values AS (
      SELECT
        $1::bigint AS ticket_id,
        NULLIF($2::text, '') AS out_msg_id,
        NULLIF($3::text, '') AS outbound_to,
        NULLIF($4::text, '') AS email_error,
        NULLIF($5::text, '') AS actor
    ),
    success_update AS (
      UPDATE triage.tickets t
      SET
        status = 'ACK_SENT',
        out_msg_id = i.out_msg_id,
        outbound_to = i.outbound_to,
        outbound_sent_at = now(),
        last_alert_error = NULL
      FROM input_values i
      WHERE t.id = i.ticket_id
        AND i.email_error IS NULL
      RETURNING t.*
    ),
    failure_update AS (
      UPDATE triage.tickets t
      SET last_alert_error = i.email_error
      FROM input_values i
      WHERE t.id = i.ticket_id
        AND i.email_error IS NOT NULL
      RETURNING t.*
    ),
    event_insert AS (
      INSERT INTO triage.events (ticket_id, actor, action, detail)
      SELECT id, (SELECT actor FROM input_values), 'tenant_reply_sent', jsonb_build_object('out_msg_id', out_msg_id, 'outbound_to', outbound_to)
      FROM success_update
      UNION ALL
      SELECT id, 'system', 'tenant_reply_send_failed', jsonb_build_object('error', (SELECT email_error FROM input_values))
      FROM failure_update
      RETURNING id
    )
    SELECT
      coalesce((SELECT id FROM success_update), (SELECT id FROM failure_update), (SELECT ticket_id FROM input_values)) AS ticket_id,
      CASE WHEN (SELECT email_error FROM input_values) IS NULL THEN 'sent' ELSE 'failed' END AS email_result,
      (SELECT out_msg_id FROM input_values) AS out_msg_id,
      (SELECT email_error FROM input_values) AS email_error;
    """

    attach_finalize_js = r"""
    const contexts = $("Attach Email Send Result").all();
    return $input.all().map((item, index) => {
      const ctx = contexts[index].json;
      const result = item.json || {};
      const sent = result.email_result === "sent";
      return {
        json: {
          ...ctx,
          action_result: sent ? "sent" : "email_failed",
          answer_text: sent ? "Sent." : "Email failed. Nothing else was sent.",
          edit_text: ctx.ticket ? `${ctx.ticket.ref}: ${sent ? "Reply sent" : "Email failed"}` : (sent ? "Reply sent" : "Email failed"),
          out_msg_id: result.out_msg_id || ctx.out_msg_id || null,
          email_error: result.email_error || ctx.email_error || null,
        },
      };
    });
    """

    result_passthrough_js = r"""
    return $input.all().map(item => ({ json: item.json }));
    """

    nodes = [
        node("Approval Action Input", "n8n-nodes-base.executeWorkflowTrigger", 1.2, [-1180, 0], {"inputSource": "passthrough", "returnOutput": "allRuns"}),
        code_node("Normalize Approval Action", [-960, 0], normalize_js),
        pg_node("Postgres Approval Gate", [-720, 0], action_query, "={{ [$json.valid, $json.ticket_id || '', $json.action_name || '', $json.actor || '', $json.telegram_chat_id || '', $json.telegram_message_id || ''] }}"),
        code_node("Prepare Email Payload", [-480, 0], prepare_email_js),
        if_node("Should Send Approved Email", [-240, 0], "={{ $json.should_send_email }}"),
        email_node("SMTP Send Approved Reply", [20, -120]),
        code_node("Attach Email Send Result", [260, -120], attach_email_js),
        pg_node("Postgres Finalize Approved Email", [500, -120], finalize_query, "={{ [$json.ticket?.id || $json.ticket_id, $json.out_msg_id || '', $json.to_email || '', $json.email_error || '', $json.actor || 'human:local'] }}"),
        code_node("Attach Final Email Result", [740, -120], attach_finalize_js),
        code_node("Return Non Email Action", [20, 140], no_email_js),
        code_node("Approval Action Result", [980, 0], result_passthrough_js),
    ]
    connections = {
        "Approval Action Input": {"main": [[{"node": "Normalize Approval Action", "type": "main", "index": 0}]]},
        "Normalize Approval Action": {"main": [[{"node": "Postgres Approval Gate", "type": "main", "index": 0}]]},
        "Postgres Approval Gate": {"main": [[{"node": "Prepare Email Payload", "type": "main", "index": 0}]]},
        "Prepare Email Payload": {"main": [[{"node": "Should Send Approved Email", "type": "main", "index": 0}]]},
        "Should Send Approved Email": {
            "main": [
                [{"node": "SMTP Send Approved Reply", "type": "main", "index": 0}],
                [{"node": "Return Non Email Action", "type": "main", "index": 0}],
            ]
        },
        "SMTP Send Approved Reply": {"main": [[{"node": "Attach Email Send Result", "type": "main", "index": 0}]]},
        "Attach Email Send Result": {"main": [[{"node": "Postgres Finalize Approved Email", "type": "main", "index": 0}]]},
        "Postgres Finalize Approved Email": {"main": [[{"node": "Attach Final Email Result", "type": "main", "index": 0}]]},
        "Attach Final Email Result": {"main": [[{"node": "Approval Action Result", "type": "main", "index": 0}]]},
        "Return Non Email Action": {"main": [[{"node": "Approval Action Result", "type": "main", "index": 0}]]},
    }
    return workflow_base(APPROVAL_ID, "Maintenance Triage Approval Action", nodes, connections)


def build_callback():
    normalize_js = r"""
    return $input.all().map((item) => {
      const cq = item.json.callback_query || item.json;
      return {
        json: {
          callback_data: cq.data || "",
          callback_query_id: cq.id || "",
          actor_username: cq.from?.username ? `human:${cq.from.username}` : (cq.from?.first_name ? `human:${cq.from.first_name}` : "human:telegram"),
          telegram_chat_id: cq.message?.chat?.id || "",
          telegram_message_id: cq.message?.message_id || "",
        },
      };
    });
    """

    nodes = [
        node(
            "Telegram Callback Trigger",
            "n8n-nodes-base.telegramTrigger",
            1.3,
            [-960, 0],
            {"updates": ["callback_query"], "additionalFields": {}},
            credentials={
                "telegramApi": {
                    "id": "stage1TelegramLocal",
                    "name": "maintenance-triage-telegram-bot",
                }
            },
        ),
        code_node("Normalize Telegram Callback", [-720, 0], normalize_js),
        execute_workflow_node("Execute Approval Action", [-480, 0], APPROVAL_ID),
        telegram_node(
            "Telegram Answer Callback",
            [-240, 0],
            {
                "resource": "callback",
                "operation": "answerQuery",
                "queryId": "={{ $json.callback_query_id }}",
                "additionalFields": {"text": "={{ $json.answer_text }}", "show_alert": False},
            },
        ),
        if_node("Has Telegram Message To Edit", [0, 0], "={{ Boolean($json.telegram_chat_id && $json.telegram_message_id) }}"),
        telegram_node(
            "Telegram Edit Alert Message",
            [240, -100],
            {
                "resource": "message",
                "operation": "editMessageText",
                "messageType": "message",
                "chatId": "={{ $json.telegram_chat_id }}",
                "messageId": "={{ $json.telegram_message_id }}",
                "text": "={{ $json.edit_text }}",
                "replyMarkup": "none",
                "additionalFields": {"parse_mode": "HTML", "disable_web_page_preview": True},
            },
        ),
    ]
    connections = {
        "Telegram Callback Trigger": {"main": [[{"node": "Normalize Telegram Callback", "type": "main", "index": 0}]]},
        "Normalize Telegram Callback": {"main": [[{"node": "Execute Approval Action", "type": "main", "index": 0}]]},
        "Execute Approval Action": {"main": [[{"node": "Telegram Answer Callback", "type": "main", "index": 0}]]},
        "Telegram Answer Callback": {"main": [[{"node": "Has Telegram Message To Edit", "type": "main", "index": 0}]]},
        "Has Telegram Message To Edit": {"main": [[{"node": "Telegram Edit Alert Message", "type": "main", "index": 0}], []]},
    }
    return workflow_base(CALLBACK_ID, "Maintenance Triage Telegram Callback", nodes, connections)


def build_escalation():
    select_query = r"""
    WITH cfg AS (
      SELECT coalesce((SELECT value FROM triage.config WHERE key = 'escalate_after'), '{"EMERGENCY_minutes":15}'::jsonb) AS value
    )
    SELECT
      t.id AS ticket_id,
      jsonb_build_object('mock_telegram', true, 'ignore_rate_cap', true, 'escalation_run', true) AS test_mode
    FROM triage.tickets t, cfg
    WHERE t.priority = 'EMERGENCY'
      AND t.acked_at IS NULL
      AND t.closed_at IS NULL
      AND t.received_at < now() - make_interval(mins => coalesce((cfg.value->>'EMERGENCY_minutes')::int, 15))
      AND (t.alerted_at IS NULL OR t.alerted_at < now() - make_interval(mins => coalesce((cfg.value->>'EMERGENCY_minutes')::int, 15)))
    ORDER BY t.received_at
    LIMIT 10;
    """
    nodes = [
        node("Every 15 Minutes", "n8n-nodes-base.scheduleTrigger", 1.2, [-600, 0], {"rule": {"interval": [{"field": "minutes", "minutesInterval": 15}]}}),
        pg_node("Postgres Select Emergency Escalations", [-360, 0], select_query, "={{ [] }}"),
        execute_workflow_node("Execute Alert Dispatch For Escalations", [-100, 0], ALERT_ID),
    ]
    connections = {
        "Every 15 Minutes": {"main": [[{"node": "Postgres Select Emergency Escalations", "type": "main", "index": 0}]]},
        "Postgres Select Emergency Escalations": {"main": [[{"node": "Execute Alert Dispatch For Escalations", "type": "main", "index": 0}]]},
    }
    return workflow_base(ESCALATION_ID, "Maintenance Triage Emergency Escalation", nodes, connections)


def build_driver():
    select_query = r"""
    SELECT ref, id, priority, status
    FROM triage.tickets
    WHERE ref BETWEEN 'MR-0001' AND 'MR-0012'
    ORDER BY ref;
    """
    dispatch_js = r"""
    const rows = $input.all().map(item => item.json);
    const cases = [];
    for (const row of rows) {
      cases.push({
        ticket_id: row.id,
        ref: row.ref,
        test_mode: { mock_telegram: true, force_business_hours: true, ignore_rate_cap: true }
      });
    }
    const byRef = Object.fromEntries(rows.map(row => [row.ref, row]));
    if (byRef["MR-0005"]) {
      cases.push({
        ticket_id: byRef["MR-0005"].id,
        ref: byRef["MR-0005"].ref,
        test_mode: { mock_telegram: true, force_quiet_hours: true, ignore_rate_cap: true }
      });
    }
    if (byRef["MR-0002"]) {
      cases.push({
        ticket_id: byRef["MR-0002"].id,
        ref: byRef["MR-0002"].ref,
        test_mode: { mock_telegram: true, force_business_hours: true, force_rate_limit: true }
      });
    }
    if (byRef["MR-0007"]) {
      cases.push({
        ticket_id: byRef["MR-0007"].id,
        ref: byRef["MR-0007"].ref,
        test_mode: { force_telegram_error: true, ignore_rate_cap: true }
      });
    }
    return cases.map(json => ({ json }));
    """
    approval_js = r"""
    const rows = $("Postgres Select Stage 6 Tickets").all().map(item => item.json);
    const byRef = Object.fromEntries(rows.map(row => [row.ref, row]));
    const cases = [];
    if (byRef["MR-0001"]) {
      cases.push({ callback_data: `act:${byRef["MR-0001"].id}:approve`, actor: "human:stage6", telegram_chat_id: "mock-chat", telegram_message_id: "61001" });
      cases.push({ callback_data: `act:${byRef["MR-0001"].id}:approve`, actor: "human:stage6-second-tap", telegram_chat_id: "mock-chat", telegram_message_id: "61001" });
    }
    if (byRef["MR-0005"]) {
      cases.push({ callback_data: `act:${byRef["MR-0005"].id}:hold`, actor: "human:stage6", telegram_chat_id: "mock-chat", telegram_message_id: "61005" });
    }
    if (byRef["MR-0002"]) {
      cases.push({ callback_data: `act:${byRef["MR-0002"].id}:not_emergency`, actor: "human:stage6", telegram_chat_id: "mock-chat", telegram_message_id: "61002" });
    }
    if (byRef["MR-0006"]) {
      cases.push({ callback_data: `act:${byRef["MR-0006"].id}:approve`, actor: "human:stage6", telegram_chat_id: "mock-chat", telegram_message_id: "61006" });
    }
    return cases.map(json => ({ json }));
    """
    nodes = [
        node("Manual Start", "n8n-nodes-base.manualTrigger", 1, [-900, 0]),
        pg_node("Postgres Select Stage 6 Tickets", [-660, 0], select_query, "={{ [] }}"),
        code_node("Prepare Mock Alert Dispatch Cases", [-420, 0], dispatch_js),
        execute_workflow_node("Execute Alert Dispatch", [-180, 0], ALERT_ID),
        code_node("Prepare Approval Cases", [60, 0], approval_js),
        execute_workflow_node("Execute Approval Actions", [300, 0], APPROVAL_ID),
    ]
    connections = {
        "Manual Start": {"main": [[{"node": "Postgres Select Stage 6 Tickets", "type": "main", "index": 0}]]},
        "Postgres Select Stage 6 Tickets": {"main": [[{"node": "Prepare Mock Alert Dispatch Cases", "type": "main", "index": 0}]]},
        "Prepare Mock Alert Dispatch Cases": {"main": [[{"node": "Execute Alert Dispatch", "type": "main", "index": 0}]]},
        "Execute Alert Dispatch": {"main": [[{"node": "Prepare Approval Cases", "type": "main", "index": 0}]]},
        "Prepare Approval Cases": {"main": [[{"node": "Execute Approval Actions", "type": "main", "index": 0}]]},
    }
    return workflow_base(DRIVER_ID, "Maintenance Triage Stage 6 Driver", nodes, connections)


def main():
    WORKFLOWS.mkdir(exist_ok=True)
    workflows = [
        ("maintenance-triage-alert-dispatch.json", build_alert_dispatch()),
        ("maintenance-triage-approval-action.json", build_approval_action()),
        ("maintenance-triage-telegram-callback.json", build_callback()),
        ("maintenance-triage-emergency-escalation.json", build_escalation()),
        ("maintenance-triage-stage-6-driver.json", build_driver()),
    ]
    for filename, workflow in workflows:
        path = WORKFLOWS / filename
        path.write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import json
import pathlib
import textwrap


ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / "workflows"

DIGEST_ID = "mt-digest-stage-8"
HEARTBEAT_ID = "mt-heartbeat-stage-8"


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


def pg_node(name, position, query, replacements_expr="={{ [] }}"):
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


def if_node(name, position, left_expr):
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
                        "rightValue": True,
                        "operator": {"type": "boolean", "operation": "true", "singleValue": True},
                    }
                ],
                "combinator": "and",
            },
        },
    )


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
            "emailFormat": "html",
            "html": "={{ $json.email_html }}",
            "options": {"appendAttribution": False, "replyTo": "={{ $json.from_email }}"},
        },
        credentials={
            "smtp": {
                "id": "stage7DemoSmtpDomain",
                "name": "maintenance-triage-demo-smtp-domain",
            }
        },
    )
    data["continueOnFail"] = True
    return data


def telegram_node(name, position):
    data = node(
        name,
        "n8n-nodes-base.telegram",
        1.2,
        position,
        {
            "resource": "message",
            "operation": "sendMessage",
            "chatId": "={{ $json.chat_id }}",
            "text": "={{ $json.message_text }}",
            "additionalFields": {
                "appendAttribution": False,
                "disable_notification": False,
                "disable_web_page_preview": True,
                "parse_mode": "HTML",
            },
        },
        credentials={
            "telegramApi": {
                "id": "stage1TelegramLocal",
                "name": "maintenance-triage-telegram-bot",
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
        "meta": {"stage": 8, "generatedBy": "scripts/build-stage-8-workflows.py"},
        "versionId": "stage-8-generated",
        "triggerCount": 0,
        "tags": [],
    }


def build_digest():
    load_query = r"""
    WITH cfg AS (
      SELECT
        coalesce((SELECT value FROM triage.config WHERE key = 'digest'), '{}'::jsonb) AS digest,
        coalesce((SELECT value FROM triage.config WHERE key = 'company'), '{}'::jsonb) AS company,
        coalesce((SELECT value FROM triage.config WHERE key = 'outbound_email'), '{}'::jsonb) AS outbound_email,
        coalesce((SELECT value FROM triage.config WHERE key = 'overdue_days'), '{}'::jsonb) AS overdue_days
    ),
    open_rows AS (
      SELECT t.*
      FROM triage.tickets t
      WHERE t.closed_at IS NULL
        AND t.status <> 'CLOSED'
    ),
    open_emergencies AS (
      SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY t.received_at), '[]'::jsonb) AS rows
      FROM open_rows t
      WHERE t.priority = 'EMERGENCY'
    ),
    breached_targets AS (
      SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY t.sla_due_at NULLS LAST, t.received_at), '[]'::jsonb) AS rows
      FROM open_rows t
      WHERE t.sla_due_at IS NOT NULL
        AND t.sla_due_at < now()
    ),
    overdue_items AS (
      SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY t.received_at), '[]'::jsonb) AS rows
      FROM open_rows t
      CROSS JOIN cfg c
      WHERE t.priority IN ('ROUTINE', 'URGENT')
        AND t.received_at < now() - make_interval(days => coalesce((c.overdue_days->>t.priority)::int, 999999))
    ),
    yesterday AS (
      SELECT jsonb_build_object(
        'total', count(*),
        'emergency', count(*) FILTER (WHERE priority = 'EMERGENCY'),
        'urgent', count(*) FILTER (WHERE priority = 'URGENT'),
        'routine', count(*) FILTER (WHERE priority = 'ROUTINE'),
        'needs_review', count(*) FILTER (WHERE priority = 'NEEDS_REVIEW'),
        'ack_sent', count(*) FILTER (WHERE status = 'ACK_SENT')
      ) AS value
      FROM triage.tickets
      WHERE received_at >= date_trunc('day', now()) - interval '1 day'
        AND received_at < date_trunc('day', now())
    )
    SELECT
      c.digest,
      c.company,
      c.outbound_email,
      c.overdue_days,
      now() AS generated_at,
      (SELECT rows FROM open_emergencies) AS open_emergencies,
      (SELECT rows FROM breached_targets) AS breached_targets,
      (SELECT rows FROM overdue_items) AS overdue_items,
      (SELECT value FROM yesterday) AS yesterday_counts
    FROM cfg c;
    """
    prepare_js = r"""
    function parseJson(value, fallback) {
      if (value === null || value === undefined || value === "") return fallback;
      if (typeof value === "string") {
        try { return JSON.parse(value); } catch (error) { return fallback; }
      }
      return value;
    }
    function esc(value) {
      return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
    }
    function rows(value) {
      const parsed = parseJson(value, []);
      return Array.isArray(parsed) ? parsed : [];
    }
    function itemLine(ticket) {
      const unit = ticket.unit_match_display || ticket.unit_identifier || "UNIT NOT STATED";
      const ref = ticket.ref || "MR-????";
      const summary = ticket.issue_summary || ticket.subject || "Maintenance request";
      const target = ticket.sla_due_at ? new Date(ticket.sla_due_at).toLocaleString("en-US", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" }) : "No target";
      return `<li><b>${esc(ref)}</b> ${esc(ticket.priority)} / ${esc(unit)} / ${esc(summary)} <span style="color:#666">Target: ${esc(target)}</span></li>`;
    }
    function section(title, list, emptyText) {
      return `<h2>${esc(title)}</h2>${list.length ? `<ul>${list.map(itemLine).join("")}</ul>` : `<p>${esc(emptyText)}</p>`}`;
    }

    return $input.all().map((item) => {
      const digest = parseJson(item.json.digest, {});
      const company = parseJson(item.json.company, {});
      const outbound = parseJson(item.json.outbound_email, {});
      const openEmergencies = rows(item.json.open_emergencies);
      const breachedTargets = rows(item.json.breached_targets);
      const overdueItems = rows(item.json.overdue_items);
      const counts = parseJson(item.json.yesterday_counts, {});
      const fromName = outbound.from_name || company.from_name || "Demo Maintenance Desk";
      const fromEmail = outbound.from_email || "maintenance@example.test";
      const toEmail = digest.to_email || outbound.test_to || outbound.from_email || fromEmail;
      const prefix = digest.subject_prefix || "Daily maintenance triage digest";
      const generated = new Date(item.json.generated_at || Date.now()).toLocaleString("en-US", { timeZone: digest.timezone || company.timezone || "America/Chicago" });
      const html = `<!doctype html>
        <html><body style="font-family:Arial,sans-serif;line-height:1.45;color:#222">
          <h1>${esc(company.name || "Demo Property Management")} maintenance digest</h1>
          <p>Generated ${esc(generated)}. Advisory demo digest; response targets are operational targets, not legal deadlines.</p>
          ${section("Still-open emergencies", openEmergencies, "No open emergencies.")}
          ${section("Breached response targets", breachedTargets, "No breached response targets.")}
          ${section("Overdue routine/urgent items", overdueItems, "No overdue routine or urgent items.")}
          <h2>Yesterday</h2>
          <p>Total ${esc(counts.total || 0)} / Emergency ${esc(counts.emergency || 0)} / Urgent ${esc(counts.urgent || 0)} / Routine ${esc(counts.routine || 0)} / Needs review ${esc(counts.needs_review || 0)} / Replies sent ${esc(counts.ack_sent || 0)}</p>
        </body></html>`;
      return {
        json: {
          should_send_digest: digest.enabled === true,
          from_email: `${fromName} <${fromEmail}>`,
          to_email: toEmail,
          email_subject: `${prefix} - ${new Date().toISOString().slice(0, 10)}`,
          email_html: html,
          open_emergency_count: openEmergencies.length,
          breached_count: breachedTargets.length,
          overdue_count: overdueItems.length,
        }
      };
    });
    """
    attach_js = r"""
    const contexts = $("Prepare Digest Email").all().filter(item => item.json.should_send_digest);
    return $input.all().map((item, index) => {
      const ctx = contexts[index]?.json || {};
      const response = item.json || {};
      return {
        json: {
          ...ctx,
          digest_error: response.error || null,
          digest_message_id: response.messageId || response.message_id || response.response || null,
        }
      };
    });
    """
    skip_js = r"""
    return $input.all()
      .filter(item => !item.json.should_send_digest)
      .map(item => ({ json: { ...item.json, digest_skipped: true } }));
    """
    nodes = [
        node("Manual Digest Trigger", "n8n-nodes-base.manualTrigger", 1, [-960, -120]),
        node("Daily 0700 Digest Schedule", "n8n-nodes-base.scheduleTrigger", 1.2, [-960, 120], {"rule": {"interval": [{"field": "cronExpression", "expression": "0 7 * * *"}]}}),
        pg_node("Postgres Load Digest Context", [-700, 0], load_query),
        code_node("Prepare Digest Email", [-460, 0], prepare_js),
        if_node("Should Send Digest Email", [-220, 0], "={{ Boolean($json.should_send_digest) }}"),
        email_node("SMTP Send Digest Email", [40, -120]),
        code_node("Attach Digest Send Result", [300, -120], attach_js),
        code_node("Return Digest Skipped", [40, 140], skip_js),
    ]
    connections = {
        "Manual Digest Trigger": {"main": [[{"node": "Postgres Load Digest Context", "type": "main", "index": 0}]]},
        "Daily 0700 Digest Schedule": {"main": [[{"node": "Postgres Load Digest Context", "type": "main", "index": 0}]]},
        "Postgres Load Digest Context": {"main": [[{"node": "Prepare Digest Email", "type": "main", "index": 0}]]},
        "Prepare Digest Email": {"main": [[{"node": "Should Send Digest Email", "type": "main", "index": 0}]]},
        "Should Send Digest Email": {
            "main": [
                [{"node": "SMTP Send Digest Email", "type": "main", "index": 0}],
                [{"node": "Return Digest Skipped", "type": "main", "index": 0}],
            ]
        },
        "SMTP Send Digest Email": {"main": [[{"node": "Attach Digest Send Result", "type": "main", "index": 0}]]},
    }
    return workflow_base(DIGEST_ID, "Maintenance Triage Daily Digest", nodes, connections)


def build_heartbeat():
    load_query = r"""
    WITH cfg AS (
      SELECT
        coalesce((SELECT value FROM triage.config WHERE key = 'heartbeat'), '{}'::jsonb) AS heartbeat,
        coalesce((SELECT value FROM triage.config WHERE key = 'contacts'), '{}'::jsonb) AS contacts,
        coalesce((SELECT value FROM triage.config WHERE key = 'company'), '{}'::jsonb) AS company,
        coalesce((SELECT value FROM triage.config WHERE key = 'board'), '{}'::jsonb) AS board
    ),
    state AS (
      SELECT
        c.*,
        coalesce(
          (SELECT max(at) FROM triage.events WHERE action = 'ingested'),
          nullif(c.heartbeat->>'baseline_at', '')::timestamptz,
          now()
        ) AS last_ingested_at,
        coalesce((c.heartbeat->>'threshold_minutes')::int, 720) AS threshold_minutes,
        coalesce((c.heartbeat->>'repeat_suppression_minutes')::int, 180) AS repeat_suppression_minutes,
        nullif(c.heartbeat->>'last_alert_at', '')::timestamptz AS last_alert_at
      FROM cfg c
    ),
    decision AS (
      SELECT
        *,
        (
          heartbeat->>'enabled' = 'true'
          AND now() - last_ingested_at > make_interval(mins => threshold_minutes)
          AND (
            last_alert_at IS NULL
            OR now() - last_alert_at > make_interval(mins => repeat_suppression_minutes)
          )
        ) AS should_alert
      FROM state
    ),
    updated AS (
      UPDATE triage.config c
      SET value = c.value
        || jsonb_build_object('last_checked_at', now())
        || CASE WHEN d.should_alert THEN jsonb_build_object('last_alert_at', now()) ELSE '{}'::jsonb END
      FROM decision d
      WHERE c.key = 'heartbeat'
      RETURNING c.value
    )
    SELECT
      d.heartbeat,
      d.contacts,
      d.company,
      d.board,
      d.last_ingested_at,
      d.threshold_minutes,
      d.repeat_suppression_minutes,
      d.last_alert_at,
      d.should_alert
    FROM decision d;
    """
    prepare_js = r"""
    function parseJson(value, fallback) {
      if (value === null || value === undefined || value === "") return fallback;
      if (typeof value === "string") {
        try { return JSON.parse(value); } catch (error) { return fallback; }
      }
      return value;
    }
    function escHtml(value) {
      return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
    }
    function boardLink(board) {
      const token = board?.token || "";
      const rawBase = board?.public_base_url || board?.base_url || board?.url || "http://localhost:5678";
      return `${String(rawBase).replace(/\/+$/, "")}/webhook/board?t=${encodeURIComponent(token)}`;
    }
    return $input.all().map((item) => {
      const contacts = parseJson(item.json.contacts, {});
      const company = parseJson(item.json.company, {});
      const board = parseJson(item.json.board, {});
      const lastIngested = item.json.last_ingested_at ? new Date(item.json.last_ingested_at) : null;
      const ageMinutes = lastIngested ? Math.round((Date.now() - lastIngested.getTime()) / 60000) : null;
      const chatId = contacts.operator_chat_id || contacts.primary_chat_id || "";
      const text = [
        "OPERATOR HEARTBEAT: maintenance triage intake is quiet",
        `Company: ${company.name || "Demo Property Management"}`,
        `Last ingested: ${lastIngested ? lastIngested.toISOString() : "unknown"}`,
        `Quiet for: ${ageMinutes === null ? "unknown" : `${ageMinutes} minutes`}`,
        `Threshold: ${item.json.threshold_minutes ?? 720} minutes`,
        `Board: ${boardLink(board)}`,
      ].map(escHtml).join("\n");
      return {
        json: {
          should_send_heartbeat: item.json.should_alert === true || item.json.should_alert === "true",
          chat_id: chatId,
          message_text: text,
        }
      };
    });
    """
    attach_js = r"""
    const contexts = $("Prepare Heartbeat Alert").all().filter(item => item.json.should_send_heartbeat);
    return $input.all().map((item, index) => {
      const ctx = contexts[index]?.json || {};
      const response = item.json || {};
      return {
        json: {
          ...ctx,
          heartbeat_error: response.error || null,
          telegram_message_id: response.result?.message_id || response.message_id || null,
        }
      };
    });
    """
    skip_js = r"""
    return $input.all()
      .filter(item => !item.json.should_send_heartbeat)
      .map(item => ({ json: { ...item.json, heartbeat_skipped: true } }));
    """
    nodes = [
        node("Manual Heartbeat Trigger", "n8n-nodes-base.manualTrigger", 1, [-960, -120]),
        node("Every 15 Minutes Heartbeat", "n8n-nodes-base.scheduleTrigger", 1.2, [-960, 120], {"rule": {"interval": [{"field": "minutes", "minutesInterval": 15}]}}),
        pg_node("Postgres Load Heartbeat State", [-700, 0], load_query),
        code_node("Prepare Heartbeat Alert", [-460, 0], prepare_js),
        if_node("Should Send Heartbeat Alert", [-220, 0], "={{ Boolean($json.should_send_heartbeat && $json.chat_id) }}"),
        telegram_node("Telegram Send Operator Heartbeat", [40, -120]),
        code_node("Attach Heartbeat Result", [300, -120], attach_js),
        code_node("Return Heartbeat Skipped", [40, 140], skip_js),
    ]
    connections = {
        "Manual Heartbeat Trigger": {"main": [[{"node": "Postgres Load Heartbeat State", "type": "main", "index": 0}]]},
        "Every 15 Minutes Heartbeat": {"main": [[{"node": "Postgres Load Heartbeat State", "type": "main", "index": 0}]]},
        "Postgres Load Heartbeat State": {"main": [[{"node": "Prepare Heartbeat Alert", "type": "main", "index": 0}]]},
        "Prepare Heartbeat Alert": {"main": [[{"node": "Should Send Heartbeat Alert", "type": "main", "index": 0}]]},
        "Should Send Heartbeat Alert": {
            "main": [
                [{"node": "Telegram Send Operator Heartbeat", "type": "main", "index": 0}],
                [{"node": "Return Heartbeat Skipped", "type": "main", "index": 0}],
            ]
        },
        "Telegram Send Operator Heartbeat": {"main": [[{"node": "Attach Heartbeat Result", "type": "main", "index": 0}]]},
    }
    return workflow_base(HEARTBEAT_ID, "Maintenance Triage Operator Heartbeat", nodes, connections)


def main():
    WORKFLOWS.mkdir(exist_ok=True)
    workflows = [
        ("maintenance-triage-daily-digest.json", build_digest()),
        ("maintenance-triage-operator-heartbeat.json", build_heartbeat()),
    ]
    for filename, workflow in workflows:
        path = WORKFLOWS / filename
        path.write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()

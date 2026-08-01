#!/usr/bin/env python3
import json
import pathlib
import textwrap


ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / "workflows"

BOARD_ID = "maintenance-triage-board-stage-5"


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
            "options": {
                "queryReplacement": replacements_expr,
            },
        },
        credentials={
            "postgres": {
                "id": "stage1PgLocal",
                "name": "maintenance-triage-postgres-local",
            }
        },
    )


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


def respond_node(name, position, status_code):
    return node(
        name,
        "n8n-nodes-base.respondToWebhook",
        1.5,
        position,
        {
            "respondWith": "text",
            "responseBody": "={{ $json.html }}",
            "options": {
                "responseCode": status_code,
                "responseHeaders": {
                    "entries": [
                        {
                            "name": "Content-Type",
                            "value": "text/html; charset=utf-8",
                        },
                        {
                            "name": "Cache-Control",
                            "value": "no-store",
                        },
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
        "meta": {"stage": 5, "generatedBy": "scripts/build-stage-5-board-workflow.py"},
        "versionId": "stage-5-generated",
        "triggerCount": 0,
        "tags": [],
    }


def build_board():
    board_query = r"""
    WITH input_values AS (
      SELECT NULLIF($1::text, '') AS token, upper(NULLIF($2::text, '')) AS requested_ref
    ),
    config AS (
      SELECT
        coalesce((SELECT value FROM triage.config WHERE key = 'board'), '{}'::jsonb) AS board,
        coalesce((SELECT value FROM triage.config WHERE key = 'company'), '{}'::jsonb) AS company,
        coalesce((SELECT value FROM triage.config WHERE key = 'overdue_days'), '{}'::jsonb) AS overdue_days
    ),
    settings AS (
      SELECT
        board,
        company,
        overdue_days,
        coalesce((board->>'recent_hours')::int, 48) AS recent_hours,
        least(greatest(coalesce((board->>'max_cards')::int, 60), 1), 200) AS max_cards,
        coalesce(company->>'name', 'Demo Property Management') AS company_name,
        coalesce(company->>'timezone', 'America/Chicago') AS company_timezone,
        coalesce((SELECT token FROM input_values) = (board->>'token'), false) AS authorized
      FROM config
    ),
    board_rows AS (
      SELECT
        t.*,
        extract(epoch FROM (now() - t.received_at))::int AS age_seconds,
        extract(epoch FROM (t.sla_due_at - now()))::int AS due_seconds,
        (
          t.priority IN ('ROUTINE', 'URGENT')
          AND t.closed_at IS NULL
          AND t.status <> 'CLOSED'
          AND t.received_at < now() - make_interval(days => coalesce((s.overdue_days->>t.priority)::int, 999999))
        ) AS overdue,
        CASE
          WHEN t.priority = 'EMERGENCY' THEN 4
          WHEN t.priority = 'NEEDS_REVIEW' THEN 3
          WHEN t.priority = 'URGENT' THEN 2
          ELSE 1
        END AS priority_rank
      FROM triage.tickets t
      CROSS JOIN settings s
      WHERE s.authorized
        AND (
          (t.closed_at IS NULL AND t.status <> 'CLOSED' AND t.priority IN ('EMERGENCY', 'URGENT', 'NEEDS_REVIEW'))
          OR (
            t.closed_at IS NULL
            AND t.status <> 'CLOSED'
            AND t.priority IN ('ROUTINE', 'URGENT')
            AND t.received_at < now() - make_interval(days => coalesce((s.overdue_days->>t.priority)::int, 999999))
          )
          OR t.received_at >= now() - make_interval(hours => s.recent_hours)
        )
      ORDER BY priority_rank DESC, overdue DESC, t.received_at DESC
      LIMIT (SELECT max_cards FROM settings)
    ),
    selected_ticket AS (
      SELECT
        t.*,
        extract(epoch FROM (now() - t.received_at))::int AS age_seconds,
        extract(epoch FROM (t.sla_due_at - now()))::int AS due_seconds,
        (
          t.priority IN ('ROUTINE', 'URGENT')
          AND t.closed_at IS NULL
          AND t.status <> 'CLOSED'
          AND t.received_at < now() - make_interval(days => coalesce((s.overdue_days->>t.priority)::int, 999999))
        ) AS overdue
      FROM triage.tickets t
      CROSS JOIN settings s
      CROSS JOIN input_values i
      WHERE s.authorized
        AND i.requested_ref IS NOT NULL
        AND t.ref = i.requested_ref
      LIMIT 1
    ),
    selected_events AS (
      SELECT e.*
      FROM triage.events e
      JOIN selected_ticket t ON t.id = e.ticket_id
      ORDER BY e.at
    ),
    board_json AS (
      SELECT coalesce(jsonb_agg(
        jsonb_build_object(
          'ref', ref,
          'source', source,
          'received_at', received_at,
          'from_address', from_address,
          'subject', subject,
          'body_clean', body_clean,
          'attachment_count', attachment_count,
          'attachment_paths', attachment_paths,
          'model_json', model_json,
          'model_priority', model_priority,
          'model_name', model_name,
          'is_maintenance_request', is_maintenance_request,
          'request_type', request_type,
          'priority', priority,
          'priority_reason', priority_reason,
          'override_applied', override_applied,
          'override_reason', override_reason,
          'human_only', human_only,
          'trade', trade,
          'unit_identifier', unit_identifier,
          'tenant_name', tenant_name,
          'tenant_contact', tenant_contact,
          'issue_summary', issue_summary,
          'safety_signals', safety_signals,
          'accommodation_or_legal_flag', accommodation_or_legal_flag,
          'accommodation_or_legal_reason', accommodation_or_legal_reason,
          'missing_info', missing_info,
          'confidence', confidence,
          'ambiguity_note', ambiguity_note,
          'language', language,
          'draft_subject', draft_subject,
          'draft_body', draft_body,
          'vendor_note', vendor_note,
          'clarifying_qs', clarifying_qs,
          'status', status,
          'sla_due_at', sla_due_at,
          'age_seconds', age_seconds,
          'due_seconds', due_seconds,
          'overdue', overdue
        )
        ORDER BY priority_rank DESC, overdue DESC, received_at DESC
      ), '[]'::jsonb) AS tickets
      FROM board_rows
    ),
    selected_json AS (
      SELECT to_jsonb(t) AS ticket
      FROM selected_ticket t
    ),
    events_json AS (
      SELECT coalesce(jsonb_agg(to_jsonb(e) ORDER BY e.at), '[]'::jsonb) AS events
      FROM selected_events e
    ),
    counts AS (
      SELECT jsonb_build_object(
        'needs_you_now', count(*) FILTER (WHERE priority IN ('EMERGENCY', 'NEEDS_REVIEW')),
        'open', count(*) FILTER (WHERE closed_at IS NULL AND status <> 'CLOSED'),
        'overdue', count(*) FILTER (WHERE overdue)
      ) AS value
      FROM board_rows
    )
    SELECT
      s.authorized,
      CASE
        WHEN NOT s.authorized THEN 404
        WHEN i.requested_ref IS NOT NULL AND NOT EXISTS (SELECT 1 FROM selected_ticket) THEN 404
        ELSE 200
      END AS status_code,
      CASE WHEN i.requested_ref IS NULL THEN 'board' ELSE 'detail' END AS page,
      CASE WHEN s.authorized THEN i.token ELSE NULL END AS request_token,
      i.requested_ref,
      now() AS server_now,
      s.company_name,
      s.company_timezone,
      s.recent_hours,
      s.max_cards,
      CASE WHEN s.authorized THEN (SELECT tickets FROM board_json) ELSE '[]'::jsonb END AS tickets,
      CASE WHEN s.authorized THEN (SELECT value FROM counts) ELSE '{}'::jsonb END AS counts,
      CASE WHEN s.authorized THEN (SELECT ticket FROM selected_json) ELSE NULL END AS selected_ticket,
      CASE WHEN s.authorized THEN (SELECT events FROM events_json) ELSE '[]'::jsonb END AS events
    FROM settings s
    CROSS JOIN input_values i;
    """

    render_js = r"""
    const row = $input.first().json;

    function parseJson(value, fallback) {
      if (value === null || value === undefined || value === "") return fallback;
      if (typeof value === "string") {
        try { return JSON.parse(value); } catch (error) { return fallback; }
      }
      return value;
    }

    const authorized = row.authorized === true || row.authorized === "true";
    const statusCode = Number(row.status_code || (authorized ? 200 : 404));
    const page = row.page || "board";
    const token = row.request_token || "";
    const requestedRef = row.requested_ref || "";
    const companyName = row.company_name || "Demo Property Management";
    const companyTimezone = row.company_timezone || "America/Chicago";
    const recentHours = Number(row.recent_hours || 48);
    const maxCards = Number(row.max_cards || 60);
    const tickets = Array.isArray(parseJson(row.tickets, [])) ? parseJson(row.tickets, []) : [];
    const counts = parseJson(row.counts, {});
    const selectedTicket = parseJson(row.selected_ticket, null);
    const events = Array.isArray(parseJson(row.events, [])) ? parseJson(row.events, []) : [];

    function esc(value) {
      return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
    }

    function prettyJson(value) {
      const parsed = parseJson(value, value);
      return esc(JSON.stringify(parsed ?? {}, null, 2));
    }

    function listValue(value) {
      const parsed = parseJson(value, []);
      if (!Array.isArray(parsed) || parsed.length === 0) return [];
      return parsed.filter((item) => item !== null && item !== undefined && String(item).trim() !== "");
    }

    function minutesLabel(seconds) {
      const abs = Math.abs(Number(seconds || 0));
      if (abs < 60) return `${abs}s`;
      if (abs < 3600) return `${Math.round(abs / 60)}m`;
      if (abs < 86400) return `${Math.round(abs / 3600)}h`;
      return `${Math.round(abs / 86400)}d`;
    }

    function ageLabel(seconds) {
      return `${minutesLabel(seconds)} ago`;
    }

    function dueLabel(seconds) {
      const value = Number(seconds || 0);
      if (value < 0) return `${minutesLabel(value)} past target`;
      return `${minutesLabel(value)} left`;
    }

    function dateLabel(value) {
      if (!value) return "Not set";
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return String(value);
      return date.toLocaleString("en-US", {
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
      });
    }

    function boardHref(ref) {
      const suffix = ref ? `&ref=${encodeURIComponent(ref)}` : "";
      return `/webhook/board?t=${encodeURIComponent(token)}${suffix}`;
    }

    function priorityLabel(priority) {
      if (priority === "NEEDS_REVIEW") return "Needs review";
      return String(priority || "ROUTINE").replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
    }

    function replyStatus(ticket) {
      if (ticket.status === "ACK_SENT") return "Reply sent";
      if (ticket.human_only || ticket.accommodation_or_legal_flag) return "Human decision required - no reply written";
      if (ticket.priority === "NEEDS_REVIEW") return "Needs human review - no reply written";
      if (ticket.draft_body) return "Reply written - waiting for you";
      return "No reply written";
    }

    function stampText(ticket) {
      if (ticket.override_applied && ticket.override_reason) {
        return `OVERRIDE - ${String(ticket.override_reason).replace(/^safety keyword:\s*/i, "").toUpperCase()}`;
      }
      if (ticket.overdue) return "OVERDUE";
      return "";
    }

    function rulesVerdict(ticket) {
      if (!ticket) return "";
      const modelPriority = ticket.model_priority || ticket.model_json?.priority || "UNKNOWN";
      if (ticket.override_applied && ticket.override_reason) {
        return `Model said ${modelPriority}. Rule ${ticket.override_reason} raised it to ${ticket.priority}.`;
      }
      if (ticket.priority === "NEEDS_REVIEW" && ticket.priority_reason) {
        return `System marked this NEEDS_REVIEW because ${ticket.priority_reason}.`;
      }
      return `Model said ${modelPriority}. No deterministic safety override changed the priority.`;
    }

    function modelReadout(ticket) {
      const model = parseJson(ticket.model_json, {});
      const signals = listValue(model.safety_signals).filter((item) => item !== "NONE");
      const missing = listValue(model.missing_info);
      const rows = [
        ["Model priority", priorityLabel(model.priority || ticket.model_priority || "UNKNOWN")],
        ["Final priority", priorityLabel(ticket.priority)],
        ["Summary", model.issue_summary || ticket.issue_summary || "Not stated"],
        ["Why", model.priority_reason || ticket.priority_reason || "Not stated"],
        ["Trade", model.trade || ticket.trade || "UNKNOWN"],
        ["Unit", model.unit_identifier || ticket.unit_identifier || "UNIT NOT STATED"],
        ["Confidence", model.confidence || ticket.confidence || "Not stated"],
        ["Safety signals", signals.length ? signals.join(", ") : "None"],
        ["Missing info", missing.length ? missing.join(", ") : "None"],
        ["Human-only reason", model.accommodation_or_legal_reason || ticket.accommodation_or_legal_reason || "None"],
      ];
      return `
        <dl class="readout">
          ${rows.map(([label, value]) => `<div><dt>${esc(label)}</dt><dd>${esc(value)}</dd></div>`).join("")}
        </dl>
      `;
    }

    function eventSentence(event) {
      const detail = parseJson(event.detail, {});
      const action = String(event.action || "");
      if (action === "ingested") return `Request received from ${detail.source || "source"} and stored.`;
      if (action === "classified") return `AI classified it as ${detail.priority || "unknown"}; final priority became ${detail.final_priority || "unknown"}.`;
      if (action === "overridden") return `${detail.override_reason ? `Rule ${detail.override_reason}` : "A safety rule"} changed the priority.`;
      if (action === "drafted") return "Tenant reply and vendor note were drafted for human review.";
      if (action === "telegram_alert_mocked") return `Demo alert recorded as ${detail.outcome || "mocked"}.`;
      if (action === "telegram_alert_sent") return `Telegram alert sent${detail.telegram_message_id ? ` as message ${detail.telegram_message_id}` : ""}.`;
      if (action === "telegram_alert_failed") return `Telegram alert failed: ${detail.error || "no error text recorded"}.`;
      if (action === "telegram_alert_skipped") return `Alert skipped: ${detail.reason || "not alertable"}.`;
      if (action === "telegram_alert_grouped") return "Alert was rate-limited and grouped instead of sent individually.";
      if (action === "approval_claimed") return `Human selected ${detail.action || "approve"}.`;
      if (action === "tenant_reply_sent") return `Approved tenant reply sent to ${detail.outbound_to || "configured test inbox"}.`;
      if (action === "tenant_reply_send_failed") return `Approved reply failed to send: ${detail.error || "no error text recorded"}.`;
      if (action === "held") return "Human put this request on hold.";
      if (action === "not_emergency") return "Human marked it not emergency; priority was downgraded to urgent.";
      return action ? `${action.replace(/_/g, " ")} recorded.` : "Event recorded.";
    }

    function chipList(items, cls = "") {
      return items.map((item) => `<span class="chip ${cls}">${esc(item)}</span>`).join("");
    }

    function renderCard(ticket) {
      const missing = listValue(ticket.missing_info);
      const safety = listValue(ticket.safety_signals).filter((item) => item !== "NONE");
      const stamp = stampText(ticket);
      const clockClass = Number(ticket.due_seconds || 0) < 0 ? "clock breach" : "clock";
      const unit = ticket.unit_identifier || "UNIT NOT STATED";
      return `
        <article class="card ${esc(String(ticket.priority || "ROUTINE").toLowerCase())} ${ticket.overdue ? "is-overdue" : ""}" aria-labelledby="card-${esc(ticket.ref)}">
          <div class="perforation" aria-hidden="true"></div>
          ${stamp ? `<div class="stamp">${esc(stamp)}</div>` : ""}
          <div class="card-top">
            <a class="ref" id="card-${esc(ticket.ref)}" href="${esc(boardHref(ticket.ref))}">${esc(ticket.ref)}</a>
            <span class="band">${esc(priorityLabel(ticket.priority))}</span>
          </div>
          <h2>${esc(ticket.issue_summary || ticket.subject || "Maintenance request needs review")}</h2>
          <div class="meta-grid">
            <span><b>Unit</b>${esc(unit)}</span>
            <span><b>Trade</b>${esc(ticket.trade || "UNKNOWN")}</span>
            <span><b>Source</b>${esc(ticket.source || "unknown")}</span>
            <span><b>Age</b>${esc(ageLabel(ticket.age_seconds))}</span>
          </div>
          <div class="${clockClass}">Response target: ${esc(dueLabel(ticket.due_seconds))}</div>
          <div class="chips">
            ${ticket.confidence && ticket.confidence !== "HIGH" ? `<span class="chip warn">Confidence ${esc(ticket.confidence)}</span>` : ""}
            ${missing.length ? chipList(missing.map((item) => `Missing ${item}`), "warn") : ""}
            ${safety.length ? chipList(safety.map((item) => `Safety ${item}`), "danger") : ""}
            ${Number(ticket.attachment_count || 0) > 0 ? `<span class="chip">Attachments ${esc(ticket.attachment_count)}</span>` : ""}
          </div>
          ${ticket.human_only || ticket.accommodation_or_legal_flag ? `<div class="human-band">HUMAN DECISION REQUIRED - no reply written</div>` : ""}
          <p class="reply">${esc(replyStatus(ticket))}</p>
        </article>
      `;
    }

    function renderBoard() {
      const countNow = Number(counts.needs_you_now || 0);
      const countOpen = Number(counts.open || 0);
      const countOverdue = Number(counts.overdue || 0);
      const cards = tickets.length
        ? `<section class="cards" aria-label="Maintenance requests">${tickets.map(renderCard).join("")}</section>`
        : `<section class="empty" aria-label="Empty board"><h2>Nothing waiting.</h2><p>New requests appear here within seconds of arriving.</p></section>`;
      return `
        <header class="page-head">
          <div>
            <p class="eyebrow">Maintenance board</p>
            <h1>${esc(companyName)}</h1>
            <p class="subtle">Open safety items plus recent requests from the last ${esc(recentHours)} hours. Limited to ${esc(maxCards)} cards.</p>
          </div>
          <dl class="counters" aria-label="Board summary">
            <div><dt>Needs you now</dt><dd>${esc(countNow)}</dd></div>
            <div><dt>Open</dt><dd>${esc(countOpen)}</dd></div>
            <div><dt>Overdue</dt><dd>${esc(countOverdue)}</dd></div>
          </dl>
        </header>
        ${cards}
      `;
    }

    function renderDetail() {
      if (!selectedTicket) {
        return `
          <header class="page-head">
            <div>
              <p class="eyebrow">Maintenance board</p>
              <h1>Reference not found</h1>
              <p class="subtle">No ticket exists for ${esc(requestedRef)}.</p>
            </div>
          </header>
          <section class="empty"><a class="back-link" href="${esc(boardHref(""))}">Back to board</a></section>
        `;
      }
      const missing = listValue(selectedTicket.missing_info);
      const clarifying = listValue(selectedTicket.clarifying_qs);
      return `
        <header class="page-head detail-head">
          <div>
            <p class="eyebrow">Ticket detail</p>
            <h1>${esc(selectedTicket.ref)} - ${esc(selectedTicket.issue_summary || selectedTicket.subject || "Maintenance request")}</h1>
            <p class="subtle">${esc(priorityLabel(selectedTicket.priority))} / ${esc(selectedTicket.unit_identifier || "UNIT NOT STATED")} / ${esc(dateLabel(selectedTicket.received_at))}</p>
          </div>
          <a class="back-link" href="${esc(boardHref(""))}">Back to board</a>
        </header>
        <main class="detail-grid" id="content">
          <section class="panel">
            <h2>Why it sorted here</h2>
            <p class="verdict">${esc(rulesVerdict(selectedTicket))}</p>
            <div class="chips detail-chips">
              <span class="chip">${esc(priorityLabel(selectedTicket.priority))}</span>
              ${selectedTicket.overdue ? `<span class="chip danger">OVERDUE</span>` : ""}
              ${missing.length ? chipList(missing.map((item) => `Missing ${item}`), "warn") : ""}
            </div>
          </section>
          <section class="panel">
            <h2>Original message</h2>
            <pre class="message">${esc(selectedTicket.body_clean || selectedTicket.body_raw || "")}</pre>
          </section>
          <section class="panel">
            <h2>The reply, waiting for you</h2>
            ${selectedTicket.draft_subject ? `<h3>${esc(selectedTicket.draft_subject)}</h3>` : ""}
            ${selectedTicket.draft_body ? `<pre class="message">${esc(selectedTicket.draft_body)}</pre>` : `<p class="subtle">No tenant reply was written for this ticket.</p>`}
            ${clarifying.length ? `<h3>Clarifying questions</h3><ul>${clarifying.map((q) => `<li>${esc(q)}</li>`).join("")}</ul>` : ""}
          </section>
          <section class="panel">
            <h2>Vendor note</h2>
            ${selectedTicket.vendor_note ? `<pre class="message">${esc(selectedTicket.vendor_note)}</pre>` : `<p class="subtle">No vendor note was written.</p>`}
          </section>
          <section class="panel wide">
            <h2>AI readout</h2>
            ${modelReadout(selectedTicket)}
            <details class="audit">
              <summary>Technical audit</summary>
              <pre class="json">${prettyJson(selectedTicket.model_json)}</pre>
            </details>
          </section>
          <section class="panel wide">
            <h2>Event trail</h2>
            ${events.length ? `<ol class="events">${events.map((event) => `
              <li>
                <time>${esc(dateLabel(event.at))}</time>
                <strong>${esc(event.actor)} / ${esc(event.action)}</strong>
                <p>${esc(eventSentence(event))}</p>
                <details class="audit">
                  <summary>Technical detail</summary>
                  <pre class="json">${prettyJson(event.detail)}</pre>
                </details>
              </li>
            `).join("")}</ol>` : `<p class="subtle">No events recorded.</p>`}
          </section>
        </main>
      `;
    }

    function renderNotFound() {
      return `
        <header class="page-head">
          <div>
            <p class="eyebrow">Maintenance board</p>
            <h1>Not found</h1>
            <p class="subtle">The board link is missing or invalid.</p>
          </div>
        </header>
      `;
    }

    const styles = `
      :root {
        --ink: #24211c;
        --muted: #6a6257;
        --paper: #f2efe6;
        --card: #fffaf0;
        --desk: #e4dfd2;
        --line: #c8bca8;
        --red: #9f2d26;
        --amber: #8a5b1e;
        --green: #355f4b;
        --blue: #2c5367;
      }
      * { box-sizing: border-box; }
      html { background: var(--desk); color: var(--ink); font-family: Georgia, "Times New Roman", serif; line-height: 1.5; }
      body { margin: 0; min-width: 320px; }
      a { color: inherit; }
      a:focus-visible { outline: 3px solid var(--blue); outline-offset: 3px; }
      .skip { position: absolute; left: -999px; top: 12px; background: var(--ink); color: var(--card); padding: 8px 12px; z-index: 10; }
      .skip:focus { left: 12px; }
      .shell { width: min(1120px, calc(100% - 32px)); margin: 0 auto; padding: 28px 0 48px; }
      .page-head { display: grid; grid-template-columns: 1fr; gap: 20px; align-items: end; margin-bottom: 24px; border-bottom: 1px solid var(--line); padding-bottom: 20px; }
      .detail-head { align-items: center; }
      .eyebrow { margin: 0 0 4px; color: var(--muted); font: 700 12px/1.2 ui-monospace, SFMono-Regular, Consolas, monospace; text-transform: uppercase; letter-spacing: 0; }
      h1 { margin: 0; font-size: clamp(26px, 3vw, 36px); line-height: 1.1; letter-spacing: 0; }
      h2 { margin: 0 0 10px; font-size: 20px; line-height: 1.2; letter-spacing: 0; }
      h3 { margin: 12px 0 6px; font-size: 16px; }
      .subtle { margin: 8px 0 0; color: var(--muted); max-width: 72ch; }
      .counters { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; margin: 0; }
      .counters div { border: 1px solid var(--line); background: rgba(255,250,240,.55); padding: 10px; min-height: 70px; }
      .counters dt { color: var(--muted); font: 700 12px/1.2 ui-monospace, SFMono-Regular, Consolas, monospace; text-transform: uppercase; }
      .counters dd { margin: 4px 0 0; font: 700 28px/1 ui-monospace, SFMono-Regular, Consolas, monospace; }
      .cards { display: grid; gap: 16px; }
      .card { position: relative; overflow: hidden; background: var(--card); border: 1px solid var(--line); border-radius: 4px; padding: 18px; animation: enter 200ms ease-out both; }
      .card.emergency { border-left: 8px solid var(--red); }
      .card.needs_review { border-left: 8px solid var(--amber); }
      .card.urgent { border-left: 8px solid var(--blue); }
      .card.routine { border-left: 8px solid var(--green); }
      .card.is-overdue { box-shadow: inset 0 0 0 2px rgba(159,45,38,.14); }
      .perforation { position: absolute; left: 0; right: 0; top: 10px; border-top: 1px dashed var(--line); }
      .stamp { position: absolute; top: 14px; right: 12px; transform: rotate(-3deg); border: 2px solid var(--red); color: var(--red); padding: 4px 8px; font: 800 12px/1 ui-monospace, SFMono-Regular, Consolas, monospace; text-transform: uppercase; background: rgba(255,250,240,.84); max-width: 44%; overflow-wrap: anywhere; }
      .card-top { display: flex; gap: 12px; align-items: center; justify-content: space-between; margin-bottom: 16px; padding-right: min(45%, 230px); }
      .ref { font: 800 18px/1 ui-monospace, SFMono-Regular, Consolas, monospace; text-decoration: underline; text-underline-offset: 3px; }
      .band { color: var(--muted); font: 700 12px/1.2 ui-monospace, SFMono-Regular, Consolas, monospace; text-transform: uppercase; }
      .card h2 { max-width: 70ch; margin-bottom: 14px; }
      .meta-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; margin-bottom: 12px; }
      .meta-grid span { min-width: 0; color: var(--ink); overflow-wrap: anywhere; }
      .meta-grid b { display: block; color: var(--muted); font: 700 12px/1.2 ui-monospace, SFMono-Regular, Consolas, monospace; text-transform: uppercase; }
      .clock { display: inline-block; margin: 0 0 12px; padding: 6px 8px; border: 1px solid var(--line); font: 700 13px/1.2 ui-monospace, SFMono-Regular, Consolas, monospace; }
      .clock.breach { border-color: var(--red); color: var(--red); }
      .chips { display: flex; flex-wrap: wrap; gap: 6px; }
      .chip { border: 1px solid var(--line); border-radius: 999px; padding: 4px 8px; font: 700 12px/1 ui-monospace, SFMono-Regular, Consolas, monospace; color: var(--muted); background: rgba(255,250,240,.6); }
      .chip.warn { border-color: var(--amber); color: var(--amber); }
      .chip.danger { border-color: var(--red); color: var(--red); }
      .human-band { margin-top: 12px; border: 1px solid var(--red); color: var(--red); padding: 8px 10px; font: 800 12px/1.2 ui-monospace, SFMono-Regular, Consolas, monospace; text-transform: uppercase; }
      .reply { margin: 12px 0 0; color: var(--muted); font-weight: 700; }
      .empty, .panel { background: var(--card); border: 1px solid var(--line); border-radius: 4px; padding: 20px; }
      .empty h2 { font-size: 24px; }
      .back-link { display: inline-flex; align-items: center; min-height: 44px; font: 700 14px/1 ui-monospace, SFMono-Regular, Consolas, monospace; text-transform: uppercase; text-decoration: underline; text-underline-offset: 4px; }
      .detail-grid { display: grid; gap: 16px; }
      .panel.wide { grid-column: 1 / -1; }
      .verdict { margin-top: 0; max-width: 72ch; }
      .readout { display: grid; gap: 8px; margin: 0; }
      .readout div { display: grid; gap: 2px; border-bottom: 1px solid rgba(200,188,168,.65); padding: 0 0 8px; }
      .readout dt { color: var(--muted); font: 700 12px/1.2 ui-monospace, SFMono-Regular, Consolas, monospace; text-transform: uppercase; }
      .readout dd { margin: 0; overflow-wrap: anywhere; }
      .message, .json { white-space: pre-wrap; overflow-wrap: anywhere; background: rgba(228,223,210,.5); border: 1px solid var(--line); padding: 12px; margin: 8px 0 0; font: 13px/1.5 ui-monospace, SFMono-Regular, Consolas, monospace; }
      .json { max-height: 520px; overflow: auto; }
      .audit { margin-top: 14px; border-top: 1px dashed var(--line); padding-top: 10px; }
      .audit summary { cursor: pointer; color: var(--muted); font: 700 12px/1.2 ui-monospace, SFMono-Regular, Consolas, monospace; text-transform: uppercase; }
      .audit summary:focus-visible { outline: 3px solid var(--blue); outline-offset: 3px; }
      .events { list-style: decimal; padding-left: 24px; margin: 0; }
      .events li { margin-bottom: 14px; }
      .events p { margin: 6px 0 0; }
      .events time { display: block; color: var(--muted); font: 700 12px/1.3 ui-monospace, SFMono-Regular, Consolas, monospace; }
      footer { margin-top: 28px; color: var(--muted); font-size: 13px; }
      @keyframes enter { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
      @media (min-width: 760px) {
        .page-head { grid-template-columns: 1fr auto; }
        .counters { min-width: 360px; }
        .meta-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
        .detail-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      }
      @media (max-width: 560px) {
        .shell { width: min(100% - 20px, 1120px); padding-top: 18px; }
        .counters { grid-template-columns: 1fr; }
        .card { padding: 16px 14px; }
        .card-top { display: grid; padding-right: 0; margin-top: 34px; }
        .stamp { left: 12px; right: auto; max-width: calc(100% - 24px); }
        .meta-grid { grid-template-columns: 1fr; }
      }
      @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; }
      }
    `;

    const body = authorized
      ? (page === "detail" ? renderDetail() : renderBoard())
      : renderNotFound();
    const refresh = authorized && page === "board" && statusCode === 200 ? '<meta http-equiv="refresh" content="5">' : "";
    const title = authorized && page === "detail" && selectedTicket
      ? `${selectedTicket.ref} - Maintenance detail`
      : `${companyName} - Maintenance board`;
    const html = `<!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      ${refresh}
      <title>${esc(title)}</title>
      <style>${styles}</style>
    </head>
    <body>
      <a class="skip" href="#content">Skip to content</a>
      <main class="shell" id="content">
        ${body}
        <footer>Read-only demo board. Response targets are operational targets, not legal deadlines. Timezone: ${esc(companyTimezone)}.</footer>
      </main>
    </body>
    </html>`;

    return [{ json: { status_code: statusCode, not_found: statusCode === 404, html } }];
    """

    board_webhook = node(
            "Board Webhook",
            "n8n-nodes-base.webhook",
            2,
            [-560, 0],
            {
                "path": "board",
                "httpMethod": "GET",
                "responseMode": "responseNode",
                "options": {},
            },
        )
    board_webhook["webhookId"] = "board"

    nodes = [
        board_webhook,
        pg_node(
            "Postgres Load Board Data",
            [-300, 0],
            board_query,
            "={{ [$json.query?.t || '', $json.query?.ref || ''] }}",
        ),
        code_node("Render Board HTML", [-40, 0], render_js),
        if_node("Should Return Not Found", [220, 0], "={{ $json.not_found }}"),
        respond_node("Respond With Not Found HTML", [480, -100], 404),
        respond_node("Respond With Board HTML", [480, 100], 200),
    ]
    connections = {
        "Board Webhook": {"main": [[{"node": "Postgres Load Board Data", "type": "main", "index": 0}]]},
        "Postgres Load Board Data": {"main": [[{"node": "Render Board HTML", "type": "main", "index": 0}]]},
        "Render Board HTML": {"main": [[{"node": "Should Return Not Found", "type": "main", "index": 0}]]},
        "Should Return Not Found": {
            "main": [
                [{"node": "Respond With Not Found HTML", "type": "main", "index": 0}],
                [{"node": "Respond With Board HTML", "type": "main", "index": 0}],
            ]
        },
    }
    return workflow_base(BOARD_ID, "Maintenance Triage Board", nodes, connections)


def main():
    WORKFLOWS.mkdir(exist_ok=True)
    path = WORKFLOWS / "maintenance-triage-board.json"
    path.write_text(json.dumps(build_board(), indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()

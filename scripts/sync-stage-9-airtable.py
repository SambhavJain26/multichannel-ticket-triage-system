#!/usr/bin/env python3
"""Re-sync local Stage 9 Postgres demo state into the typed Airtable workspace."""

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


API = "https://api.airtable.com/v0"
PROPERTIES = {"Maple Court", "Oak Terrace", "Pine House"}
INTENTS = {"request", "pairing", "receipt", "clarification", "clarification_answer", "status", "vendor_update", "vendor_dispatch", "manager_note"}


def local_env_value(name: str, default: str = "") -> str:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return default
    prefix = f"{name}="
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.startswith(prefix):
            return line[len(prefix):].strip().strip('"').strip("'")
    return default


def request(token: str, method: str, url: str, payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Airtable {method} request failed: {exc.code} {detail}") from exc


def table_url(base_id: str, table: str) -> str:
    return f"{API}/{base_id}/{urllib.parse.quote(table, safe='')}"


def psql(sql: str) -> str:
    user = local_env_value("POSTGRES_USER", "maintenance_triage")
    database = local_env_value("POSTGRES_DB", "maintenance_triage")
    result = subprocess.run(
        ["docker", "compose", "exec", "-T", "postgres", "psql", "-U", user, "-d", database, "-At", "-v", "ON_ERROR_STOP=1", "-c", sql],
        check=True, capture_output=True, text=True,
    )
    return result.stdout.strip()


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def json_rows(sql: str) -> list[dict]:
    output = psql(sql)
    return [json.loads(line) for line in output.splitlines() if line.strip()]


def all_records(token: str, base_id: str, table: str) -> list[dict]:
    records, offset = [], ""
    while True:
        url = table_url(base_id, table)
        if offset:
            url += "?" + urllib.parse.urlencode({"offset": offset})
        page = request(token, "GET", url)
        records.extend(page.get("records", []))
        offset = page.get("offset", "")
        if not offset:
            return records


def field(fields: dict, name: str, value):
    if value not in (None, "", [], {}):
        fields[name] = value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset-links", action="store_true", help="Clear local Airtable IDs before a typed demo-base rebuild.")
    args = parser.parse_args()
    token = os.environ.get("AIRTABLE_PAT", "").strip() or local_env_value("AIRTABLE_PAT")
    if not token:
        raise SystemExit("AIRTABLE_PAT must be set in .env or the local environment.")

    config_text = psql("SELECT value::text FROM triage.config WHERE key = 'airtable';")
    config = json.loads(config_text)
    if not config.get("enabled") or not config.get("base_id"):
        raise SystemExit("Local triage.config.airtable is not enabled and configured.")
    base_id = config["base_id"]
    requests_table = config.get("requests_table", "Requests")
    conversations_table = config.get("conversations_table", "Conversations")
    tenant_table = config.get("tenant_roster_table", "Tenant Roster")
    vendors_table = config.get("vendors_table", "Vendors")

    if args.reset_links:
        psql("UPDATE triage.tickets SET airtable_record_id = NULL; UPDATE triage.ticket_messages SET airtable_record_id = NULL, airtable_synced_at = NULL; DELETE FROM triage.airtable_roster_links;")

    tenants = all_records(token, base_id, tenant_table)
    vendors = all_records(token, base_id, vendors_table)
    tenant_by_email = {str(r.get("fields", {}).get("Email", "")).lower(): r["id"] for r in tenants if r.get("fields", {}).get("Email")}
    vendor_by_name = {str(r.get("fields", {}).get("Vendor Name", "")).lower(): r["id"] for r in vendors if r.get("fields", {}).get("Vendor Name")}
    for email, record_id in tenant_by_email.items():
        psql("INSERT INTO triage.airtable_roster_links (roster_kind, lookup_key, airtable_record_id) VALUES ('tenant', %s, %s) ON CONFLICT (roster_kind, lookup_key) DO UPDATE SET airtable_record_id = EXCLUDED.airtable_record_id, updated_at = now();" % (sql_literal(email), sql_literal(record_id)))
    for name, record_id in vendor_by_name.items():
        psql("INSERT INTO triage.airtable_roster_links (roster_kind, lookup_key, airtable_record_id) VALUES ('vendor', %s, %s) ON CONFLICT (roster_kind, lookup_key) DO UPDATE SET airtable_record_id = EXCLUDED.airtable_record_id, updated_at = now();" % (sql_literal(name), sql_literal(record_id)))
        psql("UPDATE triage.ticket_vendor_candidates SET vendor_id = %s WHERE lower(vendor_name) = %s; UPDATE triage.tickets SET selected_vendor_id = %s WHERE lower(coalesce(selected_vendor_name, '')) = %s;" % (sql_literal(record_id), sql_literal(name), sql_literal(record_id), sql_literal(name)))

    tickets = json_rows("""
SELECT jsonb_build_object(
  'id', id, 'ref', ref, 'status', status, 'priority', priority, 'source', source,
  'from_address', from_address, 'tenant_contact', tenant_contact, 'body_raw', body_raw,
  'unit_identifier', unit_identifier, 'trade', trade, 'issue_summary', issue_summary,
  'missing_info', missing_info, 'human_only', human_only, 'vendor_status', vendor_status,
  'tenant_chat_id', tenant_chat_id, 'selected_vendor_id', selected_vendor_id
)::text
FROM triage.tickets ORDER BY id;
""")
    request_ids: dict[int, str] = {}
    for ticket in tickets:
        body = str(ticket.get("body_raw") or "")
        property_name = ""
        for line in body.splitlines():
            if line.lower().startswith("property:"):
                property_name = line.split(":", 1)[1].strip()
                break
        email = str(ticket.get("from_address") or ticket.get("tenant_contact") or "")
        missing_info = ticket.get("missing_info")
        if isinstance(missing_info, str):
            try:
                missing_info = json.loads(missing_info)
            except json.JSONDecodeError:
                missing_info = []
        fields = {
            "Reference": ticket["ref"], "Status": ticket.get("status") or "NEW", "Priority": ticket.get("priority") or "NEEDS_REVIEW",
            "Source": ticket.get("source") or "telegram", "Summary": ticket.get("issue_summary") or "Maintenance request",
            "Missing Info": missing_info if isinstance(missing_info, list) else [],
            "Human Only": bool(ticket.get("human_only")), "Vendor Status": ticket.get("vendor_status") or "NOT_STARTED",
        }
        field(fields, "Tenant Email", "" if email.startswith("telegram:") else email)
        field(fields, "Property", property_name if property_name in PROPERTIES else "")
        field(fields, "Unit", ticket.get("unit_identifier"))
        field(fields, "Trade", ticket.get("trade"))
        field(fields, "Telegram Chat ID", ticket.get("tenant_chat_id"))
        if email.lower() in tenant_by_email:
            fields["Tenant"] = [tenant_by_email[email.lower()]]
        candidate_rows = json_rows("SELECT jsonb_build_object('vendor_id', vendor_id)::text FROM triage.ticket_vendor_candidates WHERE ticket_id = %s ORDER BY candidate_rank;" % int(ticket["id"]))
        if candidate_rows:
            fields["Suggested Vendors"] = [row["vendor_id"] for row in candidate_rows]
        if ticket.get("selected_vendor_id"):
            fields["Selected Vendor"] = [ticket["selected_vendor_id"]]
        response = request(token, "PATCH", table_url(base_id, requests_table), {"performUpsert": {"fieldsToMergeOn": ["Reference"]}, "records": [{"fields": fields}]})
        record_id = response["records"][0]["id"]
        request_ids[int(ticket["id"])] = record_id
        psql("UPDATE triage.tickets SET airtable_record_id = %s WHERE id = %s;" % (sql_literal(record_id), int(ticket["id"])))

    messages = json_rows("""
SELECT jsonb_build_object('id', m.id, 'ticket_id', m.ticket_id, 'ref', t.ref, 'direction', m.direction,
  'channel', m.channel, 'intent', m.intent, 'body', m.body, 'external_message_id', m.external_message_id,
  'delivery_state', m.delivery_state, 'created_at', m.created_at)::text
FROM triage.ticket_messages m JOIN triage.tickets t ON t.id = m.ticket_id ORDER BY m.id;
""")
    synced = 0
    for message in messages:
        request_id = request_ids.get(int(message["ticket_id"]))
        if not request_id:
            continue
        fields = {
            "Conversation": f"{message['ref']} #{message['id']}", "Request": [request_id],
            "Direction": message["direction"], "Channel": message["channel"],
            "Intent": message["intent"] if message["intent"] in INTENTS else "manager_note",
            "Body": message["body"], "Delivery State": message["delivery_state"], "At": message["created_at"],
        }
        field(fields, "External Message ID", message.get("external_message_id"))
        response = request(token, "POST", table_url(base_id, conversations_table), {"records": [{"fields": fields}]})
        psql("UPDATE triage.ticket_messages SET airtable_record_id = %s, airtable_synced_at = now() WHERE id = %s;" % (sql_literal(response["records"][0]["id"]), int(message["id"])))
        synced += 1
    print(f"Synced {len(tickets)} requests and {synced} conversation records into Airtable.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

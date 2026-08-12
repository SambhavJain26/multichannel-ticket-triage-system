#!/usr/bin/env python3
"""Create or rebuild the typed local-demo Airtable workspace.

The script uses only AIRTABLE_PAT from the local environment or ignored .env file.
``--rebuild-demo-base`` deletes only the four named Stage 9 demo tables and is never
appropriate for a client or production base.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


API = "https://api.airtable.com/v0"
META_API = f"{API}/meta"
PROPERTIES = ["Maple Court", "Oak Terrace", "Pine House"]
TRADES = ["PLUMBING", "HVAC", "ELECTRICAL", "GENERAL", "APPLIANCE", "STRUCTURAL", "PEST", "LOCKS_SECURITY"]

TENANTS = [
    ("Demo Tenant", "sambhavn8n@gmail.com", "Maple Court", "2B"),
    ("Dana Ortiz", "dana.ortiz@example.test", "Maple Court", "1A"),
    ("Priya Shah", "priya.shah@example.test", "Maple Court", "1B"),
    ("Marco Diaz", "marco.diaz@example.test", "Maple Court", "2B"),
    ("Lena Brooks", "lena.brooks@example.test", "Maple Court", "2D"),
    ("Maria Rivera", "maria.rivera@example.test", "Maple Court", "4C"),
    ("Ben Harris", "ben.harris@example.test", "Oak Terrace", "A"),
    ("Iris Chen", "iris.chen@example.test", "Oak Terrace", "B"),
    ("Elena Cruz", "elena.cruz@example.test", "Pine House", "101"),
]

VENDORS = [
    ("Maple Plumbing", "PLUMBING", "Maple Court", 1, "+1 555 010 0101"),
    ("Oak HVAC Service", "HVAC", "Oak Terrace", 1, "+1 555 010 0102"),
    ("Pine Electrical", "ELECTRICAL", "Pine House", 1, "+1 555 010 0103"),
    ("General Property Repairs", "GENERAL,APPLIANCE,STRUCTURAL,PEST,LOCKS_SECURITY", "", 50, "+1 555 010 0104"),
]


def choices(names):
    return {"choices": [{"name": name} for name in names]}


def local_env_value(name: str) -> str:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return ""
    prefix = f"{name}="
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.startswith(prefix):
            return line[len(prefix):].strip().strip('"').strip("'")
    return ""


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


def schema_url(base_id: str, suffix: str = "") -> str:
    return f"{META_API}/bases/{base_id}/tables{suffix}"


def create_table(token: str, base_id: str, name: str, fields: list[dict]) -> dict:
    return request(token, "POST", schema_url(base_id), {"name": name, "fields": fields})


def add_field(token: str, base_id: str, table_id: str, field: dict) -> dict:
    return request(token, "POST", schema_url(base_id, f"/{table_id}/fields"), field)


def field_id(table: dict, field_name: str) -> str:
    for field in table["fields"]:
        if field["name"] == field_name:
            return field["id"]
    raise RuntimeError(f"Missing {field_name!r} in Airtable table {table['name']!r}.")


def upsert_records(token: str, base_id: str, table: str, primary: str, records: list[dict]) -> None:
    request(token, "PATCH", table_url(base_id, table), {
        "performUpsert": {"fieldsToMergeOn": [primary]},
        "records": [{"fields": fields} for fields in records],
    })


def build_schema(token: str, base_id: str) -> dict[str, dict]:
    tenant_table = create_table(token, base_id, "Tenant Roster", [
        {"name": "Tenant Name", "type": "singleLineText"},
        {"name": "Email", "type": "email"},
        {"name": "Property", "type": "singleSelect", "options": choices(PROPERTIES)},
        {"name": "Unit", "type": "singleLineText"},
        {"name": "Telegram Chat ID", "type": "singleLineText"},
        {"name": "Active", "type": "checkbox", "options": {"icon": "check", "color": "greenBright"}},
        {"name": "Created", "type": "createdTime"},
    ])
    vendor_table = create_table(token, base_id, "Vendors", [
        {"name": "Vendor Name", "type": "singleLineText"},
        {"name": "Email", "type": "email"},
        {"name": "Phone", "type": "phoneNumber"},
        {"name": "Trades", "type": "multipleSelects", "options": choices(TRADES)},
        {"name": "Properties", "type": "multipleSelects", "options": choices(PROPERTIES)},
        {"name": "Priority", "type": "number", "options": {"precision": 0}},
        {"name": "Active", "type": "checkbox", "options": {"icon": "check", "color": "greenBright"}},
        {"name": "Created", "type": "createdTime"},
    ])
    request_table = create_table(token, base_id, "Requests", [
        {"name": "Reference", "type": "singleLineText"},
        {"name": "Status", "type": "singleSelect", "options": choices(["NEW", "ALERTED", "ACKED", "HELD", "CLOSED", "NEEDS_REVIEW"])},
        {"name": "Priority", "type": "singleSelect", "options": choices(["EMERGENCY", "URGENT", "ROUTINE", "NEEDS_REVIEW"])},
        {"name": "Source", "type": "singleSelect", "options": choices(["email", "form", "telegram", "fixture", "import"])},
        {"name": "Tenant", "type": "multipleRecordLinks", "options": {"linkedTableId": tenant_table["id"], "prefersSingleRecordLink": True}},
        {"name": "Tenant Email", "type": "email"},
        {"name": "Property", "type": "singleSelect", "options": choices(PROPERTIES)},
        {"name": "Unit", "type": "singleLineText"},
        {"name": "Trade", "type": "singleSelect", "options": choices(TRADES)},
        {"name": "Summary", "type": "multilineText"},
        {"name": "Missing Info", "type": "multipleSelects", "options": choices(["UNIT", "PROPERTY", "CONTACT", "ACCESS_PERMISSION", "ISSUE_DETAIL", "ONSET_TIME"])},
        {"name": "Human Only", "type": "checkbox", "options": {"icon": "warning", "color": "orangeBright"}},
        {"name": "Vendor Status", "type": "singleSelect", "options": choices(["NOT_STARTED", "AWAITING_VENDOR", "NEEDS_VENDOR_ASSIGNMENT", "SENDING", "SENT", "FAILED", "HELD"])},
        {"name": "Suggested Vendors", "type": "multipleRecordLinks", "options": {"linkedTableId": vendor_table["id"]}},
        {"name": "Selected Vendor", "type": "multipleRecordLinks", "options": {"linkedTableId": vendor_table["id"], "prefersSingleRecordLink": True}},
        {"name": "Telegram Chat ID", "type": "singleLineText"},
        {"name": "Created", "type": "createdTime"},
        {"name": "Last Updated", "type": "lastModifiedTime"},
    ])
    add_field(token, base_id, request_table["id"], {
        "name": "Vendor Email", "type": "multipleLookupValues",
        "options": {
            "recordLinkFieldId": field_id(request_table, "Selected Vendor"),
            "fieldIdInLinkedTable": field_id(vendor_table, "Email"),
        },
    })
    conversation_table = create_table(token, base_id, "Conversations", [
        {"name": "Conversation", "type": "singleLineText"},
        {"name": "Request", "type": "multipleRecordLinks", "options": {"linkedTableId": request_table["id"], "prefersSingleRecordLink": True}},
        {"name": "Direction", "type": "singleSelect", "options": choices(["inbound", "outbound"])},
        {"name": "Channel", "type": "singleSelect", "options": choices(["email", "form", "telegram"])},
        {"name": "Intent", "type": "singleSelect", "options": choices(["request", "pairing", "receipt", "clarification", "clarification_answer", "status", "vendor_update", "vendor_dispatch", "manager_note"])},
        {"name": "Body", "type": "multilineText"},
        {"name": "External Message ID", "type": "singleLineText"},
        {"name": "Delivery State", "type": "singleSelect", "options": choices(["RECORDED", "PENDING", "SENT", "FAILED", "SKIPPED"])},
        {"name": "At", "type": "date", "options": {"dateFormat": {"name": "iso"}, "timeFormat": {"name": "24hour"}, "timeZone": "utc"}},
        {"name": "Created", "type": "createdTime"},
    ])
    return {table["name"]: table for table in (tenant_table, vendor_table, request_table, conversation_table)}


def seed(token: str, base_id: str) -> None:
    upsert_records(token, base_id, "Tenant Roster", "Tenant Name", [
        {"Tenant Name": name, "Email": email, "Property": prop, "Unit": unit, "Active": True}
        for name, email, prop, unit in TENANTS
    ])
    upsert_records(token, base_id, "Vendors", "Vendor Name", [
        {"Vendor Name": name, "Email": "sambhavn8n@gmail.com", "Phone": phone,
         "Trades": trades.split(","), "Properties": properties.split(",") if properties else [],
         "Priority": priority, "Active": True}
        for name, trades, properties, priority, phone in VENDORS
    ])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-id", required=True)
    parser.add_argument("--apply", action="store_true", help="Create missing typed tables and seed the demo roster.")
    parser.add_argument("--rebuild-demo-base", action="store_true", help="Delete and recreate only Stage 9 demo tables.")
    args = parser.parse_args()
    token = os.environ.get("AIRTABLE_PAT", "").strip() or local_env_value("AIRTABLE_PAT")

    print("Stage 9 Airtable schema: Requests, Conversations, Tenant Roster, Vendors")
    print("Uses links, selects, email, phone, checkbox, number, long text, date, lookup, and audit-time fields.")
    if not args.apply:
        print("Dry run only. Add --apply after configuring AIRTABLE_PAT locally.")
        return 0
    if not token:
        raise SystemExit("AIRTABLE_PAT must be set in .env or the local environment before --apply.")
    if args.rebuild_demo_base and not args.apply:
        raise SystemExit("--rebuild-demo-base requires --apply.")

    existing = request(token, "GET", schema_url(args.base_id)).get("tables", [])
    names = {"Requests", "Conversations", "Tenant Roster", "Vendors"}
    if args.rebuild_demo_base and names & {table["name"] for table in existing}:
        raise SystemExit(
            "Airtable's public API cannot delete existing tables. Delete only Requests, Conversations, Tenant Roster, "
            "and Vendors in the Airtable UI, then rerun this command to create the typed local-demo tables."
        )
    existing_names = {table["name"] for table in existing}
    if names & existing_names:
        missing = names - existing_names
        if missing:
            raise SystemExit("Existing Stage 9 Airtable tables are incomplete. Use --rebuild-demo-base for the local demo base.")
        print("Typed Stage 9 Airtable tables already exist; roster records will be upserted.")
    else:
        build_schema(token, args.base_id)
        print("Created typed Stage 9 Airtable tables.")
    seed(token, args.base_id)
    print("Seeded 9 synthetic/demo tenants and 4 controlled-demo vendors.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

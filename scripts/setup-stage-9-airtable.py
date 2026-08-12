#!/usr/bin/env python3
"""Create or rebuild the typed local-demo Airtable workspace.

The script uses only AIRTABLE_PAT from the local environment or ignored .env file.
``--rebuild-demo-base`` deletes only the four named Stage 9 demo tables and is never
appropriate for a client or production base.
"""

import argparse
import datetime
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
MISSING_INFO = ["UNIT", "PROPERTY", "CONTACT", "ACCESS_PERMISSION", "PET_ON_SITE", "ISSUE_DETAIL", "ONSET_TIME"]

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


def timestamp_options():
    return {
        "dateFormat": {"name": "iso", "format": "YYYY-MM-DD"},
        "timeFormat": {"name": "24hour", "format": "HH:mm"},
        "timeZone": "utc",
    }


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


def update_field(token: str, base_id: str, table_id: str, field_id_value: str, field: dict) -> dict:
    return request(token, "PATCH", schema_url(base_id, f"/{table_id}/fields/{field_id_value}"), field)


def ensure_field(token: str, base_id: str, table: dict, field: dict) -> dict:
    """Create an optional post-create field once, including during a resumed rebuild."""
    for existing in table["fields"]:
        if existing["name"] == field["name"]:
            return existing
    created = add_field(token, base_id, table["id"], field)
    table["fields"].append(created)
    return created


def ensure_choice_options(token: str, base_id: str, table: dict, field_name: str, names: list[str]) -> None:
    """Report old select lists that Airtable's public schema API cannot amend."""
    current = next(field for field in table["fields"] if field["name"] == field_name)
    existing = current.get("options", {}).get("choices", [])
    existing_names = {choice.get("name") for choice in existing}
    if all(name in existing_names for name in names):
        return
    missing = ", ".join(name for name in names if name not in existing_names)
    print(f"Existing {table['name']}.{field_name} is missing select options: {missing}. New demo tables include them.")


def ensure_conversation_timestamp(token: str, base_id: str, table: dict) -> None:
    """Repair an empty partial rebuild where Airtable created `At` as date-only."""
    at_field = next((field for field in table["fields"] if field["name"] == "At"), None)
    if at_field and at_field["type"] != "dateTime":
        renamed = update_field(token, base_id, table["id"], at_field["id"], {"name": "Date"})
        table["fields"][table["fields"].index(at_field)] = renamed
    ensure_field(token, base_id, table, {"name": "At", "type": "dateTime", "options": timestamp_options()})


def ensure_inverse_link_name(token: str, base_id: str, source_table: dict, source_name: str, target_table: dict, target_name: str) -> None:
    source = next(field for field in source_table["fields"] if field["name"] == source_name)
    inverse_id = source.get("options", {}).get("inverseLinkFieldId")
    inverse = next((field for field in target_table["fields"] if field["id"] == inverse_id), None)
    if inverse and inverse["name"] != target_name:
        updated = update_field(token, base_id, target_table["id"], inverse["id"], {"name": target_name})
        target_table["fields"][target_table["fields"].index(inverse)] = updated


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


def build_schema(token: str, base_id: str, existing: list[dict]) -> dict[str, dict]:
    by_name = {table["name"]: table for table in existing}
    tenant_table = by_name.get("Tenant Roster") or create_table(token, base_id, "Tenant Roster", [
        {"name": "Tenant Name", "type": "singleLineText"},
        {"name": "Email", "type": "email"},
        {"name": "Property", "type": "singleSelect", "options": choices(PROPERTIES)},
        {"name": "Unit", "type": "singleLineText"},
        {"name": "Telegram Chat ID", "type": "singleLineText"},
        {"name": "Active", "type": "checkbox", "options": {"icon": "check", "color": "greenBright"}},
    ])
    vendor_table = by_name.get("Vendors") or create_table(token, base_id, "Vendors", [
        {"name": "Vendor Name", "type": "singleLineText"},
        {"name": "Email", "type": "email"},
        {"name": "Phone", "type": "phoneNumber"},
        {"name": "Trades", "type": "multipleSelects", "options": choices(TRADES)},
        {"name": "Properties", "type": "multipleSelects", "options": choices(PROPERTIES)},
        {"name": "Priority", "type": "number", "options": {"precision": 0}},
        {"name": "Active", "type": "checkbox", "options": {"icon": "check", "color": "greenBright"}},
    ])
    request_table = by_name.get("Requests") or create_table(token, base_id, "Requests", [
        {"name": "Reference", "type": "singleLineText"},
        {"name": "Status", "type": "singleSelect", "options": choices(["NEW", "ALERTED", "ACKED", "HELD", "CLOSED", "NEEDS_REVIEW"])},
        {"name": "Priority", "type": "singleSelect", "options": choices(["EMERGENCY", "URGENT", "ROUTINE", "NEEDS_REVIEW"])},
        {"name": "Source", "type": "singleSelect", "options": choices(["email", "form", "telegram", "fixture", "import"])},
        {"name": "Tenant", "type": "multipleRecordLinks", "options": {"linkedTableId": tenant_table["id"]}},
        {"name": "Tenant Email", "type": "email"},
        {"name": "Property", "type": "singleSelect", "options": choices(PROPERTIES)},
        {"name": "Unit", "type": "singleLineText"},
        {"name": "Trade", "type": "singleSelect", "options": choices(TRADES)},
        {"name": "Summary", "type": "multilineText"},
        {"name": "Missing Info", "type": "multipleSelects", "options": choices(MISSING_INFO)},
        {"name": "Human Only", "type": "checkbox", "options": {"icon": "check", "color": "orangeBright"}},
        {"name": "Vendor Status", "type": "singleSelect", "options": choices(["NOT_STARTED", "AWAITING_VENDOR", "NEEDS_VENDOR_ASSIGNMENT", "SENDING", "SENT", "FAILED", "HELD"])},
        {"name": "Suggested Vendors", "type": "multipleRecordLinks", "options": {"linkedTableId": vendor_table["id"]}},
        {"name": "Selected Vendor", "type": "multipleRecordLinks", "options": {"linkedTableId": vendor_table["id"]}},
        {"name": "Telegram Chat ID", "type": "singleLineText"},
    ])
    ensure_field(token, base_id, request_table, {
        "name": "Vendor Email", "type": "multipleLookupValues",
        "options": {
            "recordLinkFieldId": field_id(request_table, "Selected Vendor"),
            "fieldIdInLinkedTable": field_id(vendor_table, "Email"),
        },
    })
    conversation_table = by_name.get("Conversations") or create_table(token, base_id, "Conversations", [
        {"name": "Conversation", "type": "singleLineText"},
        {"name": "Request", "type": "multipleRecordLinks", "options": {"linkedTableId": request_table["id"]}},
        {"name": "Direction", "type": "singleSelect", "options": choices(["inbound", "outbound"])},
        {"name": "Channel", "type": "singleSelect", "options": choices(["email", "form", "telegram"])},
        {"name": "Intent", "type": "singleSelect", "options": choices(["request", "pairing", "receipt", "clarification", "clarification_answer", "status", "vendor_update", "vendor_dispatch", "manager_note"])},
        {"name": "Body", "type": "multilineText"},
        {"name": "External Message ID", "type": "singleLineText"},
        {"name": "Delivery State", "type": "singleSelect", "options": choices(["RECORDED", "PENDING", "SENT", "FAILED", "SKIPPED"])},
        {"name": "At", "type": "dateTime", "options": timestamp_options()},
    ])
    ensure_conversation_timestamp(token, base_id, conversation_table)
    ensure_choice_options(token, base_id, request_table, "Missing Info", MISSING_INFO)
    ensure_inverse_link_name(token, base_id, request_table, "Suggested Vendors", vendor_table, "Suggested Requests")
    ensure_inverse_link_name(token, base_id, request_table, "Selected Vendor", vendor_table, "Selected Requests")
    # Airtable's public schema endpoint cannot create native created/modified-time fields.
    # These fields are populated from Postgres timestamps during the controlled demo sync.
    audit_field = {"type": "dateTime", "options": timestamp_options()}
    ensure_field(token, base_id, tenant_table, {"name": "Created At", **audit_field})
    ensure_field(token, base_id, vendor_table, {"name": "Created At", **audit_field})
    ensure_field(token, base_id, request_table, {"name": "Created At", **audit_field})
    ensure_field(token, base_id, request_table, {"name": "Last Synced", **audit_field})
    ensure_field(token, base_id, conversation_table, {"name": "Created At", **audit_field})
    return {table["name"]: table for table in (tenant_table, vendor_table, request_table, conversation_table)}


def seed(token: str, base_id: str) -> None:
    created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    upsert_records(token, base_id, "Tenant Roster", "Tenant Name", [
        {"Tenant Name": name, "Email": email, "Property": prop, "Unit": unit, "Active": True, "Created At": created_at}
        for name, email, prop, unit in TENANTS
    ])
    upsert_records(token, base_id, "Vendors", "Vendor Name", [
        {"Vendor Name": name, "Email": "sambhavn8n@gmail.com", "Phone": phone,
         "Trades": trades.split(","), "Properties": properties.split(",") if properties else [],
         "Priority": priority, "Active": True, "Created At": created_at}
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
    existing_names = {table["name"] for table in existing}
    partial_typed_rebuild = bool(existing_names & names) and existing_names & names != names and all(
        any(field["type"] != "singleLineText" for field in table["fields"])
        for table in existing if table["name"] in names
    )
    if args.rebuild_demo_base and names & existing_names and not partial_typed_rebuild:
        typed_existing = all(
            any(field["type"] != "singleLineText" for field in table["fields"])
            for table in existing if table["name"] in names
        )
        if not typed_existing:
            raise SystemExit(
                "Airtable's public API cannot delete existing tables. Delete only Requests, Conversations, Tenant Roster, "
                "and Vendors in the Airtable UI, then rerun this command to create the typed local-demo tables."
            )
    if names <= existing_names:
        build_schema(token, args.base_id, existing)
        print("Verified typed Stage 9 Airtable tables; roster records will be upserted.")
    else:
        build_schema(token, args.base_id, existing)
        print("Created typed Stage 9 Airtable tables.")
    seed(token, args.base_id)
    print("Seeded 9 synthetic/demo tenants and 4 controlled-demo vendors.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

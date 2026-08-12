#!/usr/bin/env python3
"""Create the demo Airtable schema and synthetic tenant/vendor roster.

Set AIRTABLE_PAT locally, create an empty Airtable base, then run this script with
--base-id and --apply. The token and base data are intentionally never stored in git.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


API = "https://api.airtable.com/v0"
META_API = "https://api.airtable.com/v0/meta"

TABLES = {
    "Requests": [
        "Reference", "Status", "Priority", "Source", "Tenant Name", "Tenant Email", "Property", "Unit",
        "Trade", "Summary", "Missing Info", "Human Only", "Vendor Status", "Suggested Vendors",
        "Selected Vendor", "Vendor Email", "Telegram Chat ID",
    ],
    "Conversations": ["Reference", "Direction", "Channel", "Intent", "Body", "External Message ID", "Delivery State", "At"],
    "Tenant Roster": ["Tenant Name", "Email", "Property", "Unit", "Telegram Chat ID", "Active"],
    "Vendors": ["Vendor Name", "Email", "Trades", "Properties", "Priority", "Active"],
}

TENANTS = [
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
    ("Maple Plumbing", "PLUMBING", "Maple Court", 1),
    ("Oak HVAC Service", "HVAC", "Oak Terrace", 1),
    ("Pine Electrical", "ELECTRICAL", "Pine House", 1),
    ("General Property Repairs", "GENERAL,APPLIANCE,STRUCTURAL,PEST,LOCKS_SECURITY", "", 50),
]


def request(token: str, method: str, url: str, payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Airtable {method} {url} failed: {exc.code} {detail}") from exc


def table_url(base_id: str, table: str) -> str:
    return f"{API}/{base_id}/{urllib.parse.quote(table, safe='')}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-id", required=True)
    parser.add_argument("--apply", action="store_true", help="Perform Airtable writes. Without this, print the planned schema.")
    args = parser.parse_args()
    token = os.environ.get("AIRTABLE_PAT", "").strip()

    print("Airtable demo schema:")
    for name, fields in TABLES.items():
        print(f"- {name}: {', '.join(fields)}")
    print("- Seeded tenant roster: 8 synthetic records")
    print("- Seeded vendor roster: 4 synthetic records using sambhavn8n@gmail.com")
    if not args.apply:
        print("Dry run only. Set AIRTABLE_PAT locally and re-run with --apply.")
        return 0
    if not token:
        raise SystemExit("AIRTABLE_PAT must be set in the local environment before --apply.")

    existing = request(token, "GET", f"{META_API}/bases/{args.base_id}/tables")
    existing_names = {table["name"] for table in existing.get("tables", [])}
    for name, fields in TABLES.items():
        if name in existing_names:
            continue
        request(token, "POST", f"{META_API}/bases/{args.base_id}/tables", {
            "name": name,
            "fields": [{"name": field, "type": "multilineText" if field == "Body" else "singleLineText"} for field in fields],
        })
        print(f"Created table: {name}")

    roster_records = [{"fields": {"Tenant Name": name, "Email": email, "Property": prop, "Unit": unit, "Active": "Yes"}} for name, email, prop, unit in TENANTS]
    vendor_records = [{"fields": {"Vendor Name": name, "Email": "sambhavn8n@gmail.com", "Trades": trades, "Properties": properties, "Priority": str(priority), "Active": "Yes"}} for name, trades, properties, priority in VENDORS]
    request(token, "POST", table_url(args.base_id, "Tenant Roster"), {"records": roster_records})
    request(token, "POST", table_url(args.base_id, "Vendors"), {"records": vendor_records})
    print("Seeded synthetic Tenant Roster and Vendors records.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

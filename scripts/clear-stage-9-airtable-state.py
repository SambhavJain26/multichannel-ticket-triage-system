#!/usr/bin/env python3
"""Clear only request and conversation records from the configured demo Airtable base."""

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


def local_env_value(name: str, default: str = "") -> str:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return default
    prefix = f"{name}="
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.startswith(prefix):
            return line[len(prefix):].strip().strip('"').strip("'")
    return default


def request(token: str, method: str, url: str):
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Airtable {method} request failed: {exc.code} {detail}") from exc


def psql(sql: str) -> str:
    user = local_env_value("POSTGRES_USER", "maintenance_triage")
    database = local_env_value("POSTGRES_DB", "maintenance_triage")
    result = subprocess.run(
        [
            "docker", "compose", "exec", "-T", "postgres", "psql", "-U", user,
            "-d", database, "-At", "-v", "ON_ERROR_STOP=1", "-c", sql,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def table_url(base_id: str, table_name: str) -> str:
    return f"{API}/{base_id}/{urllib.parse.quote(table_name, safe='')}"


def record_ids(token: str, base_id: str, table_name: str) -> list[str]:
    ids: list[str] = []
    offset = ""
    while True:
        params = {"pageSize": "100"}
        if offset:
            params["offset"] = offset
        url = table_url(base_id, table_name) + "?" + urllib.parse.urlencode(params)
        page = request(token, "GET", url)
        ids.extend(record["id"] for record in page.get("records", []))
        offset = page.get("offset", "")
        if not offset:
            return ids


def delete_records(token: str, base_id: str, table_name: str, ids: list[str]) -> None:
    for start in range(0, len(ids), 10):
        query = urllib.parse.urlencode([("records[]", record_id) for record_id in ids[start:start + 10]])
        request(token, "DELETE", table_url(base_id, table_name) + "?" + query)


def main() -> int:
    parser = argparse.ArgumentParser(description="Clear Stage 9 operational Airtable demo records.")
    parser.add_argument("--apply", action="store_true", help="Delete records after showing the exact counts.")
    args = parser.parse_args()

    token = os.environ.get("AIRTABLE_PAT", "").strip() or local_env_value("AIRTABLE_PAT")
    if not token:
        raise SystemExit("AIRTABLE_PAT must be set in .env or the local environment.")
    config_text = psql("SELECT value::text FROM triage.config WHERE key='airtable';")
    if not config_text:
        raise SystemExit("The local Airtable configuration is missing.")
    config = json.loads(config_text)
    if not config.get("enabled") or not config.get("base_id"):
        raise SystemExit("The local Airtable configuration is not enabled.")

    base_id = str(config["base_id"])
    conversations_table = str(config.get("conversations_table", "Conversations"))
    requests_table = str(config.get("requests_table", "Requests"))
    conversations = record_ids(token, base_id, conversations_table)
    requests = record_ids(token, base_id, requests_table)
    print(f"Airtable demo state: {len(requests)} request records and {len(conversations)} conversation records.")
    print("Tenant Roster and Vendors are not reset.")

    if not args.apply:
        print("Dry run only. Add --apply to delete these operational records.")
        return 0

    delete_records(token, base_id, conversations_table, conversations)
    delete_records(token, base_id, requests_table, requests)
    remaining_conversations = record_ids(token, base_id, conversations_table)
    remaining_requests = record_ids(token, base_id, requests_table)
    if remaining_conversations or remaining_requests:
        raise RuntimeError(
            f"Airtable reset verification failed: {len(remaining_requests)} requests and "
            f"{len(remaining_conversations)} conversations remain."
        )
    print("Airtable Requests and Conversations are empty.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

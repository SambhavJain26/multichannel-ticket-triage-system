#!/usr/bin/env python3
import json
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"

ALLOWED_PRIORITIES = {"EMERGENCY", "URGENT", "ROUTINE", "NEEDS_REVIEW"}
ALLOWED_MODEL_PRIORITIES = {"EMERGENCY", "URGENT", "ROUTINE"}
ALLOWED_REQUEST_TYPES = {"NEW_ISSUE", "FOLLOW_UP", "NOT_A_REQUEST"}
ALLOWED_TRADES = {
    "PLUMBING",
    "ELECTRICAL",
    "HVAC",
    "APPLIANCE",
    "STRUCTURAL",
    "PEST",
    "LOCKS_SECURITY",
    "GENERAL",
    "UNKNOWN",
}
ALLOWED_SIGNALS = {
    "GAS",
    "CARBON_MONOXIDE",
    "SMOKE_FIRE",
    "ELECTRICAL",
    "FLOOD",
    "SEWAGE",
    "NO_HEAT",
    "NO_WATER",
    "NO_COOLING",
    "SECURITY",
    "STRUCTURAL",
    "NONE",
}
ALLOWED_MISSING_INFO = {
    "UNIT",
    "PROPERTY",
    "CONTACT",
    "ACCESS_PERMISSION",
    "PET_ON_SITE",
    "ISSUE_DETAIL",
    "ONSET_TIME",
}
ALLOWED_DRAFT_POLICIES = {"draft_allowed", "draft_suppressed"}

REQUIRED_KEYS = {
    "id",
    "slug",
    "is_live_demo",
    "expected_priority",
    "expected_model_priority",
    "expected_request_type",
    "expected_is_maintenance_request",
    "expected_trade",
    "expected_safety_signals",
    "expected_missing_info",
    "expected_language",
    "expected_habitability_flag",
    "expected_accommodation_or_legal_flag",
    "expected_human_only",
    "expected_override_applied",
    "expected_draft_policy",
    "notes",
}

REQUIRED_COVERAGE = {
    "EMERGENCY": lambda rows: any(r["expected_priority"] == "EMERGENCY" for r in rows),
    "URGENT": lambda rows: any(r["expected_priority"] == "URGENT" for r in rows),
    "ROUTINE": lambda rows: any(r["expected_priority"] == "ROUTINE" for r in rows),
    "NEEDS_REVIEW": lambda rows: any(r["expected_priority"] == "NEEDS_REVIEW" for r in rows),
    "NOT_A_REQUEST": lambda rows: any(r["expected_request_type"] == "NOT_A_REQUEST" for r in rows),
    "FOLLOW_UP": lambda rows: any(r["expected_request_type"] == "FOLLOW_UP" for r in rows),
    "SPANISH": lambda rows: any(r["expected_language"] == "es" for r in rows),
    "ACCOMMODATION_LEGAL": lambda rows: any(r["expected_accommodation_or_legal_flag"] for r in rows),
    "HUMAN_ONLY": lambda rows: any(r["expected_human_only"] for r in rows),
    "PROMPT_INJECTION": lambda rows: any(r["slug"] == "prompt-injection" for r in rows),
    "NEGATION_TRAP": lambda rows: any(r["slug"] == "negation-trap" for r in rows),
    "REPLY_THREADING": lambda rows: any(r["slug"] == "tenant-reply-threading" for r in rows),
    "AUTO_RESPONDER_LOOP": lambda rows: any(r["slug"] == "auto-responder-loop-bait" for r in rows),
    "VOICEMAIL_TRANSCRIPT": lambda rows: any(r["slug"] == "voicemail-transcript" for r in rows),
}


def fail(message: str) -> None:
    print(f"Stage 2 fixture validation failed: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_expected(path: pathlib.Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"{path.name} is not valid JSON: {exc}")


def assert_string_list(row: dict, key: str, allowed: set[str]) -> None:
    value = row.get(key)
    if not isinstance(value, list) or not value:
        fail(f"{row.get('slug', row.get('id'))}: {key} must be a non-empty array")
    unknown = set(value) - allowed
    if unknown:
        fail(f"{row['slug']}: {key} has invalid values {sorted(unknown)}")


def main() -> int:
    txt_files = sorted(FIXTURES.glob("[0-9][0-9]-*.txt"))
    expected_files = sorted(FIXTURES.glob("[0-9][0-9]-*.expected.json"))

    if len(txt_files) != 30:
        fail(f"expected 30 fixture text files, found {len(txt_files)}")
    if len(expected_files) != 30:
        fail(f"expected 30 expected JSON files, found {len(expected_files)}")

    expected_by_stem = {p.name.replace(".expected.json", ""): p for p in expected_files}
    rows = []

    for txt in txt_files:
        stem = txt.stem
        expected = expected_by_stem.get(stem)
        if expected is None:
            fail(f"{txt.name} has no matching .expected.json file")
        if not txt.read_text(encoding="utf-8").strip():
            fail(f"{txt.name} is empty")

        row = load_expected(expected)
        missing = REQUIRED_KEYS - set(row)
        if missing:
            fail(f"{expected.name} missing keys {sorted(missing)}")

        expected_prefix = f"{row['id']:02d}-{row['slug']}"
        if expected_prefix != stem:
            fail(f"{expected.name} id/slug {expected_prefix} does not match filename {stem}")

        if row["expected_priority"] not in ALLOWED_PRIORITIES:
            fail(f"{row['slug']}: invalid expected_priority")
        if row["expected_model_priority"] not in ALLOWED_MODEL_PRIORITIES:
            fail(f"{row['slug']}: invalid expected_model_priority")
        if row["expected_request_type"] not in ALLOWED_REQUEST_TYPES:
            fail(f"{row['slug']}: invalid expected_request_type")
        if row["expected_trade"] not in ALLOWED_TRADES:
            fail(f"{row['slug']}: invalid expected_trade")
        if row["expected_draft_policy"] not in ALLOWED_DRAFT_POLICIES:
            fail(f"{row['slug']}: invalid expected_draft_policy")

        assert_string_list(row, "expected_safety_signals", ALLOWED_SIGNALS)
        assert_string_list(row, "expected_missing_info", ALLOWED_MISSING_INFO | {"NONE"})

        for boolean_key in [
            "is_live_demo",
            "expected_is_maintenance_request",
            "expected_habitability_flag",
            "expected_accommodation_or_legal_flag",
            "expected_human_only",
            "expected_override_applied",
        ]:
            if not isinstance(row[boolean_key], bool):
                fail(f"{row['slug']}: {boolean_key} must be boolean")

        if row["expected_human_only"] and row["expected_draft_policy"] != "draft_suppressed":
            fail(f"{row['slug']}: human_only fixtures must suppress drafts")

        rows.append(row)

    for label, check in REQUIRED_COVERAGE.items():
        if not check(rows):
            fail(f"missing required coverage: {label}")

    live_demo = [row for row in rows if row["is_live_demo"]]
    if len(live_demo) != 6:
        fail(f"expected 6 live demo fixtures, found {len(live_demo)}")

    print("Stage 2 fixture validation passed.")
    print(f"Validated {len(rows)} fixtures and {len(live_demo)} live-demo fixtures.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

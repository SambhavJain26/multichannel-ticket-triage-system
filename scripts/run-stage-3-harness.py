#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import os
import pathlib
import re
import sys
import time
from collections import Counter, defaultdict
from typing import Any

import requests
from dotenv import load_dotenv


ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"
PROMPTS = ROOT / "prompts"
TMP_STAGE3 = ROOT / "tmp" / "stage-3"
SCORECARD = ROOT / "docs" / "stage-3-scorecard.md"
KNOWN_GOOD = FIXTURES / "known-good-request.json"

DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-5-nano"
DEFAULT_FALLBACK_MODEL = "gpt-5.6-luna"
DEFAULT_RUNS = 3

PRIORITY_RANK = {
    "ROUTINE": 1,
    "URGENT": 2,
    "NEEDS_REVIEW": 2,
    "EMERGENCY": 3,
}

STANDARD_PRICING_PER_1M = {
    "gpt-5-nano": {"input": 0.05, "cached_input": 0.005, "output": 0.40},
    "gpt-5.4-nano": {"input": 0.20, "cached_input": 0.02, "output": 1.25},
    "gpt-5.6-luna": {"input": 0.20, "cached_input": 0.02, "output": 1.20},
}

SAFETY_RULES = [
    ("GAS", re.compile(r"\b(smell(s|ing)? (of )?gas|gas leak|gas odou?r|propane leak|rotten egg smell)\b", re.I)),
    ("CARBON_MONOXIDE", re.compile(r"\b(carbon monoxide|co alarm|co detector (going off|beeping|alarming))\b", re.I)),
    ("SMOKE_FIRE", re.compile(r"\b(smoke|burning smell|smells? like burning|sparking|sparks|exposed wire|fire)\b", re.I)),
    ("FLOOD", re.compile(r"\b(flooding|flooded|water (is )?pouring|gushing|burst pipe|pipe .*burst|burst .*pipe|water everywhere|ceiling (is )?collapsing)\b", re.I)),
    ("SEWAGE", re.compile(r"\b(raw sewage|sewage backing up|sewage backup|sewer backup|toilet overflowing)\b", re.I)),
    ("NO_HEAT", re.compile(r"\b(no heat|heat (is )?(out|not working|dead)|furnace (is )?(out|dead|not working))\b", re.I)),
    ("NO_WATER", re.compile(r"\b(no water|water (is )?(shut off|not running)|no running water)\b", re.I)),
    ("SECURITY", re.compile(r"\b(broke in|broken into|won'?t lock|can'?t lock|door (is )?(broken|kicked in)|lock (is )?broken)\b", re.I)),
]

NEGATED = re.compile(r"\b(no|not|isn'?t|wasn'?t|never|without)\b[^.!?]{0,25}$", re.I)

DRAFT_LINT_RULES = [
    ("date_or_time_promise", re.compile(r"\b(tomorrow|tonight|this (morning|afternoon|evening)|within \d+|by \d{1,2}|at \d{1,2}|by end of day|same day)\b", re.I)),
    ("cost_or_charge", re.compile(r"(\$|\bcost\b|\bcharge\b|\bfee\b|\bpay\b|\bpaid\b)", re.I)),
    ("legal_language", re.compile(r"\b(legal|law|rights?|deadline|required by|liable|liability|code enforcement|habitability)\b", re.I)),
    ("repair_or_safety_advice", re.compile(r"\b(shut off|turn off|open (a )?window|evacuate|breaker|try to fix|reset|repair it yourself)\b", re.I)),
    ("appointment_promise", re.compile(r"\b(appointment|scheduled|technician will|vendor will|we will send|we'll send)\b", re.I)),
]


def load_json(path: pathlib.Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: pathlib.Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def now_stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def fail(message: str) -> None:
    print(f"Stage 3 harness failed: {message}", file=sys.stderr)
    raise SystemExit(1)


def normalize_path(path_text: str) -> pathlib.Path:
    path = pathlib.Path(path_text)
    if not path.is_absolute():
        path = ROOT / path
    return path


def expected_path_for_fixture(fixture_path: pathlib.Path) -> pathlib.Path:
    return fixture_path.with_suffix(".expected.json")


def fixture_pairs() -> list[tuple[pathlib.Path, dict[str, Any]]]:
    pairs = []
    for txt in sorted(FIXTURES.glob("[0-9][0-9]-*.txt")):
        expected_path = expected_path_for_fixture(txt)
        if not expected_path.exists():
            fail(f"{txt.name} has no matching expected JSON")
        pairs.append((txt, load_json(expected_path)))
    if len(pairs) != 30:
        fail(f"expected 30 fixtures, found {len(pairs)}")
    return pairs


def select_fixture_pairs(args: argparse.Namespace) -> list[tuple[pathlib.Path, dict[str, Any]]]:
    pairs = fixture_pairs()
    selected_ids = set()
    selected_slugs = set()

    for value in getattr(args, "fixture_id", []) or []:
        selected_ids.add(int(value))
    for value in getattr(args, "fixture_slug", []) or []:
        selected_slugs.add(value)

    if selected_ids or selected_slugs:
        pairs = [
            (path, expected)
            for path, expected in pairs
            if expected["id"] in selected_ids or expected["slug"] in selected_slugs
        ]
    elif getattr(args, "live_only", False):
        pairs = [(path, expected) for path, expected in pairs if expected["is_live_demo"]]

    if not pairs:
        fail("fixture selection produced no fixtures")
    return pairs


def validate_value(value: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    errors: list[str] = []

    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} not in enum {schema['enum']}")
        return errors

    schema_type = schema.get("type")
    if isinstance(schema_type, list):
        type_errors = []
        for one_type in schema_type:
            trial_schema = {**schema, "type": one_type}
            trial_schema.pop("enum", None)
            trial = validate_value(value, trial_schema, path)
            if not trial:
                return errors
            type_errors.extend(trial)
        errors.append(f"{path}: value does not match any allowed type {schema_type}: {type_errors[0]}")
        return errors

    if schema_type == "null":
        if value is not None:
            errors.append(f"{path}: expected null")
        return errors
    if schema_type == "boolean":
        if not isinstance(value, bool):
            errors.append(f"{path}: expected boolean")
        return errors
    if schema_type == "string":
        if not isinstance(value, str):
            errors.append(f"{path}: expected string")
        return errors
    if schema_type == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            errors.append(f"{path}: expected integer")
        return errors
    if schema_type == "number":
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            errors.append(f"{path}: expected number")
        return errors
    if schema_type == "array":
        if not isinstance(value, list):
            errors.append(f"{path}: expected array")
            return errors
        item_schema = schema.get("items", {})
        for index, item in enumerate(value):
            errors.extend(validate_value(item, item_schema, f"{path}[{index}]"))
        return errors
    if schema_type == "object":
        if not isinstance(value, dict):
            errors.append(f"{path}: expected object")
            return errors
        required = set(schema.get("required", []))
        missing = required - set(value)
        if missing:
            errors.append(f"{path}: missing required keys {sorted(missing)}")
        if schema.get("additionalProperties") is False:
            allowed = set(schema.get("properties", {}))
            extra = set(value) - allowed
            if extra:
                errors.append(f"{path}: unexpected keys {sorted(extra)}")
        for key, child_schema in schema.get("properties", {}).items():
            if key in value:
                errors.extend(validate_value(value[key], child_schema, f"{path}.{key}"))
        return errors

    return errors


def response_format(name: str, schema: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "json_schema",
        "name": name,
        "strict": True,
        "schema": schema,
    }


def load_known_good_reasoning(model: str) -> str | None:
    if not KNOWN_GOOD.exists():
        return None
    try:
        request = load_json(KNOWN_GOOD)
    except Exception:
        return None
    if request.get("model") != model:
        return None
    reasoning = request.get("reasoning")
    if isinstance(reasoning, dict):
        return reasoning.get("effort")
    return None


def build_request(
    *,
    model: str,
    instructions: str,
    input_text: str,
    schema_name: str,
    schema: dict[str, Any],
    max_output_tokens: int,
    reasoning_effort: str | None,
) -> dict[str, Any]:
    request: dict[str, Any] = {
        "model": model,
        "store": False,
        "instructions": instructions,
        "input": input_text,
        "text": {"format": response_format(schema_name, schema)},
        "max_output_tokens": max_output_tokens,
    }
    if reasoning_effort:
        request["reasoning"] = {"effort": reasoning_effort}
    return request


def auth_headers() -> dict[str, str]:
    load_dotenv(ROOT / ".env")
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        fail("OPENAI_API_KEY is not set in the environment or local .env")
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def base_url() -> str:
    load_dotenv(ROOT / ".env")
    return os.environ.get("OPENAI_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


def post_response(request_body: dict[str, Any], timeout: int = 45) -> tuple[dict[str, Any], int, int]:
    start = time.perf_counter()
    response = requests.post(
        f"{base_url()}/responses",
        headers=auth_headers(),
        json=request_body,
        timeout=timeout,
    )
    latency_ms = int((time.perf_counter() - start) * 1000)
    try:
        payload = response.json()
    except Exception:
        payload = {"error": {"message": response.text}}
    return payload, response.status_code, latency_ms


def is_reasoning_param_error(payload: dict[str, Any]) -> bool:
    text = json.dumps(payload).lower()
    return "reasoning" in text and ("unsupported" in text or "unknown" in text or "invalid" in text)


def is_model_not_found(payload: dict[str, Any], status: int) -> bool:
    text = json.dumps(payload).lower()
    return status in {400, 404} and ("model" in text and ("not found" in text or "does not exist" in text or "unsupported" in text))


def call_structured(
    *,
    model: str,
    instructions: str,
    input_text: str,
    schema_name: str,
    schema: dict[str, Any],
    max_output_tokens: int,
    reasoning_effort: str | None,
    retry_without_reasoning: bool = True,
) -> dict[str, Any]:
    request_body = build_request(
        model=model,
        instructions=instructions,
        input_text=input_text,
        schema_name=schema_name,
        schema=schema,
        max_output_tokens=max_output_tokens,
        reasoning_effort=reasoning_effort,
    )
    payload, status, latency_ms = post_response(request_body)
    used_request = request_body

    if status >= 400 and reasoning_effort and retry_without_reasoning and is_reasoning_param_error(payload):
        request_body = build_request(
            model=model,
            instructions=instructions,
            input_text=input_text,
            schema_name=schema_name,
            schema=schema,
            max_output_tokens=max_output_tokens,
            reasoning_effort=None,
        )
        payload, status, latency_ms = post_response(request_body)
        used_request = request_body

    return {
        "ok": status < 400,
        "status": status,
        "latency_ms": latency_ms,
        "request": used_request,
        "response": payload,
    }


def extract_output_text(payload: dict[str, Any]) -> str | None:
    output_text = payload.get("output_text")
    if isinstance(output_text, str):
        return output_text

    chunks: list[str] = []
    for item in payload.get("output", []) if isinstance(payload.get("output"), list) else []:
        if isinstance(item, dict):
            if isinstance(item.get("text"), str):
                chunks.append(item["text"])
            content = item.get("content")
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and isinstance(part.get("text"), str):
                        chunks.append(part["text"])
                    elif isinstance(part, str):
                        chunks.append(part)
    return "".join(chunks).strip() if chunks else None


def parse_structured_output(call_result: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    if not call_result["ok"]:
        return {
            "schema_valid": False,
            "json": None,
            "error": call_result["response"].get("error", call_result["response"]),
        }

    text = extract_output_text(call_result["response"])
    if not text:
        return {"schema_valid": False, "json": None, "error": "no output text in response"}
    try:
        parsed = json.loads(text)
    except Exception as exc:
        return {"schema_valid": False, "json": None, "error": f"invalid JSON: {exc}: {text[:200]}"}

    errors = validate_value(parsed, schema)
    return {"schema_valid": not errors, "json": parsed, "error": errors or None}


def usage_from_response(payload: dict[str, Any]) -> dict[str, int]:
    usage = payload.get("usage") if isinstance(payload, dict) else None
    if not isinstance(usage, dict):
        return {"input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    input_tokens = int(usage.get("input_tokens") or usage.get("prompt_tokens") or 0)
    output_tokens = int(usage.get("output_tokens") or usage.get("completion_tokens") or 0)
    cached_input = 0

    input_details = usage.get("input_tokens_details") or usage.get("prompt_tokens_details")
    if isinstance(input_details, dict):
        cached_input = int(input_details.get("cached_tokens") or 0)

    return {
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_input,
        "output_tokens": output_tokens,
        "total_tokens": int(usage.get("total_tokens") or input_tokens + output_tokens),
    }


def estimated_cost(model: str, usage: dict[str, int]) -> float:
    pricing = STANDARD_PRICING_PER_1M.get(model)
    if not pricing:
        return 0.0
    cached = usage.get("cached_input_tokens", 0)
    uncached_input = max(usage.get("input_tokens", 0) - cached, 0)
    return (
        uncached_input * pricing["input"]
        + cached * pricing["cached_input"]
        + usage.get("output_tokens", 0) * pricing["output"]
    ) / 1_000_000


def wrap_message(message: str) -> str:
    cleaned = message.strip()
    if len(cleaned) > 1500:
        cleaned = cleaned[:1500]
    return f"<<<MESSAGE>>>\n{cleaned}\n<<<END MESSAGE>>>"


def safety_rule_hits(message: str) -> list[str]:
    hits: list[str] = []
    for signal, regex in SAFETY_RULES:
        for match in regex.finditer(message):
            prefix = message[: match.start()]
            if NEGATED.search(prefix[-40:]):
                continue
            hits.append(signal)
            break
    return hits


def normalize_signal_list(values: Any) -> list[str]:
    if not isinstance(values, list) or not values:
        return ["NONE"]
    signals = [str(v) for v in values if v]
    if not signals:
        return ["NONE"]
    if len(signals) > 1 and "NONE" in signals:
        signals = [sig for sig in signals if sig != "NONE"]
    return sorted(set(signals))


def normalize_missing_info(values: Any) -> list[str]:
    if not isinstance(values, list) or not values:
        return ["NONE"]
    missing = [str(v) for v in values if v]
    return sorted(set(missing)) if missing else ["NONE"]


def max_priority(left: str, right: str | None) -> str:
    if not right:
        return left
    return left if PRIORITY_RANK[left] >= PRIORITY_RANK[right] else right


def is_low_information_request(triage: dict[str, Any], message: str) -> bool:
    missing = set(normalize_missing_info(triage.get("missing_info")))
    text = message.lower()
    word_count = len(re.findall(r"[a-z0-9]+", text))
    looks_unreadable = bool(re.search(r"(<html|<div|blockquote|Ã|â|=_nextpart|&&&|\?\?\?)", message, re.I))
    attachment_only = "see attached" in text and word_count <= 8
    return (
        triage.get("is_maintenance_request") is True
        and triage.get("request_type") == "NEW_ISSUE"
        and "ISSUE_DETAIL" in missing
        and (triage.get("confidence") == "LOW" or triage.get("trade") == "UNKNOWN" or looks_unreadable or attachment_only)
    )


def apply_rules(message: str, parsed: dict[str, Any] | None, model_error: bool) -> dict[str, Any]:
    rule_hits = safety_rule_hits(message)
    if model_error or not parsed:
        final_priority = "NEEDS_REVIEW"
        merged_signals = normalize_signal_list(rule_hits)
        return {
            "priority": final_priority,
            "rule_fired": bool(rule_hits),
            "rule_signals": rule_hits,
            "safety_signals": merged_signals,
            "human_only": False,
            "draft_allowed": False,
            "review_reason": "model_error_or_invalid_json",
        }

    model_priority = parsed["priority"]
    final_priority = max_priority(model_priority, "EMERGENCY" if rule_hits else None)
    model_signals = normalize_signal_list(parsed.get("safety_signals"))
    merged = set([] if model_signals == ["NONE"] else model_signals)
    merged.update(rule_hits)
    merged_signals = sorted(merged) if merged else ["NONE"]
    review_reason = None

    if parsed.get("confidence") == "LOW" and merged_signals != ["NONE"]:
        final_priority = "NEEDS_REVIEW"
        review_reason = "low_confidence_with_safety_signal"
    elif parsed.get("is_maintenance_request") is False and rule_hits:
        final_priority = "NEEDS_REVIEW"
        review_reason = "non_request_with_safety_rule"
    elif merged_signals == ["NONE"] and is_low_information_request(parsed, message):
        final_priority = "NEEDS_REVIEW"
        review_reason = "low_information_request"

    human_only = bool(parsed.get("accommodation_or_legal_flag"))
    draft_allowed = (
        final_priority != "NEEDS_REVIEW"
        and not human_only
        and parsed.get("is_maintenance_request") is True
        and parsed.get("request_type") != "NOT_A_REQUEST"
    )

    return {
        "priority": final_priority,
        "rule_fired": bool(rule_hits),
        "rule_signals": rule_hits,
        "safety_signals": merged_signals,
        "human_only": human_only,
        "draft_allowed": draft_allowed,
        "review_reason": review_reason,
    }


def classify_fixture(fixture_path: pathlib.Path, model: str, reasoning: str | None) -> dict[str, Any]:
    triage_schema = load_json(PROMPTS / "maintenance-triage.schema.json")
    system_prompt = read_text(PROMPTS / "classification-system.txt")
    message = read_text(fixture_path)
    call_result = call_structured(
        model=model,
        instructions=system_prompt,
        input_text=wrap_message(message),
        schema_name="maintenance_triage",
        schema=triage_schema,
        max_output_tokens=1200,
        reasoning_effort=reasoning,
    )
    parsed = parse_structured_output(call_result, triage_schema)
    rules = apply_rules(message, parsed["json"], model_error=not parsed["schema_valid"])
    usage = usage_from_response(call_result["response"])
    return {
        "fixture": fixture_path.name,
        "model": model,
        "latency_ms": call_result["latency_ms"],
        "status": call_result["status"],
        "schema_valid": parsed["schema_valid"],
        "model_json": parsed["json"],
        "parse_error": parsed["error"],
        "rules": rules,
        "usage": usage,
        "estimated_cost_usd": estimated_cost(model, usage),
        "raw_response": call_result["response"],
        "request": call_result["request"],
    }


def draft_for_classification(fixture_path: pathlib.Path, classification: dict[str, Any], model: str, reasoning: str | None) -> dict[str, Any]:
    if not classification["rules"]["draft_allowed"]:
        return {
            "skipped": True,
            "reason": "draft_policy_suppressed",
            "schema_valid": True,
            "json": None,
            "lint": [],
            "latency_ms": 0,
            "usage": {"input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            "estimated_cost_usd": 0.0,
        }

    draft_schema = load_json(PROMPTS / "maintenance-drafts.schema.json")
    system_prompt = read_text(PROMPTS / "drafting-system.txt")
    message = read_text(fixture_path)
    draft_input = json.dumps(
        {
            "triage": classification["model_json"],
            "post_rules": classification["rules"],
            "cleaned_message": message[:1500],
        },
        indent=2,
        sort_keys=True,
    )
    call_result = call_structured(
        model=model,
        instructions=system_prompt,
        input_text=draft_input,
        schema_name="maintenance_drafts",
        schema=draft_schema,
        max_output_tokens=2000,
        reasoning_effort=reasoning,
    )
    parsed = parse_structured_output(call_result, draft_schema)
    usage = usage_from_response(call_result["response"])
    lint = lint_draft(parsed["json"]) if parsed["json"] else ["draft_not_available"]
    return {
        "skipped": False,
        "schema_valid": parsed["schema_valid"],
        "json": parsed["json"],
        "parse_error": parsed["error"],
        "lint": lint,
        "latency_ms": call_result["latency_ms"],
        "usage": usage,
        "estimated_cost_usd": estimated_cost(model, usage),
        "raw_response": call_result["response"],
        "request": call_result["request"],
    }


def lint_draft(draft: dict[str, Any]) -> list[str]:
    text = "\n".join(
        str(draft.get(key, ""))
        for key in ["tenant_reply_subject", "tenant_reply_body", "vendor_note"]
    )
    findings = []
    for name, regex in DRAFT_LINT_RULES:
        if regex.search(text):
            findings.append(name)
    if len(str(draft.get("tenant_reply_body", "")).split()) > 90:
        findings.append("tenant_reply_over_80_words")
    if len(str(draft.get("vendor_note", "")).split()) > 70:
        findings.append("vendor_note_over_60_words")
    return findings


def expected_match(result: dict[str, Any], expected: dict[str, Any], draft_result: dict[str, Any] | None) -> dict[str, Any]:
    model_json = result["model_json"] or {}
    rules = result["rules"]
    final_signals = normalize_signal_list(rules.get("safety_signals"))
    expected_signals = normalize_signal_list(expected["expected_safety_signals"])
    final_missing = normalize_missing_info(model_json.get("missing_info"))
    expected_missing = normalize_missing_info(expected["expected_missing_info"])
    actual_draft_policy = "draft_allowed" if rules["draft_allowed"] else "draft_suppressed"

    checks = {
        "schema_valid": result["schema_valid"],
        "model_priority": model_json.get("priority") == expected["expected_model_priority"],
        "final_priority": rules["priority"] == expected["expected_priority"],
        "request_type": model_json.get("request_type") == expected["expected_request_type"],
        "is_maintenance_request": model_json.get("is_maintenance_request") == expected["expected_is_maintenance_request"],
        "trade": model_json.get("trade") == expected["expected_trade"],
        "safety_signals": set(expected_signals) == set(final_signals),
        "missing_info": set(expected_missing) == set(final_missing),
        "language": str(model_json.get("language", "")).lower().startswith(str(expected["expected_language"]).lower()),
        "accommodation_or_legal_flag": model_json.get("accommodation_or_legal_flag") == expected["expected_accommodation_or_legal_flag"],
        "human_only": rules["human_only"] == expected["expected_human_only"],
        "rule_fired": rules["rule_fired"] == expected["expected_override_applied"],
        "draft_policy": actual_draft_policy == expected["expected_draft_policy"],
    }
    if draft_result is not None:
        checks["draft_schema_valid"] = draft_result["schema_valid"]
        checks["draft_lint_clean"] = len(draft_result.get("lint", [])) == 0
    exact = all(checks.values())
    return {"checks": checks, "exact": exact}


def probe_one_model(model: str, instructions: str, input_text: str, schema: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    attempts = []
    accepted_request = None
    for reasoning in ["low", None]:
        call_result = call_structured(
            model=model,
            instructions=instructions,
            input_text=input_text,
            schema_name="stage3_probe",
            schema=schema,
            max_output_tokens=100,
            reasoning_effort=reasoning,
            retry_without_reasoning=False,
        )
        parsed = parse_structured_output(call_result, schema)
        attempts.append(
            {
                "model": model,
                "reasoning": reasoning,
                "status": call_result["status"],
                "ok": call_result["ok"],
                "schema_valid": parsed["schema_valid"],
                "latency_ms": call_result["latency_ms"],
                "error": parsed["error"],
                "usage": usage_from_response(call_result["response"]),
            }
        )
        if call_result["ok"] and parsed["schema_valid"]:
            accepted_request = call_result["request"]
            break
        if reasoning is None or not is_reasoning_param_error(call_result["response"]):
            break
    return attempts, accepted_request


def command_probe(args: argparse.Namespace) -> int:
    triage_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["ok", "label"],
        "properties": {
            "ok": {"type": "boolean"},
            "label": {"type": "string", "enum": ["probe"]},
        },
    }
    instructions = "Return JSON that matches the schema."
    input_text = "Return ok true and label probe."
    results = []
    accepted_request = None

    default_attempts, default_request = probe_one_model(args.model, instructions, input_text, triage_schema)
    results.extend(default_attempts)
    if default_request and accepted_request is None:
        accepted_request = default_request

    default_rejected = bool(default_attempts) and not default_request
    if args.model == "gpt-5-nano" and default_rejected:
        nano_attempts, nano_request = probe_one_model("gpt-5.4-nano", instructions, input_text, triage_schema)
        results.extend(nano_attempts)
        if nano_request and accepted_request is None:
            accepted_request = nano_request

    if args.fallback_model != args.model:
        fallback_attempts, fallback_request = probe_one_model(args.fallback_model, instructions, input_text, triage_schema)
        results.extend(fallback_attempts)
        if fallback_request and accepted_request is None:
            accepted_request = fallback_request

    if accepted_request:
        write_json(KNOWN_GOOD, accepted_request)

    output = {"known_good_saved": str(KNOWN_GOOD) if accepted_request else None, "results": results}
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if accepted_request else 1


def resolve_reasoning_arg(args: argparse.Namespace, model: str) -> str | None:
    if args.reasoning == "none":
        return None
    if args.reasoning == "low":
        return "low"
    return load_known_good_reasoning(model)


def command_classify(args: argparse.Namespace) -> int:
    fixture_path = normalize_path(args.fixture)
    model = args.model
    reasoning = resolve_reasoning_arg(args, model)
    result = classify_fixture(fixture_path, model, reasoning)
    printable = {k: v for k, v in result.items() if k not in {"raw_response", "request"}}
    print(json.dumps(printable, indent=2, sort_keys=True))
    return 0 if result["schema_valid"] else 1


def command_draft(args: argparse.Namespace) -> int:
    fixture_path = normalize_path(args.fixture)
    model = args.model
    reasoning = resolve_reasoning_arg(args, model)
    classification = classify_fixture(fixture_path, model, reasoning)
    draft_result = draft_for_classification(fixture_path, classification, model, reasoning)
    printable = {
        "classification": {k: v for k, v in classification.items() if k not in {"raw_response", "request"}},
        "draft": {k: v for k, v in draft_result.items() if k not in {"raw_response", "request"}},
    }
    print(json.dumps(printable, indent=2, sort_keys=True))
    return 0 if classification["schema_valid"] and draft_result["schema_valid"] else 1


def command_harness(args: argparse.Namespace) -> int:
    model = args.model
    reasoning = resolve_reasoning_arg(args, model)
    run_stamp = now_stamp()
    raw_dir = TMP_STAGE3 / run_stamp
    raw_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    confusion: dict[str, Counter[str]] = defaultdict(Counter)
    totals = Counter()
    field_failures: Counter[str] = Counter()
    live_stability: dict[str, list[str]] = defaultdict(list)
    issue_rows = []
    total_usage = Counter()
    total_cost = 0.0
    total_latency_ms = 0
    draft_lint_findings = []

    selected_fixtures = select_fixture_pairs(args)

    for run_index in range(1, args.runs + 1):
        for fixture_path, expected in selected_fixtures:
            classification = classify_fixture(fixture_path, model, reasoning)
            draft_result = draft_for_classification(fixture_path, classification, model, reasoning)
            match = expected_match(classification, expected, draft_result)
            actual_priority = classification["rules"]["priority"]
            expected_priority = expected["expected_priority"]
            confusion[expected_priority][actual_priority] += 1

            usage = classification["usage"]
            draft_usage = draft_result["usage"]
            for key in total_usage:
                pass
            for key in ["input_tokens", "cached_input_tokens", "output_tokens", "total_tokens"]:
                total_usage[key] += usage.get(key, 0) + draft_usage.get(key, 0)
            total_cost += classification["estimated_cost_usd"] + draft_result["estimated_cost_usd"]
            total_latency_ms += classification["latency_ms"] + draft_result["latency_ms"]

            expected_rank = PRIORITY_RANK[expected_priority]
            actual_rank = PRIORITY_RANK[actual_priority]
            if actual_rank > expected_rank:
                totals["over_escalations"] += 1
            elif actual_rank < expected_rank:
                totals["under_escalations"] += 1

            expected_signals = set(normalize_signal_list(expected["expected_safety_signals"])) - {"NONE"}
            actual_signals = set(normalize_signal_list(classification["rules"]["safety_signals"])) - {"NONE"}
            missed = sorted(expected_signals - actual_signals)
            if missed:
                totals["safety_signals_missed"] += len(missed)

            if expected["is_live_demo"]:
                live_stability[expected["slug"]].append(actual_priority)

            for field, ok in match["checks"].items():
                if not ok:
                    field_failures[field] += 1

            lint = draft_result.get("lint", [])
            if lint:
                draft_lint_findings.append({"fixture": fixture_path.name, "run": run_index, "lint": lint})

            row = {
                "run": run_index,
                "fixture": fixture_path.name,
                "expected": expected,
                "classification": {k: v for k, v in classification.items() if k not in {"raw_response", "request"}},
                "draft": {k: v for k, v in draft_result.items() if k not in {"raw_response", "request"}},
                "match": match,
                "missed_safety_signals": missed,
            }
            rows.append(row)
            if not match["exact"] or missed or lint:
                issue_rows.append(row)

            raw_path = raw_dir / f"run-{run_index:02d}-{fixture_path.stem}.json"
            write_json(
                raw_path,
                {
                    "classification_request": classification.get("request"),
                    "classification_response": classification.get("raw_response"),
                    "draft_request": draft_result.get("request"),
                    "draft_response": draft_result.get("raw_response"),
                    "summary": row,
                },
            )

    total_runs = len(rows)
    exact_matches = sum(1 for row in rows if row["match"]["exact"])
    live_stable = {
        slug: len(set(priorities)) == 1 and len(priorities) == args.runs
        for slug, priorities in live_stability.items()
    }
    scorecard_data = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "model": model,
        "reasoning": reasoning,
        "runs": args.runs,
        "fixture_count": len(selected_fixtures),
        "fixture_selection": "custom"
        if (getattr(args, "fixture_id", None) or getattr(args, "fixture_slug", None))
        else ("live_demo" if args.live_only else "all"),
        "total_classification_runs": total_runs,
        "exact_matches": exact_matches,
        "match_rate": exact_matches / total_runs if total_runs else 0,
        "priority_matches": total_runs - field_failures.get("final_priority", 0),
        "priority_match_rate": (total_runs - field_failures.get("final_priority", 0)) / total_runs if total_runs else 0,
        "confusion_matrix": {expected: dict(actuals) for expected, actuals in sorted(confusion.items())},
        "over_escalations": totals["over_escalations"],
        "under_escalations": totals["under_escalations"],
        "safety_signals_missed": totals["safety_signals_missed"],
        "field_failures": dict(field_failures),
        "live_demo_stability": live_stable,
        "usage": dict(total_usage),
        "estimated_cost_usd": total_cost,
        "average_latency_ms": round(total_latency_ms / total_runs, 1) if total_runs else 0,
        "draft_lint_findings": draft_lint_findings,
        "raw_output_dir": str(raw_dir),
        "issues": [
            {
                "run": row["run"],
                "fixture": row["fixture"],
                "expected_priority": row["expected"]["expected_priority"],
                "actual_priority": row["classification"]["rules"]["priority"],
                "failed_checks": [name for name, ok in row["match"]["checks"].items() if not ok],
                "missed_safety_signals": row["missed_safety_signals"],
                "draft_lint": row["draft"].get("lint", []),
            }
            for row in issue_rows
        ],
    }
    write_json(raw_dir / "scorecard.json", scorecard_data)
    SCORECARD.write_text(render_scorecard(scorecard_data), encoding="utf-8")
    print(render_console_summary(scorecard_data))
    return 0 if acceptance_passed(scorecard_data) else 1


def render_console_summary(scorecard: dict[str, Any]) -> str:
    return "\n".join(
        [
            "Stage 3 harness complete.",
            f"Model: {scorecard['model']} reasoning={scorecard['reasoning']}",
            f"Runs: {scorecard['total_classification_runs']} ({scorecard['fixture_count']} fixtures x {scorecard['runs']})",
            f"Match rate: {scorecard['match_rate']:.1%} ({scorecard['exact_matches']}/{scorecard['total_classification_runs']})",
            f"Priority match rate: {scorecard['priority_match_rate']:.1%} ({scorecard['priority_matches']}/{scorecard['total_classification_runs']})",
            f"Under-escalations: {scorecard['under_escalations']}",
            f"Over-escalations: {scorecard['over_escalations']}",
            f"Safety signals missed: {scorecard['safety_signals_missed']}",
            f"Estimated cost: ${scorecard['estimated_cost_usd']:.6f}",
            f"Scorecard: {SCORECARD}",
            f"Raw output: {scorecard['raw_output_dir']}",
        ]
    )


def render_scorecard(scorecard: dict[str, Any]) -> str:
    lines = [
        "# Stage 3 OpenAI Harness Scorecard",
        "",
        f"Generated at: `{scorecard['generated_at']}`",
        "",
        "## Model Choice",
        "",
        f"- Model: `{scorecard['model']}`",
        f"- Reasoning: `{scorecard['reasoning']}`",
        f"- Runs: {scorecard['fixture_count']} fixtures x {scorecard['runs']} = {scorecard['total_classification_runs']} classification runs",
        f"- Fixture selection: `{scorecard['fixture_selection']}`",
        f"- Average classification-plus-draft latency: {scorecard['average_latency_ms']} ms",
        f"- Estimated API cost: ${scorecard['estimated_cost_usd']:.6f}",
        "",
        "## Accuracy",
        "",
        f"- Exact match rate: {scorecard['match_rate']:.1%} ({scorecard['exact_matches']}/{scorecard['total_classification_runs']})",
        f"- Priority match rate: {scorecard['priority_match_rate']:.1%} ({scorecard['priority_matches']}/{scorecard['total_classification_runs']})",
        f"- Under-escalations: {scorecard['under_escalations']}",
        f"- Over-escalations: {scorecard['over_escalations']}",
        f"- Safety signals missed: {scorecard['safety_signals_missed']}",
        "",
        "## Confusion Matrix",
        "",
        "| Expected | Actual | Count |",
        "|---|---|---:|",
    ]
    for expected, actuals in scorecard["confusion_matrix"].items():
        for actual, count in sorted(actuals.items()):
            lines.append(f"| {expected} | {actual} | {count} |")

    lines.extend(["", "## Live Demo Stability", "", "| Fixture | Stable | Priorities |", "|---|---|---|"])
    for slug, stable in sorted(scorecard["live_demo_stability"].items()):
        priorities = []
        for issue in scorecard["issues"]:
            if slug in issue["fixture"]:
                priorities.append(issue["actual_priority"])
        lines.append(f"| {slug} | {'yes' if stable else 'no'} | {', '.join(priorities) if priorities else 'all matched'} |")

    lines.extend(["", "## Usage", "", "| Token Type | Count |", "|---|---:|"])
    for key, value in scorecard["usage"].items():
        lines.append(f"| {key} | {value} |")

    lines.extend(["", "## Field Failures", ""])
    if scorecard["field_failures"]:
        lines.extend(["| Field | Count |", "|---|---:|"])
        for field, count in sorted(scorecard["field_failures"].items()):
            lines.append(f"| {field} | {count} |")
    else:
        lines.append("No field-level failures.")

    lines.extend(["", "## Issues", ""])
    if scorecard["issues"]:
        lines.extend(["| Run | Fixture | Expected | Actual | Failed Checks | Missed Safety | Draft Lint |", "|---:|---|---|---|---|---|---|"])
        for issue in scorecard["issues"][:80]:
            lines.append(
                f"| {issue['run']} | {issue['fixture']} | {issue['expected_priority']} | {issue['actual_priority']} | "
                f"{', '.join(issue['failed_checks']) or '-'} | {', '.join(issue['missed_safety_signals']) or '-'} | {', '.join(issue['draft_lint']) or '-'} |"
            )
        if len(scorecard["issues"]) > 80:
            lines.append(f"| | {len(scorecard['issues']) - 80} additional issues omitted from markdown; see raw scorecard JSON. | | | | | |")
    else:
        lines.append("No issues found.")

    lines.extend(
        [
            "",
            "## Raw Output",
            "",
            f"Ignored raw run artifacts are in `{scorecard['raw_output_dir']}`.",
            "",
        ]
    )
    return "\n".join(lines)


def acceptance_passed(scorecard: dict[str, Any]) -> bool:
    return (
        scorecard["safety_signals_missed"] == 0
        and scorecard["under_escalations"] == 0
        and all(scorecard["live_demo_stability"].values())
        and scorecard["field_failures"].get("schema_valid", 0) == 0
        and scorecard["field_failures"].get("draft_schema_valid", 0) == 0
    )


def add_common_model_args(parser: argparse.ArgumentParser) -> None:
    load_dotenv(ROOT / ".env")
    parser.add_argument("--model", default=os.environ.get("STAGE3_MODEL", DEFAULT_MODEL))
    parser.add_argument("--fallback-model", default=os.environ.get("STAGE3_FALLBACK_MODEL", DEFAULT_FALLBACK_MODEL))
    parser.add_argument("--reasoning", choices=["auto", "low", "none"], default="auto")


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage 3 OpenAI contract and fixture accuracy harness")
    subparsers = parser.add_subparsers(dest="command", required=True)

    probe = subparsers.add_parser("probe", help="Probe model IDs and strict Responses request shape")
    add_common_model_args(probe)
    probe.set_defaults(func=command_probe)

    classify = subparsers.add_parser("classify", help="Classify one fixture")
    add_common_model_args(classify)
    classify.add_argument("fixture")
    classify.set_defaults(func=command_classify)

    draft = subparsers.add_parser("draft", help="Classify and draft one fixture if policy allows")
    add_common_model_args(draft)
    draft.add_argument("fixture")
    draft.set_defaults(func=command_draft)

    harness = subparsers.add_parser("harness", help="Run all fixtures repeatedly and write scorecard")
    add_common_model_args(harness)
    harness.add_argument("--runs", type=int, default=int(os.environ.get("STAGE3_RUNS", DEFAULT_RUNS)))
    harness.add_argument("--live-only", action="store_true", help="Run only the six live-demo fixtures")
    harness.add_argument("--fixture-id", action="append", default=[], help="Run a specific fixture id; may be repeated")
    harness.add_argument("--fixture-slug", action="append", default=[], help="Run a specific fixture slug; may be repeated")
    harness.set_defaults(func=command_harness)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

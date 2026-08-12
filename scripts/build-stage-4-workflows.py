#!/usr/bin/env python3
import json
import pathlib
import textwrap


ROOT = pathlib.Path(__file__).resolve().parents[1]
PROMPTS = ROOT / "prompts"
WORKFLOWS = ROOT / "workflows"
FIXTURES = ROOT / "fixtures"

CORE_ID = "maintenance-triage-core-stage-4"
DRIVER_ID = "maintenance-triage-stage-4-driver"


def load_json(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def node(name, node_type, type_version, position, parameters=None, credentials=None, disabled=False):
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
    if disabled:
        data["disabled"] = True
    return data


def code_node(name, position, js_code, mode="runOnceForAllItems"):
    return node(
        name,
        "n8n-nodes-base.code",
        2,
        position,
        {
            "mode": mode,
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


def http_node(name, position, body_expr):
    data = node(
        name,
        "n8n-nodes-base.httpRequest",
        4.4,
        position,
        {
            "method": "POST",
            "url": "https://api.openai.com/v1/responses",
            "authentication": "predefinedCredentialType",
            "nodeCredentialType": "openAiApi",
            "sendHeaders": True,
            "specifyHeaders": "keypair",
            "headerParameters": {
                "parameters": [
                    {"name": "Content-Type", "value": "application/json"},
                ]
            },
            "sendBody": True,
            "contentType": "json",
            "specifyBody": "json",
            "jsonBody": body_expr,
            "options": {
                "response": {
                    "response": {
                        "fullResponse": True,
                        "neverError": True,
                        "responseFormat": "json",
                    }
                },
                "timeout": 60000,
            },
        },
        credentials={
            "openAiApi": {
                "id": "sGNqtfRyAGXZQgcc",
                "name": "maintenance-triage-openai",
            }
        },
    )
    data["continueOnFail"] = True
    return data


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


def switch_node(name, position):
    return node(
        name,
        "n8n-nodes-base.switch",
        3.2,
        position,
        {
            "mode": "rules",
            "rules": {
                "values": [
                    {
                        "conditions": {
                            "conditions": [
                                {
                                    "leftValue": "={{ $json.priority }}",
                                    "rightValue": "EMERGENCY",
                                    "operator": {"type": "string", "operation": "equals"},
                                }
                            ],
                            "combinator": "and",
                        }
                    },
                    {
                        "conditions": {
                            "conditions": [
                                {
                                    "leftValue": "={{ $json.priority }}",
                                    "rightValue": "NEEDS_REVIEW",
                                    "operator": {"type": "string", "operation": "equals"},
                                }
                            ],
                            "combinator": "and",
                        }
                    },
                    {
                        "conditions": {
                            "conditions": [
                                {
                                    "leftValue": "={{ $json.priority }}",
                                    "rightValue": "URGENT",
                                    "operator": {"type": "string", "operation": "equals"},
                                }
                            ],
                            "combinator": "and",
                        }
                    },
                    {
                        "conditions": {
                            "conditions": [
                                {
                                    "leftValue": "={{ $json.priority }}",
                                    "rightValue": "ROUTINE",
                                    "operator": {"type": "string", "operation": "equals"},
                                }
                            ],
                            "combinator": "and",
                        }
                    },
                ]
            },
            "options": {},
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
        "meta": {"stage": 4, "generatedBy": "scripts/build-stage-4-workflows.py"},
        "versionId": "stage-4-generated",
        "triggerCount": 0,
        "tags": [],
    }


def build_core():
    triage_schema = load_json(PROMPTS / "maintenance-triage.schema.json")
    draft_schema = load_json(PROMPTS / "maintenance-drafts.schema.json")
    classification_prompt = load_text(PROMPTS / "classification-system.txt")
    drafting_prompt = load_text(PROMPTS / "drafting-system.txt")

    normalize_js = r"""
    function normalizeText(raw) {
      let text = String(raw ?? "");
      text = text.replace(/\r\n/g, "\n");
      text = text.split(/\nOn .{0,120}wrote:\n/i)[0];
      text = text.split(/\n-{2,}\s*\n/)[0];
      text = text.replace(/^>.*$/gm, "");
      text = text.replace(/Sent from my iPhone.*$/gim, "");
      text = text.replace(/This email.*confidential.*$/gim, "");
      text = text.replace(/\s+/g, " ").trim();
      return text.slice(0, 1500);
    }

    return $input.all().map((item) => {
      const src = item.json;
      if (!src.source || !src.body_raw) {
        throw new Error("Stage 4 core requires source and body_raw");
      }
      const attachmentPaths = Array.isArray(src.attachment_paths) ? src.attachment_paths : [];
      const bodyClean = normalizeText(src.body_raw);
      const refs = Array.isArray(src.refs) ? src.refs.join(" ") : String(src.refs ?? "");
      return {
        json: {
          source: src.source,
          from_address: src.from_address ?? null,
          subject: src.subject ?? null,
          body_raw: String(src.body_raw),
          body_clean: bodyClean,
          received_at: src.received_at ?? new Date().toISOString(),
          attachment_paths: attachmentPaths,
          attachment_count: attachmentPaths.length,
          msg_id: src.msg_id ?? null,
          in_reply_to: src.in_reply_to ?? null,
          refs,
          test_mode: src.source === "fixture" ? (src.test_mode ?? {}) : {},
        }
      };
    });
    """

    gate_query = r"""
    WITH input_values AS (
      SELECT
        $1::text AS body_clean,
        encode(digest($1::text, 'sha256'), 'hex') AS body_hash,
        NULLIF($2::text, '') AS in_reply_to,
        NULLIF($3::text, '') AS refs
    ),
    ref_tokens AS (
      SELECT trim(token) AS message_id
      FROM input_values, unnest(regexp_split_to_array(coalesce(refs, ''), '\s+')) token
      WHERE trim(token) <> ''
    ),
    duplicate_match AS (
      SELECT t.id, t.ref
      FROM triage.tickets t, input_values i
      WHERE t.body_hash = i.body_hash
        AND t.received_at >= now() - interval '24 hours'
      ORDER BY t.received_at DESC
      LIMIT 1
    ),
    thread_match AS (
      SELECT t.id, t.ref
      FROM triage.tickets t, input_values i
      WHERE NOT EXISTS (SELECT 1 FROM duplicate_match)
        AND (
          (i.in_reply_to IS NOT NULL AND (t.out_msg_id = i.in_reply_to OR t.msg_id = i.in_reply_to))
          OR t.out_msg_id IN (SELECT message_id FROM ref_tokens)
          OR t.msg_id IN (SELECT message_id FROM ref_tokens)
        )
      ORDER BY t.received_at DESC
      LIMIT 1
    ),
    duplicate_event AS (
      INSERT INTO triage.events (ticket_id, actor, action, detail)
      SELECT d.id, 'system', 'duplicate_ignored', jsonb_build_object('body_hash', i.body_hash)
      FROM duplicate_match d, input_values i
      RETURNING ticket_id
    ),
    thread_update AS (
      UPDATE triage.tickets t
      SET status = 'NEW', closed_at = NULL
      FROM thread_match m
      WHERE t.id = m.id
      RETURNING t.id, t.ref
    ),
    thread_event AS (
      INSERT INTO triage.events (ticket_id, actor, action, detail)
      SELECT u.id, 'system', 'tenant_replied', jsonb_build_object('in_reply_to', (SELECT in_reply_to FROM input_values), 'refs', (SELECT refs FROM input_values))
      FROM thread_update u
      RETURNING ticket_id
    ),
    state AS (
      SELECT
        coalesce((SELECT value FROM triage.config WHERE key = 'runtime_state'), '{}'::jsonb) AS runtime_state,
        coalesce((SELECT value FROM triage.config WHERE key = 'limits'), '{}'::jsonb) AS limits
    )
    SELECT
      CASE
        WHEN EXISTS (SELECT 1 FROM duplicate_match) THEN 'duplicate'
        WHEN EXISTS (SELECT 1 FROM thread_match) THEN 'threaded'
        ELSE 'created_candidate'
      END AS outcome,
      coalesce((SELECT id FROM duplicate_match), (SELECT id FROM thread_match)) AS ticket_id,
      coalesce((SELECT ref FROM duplicate_match), (SELECT ref FROM thread_match)) AS ref,
      (SELECT body_hash FROM input_values) AS body_hash,
      (SELECT runtime_state FROM state) AS runtime_state,
      (SELECT limits FROM state) AS limits,
      (coalesce((SELECT runtime_state FROM state)->>'degraded_until', '') <> '' AND ((SELECT runtime_state FROM state)->>'degraded_until')::timestamptz > now()) AS degraded,
      (
        coalesce(((SELECT runtime_state FROM state)->>'llm_call_day'), '') = to_char(now(), 'YYYY-MM-DD')
        AND coalesce(((SELECT runtime_state FROM state)->>'llm_calls_today')::int, 0) >= coalesce(((SELECT limits FROM state)->>'max_llm_calls_per_day')::int, 400)
      ) AS over_daily_cap;
    """

    prepare_gate_js = r"""
    const gateItems = $input.all();
    const normalizedItems = $("Normalize Request").all();
    return gateItems.map((item, index) => ({
      json: {
        ...normalizedItems[index].json,
        ...item.json,
        should_continue: item.json.outcome === "created_candidate",
      }
    }));
    """

    existing_js = r"""
    return $input.all().map((item) => ({
      json: {
        outcome: item.json.outcome,
        ticket_id: item.json.ticket_id,
        ref: item.json.ref,
        priority: null,
        route: item.json.outcome,
        human_only: false,
        override_applied: false,
        override_reason: null,
        draft_generated: false,
      }
    }));
    """

    prepare_classification_js = f"""
    const schema = {json.dumps(triage_schema, separators=(",", ":"))};
    const instructions = {json.dumps(classification_prompt)};

    return $input.all().map((item) => {{
      const j = item.json;
      const testMode = j.test_mode || {{}};
      const forceSkip = Boolean(testMode.mock_model_json || testMode.simulate_model_error || j.degraded || j.over_daily_cap);
      const request = {{
        model: "gpt-5-nano",
        store: false,
        instructions,
        input: `<<<MESSAGE>>>\\n${{j.body_clean}}\\n<<<END MESSAGE>>>`,
        text: {{
          format: {{
            type: "json_schema",
            name: "maintenance_triage",
            strict: true,
            schema,
          }}
        }},
        max_output_tokens: 2000,
        reasoning: {{ effort: "low" }},
      }};
      return {{
        json: {{
          ...j,
          should_call_classifier: !forceSkip,
          classifier_skip_reason: forceSkip ? (testMode.simulate_model_error ? "simulated_model_error" : (testMode.mock_model_json ? "mock_model_json" : (j.degraded ? "degraded" : "daily_cap"))) : null,
          classification_request: request,
        }}
      }};
    }});
    """

    filter_call_js = "return $input.all().filter(item => item.json.should_call_classifier);"
    synthetic_classifier_js = r"""
    return $input.all()
      .filter(item => !item.json.should_call_classifier)
      .map((item) => {
        const testMode = item.json.test_mode || {};
        return {
          json: {
            ...item.json,
            classifier_http_status: testMode.simulate_model_error ? 500 : 200,
            classifier_response: testMode.simulate_model_error
              ? { error: { message: "simulated model error" } }
              : { output_text: JSON.stringify(testMode.mock_model_json) },
          }
        };
      });
    """

    attach_classifier_js = r"""
    const contexts = $("Items Needing Classifier").all();
    return $input.all().map((item, index) => ({
      json: {
        ...contexts[index].json,
        classifier_http_status: item.json.statusCode ?? item.json.status ?? 200,
        classifier_response: item.json.body ?? item.json,
      }
    }));
    """

    apply_rules_js = r"""
    const PRIORITY_RANK = { ROUTINE: 1, URGENT: 2, NEEDS_REVIEW: 2, EMERGENCY: 3 };
    const RULES = [
      ["GAS", /\b(smell(s|ing)? (of )?gas|gas leak|gas odou?r|propane leak|rotten egg smell)\b/i],
      ["CARBON_MONOXIDE", /\b(carbon monoxide|co alarm|co detector (going off|beeping|alarming))\b/i],
      ["SMOKE_FIRE", /\b(smoke|burning smell|smells? like burning|sparking|sparks|exposed wire|fire)\b/i],
      ["FLOOD", /\b(flooding|flooded|water (is )?pouring|gushing|burst pipe|pipe .*burst|burst .*pipe|water everywhere|ceiling (is )?collapsing)\b/i],
      ["SEWAGE", /\b(raw sewage|sewage backing up|sewage backup|sewer backup|toilet overflowing|toilet water keeps rising and spilling)\b/i],
      ["NO_HEAT", /\b(no heat|heat (is )?(out|not working|dead)|furnace (is )?(out|dead|not working))\b/i],
      ["NO_WATER", /\b(no water|water (is )?(shut off|not running)|no running water)\b/i],
      ["NO_COOLING", /\b(ac died|a\/c died|air conditioning (is )?(out|dead|not working)|no cooling)\b/i],
      ["SECURITY", /\b(broke in|broken into|won'?t lock|can'?t lock|door (is )?(broken|kicked in)|lock (is )?broken)\b/i],
      ["ELECTRICAL", /\b(light fixture is wet|sparking outlet|exposed wire|breaker keeps tripping)\b/i],
    ];
    const NEGATED = /\b(no|not|isn'?t|wasn'?t|never|without)\b[^.!?]{0,25}$/i;

    function outputText(response) {
      if (!response) return null;
      if (typeof response.output_text === "string") return response.output_text;
      if (Array.isArray(response.output)) {
        let chunks = [];
        for (const item of response.output) {
          if (typeof item.text === "string") chunks.push(item.text);
          if (Array.isArray(item.content)) {
            for (const part of item.content) if (typeof part.text === "string") chunks.push(part.text);
          }
        }
        return chunks.join("").trim() || null;
      }
      return null;
    }
    function signalsFromRules(text) {
      const hits = [];
      for (const [sig, re] of RULES) {
        const match = re.exec(text);
        if (!match) continue;
        const prefix = text.slice(Math.max(0, match.index - 40), match.index);
        if (!NEGATED.test(prefix)) hits.push(sig);
      }
      return [...new Set(hits)];
    }
    function normalizeSignals(values) {
      if (!Array.isArray(values) || values.length === 0) return ["NONE"];
      let signals = values.filter(Boolean).map(String);
      if (signals.length > 1) signals = signals.filter(v => v !== "NONE");
      return [...new Set(signals)].sort();
    }
    function maxPriority(left, right) {
      if (!right) return left;
      return PRIORITY_RANK[left] >= PRIORITY_RANK[right] ? left : right;
    }
    function labeledValue(text, label) {
      const match = String(text || "").match(new RegExp(`(?:^|\\n)${label}:\\s*([^\\n]+)`, "i"));
      return match ? match[1].trim() : "";
    }
    function safetyTrade(signals) {
      const values = new Set(signals || []);
      if (values.has("ELECTRICAL")) return "ELECTRICAL";
      if (values.has("FLOOD") || values.has("SEWAGE") || values.has("NO_WATER")) return "PLUMBING";
      if (values.has("NO_HEAT") || values.has("NO_COOLING")) return "HVAC";
      if (values.has("SECURITY")) return "LOCKS_SECURITY";
      if (values.has("GAS") || values.has("CARBON_MONOXIDE") || values.has("SMOKE_FIRE")) return "GENERAL";
      return "";
    }
    function lowInformation(model, message, mergedSignals) {
      const missing = Array.isArray(model?.missing_info) ? model.missing_info : [];
      const text = String(message).toLowerCase();
      const wordCount = (text.match(/[a-z0-9]+/g) || []).length;
      const looksUnreadable = /(<html|<div|blockquote|Ã|â|=_nextpart|&&&|\?\?\?)/i.test(message);
      const attachmentOnly = text.includes("see attached") && wordCount <= 8;
      const unknownTradeWithNoSubstance = model?.trade === "UNKNOWN" && wordCount <= 8;
      return mergedSignals.length === 1 && mergedSignals[0] === "NONE"
        && model?.is_maintenance_request === true
        && model?.request_type === "NEW_ISSUE"
        && missing.includes("ISSUE_DETAIL")
        && (model?.confidence === "LOW" || looksUnreadable || attachmentOnly || unknownTradeWithNoSubstance);
    }
    function routineSqueakyDoor(message) {
      const text = String(message || "").toLowerCase();
      const squeakOnly = /\b(squeak|squeaky|noisy hinge|hinge noise|door noise)\b/.test(text);
      const dangerOrAccess = /\b(won'?t|cannot|can'?t|unable|stuck|jammed|block(s|ed|ing)?|close|shut|lock|latch|access|trapped|injur|hurt|security|break-?in|broken)\b/.test(text);
      return squeakOnly && !dangerOrAccess;
    }
    function containedCeilingDrip(message) {
      const text = String(message || "").toLowerCase();
      const ceilingDrip = /\b(ceiling|bedroom ceiling|bathroom ceiling)\b[^.!?]{0,80}\b(drip|dripping|leak|leaking)\b|\b(drip|dripping|leak|leaking)\b[^.!?]{0,80}\b(ceiling|bedroom ceiling|bathroom ceiling)\b/.test(text);
      const contained = /\b(bucket|bowl|towel|pan)\b/.test(text);
      const emergencyWater = /\b(flood|flooding|water everywhere|pouring|gushing|spreading|downstairs|into the hallway|electrical|outlet|sparking|breaker|collapse|collapsing|ceiling fell|ceiling falling)\b/.test(text);
      return ceilingDrip && contained && !emergencyWater;
    }

    return $input.all().map((item) => {
      const j = item.json;
      const ruleSignals = signalsFromRules(j.body_clean || j.body_raw || "");
      let modelJson = null;
      let parseError = null;
      let text = outputText(j.classifier_response);
      if (j.classifier_http_status >= 400 || j.classifier_skip_reason === "simulated_model_error") {
        parseError = j.classifier_response?.error?.message || j.classifier_skip_reason || "classifier_http_error";
      } else {
        try {
          modelJson = JSON.parse(text);
        } catch (error) {
          parseError = `invalid classifier JSON: ${error.message}`;
        }
      }

      let priority = "NEEDS_REVIEW";
      let reviewReason = parseError ? "model_error_or_invalid_json" : null;
      let mergedSignals = ruleSignals.length ? [...ruleSignals] : ["NONE"];
      let humanOnly = false;
      let draftAllowed = false;
      let overrideApplied = ruleSignals.length > 0;
      let overrideReason = ruleSignals.length ? `safety keyword: ${ruleSignals.join(",")}` : null;
      let priorityReason = reviewReason || "";

      if (modelJson) {
        // Trusted intake context fills profile fields when the model leaves them out.
        const profileText = j.body_raw || j.body_clean || "";
        const knownTenant = labeledValue(profileText, "Tenant");
        const knownProperty = labeledValue(profileText, "Property");
        const knownUnit = labeledValue(profileText, "Unit");
        const knownContact = labeledValue(profileText, "Contact") || String(j.from_address || "").trim();
        const missing = Array.isArray(modelJson.missing_info) ? modelJson.missing_info : [];
        modelJson = {
          ...modelJson,
          tenant_name: knownTenant || modelJson.tenant_name,
          tenant_contact: knownContact || modelJson.tenant_contact,
          unit_identifier: knownUnit || modelJson.unit_identifier,
          missing_info: missing.filter(value => value !== "CONTACT" && !(knownUnit && value === "UNIT") && !(knownProperty && value === "PROPERTY")),
        };
        const modelSignals = normalizeSignals(modelJson.safety_signals);
        const merged = new Set(modelSignals.filter(v => v !== "NONE"));
        for (const sig of ruleSignals) merged.add(sig);
        mergedSignals = merged.size ? [...merged].sort() : ["NONE"];
        const fallbackTrade = safetyTrade(mergedSignals);
        if (fallbackTrade && (!modelJson.trade || modelJson.trade === "UNKNOWN")) {
          modelJson = {...modelJson, trade: fallbackTrade};
        }
        priority = maxPriority(modelJson.priority, ruleSignals.length ? "EMERGENCY" : null);
        if (modelJson.confidence === "LOW" && mergedSignals[0] !== "NONE") {
          priority = "NEEDS_REVIEW";
          reviewReason = "low_confidence_with_safety_signal";
        } else if (modelJson.is_maintenance_request === false && ruleSignals.length) {
          priority = "NEEDS_REVIEW";
          reviewReason = "non_request_with_safety_rule";
        } else if (lowInformation(modelJson, j.body_clean || "", mergedSignals)) {
          priority = "NEEDS_REVIEW";
          reviewReason = "low_information_request";
        }
        humanOnly = Boolean(modelJson.accommodation_or_legal_flag);
        if (humanOnly && ruleSignals.length === 0 && priority !== "NEEDS_REVIEW") {
          priority = "ROUTINE";
        }
        priorityReason = reviewReason || modelJson.priority_reason || "";
        if (ruleSignals.length === 0 && modelJson.is_maintenance_request === true && routineSqueakyDoor(j.body_clean || j.body_raw || "")) {
          priority = "ROUTINE";
          priorityReason = "Routine squeaky/noisy door or hinge complaint with no lock, closure, access, injury, or safety detail.";
        }
        if (ruleSignals.length === 0 && modelJson.is_maintenance_request === true && priority === "EMERGENCY" && containedCeilingDrip(j.body_clean || j.body_raw || "")) {
          priority = "URGENT";
          priorityReason = "Contained ceiling drip with a bucket and no spreading water, collapse, or electrical hazard detail.";
        }
        draftAllowed = priority !== "NEEDS_REVIEW"
          && !humanOnly
          && modelJson.is_maintenance_request === true
          && modelJson.request_type !== "NOT_A_REQUEST";
      }

      return {
        json: {
          ...j,
          model_json: modelJson,
          model_error: parseError,
          model_name: "gpt-5-nano",
          model_latency_ms: null,
          prompt_tokens: j.classifier_response?.usage?.input_tokens ?? 0,
          completion_tokens: j.classifier_response?.usage?.output_tokens ?? 0,
          priority,
          override_applied: overrideApplied,
          override_reason: overrideReason,
          human_only: humanOnly,
          draft_allowed: draftAllowed,
          rule_signals: ruleSignals,
          safety_signals: mergedSignals,
          review_reason: reviewReason,
          priority_reason: priorityReason,
        }
      };
    });
    """

    persist_query = r"""
    WITH inserted AS (
      INSERT INTO triage.tickets (
        ref, source, received_at, from_address, subject, body_raw, body_clean, body_hash,
        attachment_count, attachment_paths, msg_id, in_reply_to, refs,
        model_json, model_priority, model_name, model_latency_ms, prompt_tokens, completion_tokens, degraded,
        is_maintenance_request, request_type, priority, priority_reason, override_applied, override_reason,
        human_only, trade, unit_identifier, tenant_name, tenant_contact, issue_summary,
        habitability_flag, habitability_reason, safety_signals, access_notes,
        accommodation_or_legal_flag, accommodation_or_legal_reason, missing_info, confidence,
        ambiguity_note, language, status, sla_due_at
      )
      SELECT
        triage.next_ticket_ref(),
        $1::text,
        coalesce(NULLIF($2::text, '')::timestamptz, now()),
        NULLIF($3::text, ''),
        NULLIF($4::text, ''),
        $5::text,
        $6::text,
        $7::text,
        $8::int,
        $9::jsonb,
        NULLIF($10::text, ''),
        NULLIF($11::text, ''),
        NULLIF($12::text, ''),
        NULLIF($13::text, '')::jsonb,
        NULLIF($14::text, ''),
        NULLIF($15::text, ''),
        NULLIF($16::text, '')::int,
        $17::int,
        $18::int,
        $19::boolean,
        $20::boolean,
        NULLIF($21::text, ''),
        $22::text,
        NULLIF($23::text, ''),
        $24::boolean,
        NULLIF($25::text, ''),
        $26::boolean,
        NULLIF($27::text, ''),
        NULLIF($28::text, ''),
        NULLIF($29::text, ''),
        NULLIF($30::text, ''),
        NULLIF($31::text, ''),
        $32::boolean,
        NULLIF($33::text, ''),
        $34::jsonb,
        NULLIF($35::text, ''),
        $36::boolean,
        NULLIF($37::text, ''),
        $38::jsonb,
        NULLIF($39::text, ''),
        NULLIF($40::text, ''),
        NULLIF($41::text, ''),
        'NEW',
        now() + make_interval(mins => coalesce(((SELECT value FROM triage.config WHERE key = 'sla_minutes')->>($22::text))::int, 120))
      RETURNING *
    ),
    ingested AS (
      INSERT INTO triage.events (ticket_id, actor, action, detail)
      SELECT id, 'system', 'ingested', jsonb_build_object('source', source, 'body_hash', body_hash)
      FROM inserted
      RETURNING ticket_id
    ),
    classified AS (
      INSERT INTO triage.events (ticket_id, actor, action, detail)
      SELECT id, 'model', 'classified', jsonb_build_object('priority', model_priority, 'final_priority', priority, 'model_error', $42::text)
      FROM inserted
      RETURNING ticket_id
    ),
    overridden AS (
      INSERT INTO triage.events (ticket_id, actor, action, detail)
      SELECT id, 'rules', 'overridden', jsonb_build_object('override_reason', override_reason, 'signals', safety_signals)
      FROM inserted
      WHERE override_applied
      RETURNING ticket_id
    ),
    runtime_update AS (
      UPDATE triage.config
      SET value = CASE
        WHEN $42::text IS NULL OR $42::text = '' THEN
          value || jsonb_build_object(
            'consecutive_model_failures', 0,
            'last_model_success_at', now(),
            'llm_call_day', to_char(now(), 'YYYY-MM-DD'),
            'llm_calls_today',
              CASE WHEN value->>'llm_call_day' = to_char(now(), 'YYYY-MM-DD')
                THEN coalesce((value->>'llm_calls_today')::int, 0) + 1
                ELSE 1
              END
          )
        ELSE
          value || jsonb_build_object(
            'consecutive_model_failures', coalesce((value->>'consecutive_model_failures')::int, 0) + 1,
            'last_model_failure_at', now(),
            'degraded_until',
              CASE WHEN coalesce((value->>'consecutive_model_failures')::int, 0) + 1 >= 3
                THEN now() + interval '10 minutes'
                ELSE NULL
              END
          )
        END
      WHERE key = 'runtime_state'
      RETURNING value
    )
    SELECT
      'created' AS outcome,
      id AS ticket_id,
      ref,
      priority,
      CASE priority WHEN 'EMERGENCY' THEN 'EMERGENCY' WHEN 'NEEDS_REVIEW' THEN 'NEEDS_REVIEW' WHEN 'URGENT' THEN 'URGENT' ELSE 'ROUTINE' END AS route,
      human_only,
      override_applied,
      override_reason,
      $43::boolean AS draft_allowed,
      false AS draft_generated
    FROM inserted;
    """

    persist_replacements = """={{ [
      $json.source,
      $json.received_at,
      $json.from_address,
      $json.subject,
      $json.body_raw,
      $json.body_clean,
      $json.body_hash,
      $json.attachment_count,
      JSON.stringify($json.attachment_paths || []),
      $json.msg_id,
      $json.in_reply_to,
      $json.refs,
      $json.model_json ? JSON.stringify($json.model_json) : '',
      $json.model_json?.priority || '',
      $json.model_name,
      $json.model_latency_ms || '',
      $json.prompt_tokens || 0,
      $json.completion_tokens || 0,
      Boolean($json.degraded),
      Boolean($json.model_json?.is_maintenance_request),
      $json.model_json?.request_type || '',
      $json.priority,
      $json.priority_reason || $json.model_json?.priority_reason || $json.review_reason || '',
      Boolean($json.override_applied),
      $json.override_reason || '',
      Boolean($json.human_only),
      $json.model_json?.trade || '',
      $json.model_json?.unit_identifier || '',
      $json.model_json?.tenant_name || '',
      $json.model_json?.tenant_contact || '',
      $json.model_json?.issue_summary || '',
      Boolean($json.model_json?.habitability_flag),
      $json.model_json?.habitability_reason || '',
      JSON.stringify($json.safety_signals || ['NONE']),
      $json.model_json?.access_notes || '',
      Boolean($json.model_json?.accommodation_or_legal_flag),
      $json.model_json?.accommodation_or_legal_reason || '',
      JSON.stringify($json.model_json?.missing_info || []),
      $json.model_json?.confidence || '',
      $json.model_json?.ambiguity_note || '',
      $json.model_json?.language || '',
      $json.model_error || '',
      Boolean($json.draft_allowed)
    ] }}"""

    after_persist_js = r"""
    const persisted = $input.all();
    const rulesItems = $("Apply Safety Rules").all();
    return persisted.map((item, index) => ({
      json: {
        ...rulesItems[index].json,
        ...item.json,
        should_generate_draft: Boolean(item.json.draft_allowed),
      }
    }));
    """

    filter_draft_js = "return $input.all().filter(item => item.json.should_generate_draft);"
    no_draft_js = r"""
    return $input.all().filter(item => !item.json.should_generate_draft).map(item => ({
      json: {
        outcome: item.json.outcome,
        ticket_id: item.json.ticket_id,
        ref: item.json.ref,
        priority: item.json.priority,
        route: item.json.route,
        human_only: item.json.human_only,
        override_applied: item.json.override_applied,
        override_reason: item.json.override_reason,
        draft_generated: false,
      }
    }));
    """

    prepare_draft_js = f"""
    const schema = {json.dumps(draft_schema, separators=(",", ":"))};
    const instructions = {json.dumps(drafting_prompt)};
    return $input.all().map((item) => {{
      const j = item.json;
      return {{
        json: {{
          ...j,
          draft_request: {{
            model: "gpt-5-nano",
            store: false,
            instructions,
            input: JSON.stringify({{
              triage: j.model_json,
              post_rules: {{
                priority: j.priority,
                safety_signals: j.safety_signals,
                override_applied: j.override_applied,
                override_reason: j.override_reason
              }},
              cleaned_message: j.body_clean
            }}),
            text: {{
              format: {{
                type: "json_schema",
                name: "maintenance_drafts",
                strict: true,
                schema,
              }}
            }},
            max_output_tokens: 2000,
            reasoning: {{ effort: "low" }},
          }}
        }}
      }};
    }});
    """

    attach_draft_js = r"""
    const contexts = $("Prepare Draft Request").all();
    function outputText(response) {
      if (!response) return null;
      if (typeof response.output_text === "string") return response.output_text;
      if (Array.isArray(response.output)) {
        let chunks = [];
        for (const item of response.output) {
          if (typeof item.text === "string") chunks.push(item.text);
          if (Array.isArray(item.content)) {
            for (const part of item.content) if (typeof part.text === "string") chunks.push(part.text);
          }
        }
        return chunks.join("").trim() || null;
      }
      return null;
    }
    return $input.all().map((item, index) => {
      const ctx = contexts[index].json;
      const body = item.json.body ?? item.json;
      let draft = null;
      let error = null;
      try {
        draft = JSON.parse(outputText(body));
      } catch (err) {
        error = err.message;
      }
      return { json: { ...ctx, draft_json: draft, draft_error: error, draft_response: body } };
    });
    """

    update_draft_query = r"""
    UPDATE triage.tickets
    SET
      draft_subject = NULLIF($2::text, ''),
      draft_body = NULLIF($3::text, ''),
      vendor_note = NULLIF($4::text, ''),
      clarifying_qs = $5::jsonb,
      completion_tokens = completion_tokens + $6::int,
      prompt_tokens = prompt_tokens + $7::int
    WHERE id = $1::bigint
    RETURNING
      'created' AS outcome,
      id AS ticket_id,
      ref,
      priority,
      CASE priority WHEN 'EMERGENCY' THEN 'EMERGENCY' WHEN 'NEEDS_REVIEW' THEN 'NEEDS_REVIEW' WHEN 'URGENT' THEN 'URGENT' ELSE 'ROUTINE' END AS route,
      human_only,
      override_applied,
      override_reason,
      true AS draft_generated;
    """

    update_draft_replacements = """={{ [
      $json.ticket_id,
      $json.draft_json?.tenant_reply_subject || '',
      $json.draft_json?.tenant_reply_body || '',
      $json.draft_json?.vendor_note || '',
      JSON.stringify($json.draft_json?.clarifying_questions || []),
      $json.draft_response?.usage?.output_tokens || 0,
      $json.draft_response?.usage?.input_tokens || 0
    ] }}"""

    result_passthrough_js = "return $input.all().map(item => ({ json: item.json }));"

    nodes = [
        node(
            "Core Input",
            "n8n-nodes-base.executeWorkflowTrigger",
            1.2,
            [-1200, 0],
            {"inputSource": "passthrough", "returnOutput": "allRuns"},
        ),
        code_node("Normalize Request", [-1000, 0], normalize_js),
        pg_node("Postgres Dedupe Thread Gate", [-780, 0], gate_query, "={{ [$json.body_clean, $json.in_reply_to || '', $json.refs || ''] }}"),
        code_node("Prepare Gate Decision", [-560, 0], prepare_gate_js),
        if_node("Should Create Ticket", [-360, 0], "={{ $json.should_continue }}"),
        code_node("Return Existing Outcome", [-140, 180], existing_js),
        code_node("Prepare Classification Request", [-140, -120], prepare_classification_js),
        code_node("Items Needing Classifier", [80, -220], filter_call_js),
        code_node("Synthetic Classification Result", [80, 40], synthetic_classifier_js),
        http_node("HTTP OpenAI Classification", [300, -220], "={{ $json.classification_request }}"),
        code_node("Attach Classifier Response", [520, -220], attach_classifier_js),
        code_node("Apply Safety Rules", [740, -80], apply_rules_js),
        pg_node("Postgres Insert Ticket Events", [960, -80], persist_query, persist_replacements),
        code_node("Attach Persisted Ticket", [1180, -80], after_persist_js),
        code_node("Items Needing Draft", [1400, -180], filter_draft_js),
        code_node("Return Without Draft", [1400, 40], no_draft_js),
        code_node("Prepare Draft Request", [1620, -180], prepare_draft_js),
        http_node("HTTP OpenAI Draft", [1840, -180], "={{ $json.draft_request }}"),
        code_node("Attach Draft Response", [2060, -180], attach_draft_js),
        pg_node("Postgres Update Draft", [2280, -180], update_draft_query, update_draft_replacements),
        switch_node("Route By Priority", [2500, -40]),
        code_node("Emergency Result", [2720, -260], result_passthrough_js),
        code_node("Needs Review Result", [2720, -120], result_passthrough_js),
        code_node("Urgent Result", [2720, 20], result_passthrough_js),
        code_node("Routine Result", [2720, 160], result_passthrough_js),
    ]

    connections = {
        "Core Input": {"main": [[{"node": "Normalize Request", "type": "main", "index": 0}]]},
        "Normalize Request": {"main": [[{"node": "Postgres Dedupe Thread Gate", "type": "main", "index": 0}]]},
        "Postgres Dedupe Thread Gate": {"main": [[{"node": "Prepare Gate Decision", "type": "main", "index": 0}]]},
        "Prepare Gate Decision": {"main": [[{"node": "Should Create Ticket", "type": "main", "index": 0}]]},
        "Should Create Ticket": {
            "main": [
                [{"node": "Prepare Classification Request", "type": "main", "index": 0}],
                [{"node": "Return Existing Outcome", "type": "main", "index": 0}],
            ]
        },
        "Prepare Classification Request": {
            "main": [[
                {"node": "Items Needing Classifier", "type": "main", "index": 0},
                {"node": "Synthetic Classification Result", "type": "main", "index": 0},
            ]]
        },
        "Items Needing Classifier": {"main": [[{"node": "HTTP OpenAI Classification", "type": "main", "index": 0}]]},
        "HTTP OpenAI Classification": {"main": [[{"node": "Attach Classifier Response", "type": "main", "index": 0}]]},
        "Attach Classifier Response": {"main": [[{"node": "Apply Safety Rules", "type": "main", "index": 0}]]},
        "Synthetic Classification Result": {"main": [[{"node": "Apply Safety Rules", "type": "main", "index": 0}]]},
        "Apply Safety Rules": {"main": [[{"node": "Postgres Insert Ticket Events", "type": "main", "index": 0}]]},
        "Postgres Insert Ticket Events": {"main": [[{"node": "Attach Persisted Ticket", "type": "main", "index": 0}]]},
        "Attach Persisted Ticket": {
            "main": [[
                {"node": "Items Needing Draft", "type": "main", "index": 0},
                {"node": "Return Without Draft", "type": "main", "index": 0},
            ]]
        },
        "Items Needing Draft": {"main": [[{"node": "Prepare Draft Request", "type": "main", "index": 0}]]},
        "Prepare Draft Request": {"main": [[{"node": "HTTP OpenAI Draft", "type": "main", "index": 0}]]},
        "HTTP OpenAI Draft": {"main": [[{"node": "Attach Draft Response", "type": "main", "index": 0}]]},
        "Attach Draft Response": {"main": [[{"node": "Postgres Update Draft", "type": "main", "index": 0}]]},
        "Postgres Update Draft": {"main": [[{"node": "Route By Priority", "type": "main", "index": 0}]]},
        "Return Without Draft": {"main": [[{"node": "Route By Priority", "type": "main", "index": 0}]]},
        "Route By Priority": {
            "main": [
                [{"node": "Emergency Result", "type": "main", "index": 0}],
                [{"node": "Needs Review Result", "type": "main", "index": 0}],
                [{"node": "Urgent Result", "type": "main", "index": 0}],
                [{"node": "Routine Result", "type": "main", "index": 0}],
            ]
        },
    }
    return workflow_base(CORE_ID, "Maintenance Triage Engine", nodes, connections)


def fixture_payload(stem: str) -> dict:
    text = (FIXTURES / f"{stem}.txt").read_text(encoding="utf-8").strip()
    return {
        "source": "fixture",
        "from_address": f"{stem}@fixture.example",
        "subject": stem,
        "body_raw": text,
        "received_at": "2026-07-31T12:00:00Z",
        "attachment_paths": [],
        "msg_id": f"<{stem}@fixture.example>",
        "in_reply_to": None,
        "refs": None,
    }


def build_driver():
    live_stems = [
        "01-understated-gas",
        "02-panicked-burst-pipe-no-unit",
        "03-urgent-squeaky-door",
        "04-buried-lede",
        "05-spanish-no-hot-water",
        "06-accommodation-request",
    ]
    cases = [fixture_payload(stem) for stem in live_stems]
    duplicate = fixture_payload("01-understated-gas")
    duplicate["msg_id"] = "<01-understated-gas-duplicate@fixture.example>"
    cases.append(duplicate)

    mock_model = {
        "is_maintenance_request": True,
        "request_type": "NEW_ISSUE",
        "unit_identifier": "2B",
        "tenant_name": "Dana",
        "tenant_contact": None,
        "issue_summary": "Gas smell in hallway",
        "priority": "ROUTINE",
        "priority_reason": "Mocked low priority for override test",
        "trade": "GENERAL",
        "habitability_flag": False,
        "habitability_reason": None,
        "safety_signals": ["NONE"],
        "access_notes": None,
        "accommodation_or_legal_flag": False,
        "accommodation_or_legal_reason": None,
        "missing_info": [],
        "confidence": "HIGH",
        "ambiguity_note": None,
        "language": "en",
    }
    mock_gas = fixture_payload("01-understated-gas")
    mock_gas["subject"] = "mock routine gas"
    mock_gas["msg_id"] = "<mock-routine-gas@fixture.example>"
    mock_gas["body_raw"] = mock_gas["body_raw"] + " This is a separate follow-up from the same tenant for the Stage 4 rule test."
    mock_gas["test_mode"] = {"mock_model_json": mock_model}
    cases.append(mock_gas)

    negation = fixture_payload("22-negation-trap")
    negation["msg_id"] = "<22-negation-trap@fixture.example>"
    negation["test_mode"] = {"mock_model_json": {
        **mock_model,
        "unit_identifier": "9C",
        "issue_summary": "Resolved heat complaint follow-up",
        "priority": "ROUTINE",
        "priority_reason": "Negated safety wording",
        "safety_signals": ["NONE"],
        "request_type": "FOLLOW_UP",
    }}
    cases.append(negation)

    error_case = fixture_payload("23-garbage-input")
    error_case["msg_id"] = "<23-garbage-input@fixture.example>"
    error_case["test_mode"] = {"simulate_model_error": True}
    cases.append(error_case)

    for i in range(3):
        failure = fixture_payload("23-garbage-input")
        failure["msg_id"] = f"<23-garbage-input-failure-{i}@fixture.example>"
        failure["subject"] = f"simulated failure {i}"
        failure["body_raw"] = failure["body_raw"] + f" failure {i}"
        failure["test_mode"] = {"simulate_model_error": True}
        cases.append(failure)

    load_cases_js = f"return {json.dumps([{'json': c} for c in cases], indent=2)};"
    nodes = [
        node("Manual Start", "n8n-nodes-base.manualTrigger", 1, [-500, 0]),
        code_node("Load Stage 4 Cases", [-280, 0], load_cases_js),
        node(
            "Execute Core Workflow",
            "n8n-nodes-base.executeWorkflow",
            1,
            [-40, 0],
            {
                "source": "database",
                "workflowId": CORE_ID,
                "mode": "each",
                "options": {"waitForSubWorkflow": True},
            },
        ),
    ]
    connections = {
        "Manual Start": {"main": [[{"node": "Load Stage 4 Cases", "type": "main", "index": 0}]]},
        "Load Stage 4 Cases": {"main": [[{"node": "Execute Core Workflow", "type": "main", "index": 0}]]},
    }
    return workflow_base(DRIVER_ID, "Maintenance Triage Stage 4 Driver", nodes, connections)


def main():
    WORKFLOWS.mkdir(exist_ok=True)
    for path, workflow in [
        (WORKFLOWS / "maintenance-triage-core.json", build_core()),
        (WORKFLOWS / "maintenance-triage-stage-4-driver.json", build_driver()),
    ]:
        path.write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()

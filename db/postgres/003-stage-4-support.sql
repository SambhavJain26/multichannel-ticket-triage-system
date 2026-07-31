CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SEQUENCE IF NOT EXISTS triage.ticket_ref_seq START WITH 1 INCREMENT BY 1;

INSERT INTO triage.config (key, value)
VALUES (
  'runtime_state',
  '{
    "consecutive_model_failures": 0,
    "degraded_until": null,
    "degraded_alerted_at": null,
    "last_model_success_at": null,
    "last_model_failure_at": null,
    "llm_calls_today": 0,
    "llm_call_day": null
  }'::jsonb
)
ON CONFLICT (key) DO UPDATE
SET value = triage.config.value || EXCLUDED.value;

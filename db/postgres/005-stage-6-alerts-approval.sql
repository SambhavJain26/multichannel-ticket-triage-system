CREATE EXTENSION IF NOT EXISTS pgcrypto;

ALTER TABLE triage.tickets
  ADD COLUMN IF NOT EXISTS telegram_chat_id TEXT,
  ADD COLUMN IF NOT EXISTS outbound_to TEXT,
  ADD COLUMN IF NOT EXISTS outbound_sent_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS last_alert_error TEXT;

INSERT INTO triage.config (key, value)
VALUES (
  'outbound_email',
  '{
    "mode": "test_only",
    "test_to": "maintenance@example.test",
    "from_email": "maintenance@example.test",
    "from_name": "Demo Maintenance Desk",
    "message_id_domain": "maintenance-triage.local"
  }'::jsonb
)
ON CONFLICT (key) DO UPDATE
SET value = triage.config.value || EXCLUDED.value;

CREATE INDEX IF NOT EXISTS tickets_stage_6_emergency_escalation_idx
  ON triage.tickets (received_at)
  WHERE priority = 'EMERGENCY' AND acked_at IS NULL AND closed_at IS NULL;

CREATE INDEX IF NOT EXISTS tickets_stage_6_approval_guard_idx
  ON triage.tickets (id, status, priority)
  WHERE status IN ('NEW', 'ALERTED', 'ACKED', 'HELD');

CREATE INDEX IF NOT EXISTS events_stage_6_alert_rate_idx
  ON triage.events (at)
  WHERE action IN ('telegram_alert_sent', 'telegram_alert_mocked', 'telegram_alert_grouped');

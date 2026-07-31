INSERT INTO triage.config (key, value) VALUES
  ('sla_minutes', '{"EMERGENCY":60,"URGENT":1440,"ROUTINE":4320,"NEEDS_REVIEW":120}'::jsonb),
  ('overdue_days', '{"ROUTINE":10,"URGENT":3}'::jsonb),
  ('escalate_after', '{"EMERGENCY_minutes":15}'::jsonb),
  ('contacts', '{"primary_chat_id":"PLACEHOLDER_PRIMARY_CHAT_ID","secondary_chat_id":"PLACEHOLDER_SECONDARY_CHAT_ID","operator_chat_id":"PLACEHOLDER_OPERATOR_CHAT_ID"}'::jsonb),
  ('company', '{"name":"Demo Property Management","office_hours":"Mon-Fri 9-5","from_name":"Demo Maintenance Desk","timezone":"America/Chicago"}'::jsonb),
  ('quiet_hours', '{"start":"20:00","end":"07:00","tz":"America/Chicago","emergency_only":true}'::jsonb),
  ('limits', '{"max_llm_calls_per_day":400,"max_alerts_per_hour":6}'::jsonb)
ON CONFLICT (key) DO UPDATE
SET value = EXCLUDED.value;

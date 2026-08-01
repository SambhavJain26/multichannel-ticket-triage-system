-- Stage 8 demo hardening config.
-- This file only seeds local demo config. It does not reset operational data.

INSERT INTO triage.config (key, value)
VALUES
  (
    'digest',
    jsonb_build_object(
      'enabled', false,
      'send_hour', 7,
      'timezone', 'America/Chicago',
      'to_email', 'maintenance@example.test',
      'subject_prefix', 'Daily maintenance triage digest'
    )
  ),
  (
    'heartbeat',
    jsonb_build_object(
      'enabled', false,
      'threshold_minutes', 720,
      'repeat_suppression_minutes', 180,
      'baseline_at', now(),
      'last_alert_at', null,
      'last_checked_at', null
    )
  )
ON CONFLICT (key) DO UPDATE
SET value = triage.config.value || EXCLUDED.value;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

INSERT INTO triage.config (key, value)
VALUES (
  'board',
  jsonb_build_object(
    'token', encode(gen_random_bytes(24), 'hex'),
    'recent_hours', 48,
    'max_cards', 60
  )
)
ON CONFLICT (key) DO UPDATE
SET value = jsonb_build_object(
  'token',
    CASE
      WHEN triage.config.value ? 'token' AND length(triage.config.value->>'token') >= 32
        THEN triage.config.value->>'token'
      ELSE encode(gen_random_bytes(24), 'hex')
    END,
  'recent_hours', coalesce((triage.config.value->>'recent_hours')::int, 48),
  'max_cards', coalesce((triage.config.value->>'max_cards')::int, 60)
);

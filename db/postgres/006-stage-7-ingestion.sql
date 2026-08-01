CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS triage.units (
  id BIGSERIAL PRIMARY KEY,
  property_name TEXT NOT NULL,
  unit_label TEXT NOT NULL,
  tenant_name TEXT,
  tenant_email TEXT,
  tenant_phone TEXT,
  active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (property_name, unit_label)
);

ALTER TABLE triage.tickets
  ADD COLUMN IF NOT EXISTS unit_match_status TEXT CHECK (
    unit_match_status IS NULL OR unit_match_status IN ('EXACT', 'NEAR_MISS', 'AMBIGUOUS', 'NOT_FOUND', 'NOT_STATED')
  ),
  ADD COLUMN IF NOT EXISTS matched_unit_id BIGINT REFERENCES triage.units(id),
  ADD COLUMN IF NOT EXISTS unit_match_display TEXT,
  ADD COLUMN IF NOT EXISTS unit_match_reason TEXT;

CREATE TABLE IF NOT EXISTS triage.import_batches (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  label TEXT NOT NULL,
  source_dir TEXT NOT NULL,
  report_path TEXT,
  review_csv_path TEXT,
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at TIMESTAMPTZ,
  item_count INT NOT NULL DEFAULT 0,
  alert_count INT NOT NULL DEFAULT 0,
  needs_review_count INT NOT NULL DEFAULT 0,
  over_48h_count INT NOT NULL DEFAULT 0,
  wrong_count INT,
  status TEXT NOT NULL DEFAULT 'RUNNING' CHECK (status IN ('RUNNING', 'COMPLETE', 'FAILED'))
);

CREATE TABLE IF NOT EXISTS triage.import_items (
  id BIGSERIAL PRIMARY KEY,
  batch_id UUID REFERENCES triage.import_batches(id) ON DELETE CASCADE,
  source_path TEXT NOT NULL,
  message_date TIMESTAMPTZ,
  from_address TEXT,
  subject TEXT,
  ticket_id BIGINT REFERENCES triage.tickets(id),
  ref TEXT,
  expected_priority TEXT,
  actual_priority TEXT,
  expected_trade TEXT,
  actual_trade TEXT,
  expected_safety BOOLEAN,
  actual_safety BOOLEAN,
  is_wrong BOOLEAN,
  error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS units_active_unit_label_idx
  ON triage.units (active, lower(regexp_replace(unit_label, '[^a-zA-Z0-9]+', '', 'g')));

CREATE INDEX IF NOT EXISTS tickets_stage_7_unit_match_idx
  ON triage.tickets (unit_match_status, matched_unit_id);

CREATE INDEX IF NOT EXISTS import_items_batch_id_idx
  ON triage.import_items (batch_id, id);

INSERT INTO triage.config (key, value)
VALUES (
  'ingestion',
  jsonb_build_object(
    'import_token', encode(gen_random_bytes(24), 'hex'),
    'attachment_root', '/data/attachments',
    'batch_root', '/data/import-batches'
  )
)
ON CONFLICT (key) DO UPDATE
SET value = jsonb_build_object(
  'import_token',
    CASE
      WHEN triage.config.value ? 'import_token' AND length(triage.config.value->>'import_token') >= 32
        THEN triage.config.value->>'import_token'
      ELSE encode(gen_random_bytes(24), 'hex')
    END,
  'attachment_root', coalesce(triage.config.value->>'attachment_root', '/data/attachments'),
  'batch_root', coalesce(triage.config.value->>'batch_root', '/data/import-batches')
);

INSERT INTO triage.config (key, value)
VALUES (
  'outbound_email',
  '{
    "mode": "live",
    "test_to": null,
    "from_email": "PLACEHOLDER_DEMO_MAILBOX",
    "from_name": "Demo Maintenance Desk",
    "message_id_domain": "demo-mailbox.local"
  }'::jsonb
)
ON CONFLICT (key) DO UPDATE
SET value = triage.config.value || jsonb_build_object(
  'mode', 'live',
  'from_email', coalesce(nullif(triage.config.value->>'from_email', ''), 'PLACEHOLDER_DEMO_MAILBOX'),
  'from_name', coalesce(nullif(triage.config.value->>'from_name', ''), 'Demo Maintenance Desk'),
  'message_id_domain', coalesce(nullif(triage.config.value->>'message_id_domain', ''), 'demo-mailbox.local')
);

INSERT INTO triage.units (property_name, unit_label, tenant_name, tenant_email, tenant_phone)
VALUES
  ('Maple Court', '1A', 'Dana Ortiz', 'dana.ortiz@example.test', '555-0101'),
  ('Maple Court', '1B', 'Priya Shah', 'priya.shah@example.test', '555-0102'),
  ('Maple Court', '2B', 'Marco Diaz', 'marco.diaz@example.test', '555-0103'),
  ('Maple Court', '2D', 'Lena Brooks', 'lena.brooks@example.test', '555-0104'),
  ('Maple Court', '4C', 'Maria Rivera', 'maria.rivera@example.test', '555-0105'),
  ('Oak Terrace', 'A', 'Ben Harris', 'ben.harris@example.test', '555-0111'),
  ('Oak Terrace', 'B', 'Iris Chen', 'iris.chen@example.test', '555-0112'),
  ('Oak Terrace', 'C', 'Jon Bell', 'jon.bell@example.test', '555-0113'),
  ('Oak Terrace', 'D', 'Nadia Singh', 'nadia.singh@example.test', '555-0114'),
  ('Pine House', '101', 'Elena Cruz', 'elena.cruz@example.test', '555-0121'),
  ('Pine House', '102', 'Avery Reed', 'avery.reed@example.test', '555-0122'),
  ('Pine House', '201', 'Sam Patel', 'sam.patel@example.test', '555-0123'),
  ('Pine House', '202', 'Tara Cole', 'tara.cole@example.test', '555-0124'),
  ('Cedar Lofts', '3', 'Noah Grant', 'noah.grant@example.test', '555-0131'),
  ('Cedar Lofts', '4', 'Ana Lopez', 'ana.lopez@example.test', '555-0132'),
  ('Cedar Lofts', '5', 'Maya Ellis', 'maya.ellis@example.test', '555-0133'),
  ('Cedar Lofts', '6', 'Owen Kim', 'owen.kim@example.test', '555-0134'),
  ('River Bend', '12', 'Grace Miller', 'grace.miller@example.test', '555-0141'),
  ('River Bend', '14', 'Theo Martin', 'theo.martin@example.test', '555-0142'),
  ('River Bend', '16', 'Camila Torres', 'camila.torres@example.test', '555-0143')
ON CONFLICT (property_name, unit_label) DO UPDATE
SET tenant_name = EXCLUDED.tenant_name,
    tenant_email = EXCLUDED.tenant_email,
    tenant_phone = EXCLUDED.tenant_phone,
    active = true;

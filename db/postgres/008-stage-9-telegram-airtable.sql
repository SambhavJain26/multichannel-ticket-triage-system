CREATE EXTENSION IF NOT EXISTS pgcrypto;

ALTER TABLE triage.tickets
  DROP CONSTRAINT IF EXISTS tickets_source_check;

ALTER TABLE triage.tickets
  ADD CONSTRAINT tickets_source_check
  CHECK (source IN ('email', 'form', 'telegram', 'fixture', 'import'));

ALTER TABLE triage.tickets
  ADD COLUMN IF NOT EXISTS airtable_record_id TEXT,
  ADD COLUMN IF NOT EXISTS tenant_chat_id TEXT,
  ADD COLUMN IF NOT EXISTS clarification_round SMALLINT NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS vendor_status TEXT NOT NULL DEFAULT 'NOT_STARTED' CHECK (
    vendor_status IN ('NOT_STARTED', 'AWAITING_VENDOR', 'NEEDS_VENDOR_ASSIGNMENT', 'SENDING', 'SENT', 'FAILED', 'HELD')
  ),
  ADD COLUMN IF NOT EXISTS selected_vendor_id TEXT,
  ADD COLUMN IF NOT EXISTS selected_vendor_name TEXT,
  ADD COLUMN IF NOT EXISTS selected_vendor_email TEXT,
  ADD COLUMN IF NOT EXISTS vendor_email_message_id TEXT,
  ADD COLUMN IF NOT EXISTS vendor_email_sent_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS vendor_email_error TEXT;

CREATE TABLE IF NOT EXISTS triage.tenant_chats (
  id BIGSERIAL PRIMARY KEY,
  telegram_chat_id TEXT UNIQUE NOT NULL,
  telegram_user_id TEXT,
  telegram_username TEXT,
  tenant_email TEXT,
  tenant_name TEXT,
  matched_unit_id BIGINT REFERENCES triage.units(id),
  active_ticket_id BIGINT REFERENCES triage.tickets(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS triage.tenant_pairing_tokens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ticket_id BIGINT NOT NULL REFERENCES triage.tickets(id) ON DELETE CASCADE,
  tenant_email TEXT NOT NULL,
  token TEXT UNIQUE NOT NULL DEFAULT encode(gen_random_bytes(24), 'hex'),
  expires_at TIMESTAMPTZ NOT NULL DEFAULT now() + interval '7 days',
  consumed_at TIMESTAMPTZ,
  consumed_chat_id TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS triage.ticket_messages (
  id BIGSERIAL PRIMARY KEY,
  ticket_id BIGINT NOT NULL REFERENCES triage.tickets(id) ON DELETE CASCADE,
  channel TEXT NOT NULL CHECK (channel IN ('email', 'form', 'telegram')),
  direction TEXT NOT NULL CHECK (direction IN ('inbound', 'outbound')),
  intent TEXT NOT NULL CHECK (intent IN ('request', 'pairing', 'receipt', 'clarification', 'clarification_answer', 'status', 'vendor_update', 'manager_note')),
  body TEXT NOT NULL,
  external_message_id TEXT,
  delivery_state TEXT NOT NULL DEFAULT 'RECORDED' CHECK (delivery_state IN ('RECORDED', 'PENDING', 'SENT', 'FAILED', 'SKIPPED')),
  detail JSONB NOT NULL DEFAULT '{}'::jsonb,
  airtable_record_id TEXT,
  airtable_synced_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (channel, direction, external_message_id)
);

ALTER TABLE triage.ticket_messages
  DROP CONSTRAINT IF EXISTS ticket_messages_intent_check;

ALTER TABLE triage.ticket_messages
  ADD CONSTRAINT ticket_messages_intent_check CHECK (
    intent IN ('request', 'pairing', 'receipt', 'clarification', 'clarification_answer', 'status', 'vendor_update', 'vendor_dispatch', 'manager_note')
  );

ALTER TABLE triage.ticket_messages
  ADD COLUMN IF NOT EXISTS airtable_record_id TEXT,
  ADD COLUMN IF NOT EXISTS airtable_synced_at TIMESTAMPTZ;

CREATE TABLE IF NOT EXISTS triage.vendor_send_attempts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ticket_id BIGINT NOT NULL REFERENCES triage.tickets(id) ON DELETE CASCADE,
  vendor_id TEXT NOT NULL,
  vendor_name TEXT NOT NULL,
  vendor_email TEXT NOT NULL,
  manager_chat_id TEXT,
  manager_message_id BIGINT,
  actor TEXT NOT NULL,
  state TEXT NOT NULL CHECK (state IN ('CLAIMED', 'SENT', 'FAILED', 'HELD')),
  smtp_message_id TEXT,
  error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at TIMESTAMPTZ,
  UNIQUE (ticket_id)
);

CREATE TABLE IF NOT EXISTS triage.ticket_vendor_candidates (
  ticket_id BIGINT NOT NULL REFERENCES triage.tickets(id) ON DELETE CASCADE,
  vendor_id TEXT NOT NULL,
  vendor_name TEXT NOT NULL,
  vendor_email TEXT NOT NULL,
  candidate_rank SMALLINT NOT NULL CHECK (candidate_rank BETWEEN 1 AND 3),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (ticket_id, vendor_id),
  UNIQUE (ticket_id, candidate_rank)
);

CREATE TABLE IF NOT EXISTS triage.airtable_roster_links (
  roster_kind TEXT NOT NULL CHECK (roster_kind IN ('tenant', 'vendor')),
  lookup_key TEXT NOT NULL,
  airtable_record_id TEXT NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (roster_kind, lookup_key)
);

CREATE INDEX IF NOT EXISTS tenant_pairing_tokens_active_idx
  ON triage.tenant_pairing_tokens (token, expires_at)
  WHERE consumed_at IS NULL;

CREATE INDEX IF NOT EXISTS tenant_chats_active_ticket_idx
  ON triage.tenant_chats (active_ticket_id)
  WHERE active_ticket_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS ticket_messages_ticket_created_idx
  ON triage.ticket_messages (ticket_id, created_at);

CREATE INDEX IF NOT EXISTS tickets_stage_9_vendor_queue_idx
  ON triage.tickets (vendor_status, received_at)
  WHERE vendor_status IN ('AWAITING_VENDOR', 'NEEDS_VENDOR_ASSIGNMENT', 'FAILED');

INSERT INTO triage.config (key, value)
VALUES
  ('tenant_telegram', '{"bot_username":"PLACEHOLDER_TENANT_BOT_USERNAME","pairing_days":7,"max_clarification_rounds":2}'::jsonb),
  ('airtable', '{"enabled":false,"base_id":"","base_url":"","requests_table":"Requests","conversations_table":"Conversations","tenant_roster_table":"Tenant Roster","vendors_table":"Vendors"}'::jsonb),
  ('system_mail', '{"subject_prefix":"[MT-SYSTEM]","onboarding_subject":"[MT-SYSTEM] Continue your maintenance request in Telegram","vendor_subject_prefix":"[MT-SYSTEM][VENDOR]"}'::jsonb)
ON CONFLICT (key) DO UPDATE
SET value = EXCLUDED.value || triage.config.value;

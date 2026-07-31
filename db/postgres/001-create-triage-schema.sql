CREATE SCHEMA IF NOT EXISTS triage;

CREATE TABLE IF NOT EXISTS triage.tickets (
  id BIGSERIAL PRIMARY KEY,
  ref TEXT UNIQUE NOT NULL,
  source TEXT NOT NULL CHECK (source IN ('email', 'form', 'fixture', 'import')),
  received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  from_address TEXT,
  subject TEXT,
  body_raw TEXT,
  body_clean TEXT,
  body_hash TEXT NOT NULL,
  attachment_count INT NOT NULL DEFAULT 0 CHECK (attachment_count >= 0),
  attachment_paths JSONB NOT NULL DEFAULT '[]'::jsonb,

  msg_id TEXT,
  in_reply_to TEXT,
  refs TEXT,
  out_msg_id TEXT,
  thread_root_id BIGINT REFERENCES triage.tickets(id),

  model_json JSONB,
  model_priority TEXT CHECK (model_priority IS NULL OR model_priority IN ('EMERGENCY', 'URGENT', 'ROUTINE')),
  model_name TEXT,
  model_latency_ms INT CHECK (model_latency_ms IS NULL OR model_latency_ms >= 0),
  prompt_tokens INT CHECK (prompt_tokens IS NULL OR prompt_tokens >= 0),
  completion_tokens INT CHECK (completion_tokens IS NULL OR completion_tokens >= 0),
  degraded BOOLEAN NOT NULL DEFAULT false,

  is_maintenance_request BOOLEAN,
  request_type TEXT CHECK (request_type IS NULL OR request_type IN ('NEW_ISSUE', 'FOLLOW_UP', 'NOT_A_REQUEST')),
  priority TEXT NOT NULL CHECK (priority IN ('EMERGENCY', 'URGENT', 'ROUTINE', 'NEEDS_REVIEW')),
  priority_reason TEXT,
  override_applied BOOLEAN NOT NULL DEFAULT false,
  override_reason TEXT,
  human_only BOOLEAN NOT NULL DEFAULT false,
  trade TEXT CHECK (trade IS NULL OR trade IN ('PLUMBING', 'ELECTRICAL', 'HVAC', 'APPLIANCE', 'STRUCTURAL', 'PEST', 'LOCKS_SECURITY', 'GENERAL', 'UNKNOWN')),
  unit_identifier TEXT,
  tenant_name TEXT,
  tenant_contact TEXT,
  issue_summary TEXT,
  habitability_flag BOOLEAN NOT NULL DEFAULT false,
  habitability_reason TEXT,
  safety_signals JSONB NOT NULL DEFAULT '[]'::jsonb,
  access_notes TEXT,
  accommodation_or_legal_flag BOOLEAN NOT NULL DEFAULT false,
  accommodation_or_legal_reason TEXT,
  missing_info JSONB NOT NULL DEFAULT '[]'::jsonb,
  confidence TEXT CHECK (confidence IS NULL OR confidence IN ('HIGH', 'MEDIUM', 'LOW')),
  ambiguity_note TEXT,
  language TEXT,

  draft_subject TEXT,
  draft_body TEXT,
  vendor_note TEXT,
  clarifying_qs JSONB NOT NULL DEFAULT '[]'::jsonb,

  status TEXT NOT NULL DEFAULT 'NEW' CHECK (status IN ('NEW', 'ALERTED', 'ACKED', 'ACK_SENT', 'HELD', 'CLOSED')),
  sla_due_at TIMESTAMPTZ,
  alerted_at TIMESTAMPTZ,
  acked_at TIMESTAMPTZ,
  acked_by TEXT,
  telegram_msg_id BIGINT,
  closed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS tickets_status_priority_received_at_idx
  ON triage.tickets (status, priority, received_at DESC);

CREATE INDEX IF NOT EXISTS tickets_body_hash_received_at_idx
  ON triage.tickets (body_hash, received_at);

CREATE INDEX IF NOT EXISTS tickets_thread_root_id_idx
  ON triage.tickets (thread_root_id);

CREATE INDEX IF NOT EXISTS tickets_msg_id_idx
  ON triage.tickets (msg_id);

CREATE INDEX IF NOT EXISTS tickets_out_msg_id_idx
  ON triage.tickets (out_msg_id);

CREATE TABLE IF NOT EXISTS triage.events (
  id BIGSERIAL PRIMARY KEY,
  ticket_id BIGINT REFERENCES triage.tickets(id),
  at TIMESTAMPTZ NOT NULL DEFAULT now(),
  actor TEXT NOT NULL,
  action TEXT NOT NULL,
  detail JSONB
);

CREATE INDEX IF NOT EXISTS events_ticket_id_at_idx
  ON triage.events (ticket_id, at);

CREATE INDEX IF NOT EXISTS events_action_at_idx
  ON triage.events (action, at);

CREATE TABLE IF NOT EXISTS triage.config (
  key TEXT PRIMARY KEY,
  value JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS triage.feedback (
  id BIGSERIAL PRIMARY KEY,
  ticket_id BIGINT REFERENCES triage.tickets(id),
  at TIMESTAMPTZ NOT NULL DEFAULT now(),
  was TEXT,
  became TEXT,
  by_user TEXT
);

CREATE INDEX IF NOT EXISTS feedback_ticket_id_at_idx
  ON triage.feedback (ticket_id, at);

ALTER TABLE triage.tenant_chats
  ADD COLUMN IF NOT EXISTS pending_intake_body TEXT,
  ADD COLUMN IF NOT EXISTS pending_intake_started_at TIMESTAMPTZ;

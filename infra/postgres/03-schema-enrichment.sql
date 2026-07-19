-- Idempotent enrichment for existing Relay volumes (safe to re-run).
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(64) PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(64) NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE tool_call_audit
    ADD COLUMN IF NOT EXISTS source VARCHAR(32) NOT NULL DEFAULT 'native';

ALTER TABLE agent_runs
    ADD COLUMN IF NOT EXISTS groundedness_passed BOOLEAN,
    ADD COLUMN IF NOT EXISTS groundedness_explanation TEXT;

CREATE TABLE IF NOT EXISTS pending_approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id VARCHAR(64) NOT NULL,
    session_id VARCHAR(128) NOT NULL,
    tool_name VARCHAR(128) NOT NULL,
    arguments JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_by_sub VARCHAR(128) NOT NULL,
    status next_action_status NOT NULL DEFAULT 'pending',
    decided_by_sub VARCHAR(128),
    decided_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS prompt_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(128) NOT NULL,
    version INTEGER NOT NULL,
    body TEXT NOT NULL,
    is_production BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (name, version)
);

CREATE TABLE IF NOT EXISTS eval_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    suite_name VARCHAR(128) NOT NULL,
    question_id VARCHAR(64) NOT NULL,
    role_name VARCHAR(64) NOT NULL,
    passed BOOLEAN NOT NULL,
    score NUMERIC(5, 2),
    latency_ms INTEGER,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS metric_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name VARCHAR(128) NOT NULL,
    metric_value NUMERIC NOT NULL,
    labels JSONB NOT NULL DEFAULT '{}'::jsonb,
    captured_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_issues_priority ON issues(priority);
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_document ON knowledge_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_tool_audit_request ON tool_call_audit(request_id);
CREATE INDEX IF NOT EXISTS idx_tool_audit_source ON tool_call_audit(source);
CREATE INDEX IF NOT EXISTS idx_agent_runs_created ON agent_runs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_runs_groundedness ON agent_runs(groundedness_passed);
CREATE INDEX IF NOT EXISTS idx_pending_approvals_status ON pending_approvals(status);
CREATE INDEX IF NOT EXISTS idx_eval_runs_suite ON eval_runs(suite_name, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_metric_snapshots_name ON metric_snapshots(metric_name, captured_at DESC);

INSERT INTO schema_migrations (version, description)
VALUES ('003_enrichment', 'Groundedness, MCP source, approvals, orgs, eval/metrics tables')
ON CONFLICT (version) DO NOTHING;

INSERT INTO organizations (slug, display_name)
VALUES ('acme-ops', 'Acme Operations')
ON CONFLICT (slug) DO NOTHING;

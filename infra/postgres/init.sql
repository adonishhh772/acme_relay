-- Relay ops schema (PostgreSQL 16 + pgvector)
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TYPE app_role AS ENUM ('sales_user', 'support_user', 'operations_user', 'admin');
CREATE TYPE issue_status AS ENUM ('open', 'in_progress', 'resolved', 'closed');
CREATE TYPE issue_priority AS ENUM ('low', 'medium', 'high', 'critical');
CREATE TYPE next_action_status AS ENUM ('pending', 'approved', 'completed', 'rejected');
CREATE TYPE knowledge_sensitivity AS ENUM ('public', 'internal', 'restricted');

CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    industry VARCHAR(128),
    tier VARCHAR(32) NOT NULL DEFAULT 'standard',
    account_owner VARCHAR(255),
    region VARCHAR(64),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    role app_role NOT NULL,
    keycloak_sub VARCHAR(128) UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE user_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    keycloak_sub VARCHAR(128) NOT NULL UNIQUE,
    username VARCHAR(128) NOT NULL,
    role app_role NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    issue_key VARCHAR(32) NOT NULL UNIQUE,
    title VARCHAR(512) NOT NULL,
    description TEXT,
    status issue_status NOT NULL DEFAULT 'open',
    priority issue_priority NOT NULL DEFAULT 'medium',
    assigned_to VARCHAR(128),
    sla_hours INTEGER NOT NULL DEFAULT 24,
    sla_due_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE issue_updates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    issue_id UUID NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    author VARCHAR(128) NOT NULL,
    body TEXT NOT NULL,
    is_internal BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE next_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    issue_id UUID NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    action_text TEXT NOT NULL,
    suggested_by VARCHAR(64) NOT NULL DEFAULT 'relay',
    owner VARCHAR(128),
    status next_action_status NOT NULL DEFAULT 'pending',
    created_by_sub VARCHAR(128),
    approved_by_sub VARCHAR(128),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE schema_migrations (
    version VARCHAR(64) PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(64) NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE tool_call_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id VARCHAR(64),
    user_sub VARCHAR(128),
    user_roles TEXT[],
    tool_name VARCHAR(128) NOT NULL,
    arguments JSONB,
    result_summary TEXT,
    latency_ms INTEGER,
    success BOOLEAN NOT NULL DEFAULT true,
    source VARCHAR(32) NOT NULL DEFAULT 'native',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE agent_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id VARCHAR(64),
    user_sub VARCHAR(128),
    query TEXT NOT NULL,
    answer TEXT,
    tools_used TEXT[],
    latency_ms INTEGER,
    prompt_name VARCHAR(128),
    prompt_version INTEGER,
    groundedness_passed BOOLEAN,
    groundedness_explanation TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE pending_approvals (
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

CREATE TABLE prompt_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(128) NOT NULL,
    version INTEGER NOT NULL,
    body TEXT NOT NULL,
    is_production BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (name, version)
);

CREATE TABLE eval_runs (
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

CREATE TABLE metric_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name VARCHAR(128) NOT NULL,
    metric_value NUMERIC NOT NULL,
    labels JSONB NOT NULL DEFAULT '{}'::jsonb,
    captured_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE knowledge_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(512) NOT NULL,
    source_path VARCHAR(1024) NOT NULL,
    doc_type VARCHAR(64) NOT NULL DEFAULT 'playbook',
    sensitivity knowledge_sensitivity NOT NULL DEFAULT 'internal',
    allowed_roles app_role[] NOT NULL DEFAULT ARRAY['sales_user','support_user','operations_user','admin']::app_role[],
    ingest_status VARCHAR(32) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE knowledge_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),
    allowed_roles app_role[] NOT NULL,
    sensitivity knowledge_sensitivity NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_issues_customer ON issues(customer_id);
CREATE INDEX idx_issues_status ON issues(status);
CREATE INDEX idx_issues_priority ON issues(priority);
CREATE INDEX idx_next_actions_status ON next_actions(status);
CREATE INDEX idx_knowledge_chunks_roles ON knowledge_chunks USING GIN (allowed_roles);
CREATE INDEX idx_knowledge_chunks_document ON knowledge_chunks(document_id);
CREATE INDEX idx_tool_audit_created ON tool_call_audit(created_at DESC);
CREATE INDEX idx_tool_audit_request ON tool_call_audit(request_id);
CREATE INDEX idx_tool_audit_source ON tool_call_audit(source);
CREATE INDEX idx_agent_runs_created ON agent_runs(created_at DESC);
CREATE INDEX idx_agent_runs_groundedness ON agent_runs(groundedness_passed);
CREATE INDEX idx_pending_approvals_status ON pending_approvals(status);
CREATE INDEX idx_eval_runs_suite ON eval_runs(suite_name, created_at DESC);
CREATE INDEX idx_metric_snapshots_name ON metric_snapshots(metric_name, captured_at DESC);

INSERT INTO schema_migrations (version, description) VALUES
    ('001_init', 'Core Relay ops schema with groundedness, MCP audit source, approvals'),
    ('002_enrichment', 'Organizations, prompt_versions, eval_runs, metric_snapshots');

INSERT INTO organizations (slug, display_name) VALUES
    ('acme-ops', 'Acme Operations');

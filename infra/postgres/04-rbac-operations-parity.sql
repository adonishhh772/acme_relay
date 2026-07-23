-- RBAC + operations_user + tenant columns + tasks/CSAT (Ops parity P0/P1)
-- Idempotent for existing volumes.

DO $$
BEGIN
    ALTER TYPE app_role ADD VALUE IF NOT EXISTS 'operations_user';
EXCEPTION
    WHEN duplicate_object THEN NULL;
    WHEN undefined_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR(64) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    category VARCHAR(64) NOT NULL DEFAULT 'general',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS rbac_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    slug VARCHAR(64) NOT NULL,
    name VARCHAR(128) NOT NULL,
    description TEXT,
    is_system BOOLEAN NOT NULL DEFAULT false,
    keycloak_role_name VARCHAR(64),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT rbac_roles_org_slug_unique UNIQUE (organization_id, slug)
);

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id UUID NOT NULL REFERENCES rbac_roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE IF NOT EXISTS user_role_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES rbac_roles(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    assigned_by UUID REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT user_role_assignments_unique UNIQUE (user_id, role_id, organization_id)
);

ALTER TABLE users ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id);
ALTER TABLE user_roles ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id);
ALTER TABLE customers ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id);
ALTER TABLE knowledge_documents ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id);
ALTER TABLE knowledge_documents ADD COLUMN IF NOT EXISTS department VARCHAR(64);
ALTER TABLE knowledge_documents ADD COLUMN IF NOT EXISTS created_by_sub VARCHAR(128);

UPDATE users u
SET organization_id = o.id
FROM organizations o
WHERE o.slug = 'acme-ops' AND u.organization_id IS NULL;

UPDATE customers c
SET organization_id = o.id
FROM organizations o
WHERE o.slug = 'acme-ops' AND c.organization_id IS NULL;

UPDATE knowledge_documents k
SET organization_id = o.id
FROM organizations o
WHERE o.slug = 'acme-ops' AND k.organization_id IS NULL;

CREATE TABLE IF NOT EXISTS user_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    keycloak_sub VARCHAR(128) NOT NULL,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    priority VARCHAR(16) NOT NULL DEFAULT 'medium'
        CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    status VARCHAR(16) NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'completed')),
    due_at TIMESTAMPTZ,
    issue_key VARCHAR(32),
    customer_external_id VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    CONSTRAINT user_tasks_title_not_blank CHECK (length(trim(title)) > 0)
);

CREATE INDEX IF NOT EXISTS idx_user_tasks_owner_status ON user_tasks (keycloak_sub, status);

CREATE TABLE IF NOT EXISTS issue_csat_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    issue_key VARCHAR(32) NOT NULL,
    score INTEGER NOT NULL CHECK (score BETWEEN 1 AND 5),
    comment TEXT,
    submitted_by_sub VARCHAR(128),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chat_feedback_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id VARCHAR(64),
    rating VARCHAR(16) NOT NULL CHECK (rating IN ('up', 'down')),
    comment TEXT,
    user_sub VARCHAR(128),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO permissions (key, description, category) VALUES
    ('read_customer', 'View customer records', 'customers'),
    ('read_issues', 'View support issues', 'issues'),
    ('read_issue_updates', 'View issue update history', 'issues'),
    ('update_issue', 'Modify issue status and details', 'issues'),
    ('create_next_action', 'Create follow-up actions', 'actions'),
    ('approve_next_action', 'Approve or reject suggested actions', 'actions'),
    ('summarize_issues', 'Generate issue summaries', 'issues'),
    ('recommend_action', 'Recommend next actions on issues', 'actions'),
    ('search_knowledge', 'Search knowledge base', 'knowledge'),
    ('ingest_knowledge', 'Ingest knowledge documents', 'knowledge'),
    ('run_skill', 'Run reusable agent skills', 'agent'),
    ('mcp_read', 'Use read-oriented MCP tools', 'mcp'),
    ('mcp_sql', 'Use SELECT-only Postgres MCP', 'mcp'),
    ('manage_users', 'Create and manage user accounts', 'admin'),
    ('manage_roles', 'Create and assign custom roles', 'admin'),
    ('manage_organizations', 'Manage tenant organizations', 'admin'),
    ('view_audit', 'View audit logs', 'admin'),
    ('run_evals', 'Run and view evaluations', 'admin'),
    ('manage_tasks', 'Manage personal tasks', 'tasks')
ON CONFLICT (key) DO NOTHING;

INSERT INTO rbac_roles (id, organization_id, slug, name, description, is_system, keycloak_role_name)
VALUES
    ('10000000-0000-0000-0000-000000000001', NULL, 'sales_user', 'Sales User', 'Read-only customer and case access', true, 'sales_user'),
    ('10000000-0000-0000-0000-000000000002', NULL, 'support_user', 'Support User', 'Case management and recommendations', true, 'support_user'),
    ('10000000-0000-0000-0000-000000000003', NULL, 'admin', 'Administrator', 'Full platform access', true, 'admin'),
    ('10000000-0000-0000-0000-000000000004', NULL, 'operations_user', 'Operations User', 'Operations department queue and cross-functional actions', true, 'operations_user')
ON CONFLICT (organization_id, slug) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM rbac_roles r CROSS JOIN permissions p
WHERE r.slug = 'sales_user'
  AND p.key IN ('read_customer', 'read_issues', 'read_issue_updates', 'summarize_issues', 'search_knowledge', 'run_skill', 'mcp_read', 'manage_tasks')
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM rbac_roles r CROSS JOIN permissions p
WHERE r.slug = 'support_user'
  AND p.key IN (
      'read_customer', 'read_issues', 'read_issue_updates', 'summarize_issues',
      'update_issue', 'create_next_action', 'recommend_action', 'search_knowledge',
      'ingest_knowledge', 'run_skill', 'mcp_read', 'mcp_sql', 'manage_tasks'
  )
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM rbac_roles r CROSS JOIN permissions p
WHERE r.slug = 'operations_user'
  AND p.key IN (
      'read_customer', 'read_issues', 'read_issue_updates', 'summarize_issues',
      'update_issue', 'create_next_action', 'recommend_action', 'search_knowledge',
      'ingest_knowledge', 'run_skill', 'mcp_read', 'mcp_sql', 'manage_tasks', 'view_audit'
  )
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM rbac_roles r CROSS JOIN permissions p
WHERE r.slug = 'admin'
ON CONFLICT DO NOTHING;

INSERT INTO users (email, display_name, role, organization_id)
SELECT 'dana@acme.local', 'Dana Operations', 'operations_user'::app_role, o.id
FROM organizations o WHERE o.slug = 'acme-ops'
ON CONFLICT (email) DO UPDATE
SET display_name = EXCLUDED.display_name,
    role = EXCLUDED.role,
    organization_id = EXCLUDED.organization_id;

INSERT INTO user_tasks (keycloak_sub, organization_id, title, description, priority, issue_key, customer_external_id)
SELECT 'dana-ops', o.id, 'Review VaultLedger settlement SLA', 'Confirm OPS-3101 mitigation plan', 'high', 'OPS-3101', 'VAULTLEDGER'
FROM organizations o
WHERE o.slug = 'acme-ops'
  AND NOT EXISTS (
    SELECT 1 FROM user_tasks t WHERE t.title = 'Review VaultLedger settlement SLA'
  );

INSERT INTO schema_migrations (version, description)
VALUES ('004_rbac_operations_parity', 'RBAC tables, operations_user, tenant columns, tasks, CSAT')
ON CONFLICT (version) DO NOTHING;

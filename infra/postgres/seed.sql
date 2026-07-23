-- Relay demo seed (distinct from inspiration AsteriaPay data)

INSERT INTO customers (
    external_id, name, industry, tier, account_owner, support_manager, account_manager,
    region, contract_value_gbp, renewal_date
) VALUES
  (
    'VAULTLEDGER', 'VaultLedger Payments', 'Fintech', 'strategic',
    'Priya Nair', 'Bob Martinez', 'priya.nair@acme.local',
    'EMEA', 680000.00, DATE '2026-09-30'
  ),
  (
    'NEXUSFREIGHT', 'Nexus Freight', 'Logistics', 'enterprise',
    'James Okonkwo', 'Bob Martinez', 'james.okonkwo@acme.local',
    'UK', 420000.00, DATE '2026-11-15'
  ),
  (
    'AURORABANK', 'Aurora Bank', 'Financial Services', 'standard',
    'Elena Vogt', 'Sarah Lim', 'elena.vogt@acme.local',
    'DACH', 185000.00, DATE '2026-08-20'
  );

INSERT INTO users (email, display_name, role) VALUES
  ('alice@acme.local', 'Alice Chen', 'sales_user'),
  ('bob@acme.local', 'Bob Martinez', 'support_user'),
  ('admin@acme.local', 'Dana Admin', 'admin');

INSERT INTO user_roles (user_id, keycloak_sub, username, role)
SELECT id, 'pending-' || role::text, split_part(email, '@', 1), role FROM users;

INSERT INTO issues (customer_id, issue_key, title, description, status, priority, assigned_to, sla_hours, sla_due_at)
SELECT c.id, 'OPS-3101', 'Settlement batch stuck in pending',
       'Overnight settlement for merchant cohort M-441 failed to clear.',
       'open', 'critical', 'Bob Martinez', 8, now() + interval '6 hours'
FROM customers c WHERE c.external_id = 'VAULTLEDGER';

INSERT INTO issues (customer_id, issue_key, title, description, status, priority, assigned_to, sla_hours, sla_due_at)
SELECT c.id, 'OPS-3102', 'Webhook retries exhausting merchant endpoint',
       'Aurora Bank payment gateway receiving duplicate settlement webhooks.',
       'in_progress', 'high', 'Bob Martinez', 24, now() + interval '18 hours'
FROM customers c WHERE c.external_id = 'AURORABANK';

INSERT INTO issues (customer_id, issue_key, title, description, status, priority, assigned_to, sla_hours, sla_due_at)
SELECT c.id, 'OPS-3103', 'POD scan delay at hub NL-03',
       'Proof-of-delivery scans delayed during peak window for Nexus Freight hubs.',
       'open', 'medium', 'Elena Vogt', 48, now() + interval '40 hours'
FROM customers c WHERE c.external_id = 'NEXUSFREIGHT';

INSERT INTO issue_updates (issue_id, author, body, is_internal)
SELECT i.id, 'Bob Martinez', 'Replayed settlement job; 12 of 18 batches cleared. Investigating ledger lock on merchant M-441.', false
FROM issues i WHERE i.issue_key = 'OPS-3101';

INSERT INTO issue_updates (issue_id, author, body, is_internal)
SELECT i.id, 'Priya Nair', 'Customer escalated to VP Finance — need status before EOD.', false
FROM issues i WHERE i.issue_key = 'OPS-3101';

INSERT INTO issue_updates (issue_id, author, body, is_internal)
SELECT i.id, 'system', 'Internal: ledger lock correlates with migration window — do not share raw SQL with sales.', true
FROM issues i WHERE i.issue_key = 'OPS-3101';

INSERT INTO issue_updates (issue_id, author, body, is_internal)
SELECT i.id, 'Bob Martinez', 'Disabled aggressive retry; merchant confirmed 200s again.', false
FROM issues i WHERE i.issue_key = 'OPS-3102';

INSERT INTO next_actions (issue_id, action_text, owner, status)
SELECT i.id, 'Schedule bridge call with VaultLedger finance + platform SRE before 16:00 UTC.', 'Priya Nair', 'pending'
FROM issues i WHERE i.issue_key = 'OPS-3101';

INSERT INTO knowledge_documents (title, source_path, doc_type, sensitivity, allowed_roles, ingest_status) VALUES
  (
    'Relay Command Desk business value',
    '/data/knowledge/public/relay-command-desk-value.md',
    'guide',
    'public',
    ARRAY['sales_user','support_user','operations_user','admin']::app_role[],
    'pending'
  ),
  (
    'Customer tier, SLA and commercial guide',
    '/data/knowledge/public/sla-overview.md',
    'sla',
    'public',
    ARRAY['sales_user','support_user','operations_user','admin']::app_role[],
    'pending'
  ),
  (
    'Support and operations escalation playbook',
    '/data/knowledge/internal/escalation-playbook.md',
    'playbook',
    'internal',
    ARRAY['support_user','operations_user','admin']::app_role[],
    'pending'
  ),
  (
    'VaultLedger settlement incident runbook',
    '/data/knowledge/internal/vaultledger-settlement-runbook.md',
    'runbook',
    'internal',
    ARRAY['support_user','operations_user','admin']::app_role[],
    'pending'
  ),
  (
    'Aurora Bank payment webhook runbook',
    '/data/knowledge/internal/aurora-webhook-runbook.md',
    'runbook',
    'internal',
    ARRAY['support_user','operations_user','admin']::app_role[],
    'pending'
  ),
  (
    'Nexus Freight POD hub operations guide',
    '/data/knowledge/internal/nexus-pod-ops-guide.md',
    'runbook',
    'internal',
    ARRAY['support_user','operations_user','admin']::app_role[],
    'pending'
  ),
  (
    'HITL approvals and safe mutations',
    '/data/knowledge/internal/hitl-approvals-and-safe-mutations.md',
    'playbook',
    'internal',
    ARRAY['support_user','operations_user','admin']::app_role[],
    'pending'
  ),
  (
    'Executive incident protocol',
    '/data/knowledge/restricted/executive-incident.md',
    'runbook',
    'restricted',
    ARRAY['admin']::app_role[],
    'pending'
  ),
  (
    'Commercial risk and renewal war-room',
    '/data/knowledge/restricted/commercial-risk-renewal-war-room.md',
    'runbook',
    'restricted',
    ARRAY['admin']::app_role[],
    'pending'
  );

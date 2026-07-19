-- Relay demo seed (distinct from inspiration AsteriaPay data)

INSERT INTO customers (external_id, name, industry, tier, account_owner, region) VALUES
  ('MERIDIAN', 'Meridian Pay', 'Fintech', 'strategic', 'Priya Nair', 'EMEA'),
  ('CASCADE', 'Cascade Retail Group', 'Retail', 'enterprise', 'James Okonkwo', 'UK'),
  ('NORTHLINE', 'Northline Logistics', 'Logistics', 'standard', 'Elena Vogt', 'DACH');

INSERT INTO users (email, display_name, role) VALUES
  ('alice@acme.local', 'Alice Chen', 'sales_user'),
  ('bob@acme.local', 'Bob Martinez', 'support_user'),
  ('admin@acme.local', 'Dana Admin', 'admin');

INSERT INTO user_roles (user_id, keycloak_sub, username, role)
SELECT id, 'pending-' || role::text, split_part(email, '@', 1), role FROM users;

INSERT INTO issues (customer_id, issue_key, title, description, status, priority, assigned_to, sla_hours, sla_due_at)
SELECT c.id, 'CASE-2001', 'Settlement batch stuck in pending',
       'Overnight settlement for merchant cohort M-441 failed to clear.',
       'open', 'critical', 'Bob Martinez', 8, now() + interval '6 hours'
FROM customers c WHERE c.external_id = 'MERIDIAN';

INSERT INTO issues (customer_id, issue_key, title, description, status, priority, assigned_to, sla_hours, sla_due_at)
SELECT c.id, 'CASE-2002', 'Webhook retries exhausting merchant endpoint',
       'Cascade storefront receiving duplicate payment webhooks.',
       'in_progress', 'high', 'Bob Martinez', 24, now() + interval '18 hours'
FROM customers c WHERE c.external_id = 'CASCADE';

INSERT INTO issues (customer_id, issue_key, title, description, status, priority, assigned_to, sla_hours, sla_due_at)
SELECT c.id, 'CASE-2003', 'POD scan delay at hub NL-03',
       'Proof-of-delivery scans delayed during peak window.',
       'open', 'medium', 'Elena Vogt', 48, now() + interval '40 hours'
FROM customers c WHERE c.external_id = 'NORTHLINE';

INSERT INTO issue_updates (issue_id, author, body, is_internal)
SELECT i.id, 'Bob Martinez', 'Replayed settlement job; 12 of 18 batches cleared. Investigating ledger lock on merchant M-441.', false
FROM issues i WHERE i.issue_key = 'CASE-2001';

INSERT INTO issue_updates (issue_id, author, body, is_internal)
SELECT i.id, 'Priya Nair', 'Customer escalated to VP Finance — need status before EOD.', false
FROM issues i WHERE i.issue_key = 'CASE-2001';

INSERT INTO issue_updates (issue_id, author, body, is_internal)
SELECT i.id, 'system', 'Internal: ledger lock correlates with migration window — do not share raw SQL with sales.', true
FROM issues i WHERE i.issue_key = 'CASE-2001';

INSERT INTO issue_updates (issue_id, author, body, is_internal)
SELECT i.id, 'Bob Martinez', 'Disabled aggressive retry; merchant confirmed 200s again.', false
FROM issues i WHERE i.issue_key = 'CASE-2002';

INSERT INTO next_actions (issue_id, action_text, owner, status)
SELECT i.id, 'Schedule bridge call with Meridian finance + platform SRE before 16:00 UTC.', 'Priya Nair', 'pending'
FROM issues i WHERE i.issue_key = 'CASE-2001';

INSERT INTO knowledge_documents (title, source_path, doc_type, sensitivity, allowed_roles, ingest_status) VALUES
  ('Public SLA overview', '/data/knowledge/public/sla-overview.md', 'sla', 'public',
   ARRAY['sales_user','support_user','admin']::app_role[], 'pending'),
  ('Support escalation playbook', '/data/knowledge/internal/escalation-playbook.md', 'playbook', 'internal',
   ARRAY['support_user','admin']::app_role[], 'pending'),
  ('Executive incident protocol', '/data/knowledge/restricted/executive-incident.md', 'runbook', 'restricted',
   ARRAY['admin']::app_role[], 'pending');

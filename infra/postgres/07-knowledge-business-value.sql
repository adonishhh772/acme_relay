-- Expand Relay knowledge catalog for business-value RAG (idempotent reseed).

DELETE FROM knowledge_chunks
WHERE document_id IN (SELECT id FROM knowledge_documents);

DELETE FROM knowledge_documents;

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

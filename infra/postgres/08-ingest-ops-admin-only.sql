-- Enterprise: only operations_user + admin may ingest knowledge (not support_user).

DELETE FROM role_permissions rp
USING rbac_roles r, permissions p
WHERE rp.role_id = r.id
  AND rp.permission_id = p.id
  AND r.slug = 'support_user'
  AND p.key = 'ingest_knowledge';

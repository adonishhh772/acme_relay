from auth.rbac import PERMISSIONS
from schemas.enums import Role


def test_all_staff_share_read_permissions() -> None:
    for role in (Role.SALES, Role.SUPPORT, Role.OPERATIONS, Role.ADMIN):
        assert role in PERMISSIONS["read_customer"]
        assert role in PERMISSIONS["read_issues"]
        assert role in PERMISSIONS["manage_tasks"]


def test_operations_permission_matrix() -> None:
    assert Role.OPERATIONS in PERMISSIONS["update_issue"]
    assert Role.OPERATIONS in PERMISSIONS["view_audit"]
    assert Role.OPERATIONS not in PERMISSIONS["manage_users"]
    assert Role.OPERATIONS not in PERMISSIONS["run_evals"]


def test_ingest_knowledge_ops_and_admin_only() -> None:
    assert Role.SUPPORT not in PERMISSIONS["ingest_knowledge"]
    assert Role.SALES not in PERMISSIONS["ingest_knowledge"]
    assert Role.OPERATIONS in PERMISSIONS["ingest_knowledge"]
    assert Role.ADMIN in PERMISSIONS["ingest_knowledge"]

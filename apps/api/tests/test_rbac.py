from auth.rbac import has_permission, requires_hitl, tool_allowed
from schemas.enums import Role


def test_sales_cannot_create_next_action() -> None:
    roles = {Role.SALES}
    assert tool_allowed(roles, "get_open_issues")
    assert not tool_allowed(roles, "create_next_action")
    assert not has_permission(roles, "approve_next_action")


def test_support_can_mutate_with_hitl() -> None:
    roles = {Role.SUPPORT}
    assert tool_allowed(roles, "create_next_action")
    assert requires_hitl("create_next_action")


def test_operations_can_mutate_and_view_audit() -> None:
    roles = {Role.OPERATIONS}
    assert tool_allowed(roles, "update_issue")
    assert tool_allowed(roles, "create_next_action")
    assert has_permission(roles, "view_audit")
    assert has_permission(roles, "mcp_sql")
    assert not has_permission(roles, "approve_next_action")
    assert not has_permission(roles, "manage_users")


def test_admin_can_approve_and_manage() -> None:
    assert tool_allowed({Role.ADMIN}, "approve_next_action")
    assert has_permission({Role.ADMIN}, "manage_users")
    assert has_permission({Role.ADMIN}, "run_evals")


def test_sales_can_use_domain_and_filesystem_mcp() -> None:
    roles = {Role.SALES}
    assert tool_allowed(roles, "domain_relay_get_customer_by_name")
    assert tool_allowed(roles, "filesystem_fs_read_file")
    assert not tool_allowed(roles, "postgres_postgres_query")


def test_support_can_use_postgres_mcp() -> None:
    assert tool_allowed({Role.SUPPORT}, "postgres_postgres_query")
    assert tool_allowed({Role.OPERATIONS}, "postgres_postgres_query")

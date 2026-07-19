from schemas.enums import Role

ALL_STAFF: set[Role] = {Role.SALES, Role.SUPPORT, Role.OPERATIONS, Role.ADMIN}
MUTATORS: set[Role] = {Role.SUPPORT, Role.OPERATIONS, Role.ADMIN}
OPERATORS: set[Role] = {Role.OPERATIONS, Role.ADMIN}

PERMISSIONS: dict[str, set[Role]] = {
    "read_customer": ALL_STAFF,
    "read_issues": ALL_STAFF,
    "read_issue_updates": ALL_STAFF,
    "summarize_issues": ALL_STAFF,
    "recommend_action": MUTATORS,
    "search_knowledge": ALL_STAFF,
    "run_skill": ALL_STAFF,
    "mcp_read": ALL_STAFF,
    "mcp_sql": MUTATORS,
    "update_issue": MUTATORS,
    "create_next_action": MUTATORS,
    "approve_next_action": {Role.ADMIN},
    "ingest_knowledge": MUTATORS,
    "manage_tasks": ALL_STAFF,
    "view_audit": OPERATORS,
    "run_evals": {Role.ADMIN},
    "manage_users": {Role.ADMIN},
    "manage_roles": {Role.ADMIN},
    "manage_organizations": {Role.ADMIN},
}

MCP_TOOL_PREFIX_PERMISSION: dict[str, str] = {
    "domain_": "mcp_read",
    "filesystem_": "mcp_read",
    "postgres_": "mcp_sql",
}

MUTATING_TOOLS = frozenset(
    {"update_issue", "create_next_action", "approve_next_action"}
)

TOOL_PERMISSION: dict[str, str] = {
    "get_customer_profile_by_name": "read_customer",
    "get_open_issues": "read_issues",
    "summarize_issue_history": "summarize_issues",
    "create_next_action": "create_next_action",
    "update_issue": "update_issue",
    "search_knowledge": "search_knowledge",
    "run_escalation_summary_skill": "run_skill",
    "run_sla_breach_assessment_skill": "run_skill",
    "run_issue_triage_skill": "run_skill",
    "run_shift_handoff_skill": "run_skill",
    "approve_next_action": "approve_next_action",
}


def roles_from_claims(realm_roles: list[str]) -> set[Role]:
    mapped: set[Role] = set()
    for role_name in realm_roles:
        try:
            mapped.add(Role(role_name))
        except ValueError:
            continue
    return mapped


def has_permission(roles: set[Role], permission: str) -> bool:
    allowed = PERMISSIONS.get(permission, set())
    return bool(roles & allowed)


def tool_allowed(roles: set[Role], tool_name: str) -> bool:
    permission = TOOL_PERMISSION.get(tool_name)
    if permission is None:
        for prefix, mcp_permission in MCP_TOOL_PREFIX_PERMISSION.items():
            if tool_name.startswith(prefix):
                return has_permission(roles, mcp_permission)
        return Role.ADMIN in roles
    return has_permission(roles, permission)


def requires_hitl(tool_name: str) -> bool:
    return tool_name in MUTATING_TOOLS


def roles_for_knowledge_filter(roles: set[Role]) -> list[str]:
    return [role.value for role in roles]

export type RelayRole = "sales_user" | "support_user" | "operations_user" | "admin";

export function hasRole(roles: string[], role: RelayRole): boolean {
  return roles.includes(role);
}

export function isAdmin(roles: string[]): boolean {
  return hasRole(roles, "admin");
}

export function canSeeApprovals(roles: string[]): boolean {
  return (
    hasRole(roles, "support_user") ||
    hasRole(roles, "operations_user") ||
    hasRole(roles, "admin")
  );
}

export function canSeeAudit(roles: string[]): boolean {
  return hasRole(roles, "operations_user") || hasRole(roles, "admin");
}

export function canSeeGovernance(roles: string[]): boolean {
  return hasRole(roles, "admin");
}

export function canIngest(roles: string[]): boolean {
  return hasRole(roles, "operations_user") || hasRole(roles, "admin");
}

export function canManageUsers(roles: string[]): boolean {
  return hasRole(roles, "admin");
}

export function canRunEvals(roles: string[]): boolean {
  return hasRole(roles, "admin");
}

export function canViewOrgWideInsights(roles: string[]): boolean {
  return hasRole(roles, "operations_user") || hasRole(roles, "admin");
}

export function roleLabel(role: string): string {
  const labels: Record<string, string> = {
    sales_user: "Sales",
    support_user: "Support",
    operations_user: "Operations",
    admin: "Admin",
  };
  return labels[role] ?? role;
}

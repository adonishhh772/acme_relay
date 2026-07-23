import { Shield } from "lucide-react";
import { useEffect, useState } from "react";

import { PageHeader } from "../components/layout/PageHeader";
import { apiFetch } from "../lib/api";
import { roleLabel } from "../lib/rbac";
import { useAuth } from "../providers/AuthProvider";

type Tab = "users" | "rbac" | "orgs";

type UserRow = {
  id: string;
  email: string;
  display_name: string;
  role: string;
  is_active: boolean;
  keycloak_sub?: string | null;
  organization_slug: string | null;
  organization_name?: string | null;
  totp_configured?: boolean;
  mfa_setup_pending?: boolean;
  mfa_status_error?: boolean;
};

type PermissionRow = {
  key: string;
  description: string;
  category: string;
};

type RoleMatrixRow = {
  slug: string;
  name: string;
  keycloak_role_name: string | null;
  is_system: boolean;
  permission_keys: string[];
};

type OrgRow = {
  slug: string;
  display_name: string;
  is_active: boolean;
  user_count: number;
  customer_count: number;
};

type Overview = {
  users: number;
  active_users: number;
  roles: number;
  permissions: number;
  organizations: number;
};

const APP_ROLES = ["sales_user", "support_user", "operations_user", "admin"];

export function AdminPage() {
  const { token } = useAuth();
  const [tab, setTab] = useState<Tab>("rbac");
  const [overview, setOverview] = useState<Overview | null>(null);
  const [users, setUsers] = useState<UserRow[]>([]);
  const [permissions, setPermissions] = useState<PermissionRow[]>([]);
  const [roles, setRoles] = useState<RoleMatrixRow[]>([]);
  const [orgs, setOrgs] = useState<OrgRow[]>([]);
  const [selectedRole, setSelectedRole] = useState<string>("support_user");
  const [draftKeys, setDraftKeys] = useState<string[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function loadAll() {
    if (!token) {
      return;
    }
    setIsLoading(true);
    try {
      const [overviewRes, usersRes, matrixRes, orgsRes] = await Promise.all([
        apiFetch<Overview>("/api/admin/overview", token),
        apiFetch<{ items: UserRow[] }>("/api/admin/users", token),
        apiFetch<{
          permissions: PermissionRow[];
          roles: RoleMatrixRow[];
        }>("/api/admin/rbac-matrix", token),
        apiFetch<{ items: OrgRow[] }>("/api/admin/organizations", token),
      ]);
      setOverview(overviewRes);
      setUsers(usersRes.items);
      setPermissions(matrixRes.permissions);
      setRoles(matrixRes.roles);
      setOrgs(orgsRes.items);
      const current =
        matrixRes.roles.find((role) => role.slug === selectedRole) ??
        matrixRes.roles[0];
      if (current) {
        setSelectedRole(current.slug);
        setDraftKeys(current.permission_keys);
      }
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load admin data");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadAll();
  }, [token]);

  function handleSelectRole(slug: string) {
    setSelectedRole(slug);
    const role = roles.find((item) => item.slug === slug);
    setDraftKeys(role?.permission_keys ?? []);
    setMessage(null);
  }

  function handleTogglePermission(key: string) {
    setDraftKeys((current) =>
      current.includes(key) ? current.filter((item) => item !== key) : [...current, key],
    );
  }

  async function handleSavePermissions() {
    if (!token) {
      return;
    }
    setIsLoading(true);
    setMessage(null);
    try {
      const result = await apiFetch<{ note: string; permission_keys: string[] }>(
        `/api/admin/roles/${selectedRole}/permissions`,
        token,
        {
          method: "PUT",
          body: JSON.stringify({ permission_keys: draftKeys }),
        },
      );
      setMessage(result.note);
      await loadAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save permissions");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleUpdateUser(email: string, patch: { role?: string; is_active?: boolean }) {
    if (!token) {
      return;
    }
    setIsLoading(true);
    try {
      await apiFetch(`/api/admin/users/${encodeURIComponent(email)}`, token, {
        method: "PATCH",
        body: JSON.stringify(patch),
      });
      setMessage(`Updated ${email}`);
      await loadAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update user");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleRequireMfa(row: UserRow) {
    if (!token || !row.keycloak_sub) {
      setError("User has no Keycloak subject — cannot manage MFA.");
      return;
    }
    setIsLoading(true);
    try {
      const result = await apiFetch<{ message: string }>(
        `/api/admin/users/${encodeURIComponent(row.keycloak_sub)}/require-2fa`,
        token,
        { method: "POST" },
      );
      setMessage(result.message);
      setError(null);
      await loadAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to require MFA");
      setIsLoading(false);
    }
  }

  async function handleDisableMfa(row: UserRow) {
    if (!token || !row.keycloak_sub) {
      setError("User has no Keycloak subject — cannot manage MFA.");
      return;
    }
    setIsLoading(true);
    try {
      const result = await apiFetch<{ message: string }>(
        `/api/admin/users/${encodeURIComponent(row.keycloak_sub)}/disable-2fa`,
        token,
        { method: "POST" },
      );
      setMessage(result.message);
      setError(null);
      await loadAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to disable MFA");
      setIsLoading(false);
    }
  }

  function mfaLabel(row: UserRow): string {
    if (row.mfa_status_error) {
      return "Unknown";
    }
    if (row.totp_configured) {
      return "On";
    }
    if (row.mfa_setup_pending) {
      return "Pending";
    }
    return "Off";
  }

  const categories = Array.from(new Set(permissions.map((item) => item.category)));

  return (
    <div data-testid="admin-page" className="p-6 lg:p-8">
      <PageHeader
        icon={Shield}
        title="Admin"
        description="Manage desk users, the RBAC permission catalog, and tenant organisations. Keycloak still issues JWTs — keep realm role names aligned with these slugs."
      />

      {error ? <p className="error-text">{error}</p> : null}
      {message ? (
        <p className="mb-4 rounded-xl border border-cyan-200 bg-cyan-50 px-3 py-2 text-sm text-cyan-950">
          {message}
        </p>
      ) : null}

      <div className="mb-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        {[
          ["Users", overview?.users],
          ["Active", overview?.active_users],
          ["Roles", overview?.roles],
          ["Permissions", overview?.permissions],
          ["Orgs", overview?.organizations],
        ].map(([label, value]) => (
          <div key={String(label)} className="card p-4">
            <p className="section-label">{label}</p>
            <strong className="mt-1 block font-display text-2xl">{value ?? "—"}</strong>
          </div>
        ))}
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        {(
          [
            ["rbac", "RBAC control"],
            ["users", "Users"],
            ["orgs", "Organisations"],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            type="button"
            className={tab === id ? "btn-primary" : "btn-secondary"}
            onClick={() => setTab(id)}
          >
            {label}
          </button>
        ))}
        <button type="button" className="btn-secondary" onClick={() => void loadAll()} disabled={isLoading}>
          Refresh
        </button>
      </div>

      {tab === "rbac" ? (
        <div className="grid gap-4 lg:grid-cols-[220px_1fr]">
          <aside className="card p-3">
            <p className="section-label mb-2 px-2">Roles</p>
            {roles.map((role) => (
              <button
                key={role.slug}
                type="button"
                className={
                  selectedRole === role.slug
                    ? "mb-1 w-full rounded-lg bg-cyan-500/15 px-3 py-2 text-left text-sm font-medium text-cyan-900"
                    : "mb-1 w-full rounded-lg px-3 py-2 text-left text-sm text-ink-secondary hover:bg-surface-muted"
                }
                onClick={() => handleSelectRole(role.slug)}
              >
                <span className="block font-medium">{role.name}</span>
                <span className="font-mono text-[11px] text-ink-muted">{role.slug}</span>
              </button>
            ))}
          </aside>
          <section className="card p-5">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="font-display text-lg font-semibold">
                  Permissions for {roleLabel(selectedRole)}
                </h2>
                <p className="text-sm text-ink-secondary">
                  Toggle catalog permissions, then save. This updates Postgres{" "}
                  <code>role_permissions</code>.
                </p>
              </div>
              <button
                type="button"
                className="btn-primary"
                disabled={isLoading}
                onClick={() => void handleSavePermissions()}
              >
                Save RBAC
              </button>
            </div>
            <div className="space-y-5">
              {categories.map((category) => (
                <div key={category}>
                  <p className="section-label mb-2">{category}</p>
                  <div className="grid gap-2 md:grid-cols-2">
                    {permissions
                      .filter((permission) => permission.category === category)
                      .map((permission) => {
                        const checked = draftKeys.includes(permission.key);
                        return (
                          <label
                            key={permission.key}
                            className="flex cursor-pointer items-start gap-3 rounded-xl border border-surface-border px-3 py-2.5 hover:bg-surface-muted"
                          >
                            <input
                              type="checkbox"
                              className="mt-1"
                              checked={checked}
                              onChange={() => handleTogglePermission(permission.key)}
                            />
                            <span>
                              <span className="block font-mono text-xs text-ink-primary">
                                {permission.key}
                              </span>
                              <span className="text-sm text-ink-secondary">
                                {permission.description}
                              </span>
                            </span>
                          </label>
                        );
                      })}
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      ) : null}

      {tab === "users" ? (
        <div className="card overflow-hidden">
          <table className="data-table mt-0" data-testid="admin-users-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Role</th>
                <th>Org</th>
                <th>Status</th>
                <th>MFA</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((row) => (
                <tr key={row.email}>
                  <td>{row.display_name}</td>
                  <td className="mono">{row.email}</td>
                  <td>
                    <select
                      className="form-input py-1.5"
                      value={row.role}
                      onChange={(event) =>
                        void handleUpdateUser(row.email, { role: event.target.value })
                      }
                    >
                      {APP_ROLES.map((role) => (
                        <option key={role} value={role}>
                          {roleLabel(role)}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td>{row.organization_name ?? row.organization_slug ?? "—"}</td>
                  <td>
                    <span className={row.is_active ? "pill" : "text-xs text-ink-muted"}>
                      {row.is_active ? "Active" : "Disabled"}
                    </span>
                  </td>
                  <td>
                    <span
                      className={
                        row.totp_configured
                          ? "text-sm font-medium text-relay-mint"
                          : row.mfa_setup_pending
                            ? "text-sm font-medium text-relay-warn"
                            : "text-sm text-ink-muted"
                      }
                      data-testid={`admin-mfa-status-${row.email}`}
                    >
                      {mfaLabel(row)}
                    </span>
                  </td>
                  <td>
                    <div className="flex flex-wrap gap-2">
                      <button
                        type="button"
                        className="btn-secondary !px-3 !py-1.5 text-xs"
                        onClick={() =>
                          void handleUpdateUser(row.email, { is_active: !row.is_active })
                        }
                      >
                        {row.is_active ? "Disable" : "Enable"}
                      </button>
                      {row.keycloak_sub ? (
                        <>
                          {!row.totp_configured ? (
                            <button
                              type="button"
                              className="btn-secondary !px-3 !py-1.5 text-xs"
                              onClick={() => void handleRequireMfa(row)}
                              disabled={isLoading || row.mfa_setup_pending}
                              data-testid={`admin-require-mfa-${row.email}`}
                            >
                              {row.mfa_setup_pending ? "MFA pending" : "Require MFA"}
                            </button>
                          ) : null}
                          {row.totp_configured || row.mfa_setup_pending ? (
                            <button
                              type="button"
                              className="btn-secondary !px-3 !py-1.5 text-xs"
                              onClick={() => void handleDisableMfa(row)}
                              disabled={isLoading}
                              data-testid={`admin-disable-mfa-${row.email}`}
                            >
                              Disable MFA
                            </button>
                          ) : null}
                        </>
                      ) : (
                        <span className="text-xs text-ink-muted">No Keycloak link</span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="border-t border-surface-border px-4 py-3 text-xs text-ink-muted">
            Require MFA flags the user for authenticator setup on next login. Disable MFA removes
            their OTP credential in Keycloak. Role changes update the app directory — matching
            Keycloak realm roles are still required for JWT-gated tools.
          </p>
        </div>
      ) : null}

      {tab === "orgs" ? (
        <div className="grid gap-4 md:grid-cols-2">
          {orgs.map((org) => (
            <article key={org.slug} className="card p-5">
              <p className="section-label">{org.is_active ? "Active tenant" : "Inactive"}</p>
              <h2 className="mt-1 font-display text-lg font-semibold">{org.display_name}</h2>
              <p className="mono text-xs text-ink-muted">{org.slug}</p>
              <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
                <div>
                  <dt className="text-ink-muted">Users</dt>
                  <dd className="font-semibold">{org.user_count}</dd>
                </div>
                <div>
                  <dt className="text-ink-muted">Customers</dt>
                  <dd className="font-semibold">{org.customer_count}</dd>
                </div>
              </dl>
            </article>
          ))}
        </div>
      ) : null}
    </div>
  );
}

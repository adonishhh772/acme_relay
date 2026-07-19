import { useEffect, useState } from "react";

import { apiFetch } from "../lib/api";
import { useAuth } from "../providers/AuthProvider";

type UserRow = {
  email: string;
  display_name: string;
  role: string;
  is_active: boolean;
  organization_slug: string | null;
};

type RoleRow = {
  slug: string;
  name: string;
  description: string | null;
  keycloak_role_name: string | null;
};

export function AdminPage() {
  const { token } = useAuth();
  const [users, setUsers] = useState<UserRow[]>([]);
  const [roles, setRoles] = useState<RoleRow[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    void Promise.all([
      apiFetch<{ items: UserRow[] }>("/api/admin/users", token),
      apiFetch<{ items: RoleRow[] }>("/api/admin/roles", token),
    ])
      .then(([usersResponse, rolesResponse]) => {
        setUsers(usersResponse.items);
        setRoles(rolesResponse.items);
        setError(null);
      })
      .catch((err: Error) => setError(err.message));
  }, [token]);

  return (
    <div data-testid="admin-page">
      <h1>Admin</h1>
      <p className="page-lead">Users, system roles, and tenant organisations.</p>
      {error ? <p className="error-text">{error}</p> : null}
      <h2>Users</h2>
      <table className="data-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Role</th>
            <th>Org</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => (
            <tr key={user.email}>
              <td>{user.display_name}</td>
              <td>{user.email}</td>
              <td>{user.role}</td>
              <td>{user.organization_slug ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <h2>Roles</h2>
      <table className="data-table">
        <thead>
          <tr>
            <th>Slug</th>
            <th>Name</th>
            <th>Keycloak</th>
          </tr>
        </thead>
        <tbody>
          {roles.map((role) => (
            <tr key={role.slug}>
              <td>{role.slug}</td>
              <td>{role.name}</td>
              <td>{role.keycloak_role_name ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

import { useEffect, useState } from "react";

import { apiFetch } from "../lib/api";
import { roleLabel } from "../lib/rbac";
import { useAuth } from "../providers/AuthProvider";

type MeResponse = {
  sub: string;
  username: string;
  email: string;
  roles: string[];
  permissions: string[];
  organization: string;
};

export function AccountProfilePage() {
  const { token } = useAuth();
  const [me, setMe] = useState<MeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    void apiFetch<MeResponse>("/api/account/me", token)
      .then((data) => {
        setMe(data);
        setError(null);
      })
      .catch((err: Error) => setError(err.message));
  }, [token]);

  return (
    <div data-testid="account-profile-page">
      <h1>Profile</h1>
      {error ? <p className="error-text">{error}</p> : null}
      <dl className="detail-list">
        <div>
          <dt>Username</dt>
          <dd>{me?.username ?? "—"}</dd>
        </div>
        <div>
          <dt>Email</dt>
          <dd>{me?.email || "—"}</dd>
        </div>
        <div>
          <dt>Organisation</dt>
          <dd>{me?.organization ?? "—"}</dd>
        </div>
        <div>
          <dt>Roles</dt>
          <dd>{(me?.roles ?? []).map(roleLabel).join(", ") || "—"}</dd>
        </div>
        <div>
          <dt>Permissions</dt>
          <dd className="mono">{(me?.permissions ?? []).join(", ") || "—"}</dd>
        </div>
      </dl>
    </div>
  );
}

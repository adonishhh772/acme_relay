import { useEffect, useState } from "react";

import { apiFetch } from "../lib/api";
import { useAuth } from "../providers/AuthProvider";

type SecurityInfo = {
  totp_supported: boolean;
  account_console_url: string;
  hint: string;
};

export function AccountSecurityPage() {
  const { token } = useAuth();
  const [info, setInfo] = useState<SecurityInfo | null>(null);

  useEffect(() => {
    if (!token) return;
    void apiFetch<SecurityInfo>("/api/account/security", token).then(setInfo);
  }, [token]);

  return (
    <div data-testid="account-security-page">
      <h1>Security</h1>
      <p className="page-lead">{info?.hint ?? "Loading security settings…"}</p>
      <ul>
        <li>TOTP / MFA: {info?.totp_supported ? "Supported via Keycloak" : "—"}</li>
      </ul>
      {info?.account_console_url ? (
        <a className="btn" href={info.account_console_url} target="_blank" rel="noreferrer">
          Open Keycloak account console
        </a>
      ) : null}
    </div>
  );
}

import { KeyRound } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { PageHeader } from "../components/layout/PageHeader";
import { apiFetch } from "../lib/api";
import { useAuth } from "../providers/AuthProvider";

type SecurityInfo = {
  username: string;
  email: string;
  totp_supported: boolean;
  totp_configured: boolean;
  required_actions: string[];
  setup_pending: boolean;
  steps: string[];
  hint: string;
};

type Require2FaResponse = {
  message: string;
  totp_configured: boolean;
  setup_pending: boolean;
  required_actions: string[];
};

type Sync2FaResponse = {
  message: string;
  totp_configured: boolean;
  setup_pending: boolean;
  required_actions: string[];
};

export function AccountSecurityPage() {
  const { token, logout } = useAuth();
  const [info, setInfo] = useState<SecurityInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isWorking, setIsWorking] = useState(false);

  const refresh = useCallback(async () => {
    if (!token) {
      return;
    }
    setIsLoading(true);
    try {
      const data = await apiFetch<SecurityInfo>("/api/account/security", token);
      setInfo(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load security status");
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    function handleFocus() {
      void refresh();
    }
    window.addEventListener("focus", handleFocus);
    return () => window.removeEventListener("focus", handleFocus);
  }, [refresh]);

  async function handleEnableMfa() {
    if (!token) {
      return;
    }
    setIsWorking(true);
    setMessage(null);
    try {
      const result = await apiFetch<Require2FaResponse>("/api/account/require-2fa", token, {
        method: "POST",
      });
      setMessage(result.message);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to enable MFA");
    } finally {
      setIsWorking(false);
    }
  }

  async function handleConfirmMfa() {
    if (!token) {
      return;
    }
    setIsWorking(true);
    setMessage(null);
    try {
      const result = await apiFetch<Sync2FaResponse>("/api/account/sync-2fa", token, {
        method: "POST",
      });
      setMessage(result.message);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to confirm MFA");
    } finally {
      setIsWorking(false);
    }
  }

  function handleSignOutToSetup() {
    logout();
  }

  const totpConfigured = info?.totp_configured ?? false;
  const setupPending = info?.setup_pending ?? false;

  return (
    <div data-testid="account-security-page" className="p-6 lg:p-8">
      <PageHeader
        icon={KeyRound}
        title="Security"
        description="Enable MFA and manage authenticator status from Relay. Identity credentials stay in Keycloak; you do not need the account console."
      />

      {error ? <p className="error-text mb-4">{error}</p> : null}
      {message ? <p className="mb-4 text-sm text-relay-mint">{message}</p> : null}

      <div className="mb-4 flex flex-wrap gap-2">
        <Link className="btn-secondary" to="/account/profile">
          Back to profile
        </Link>
        <button
          type="button"
          className="btn-secondary"
          onClick={() => void refresh()}
          disabled={isLoading}
        >
          Refresh status
        </button>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="card p-5" data-testid="account-2fa-section">
          <p className="section-label">Multi-factor authentication</p>
          <h2 className="mt-2 font-display text-lg font-semibold">
            {totpConfigured
              ? "Authenticator enabled"
              : setupPending
                ? "Setup pending — sign in again"
                : "Authenticator not enabled"}
          </h2>
          <p className="mt-2 text-sm text-ink-secondary">{info?.hint}</p>
          <ol className="mt-4 list-decimal space-y-2 pl-5 text-sm text-ink-secondary">
            {(info?.steps ?? []).map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
          <div className="mt-5 flex flex-wrap gap-2">
            {!totpConfigured ? (
              <button
                type="button"
                className="btn-primary"
                onClick={() => void handleEnableMfa()}
                disabled={isWorking || setupPending}
                data-testid="enable-mfa"
              >
                {setupPending ? "MFA flagged" : "Enable MFA"}
              </button>
            ) : null}
            {setupPending || totpConfigured ? (
              <button
                type="button"
                className="btn-secondary"
                onClick={() => void handleConfirmMfa()}
                disabled={isWorking}
                data-testid="confirm-mfa"
              >
                Confirm MFA setup
              </button>
            ) : null}
            {setupPending ? (
              <button
                type="button"
                className="btn-secondary"
                onClick={handleSignOutToSetup}
                data-testid="sign-out-for-mfa"
              >
                Sign out to finish setup
              </button>
            ) : null}
          </div>
        </section>

        <section className="card p-5">
          <p className="section-label">Session context</p>
          <dl className="mt-3 space-y-3 text-sm">
            <div>
              <dt className="text-ink-muted">Signed in as</dt>
              <dd className="font-semibold">{info?.username ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-ink-muted">Email</dt>
              <dd>{info?.email || "—"}</dd>
            </div>
            <div>
              <dt className="text-ink-muted">MFA status</dt>
              <dd>
                {totpConfigured ? "Active" : setupPending ? "Pending setup" : "Off"}
              </dd>
            </div>
          </dl>
          <div className="mt-5 rounded-xl bg-surface-muted px-3 py-3 text-sm text-ink-secondary">
            After MFA is active, your next login will ask for the authenticator code. Passwords and
            TOTP secrets are never stored in Relay itself.
          </div>
        </section>
      </div>
    </div>
  );
}

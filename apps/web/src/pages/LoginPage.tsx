import { ORGANISATION_NAME, PRODUCT_NAME, SHELL_NAME } from "../constants/branding";
import { useAuth } from "../providers/AuthProvider";

export function LoginPage() {
  const { login } = useAuth();

  return (
    <div className="login-screen" data-testid="login-page">
      <div className="login-card">
        <div className="brand-mark">{PRODUCT_NAME}</div>
        <h1>{SHELL_NAME}</h1>
        <p style={{ color: "var(--ink-muted)", marginTop: 0 }}>
          Secure ops assistant for {ORGANISATION_NAME}. Sign in with Keycloak — MFA
          (TOTP) can be required per realm policy.
        </p>
        <button type="button" className="btn" data-testid="login-sign-in" onClick={login}>
          Continue with Keycloak
        </button>
        <p className="mono" style={{ marginTop: "1.5rem", fontSize: "0.8rem", color: "var(--ink-muted)" }}>
          Demo: alice/alice123 · bob/bob123 · dana/dana123 · admin/admin123
        </p>
      </div>
    </div>
  );
}

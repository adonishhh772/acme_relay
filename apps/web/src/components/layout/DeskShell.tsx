import { NavLink, Outlet } from "react-router-dom";

import { ORGANISATION_NAME, PRODUCT_NAME, SHELL_NAME } from "../../constants/branding";
import {
  canManageUsers,
  canRunEvals,
  canSeeApprovals,
  canSeeAudit,
  canSeeGovernance,
  roleLabel,
} from "../../lib/rbac";
import { useAuth } from "../../providers/AuthProvider";

function navClass({ isActive }: { isActive: boolean }): string {
  return isActive ? "nav-link active" : "nav-link";
}

export function DeskShell() {
  const { username, roles, logout } = useAuth();

  function handleLogout() {
    logout();
  }

  return (
    <div className="app-shell" data-testid="desk-shell">
      <aside className="sidebar">
        <div className="brand-mark">{PRODUCT_NAME}</div>
        <p className="brand-sub">
          {SHELL_NAME}
          <br />
          {ORGANISATION_NAME}
        </p>
        <nav aria-label="Primary">
          <div className="nav-section">Work</div>
          <NavLink to="/assistant" className={navClass}>
            Assistant
          </NavLink>
          <NavLink to="/dashboard" className={navClass}>
            Dashboard
          </NavLink>
          <NavLink to="/customers" className={navClass}>
            Customers
          </NavLink>
          <NavLink to="/issues" className={navClass}>
            Issues
          </NavLink>
          <NavLink to="/tasks" className={navClass}>
            Tasks
          </NavLink>
          {canSeeApprovals(roles) ? (
            <NavLink to="/approvals" className={navClass}>
              Approvals
            </NavLink>
          ) : null}
          <NavLink to="/knowledge" className={navClass}>
            Knowledge
          </NavLink>

          <div className="nav-section">System</div>
          {canRunEvals(roles) ? (
            <NavLink to="/evaluations" className={navClass}>
              Evaluations
            </NavLink>
          ) : null}
          {canSeeAudit(roles) ? (
            <NavLink to="/audit" className={navClass}>
              Audit
            </NavLink>
          ) : null}
          {canSeeGovernance(roles) ? (
            <NavLink to="/governance" className={navClass}>
              AI Governance
            </NavLink>
          ) : null}
          {canManageUsers(roles) ? (
            <NavLink to="/admin" className={navClass}>
              Admin
            </NavLink>
          ) : null}
          <NavLink to="/settings" className={navClass}>
            Settings
          </NavLink>

          <div className="nav-section">Account</div>
          <NavLink to="/account/profile" className={navClass}>
            Profile
          </NavLink>
          <NavLink to="/account/security" className={navClass}>
            Security
          </NavLink>

          <div className="nav-section">Trust &amp; Help</div>
          <NavLink to="/trust/privacy" className={navClass}>
            Privacy
          </NavLink>
          <NavLink to="/trust/ai-information" className={navClass}>
            AI notice
          </NavLink>
          <NavLink to="/trust/security" className={navClass}>
            Security
          </NavLink>
          <NavLink to="/help/guide" className={navClass}>
            Guide
          </NavLink>
          <NavLink to="/help/faq" className={navClass}>
            FAQ
          </NavLink>
        </nav>
        <div style={{ marginTop: "2rem" }}>
          <div className="mono" style={{ fontSize: "0.8rem", marginBottom: "0.35rem" }}>
            {username}
          </div>
          <div className="mono" style={{ fontSize: "0.75rem", marginBottom: "0.5rem", color: "var(--ink-muted)" }}>
            {roles.map(roleLabel).join(" · ")}
          </div>
          <button type="button" className="btn secondary" onClick={handleLogout}>
            Sign out
          </button>
        </div>
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}

import {
  AlertCircle,
  BookOpen,
  Bot,
  Building2,
  CheckSquare,
  CircleHelp,
  ClipboardList,
  FileText,
  Gauge,
  LayoutDashboard,
  ListTodo,
  LogOut,
  ScrollText,
  Settings,
  Shield,
  ShieldCheck,
  UserCog,
} from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";

import { RelayLogo } from "../brand/RelayLogo";
import { EvalRunBanner } from "./EvalRunBanner";
import {
  canManageUsers,
  canRunEvals,
  canSeeApprovals,
  canSeeAudit,
  canSeeGovernance,
  roleLabel,
} from "../../lib/rbac";
import { cn } from "../../lib/cn";
import { useEvalRunMonitor } from "../../hooks/useEvalRunMonitor";
import { useAuth } from "../../providers/AuthProvider";

function navClass({ isActive }: { isActive: boolean }): string {
  return cn("nav-item", isActive && "nav-item-active");
}

export function DeskShell() {
  const { username, roles, logout, token } = useAuth();
  const { runStatus, isRunning } = useEvalRunMonitor(token, roles);

  function handleLogout() {
    logout();
  }

  return (
    <div className="flex h-screen bg-surface-page" data-testid="desk-shell">
      <aside className="hidden h-full w-60 shrink-0 flex-col bg-relay-sidebar text-white lg:flex">
        <div className="border-b border-white/10 px-4 py-5">
          <RelayLogo size="sm" variant="light" showTagline={false} to="/assistant" />
        </div>
        <nav className="flex-1 space-y-5 overflow-y-auto p-3 pt-4" aria-label="Primary">
          <div>
            <p className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
              Desk
            </p>
            <NavLink to="/assistant" className={navClass}>
              <Bot className="h-4 w-4" />
              Assistant
            </NavLink>
            <NavLink to="/dashboard" className={navClass}>
              <LayoutDashboard className="h-4 w-4" />
              Dashboard
            </NavLink>
            <NavLink to="/customers" className={navClass}>
              <Building2 className="h-4 w-4" />
              Customers
            </NavLink>
            <NavLink to="/issues" className={navClass}>
              <AlertCircle className="h-4 w-4" />
              Issues
            </NavLink>
            <NavLink to="/tasks" className={navClass}>
              <ListTodo className="h-4 w-4" />
              Tasks
            </NavLink>
            <NavLink to="/knowledge" className={navClass}>
              <FileText className="h-4 w-4" />
              Knowledge
            </NavLink>
            {canSeeApprovals(roles) ? (
              <NavLink to="/approvals" className={navClass}>
                <CheckSquare className="h-4 w-4" />
                Approvals
              </NavLink>
            ) : null}
          </div>

          <div>
            <p className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
              Control
            </p>
            {canRunEvals(roles) ? (
              <NavLink to="/evaluations" className={navClass}>
                <Gauge className="h-4 w-4" />
                Evaluations
                {isRunning ? (
                  <span
                    className="ml-auto h-2 w-2 rounded-full bg-relay-cyan"
                    aria-label="Suite running"
                  />
                ) : null}
              </NavLink>
            ) : null}
            {canSeeAudit(roles) ? (
              <NavLink to="/audit" className={navClass}>
                <ScrollText className="h-4 w-4" />
                Audit
              </NavLink>
            ) : null}
            {canSeeGovernance(roles) ? (
              <NavLink to="/governance" className={navClass}>
                <ShieldCheck className="h-4 w-4" />
                Governance
              </NavLink>
            ) : null}
            {canManageUsers(roles) ? (
              <NavLink to="/admin" className={navClass}>
                <UserCog className="h-4 w-4" />
                Admin
              </NavLink>
            ) : null}
            <NavLink to="/settings" className={navClass}>
              <Settings className="h-4 w-4" />
              Settings
            </NavLink>
          </div>

          <div>
            <p className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
              You
            </p>
            <NavLink to="/account/profile" className={navClass}>
              <ClipboardList className="h-4 w-4" />
              Profile
            </NavLink>
            <NavLink to="/account/security" className={navClass}>
              <Shield className="h-4 w-4" />
              Security
            </NavLink>
            <NavLink to="/trust/privacy" className={navClass}>
              <BookOpen className="h-4 w-4" />
              Privacy
            </NavLink>
            <NavLink to="/trust/ai-information" className={navClass}>
              <Shield className="h-4 w-4" />
              AI notice
            </NavLink>
            <NavLink to="/help/guide" className={navClass}>
              <CircleHelp className="h-4 w-4" />
              Guide
            </NavLink>
            <NavLink to="/help/faq" className={navClass}>
              <CircleHelp className="h-4 w-4" />
              FAQ
            </NavLink>
          </div>
        </nav>
        <div className="border-t border-white/10 p-4">
          <p className="truncate text-sm font-medium text-white">{username}</p>
          <p className="mt-0.5 font-mono text-[11px] text-slate-400">
            {roles.map(roleLabel).join(" · ")}
          </p>
          <button
            type="button"
            className="mt-3 inline-flex items-center gap-2 text-sm text-slate-300 transition hover:text-white"
            onClick={handleLogout}
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 items-center justify-between border-b border-surface-border bg-white/90 px-4 backdrop-blur lg:hidden">
          <RelayLogo size="sm" showTagline={false} to="/assistant" />
          <button type="button" className="btn-ghost" onClick={handleLogout}>
            <LogOut className="h-4 w-4" />
          </button>
        </header>
        {isRunning && runStatus ? <EvalRunBanner runStatus={runStatus} /> : null}
        <main className="min-h-0 flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

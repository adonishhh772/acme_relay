import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";

import { RelayLogo } from "../components/brand/RelayLogo";
import { ORGANISATION_NAME } from "../constants/branding";
import { useAuth } from "../providers/AuthProvider";

const demoUsers = [
  { user: "alice", pass: "alice123", role: "Sales" },
  { user: "bob", pass: "bob123", role: "Support" },
  { user: "dana", pass: "dana123", role: "Operations" },
  { user: "admin", pass: "admin123", role: "Admin" },
];

export function LoginPage() {
  const { login } = useAuth();

  function handleSignIn() {
    login();
  }

  return (
    <div className="relative min-h-screen overflow-hidden bg-relay-mesh" data-testid="login-page">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-64 bg-gradient-to-b from-cyan-500/10 to-transparent" />
      <div className="relative mx-auto flex min-h-screen max-w-lg flex-col justify-center px-6 py-12">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35 }}
          className="card p-8 shadow-soft"
        >
          <RelayLogo size="lg" />
          <h1 className="mt-8 font-display text-3xl font-semibold tracking-tight text-ink-primary">
            Sign in to keep ops moving
          </h1>
          <p className="mt-3 text-sm leading-relaxed text-ink-secondary">
            {ORGANISATION_NAME} staff authenticate via Keycloak. Relay streams tool progress
            and verifies answers against evidence before you act.
          </p>

          <button
            type="button"
            className="btn-primary mt-8 w-full"
            data-testid="login-sign-in"
            onClick={handleSignIn}
          >
            Continue with Keycloak
            <ArrowRight className="h-4 w-4" />
          </button>

          <div className="mt-6 rounded-xl border border-cyan-200 bg-cyan-50 px-4 py-3 text-sm text-cyan-950">
            Local demo only — seeded users below. Enable MFA from Profile → Security when you want TOTP.
          </div>

          <ul className="mt-5 space-y-2">
            {demoUsers.map((demo) => (
              <li
                key={demo.user}
                className="flex items-center justify-between rounded-xl bg-surface-muted px-3 py-2.5"
              >
                <span className="font-mono text-sm text-ink-primary">
                  {demo.user} / {demo.pass}
                </span>
                <span className="text-xs font-medium text-ink-muted">{demo.role}</span>
              </li>
            ))}
          </ul>
        </motion.div>
      </div>
    </div>
  );
}

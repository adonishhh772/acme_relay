import { Bot, Lock, ShieldCheck } from "lucide-react";
import { Link } from "react-router-dom";

import { PageHeader } from "../components/layout/PageHeader";

export function PrivacyPolicyPage() {
  return (
    <div data-testid="trust-privacy-page" className="space-y-6 p-6 lg:p-8">
      <PageHeader
        icon={Lock}
        title="Privacy"
        description="How Relay handles operational and identity data for authenticated Acme staff in this assessment demo."
      />

      <section className="card border-l-4 border-l-relay-cyan p-5">
        <p className="section-label">Summary</p>
        <p className="mt-2 text-sm text-ink-secondary">
          Relay is an internal Command Desk for Acme staff. It processes desk and chat data needed
          to operate the assistant. It does not sell personal data, and it does not store passwords
          — identity is delegated to Keycloak.
        </p>
      </section>

      <section className="card p-5">
        <h2 className="font-display text-lg font-semibold">Who this applies to</h2>
        <p className="mt-2 text-sm text-ink-secondary">
          Authenticated Acme staff using Relay (sales, support, operations, admin). Customer
          account records in the desk are business operational data used to resolve cases — not a
          consumer product privacy notice for end customers.
        </p>
      </section>

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="card p-5">
          <h2 className="font-display text-lg font-semibold">What we process</h2>
          <ul className="mt-3 list-disc space-y-1.5 pl-5 text-sm text-ink-secondary">
            <li>
              Customer / case records in PostgreSQL (e.g. VaultLedger, Nexus Freight, Aurora Bank
              demo accounts)
            </li>
            <li>Chat queries, tool results, and groundedness outcomes on agent runs</li>
            <li>Tasks, approvals, and audit rows tied to desk actions</li>
            <li>Keycloak identity attributes (username, email, realm roles)</li>
            <li>Knowledge document chunks with role-based access metadata</li>
          </ul>
        </section>
        <section className="card p-5">
          <h2 className="font-display text-lg font-semibold">What we do not do</h2>
          <ul className="mt-3 list-disc space-y-1.5 pl-5 text-sm text-ink-secondary">
            <li>Store passwords in Relay — Keycloak owns credentials and MFA</li>
            <li>
              Expose restricted knowledge chunks to roles outside <code>allowed_roles</code>
            </li>
            <li>Send full database dumps to the LLM — only tool-scoped payloads</li>
            <li>Use desk data for advertising or sell it to third parties</li>
          </ul>
        </section>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="card p-5">
          <h2 className="font-display text-lg font-semibold">Why we process it</h2>
          <ul className="mt-3 list-disc space-y-1.5 pl-5 text-sm text-ink-secondary">
            <li>Operate the desk assistant and grounded answers</li>
            <li>Enforce RBAC, HITL approvals, and auditability</li>
            <li>Support account management and case investigation workflows</li>
            <li>Debug and improve reliability via observability (traces, metrics, errors)</li>
          </ul>
        </section>
        <section className="card p-5">
          <h2 className="font-display text-lg font-semibold">Who can access it</h2>
          <ul className="mt-3 list-disc space-y-1.5 pl-5 text-sm text-ink-secondary">
            <li>You — within the permissions of your JWT roles</li>
            <li>Admins — users, RBAC catalog, and broader desk visibility as configured</li>
            <li>
              Platform operators — Postgres, Keycloak, and observability services in the Compose /
              deploy environment
            </li>
            <li>
              Model providers — only the tool-scoped content included in a given agent request
            </li>
          </ul>
        </section>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="card p-5">
          <h2 className="font-display text-lg font-semibold">Retention (demo)</h2>
          <p className="mt-2 text-sm text-ink-secondary">
            This assessment stack keeps chat/audit/desk data in local Postgres for the life of the
            demo environment. Reseeding or tearing down Compose volumes clears seeded and runtime
            data. Production deployments should define explicit retention and deletion policies
            before go-live.
          </p>
        </section>
        <section className="card p-5">
          <h2 className="font-display text-lg font-semibold">Your responsibilities</h2>
          <ul className="mt-3 list-disc space-y-1.5 pl-5 text-sm text-ink-secondary">
            <li>Only query and share data needed for the desk task</li>
            <li>Do not paste unrelated personal data, secrets, or credentials into chat</li>
            <li>Respect role boundaries — do not attempt to bypass RBAC or HITL</li>
            <li>Raise access or data concerns with your desk lead / admin</li>
          </ul>
        </section>
      </div>

      <section className="card p-5">
        <h2 className="font-display text-lg font-semibold">Related pages</h2>
        <ul className="mt-3 space-y-2 text-sm text-ink-secondary">
          <li>
            <Link className="text-relay-cyan underline" to="/trust/ai-information">
              AI information notice
            </Link>{" "}
            — how the agent works and its limits
          </li>
          <li>
            <Link className="text-relay-cyan underline" to="/trust/security">
              Security &amp; data protection
            </Link>{" "}
            — auth, authorisation, audit, network
          </li>
          <li>
            <Link className="text-relay-cyan underline" to="/account/security">
              Account security
            </Link>{" "}
            — MFA enable / confirm in Relay
          </li>
          <li>
            <Link className="text-relay-cyan underline" to="/audit">
              Audit trail
            </Link>
            {" · "}
            <Link className="text-relay-cyan underline" to="/settings">
              Settings
            </Link>
          </li>
        </ul>
      </section>
    </div>
  );
}

export function AiInformationNoticePage() {
  return (
    <div data-testid="trust-ai-page" className="space-y-6 p-6 lg:p-8">
      <PageHeader
        icon={Bot}
        title="AI information notice"
        description="Transparency notice for Relay — an agentic desk assistant. Treat answers as tool-backed drafts under human oversight, not unsupervised truth."
      />

      <section className="card border-l-4 border-l-relay-cyan p-5">
        <p className="section-label">Disclosure</p>
        <p className="mt-2 text-sm text-ink-secondary">
          You are interacting with <strong className="text-ink-primary">Relay</strong>, an AI
          system (LLM + tools) operated for authenticated Acme staff. Outputs can be incomplete or
          incorrect. Verify material claims against desk data, Approvals, and Audit before you act.
        </p>
      </section>

      <section className="card p-5">
        <h2 className="font-display text-lg font-semibold">Purpose &amp; intended use</h2>
        <p className="mt-2 text-sm text-ink-secondary">
          Relay helps internal staff investigate accounts and cases, summarise open work, and stage
          next actions for human approval. It is{" "}
          <strong className="text-ink-primary">not</strong> authorised for unsupervised
          customer-facing decisions, legal or financial advice, or bypassing RBAC / HITL controls.
        </p>
        <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-xs font-medium uppercase tracking-wide text-ink-muted">System</dt>
            <dd className="mt-1 text-ink-primary">Relay Command Desk assistant</dd>
          </div>
          <div>
            <dt className="text-xs font-medium uppercase tracking-wide text-ink-muted">Type</dt>
            <dd className="mt-1 text-ink-primary">Agentic LLM with native, MCP, and skill tools</dd>
          </div>
          <div>
            <dt className="text-xs font-medium uppercase tracking-wide text-ink-muted">Audience</dt>
            <dd className="mt-1 text-ink-primary">Authenticated Acme staff (role-scoped)</dd>
          </div>
          <div>
            <dt className="text-xs font-medium uppercase tracking-wide text-ink-muted">Status</dt>
            <dd className="mt-1 text-ink-primary">Assessment / demo deployment</dd>
          </div>
        </dl>
      </section>

      <section className="card p-5">
        <h2 className="font-display text-lg font-semibold">How answers are produced</h2>
        <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm text-ink-secondary">
          <li>Your JWT roles determine the allowed toolbelt and knowledge ACL.</li>
          <li>LangGraph ReAct selects native, MCP, or skill tools to gather evidence.</li>
          <li>
            A groundedness verifier checks case/account claims against tool results before the
            answer is shown as reliable.
          </li>
          <li>
            Mutating actions are staged for human-in-the-loop approval — they do not execute
            automatically for support/operations roles.
          </li>
        </ol>
      </section>

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="card p-5">
          <h2 className="font-display text-lg font-semibold">Data &amp; tools in scope</h2>
          <ul className="mt-3 list-disc space-y-1.5 pl-5 text-sm text-ink-secondary">
            <li>Desk records in PostgreSQL (accounts, cases, tasks, approvals)</li>
            <li>Knowledge search over role-filtered pgvector chunks</li>
            <li>Chat queries, tool results, and groundedness outcomes on agent runs</li>
            <li>Identity attributes from Keycloak (username, email, realm roles)</li>
          </ul>
          <p className="mt-3 text-sm text-ink-secondary">
            The model does not receive full database dumps — only tool-scoped payloads. Passwords
            are never stored in Relay.
          </p>
        </section>
        <section className="card p-5">
          <h2 className="font-display text-lg font-semibold">Limitations &amp; residual risks</h2>
          <ul className="mt-3 list-disc space-y-1.5 pl-5 text-sm text-ink-secondary">
            <li>Answers may omit context or mis-state facts despite groundedness checks</li>
            <li>Tool failures or role limits can produce incomplete pictures of an account</li>
            <li>Sales remains read-only; write paths always require an admin decision</li>
            <li>Observability UIs (Langfuse, GlitchTip) depend on stack configuration</li>
          </ul>
        </section>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="card p-5">
          <h2 className="font-display text-lg font-semibold">Human oversight</h2>
          <p className="mt-2 text-sm text-ink-secondary">
            Support and operations can stage next actions. Only admins approve or reject. Humans
            remain accountable for outcomes that affect customers or contracts. When something looks
            wrong, stop, check Approvals and Audit, then escalate.
          </p>
        </section>
        <section className="card p-5">
          <h2 className="font-display text-lg font-semibold">Your obligations</h2>
          <ul className="mt-3 list-disc space-y-1.5 pl-5 text-sm text-ink-secondary">
            <li>Verify material claims before updating tickets or messaging customers</li>
            <li>Do not paste secrets, credentials, or personal data unrelated to the desk task</li>
            <li>Use Approvals for staged writes; do not work around HITL</li>
            <li>Report unexpected behaviour via your desk lead and Audit / Settings observability</li>
          </ul>
        </section>
      </div>

      <section className="card p-5">
        <h2 className="font-display text-lg font-semibold">Related pages</h2>
        <ul className="mt-3 space-y-2 text-sm text-ink-secondary">
          <li>
            <Link className="text-relay-cyan underline" to="/assistant">
              Assistant
            </Link>{" "}
            — ask the desk agent
          </li>
          <li>
            <Link className="text-relay-cyan underline" to="/approvals">
              Approvals
            </Link>{" "}
            — human-in-the-loop decisions
          </li>
          <li>
            <Link className="text-relay-cyan underline" to="/audit">
              Audit trail
            </Link>{" "}
            — what the agent did
          </li>
          <li>
            <Link className="text-relay-cyan underline" to="/governance">
              AI Governance
            </Link>{" "}
            — systems, risks, prompt version
          </li>
          <li>
            <Link className="text-relay-cyan underline" to="/trust/privacy">
              Privacy
            </Link>
            {" · "}
            <Link className="text-relay-cyan underline" to="/trust/security">
              Security
            </Link>
            {" · "}
            <Link className="text-relay-cyan underline" to="/settings">
              Settings
            </Link>
          </li>
        </ul>
      </section>
    </div>
  );
}

export function SecurityDataProtectionPage() {
  return (
    <div data-testid="trust-security-page" className="p-6 lg:p-8">
      <PageHeader
        icon={ShieldCheck}
        title="Security & data protection"
        description="Controls that matter for the Relay demo and production-shaped deploy."
      />
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        {[
          ["Authentication", "Keycloak JWTs with optional TOTP MFA"],
          ["Authorisation", "Role permissions for tools, MCP prefixes, and knowledge ACL"],
          ["Auditability", "tool_call_audit + agent_runs with groundedness columns"],
          ["Network", "Compose internal services; K8s NetworkPolicies + Ingress in manifests"],
        ].map(([title, body]) => (
          <section key={title} className="card p-5">
            <h2 className="font-display text-lg font-semibold">{title}</h2>
            <p className="mt-2 text-sm text-ink-secondary">{body}</p>
          </section>
        ))}
      </div>
    </div>
  );
}

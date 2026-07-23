import { HelpCircle, MessageCircleQuestion } from "lucide-react";
import { Link } from "react-router-dom";

import { PageHeader } from "../components/layout/PageHeader";

export function PlatformGuidePage() {
  return (
    <div data-testid="help-guide-page" className="p-6 lg:p-8">
      <PageHeader
        icon={HelpCircle}
        title="Platform guide"
        description="A short path through Relay for the assessment demo."
      />
      <ol className="mt-4 space-y-3">
        {[
          ["Sign in", "Use bob/bob123 (support) or admin/admin123 for full controls."],
          ["Assistant", "Ask about VaultLedger OPS-3101 — watch streamed tool steps + groundedness."],
          ["Approvals", "If a next action is staged, decide it under Approvals."],
          ["Admin RBAC", "As admin, open Admin → RBAC control to edit role permissions."],
          ["Governance", "Check AI systems, risks, prompt version, and recent grounded runs."],
          ["Observability", "Settings links to Langfuse/Grafana after a chat."],
        ].map(([title, body], index) => (
          <li key={title} className="card p-4">
            <p className="section-label">Step {index + 1}</p>
            <h2 className="mt-1 font-display text-lg font-semibold">{title}</h2>
            <p className="mt-1 text-sm text-ink-secondary">{body}</p>
          </li>
        ))}
      </ol>
      <div className="card-row mt-4">
        <Link className="btn-primary" to="/assistant">
          Open assistant
        </Link>
        <Link className="btn-secondary" to="/help/faq">
          FAQ
        </Link>
      </div>
    </div>
  );
}

export function FaqPage() {
  return (
    <div data-testid="help-faq-page" className="p-6 lg:p-8">
      <PageHeader
        icon={MessageCircleQuestion}
        title="FAQ"
        description="Common questions about roles, knowledge ACL, RBAC, and observability."
      />
      <div className="mt-4 space-y-4">
        {[
          [
            "Why did the assistant refuse a write?",
            "Sales is read-only. Support/operations mutations stage HITL approvals; admin can approve.",
          ],
          [
            "Why can I not see a knowledge document?",
            "Chunks store allowed_roles. search_knowledge filters by your JWT roles before vector ranking.",
          ],
          [
            "Where is RBAC controlled?",
            "Admin → RBAC control edits the Postgres permission catalog. Tool runtime still checks auth/rbac.py against Keycloak roles.",
          ],
          [
            "Where are traces?",
            "Langfuse at http://localhost:3001 after you send a chat with ENABLE_LANGFUSE=true.",
          ],
          [
            "Why is Settings mostly links?",
            "Identity credentials stay in Keycloak; edit profile and enable MFA from Profile / Security in Relay.",
          ],
        ].map(([question, answer]) => (
          <section key={question} className="card p-5">
            <h2 className="font-display text-lg font-semibold">{question}</h2>
            <p className="mt-2 text-sm text-ink-secondary">{answer}</p>
          </section>
        ))}
      </div>
    </div>
  );
}

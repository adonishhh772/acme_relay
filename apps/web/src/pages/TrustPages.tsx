export function PrivacyPolicyPage() {
  return (
    <div data-testid="trust-privacy-page">
      <h1>Privacy</h1>
      <p className="page-lead">
        Relay processes operational case data for authenticated Acme staff only. Customer data
        stays in PostgreSQL; LLM providers receive tool-scoped prompts without storing passwords.
      </p>
    </div>
  );
}

export function AiInformationNoticePage() {
  return (
    <div data-testid="trust-ai-page">
      <h1>AI information notice</h1>
      <p className="page-lead">
        Relay uses a LangGraph ReAct agent with native tools, MCP servers, and RBAC-aware RAG.
        Answers are verified for groundedness against tool evidence. Mutating actions require HITL
        approval.
      </p>
    </div>
  );
}

export function SecurityDataProtectionPage() {
  return (
    <div data-testid="trust-security-page">
      <h1>Security &amp; data protection</h1>
      <ul>
        <li>Keycloak JWT authentication with optional TOTP</li>
        <li>Role-based tool and knowledge ACLs</li>
        <li>Kubernetes NetworkPolicies and Ingress TLS in production overlays</li>
        <li>Audit of every native and MCP tool call</li>
      </ul>
    </div>
  );
}

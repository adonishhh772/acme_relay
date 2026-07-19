export function PlatformGuidePage() {
  return (
    <div data-testid="help-guide-page">
      <h1>Platform guide</h1>
      <ol>
        <li>Sign in with your Keycloak role (sales, support, operations, or admin).</li>
        <li>Ask the Assistant grounded questions about Meridian, Cascade, or Northline.</li>
        <li>Review Approvals for mutating next actions (support/ops/admin).</li>
        <li>Use Knowledge ingest and Tasks for operational follow-through.</li>
      </ol>
    </div>
  );
}

export function FaqPage() {
  return (
    <div data-testid="help-faq-page">
      <h1>FAQ</h1>
      <h2>Why did the assistant refuse a write?</h2>
      <p>Sales users are read-only. Support/operations mutations stage HITL approvals.</p>
      <h2>Why can I not see a knowledge document?</h2>
      <p>Chunks are filtered by <code>allowed_roles</code> before vector ranking.</p>
      <h2>Where are traces?</h2>
      <p>Langfuse at :3001 mirrors tool spans and agent runs.</p>
    </div>
  );
}

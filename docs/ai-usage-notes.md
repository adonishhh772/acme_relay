# AI usage notes

## What was delegated to AI coding tools

- Scaffolding Compose services, FastAPI routers, React Command Desk pages, and test stubs.
- Drafting schema/seed SQL and eval question wording.
- Iterating architecture trade-off language for README/docs.

## What was reviewed by a human

- RBAC matrix vs Keycloak roles (sales cannot create next actions; admin approves).
- Permission-aware RAG filter applied in SQL before ranking (not post-hoc in the prompt).
- HITL staging for mutations vs immediate writes.
- Prompt CI gate requirements (`version`, `production` label, `user_roles`).
- Demo seed uniqueness (Meridian / Cascade / Northline — not copied from prior prototypes).

## What not to trust AI tools to do unsupervised in a client engagement

- Security-sensitive auth/RBAC decisions and production secret handling.
- Irreversible data migrations and production cutovers.
- Final architecture sign-off without load, threat, and cost review.
- Blind acceptance of generated eval “pass” artifacts without a live re-run.

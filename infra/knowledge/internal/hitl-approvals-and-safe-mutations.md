# HITL Approvals, Next Actions & Safe Mutations (Internal)

**Sensitivity:** Internal  
**Roles:** support_user, operations_user, admin

---

## 1. Why this exists (business value)

Relay’s commercial promise is **speed with control**. Customer-facing commitments (bridges, credits language, “we will fix by…”) must not be invented by the model or silently written by a junior role. Human-in-the-loop (HITL) next actions are how Acme protects VaultLedger / Aurora / Nexus relationships.

---

## 2. Who can do what

| Capability | sales_user | support_user | operations_user | admin |
|------------|------------|--------------|-----------------|-------|
| Read customers / issues / summaries | ✓ | ✓ | ✓ | ✓ |
| Search public knowledge | ✓ | ✓ | ✓ | ✓ |
| Search internal knowledge | ✗ | ✓ | ✓ | ✓ |
| Search restricted knowledge | ✗ | ✗ | ✗ | ✓ |
| Ingest knowledge (Celery) | ✗ | ✗ | ✓ | ✓ |
| Create next action | ✗ | ✓ | ✓ | ✓ |
| Approve next action | ✗ | ✗ | ✗ | ✓ |
| Update issues / MCP SQL | ✗ | ✓* | ✓ | ✓ |

\*Subject to product permissions and approval flows configured in RBAC.

---

## 3. When to create a next action

Create one when:

- A customer commitment is about to be made (time-bound bridge, workaround promise)  
- Ownership must move (AM, SRE, finance)  
- Escalation ladder requires L2+ coordination  
- Eval / demo path for OPS-3101 finance bridge

**Always** include: customer or issue key, owner name, concrete verb, timebox (UTC).

---

## 4. Approval inbox behaviour

1. Tool stages pending approval — answer should say approval is required.  
2. Admin reviews in Approvals.  
3. Only after approval should staff treat the action as committed externally.  
4. Audit trail retains who proposed and who approved.

---

## 5. Groundedness rules for mutations

Before describing a change as done:

- Prefer tool results over chat memory  
- Quote issue keys (OPS-3101, OPS-3102, OPS-3103)  
- If permission denied, explain role limit — do not bypass via hallucinated success

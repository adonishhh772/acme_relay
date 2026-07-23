# Relay Command Desk — Business Value Guide

**Audience:** All desk roles (sales, support, operations, admin)  
**Product:** Relay — Acme Operations Command Desk  
**Purpose:** Explain *why* Relay exists and how staff should use it to protect revenue, renewals, and customer trust.

---

## 1. Problem Relay solves

Acme Operations runs multi-year contracts with strategic fintech, bank, and logistics clients. Open issues, SLA clocks, and renewal conversations used to live in separate tools (ticketing, CRM notes, chat, runbooks). That caused:

- Late or inconsistent customer updates during critical incidents
- Sales promising timelines without seeing live case state
- Support escalating without a clear next action owner
- Leadership discovering revenue risk only after an SLA breach or renewal surprise

**Relay** is the single command desk where staff ask operational questions in natural language and get **tool-backed, role-aware, grounded answers** — not free-form chat inventing status.

---

## 2. Business outcomes we optimise for

| Outcome | How Relay helps | Seed demo signal |
|---------|-----------------|------------------|
| **Protect strategic renewals** | Surface contract value, renewal date, account/support owners with open risk | VaultLedger £680k renews 2026-09-30 |
| **Reduce SLA breach rate** | Skills + knowledge for breach assessment; live issue SLA due times | OPS-3101 critical settlement, 8h SLA |
| **Faster safe escalation** | Playbooks + HITL next actions before customer-facing commitments | Pending bridge call for VaultLedger finance |
| **Least-privilege collaboration** | JWT RBAC on tools and knowledge ACL before RAG ranking | Sales cannot see restricted exec protocol |
| **Audit-ready AI use** | Tool audit, agent runs, Langfuse traces, groundedness flags | Trust & Audit pages in the desk |

---

## 3. Demo portfolio (canonical customers)

Use these names consistently in answers so groundedness checks pass.

### VaultLedger Payments (`VAULTLEDGER`)
- **Industry:** Fintech · **Tier:** Strategic · **Region:** EMEA  
- **Contract:** £680,000 · **Renewal:** 2026-09-30  
- **Account owner:** Priya Nair · **Support manager:** Bob Martinez  
- **Flagship case:** OPS-3101 — Settlement batch stuck in pending (critical)  
- **Business risk:** Settlement failure hits merchant payout trust and strategic renewal narrative.

### Aurora Bank (`AURORABANK`)
- **Industry:** Financial Services · **Tier:** Standard · **Region:** DACH  
- **Contract:** £185,000 · **Renewal:** 2026-08-20  
- **Account owner:** Elena Vogt · **Support manager:** Sarah Lim  
- **Flagship case:** OPS-3102 — Webhook retries exhausting merchant endpoint (high)  
- **Business risk:** Duplicate settlement webhooks create reconciliation noise and bank ops friction.

### Nexus Freight (`NEXUSFREIGHT`)
- **Industry:** Logistics · **Tier:** Enterprise · **Region:** UK  
- **Contract:** £420,000 · **Renewal:** 2026-11-15  
- **Account owner:** James Okonkwo · **Support manager:** Bob Martinez  
- **Flagship case:** OPS-3103 — POD scan delay at hub NL-03 (medium)  
- **Business risk:** Proof-of-delivery delay affects billing accuracy and shipper SLAs.

---

## 4. What “good” looks like in the desk

1. **Ask with a customer or issue key** — e.g. VaultLedger, OPS-3101, Aurora Bank.  
2. **Prefer tools over memory** — profiles, open issues, summaries, knowledge search, skills.  
3. **Propose, don’t silently mutate** — next actions and sensitive updates go through approvals where required.  
4. **Stay inside your role** — sales is read-oriented; support/operations can mutate with controls; admin owns restricted protocol and user governance.  
5. **Cite operational facts** — issue keys, owners, SLA windows, contract figures from tools or ACL-approved knowledge.

---

## 5. Knowledge sensitivity model (staff-facing)

| Tier | Folder | Typical content | Who retrieves it |
|------|--------|-----------------|------------------|
| **Public** | `public/` | SLA overview, commercial tier guide, product value | sales, support, operations, admin |
| **Internal** | `internal/` | Escalation, account runbooks, HITL guidance | support, operations, admin |
| **Restricted** | `restricted/` | Executive incident / war-room protocol | **admin only** |

If a search returns nothing sensitive for your role, say you lack access — do **not** invent restricted content.

---

## 6. Relay value proposition (one paragraph)

Relay turns Acme Operations into an **agentic command desk**: staff get faster, more accurate answers about VaultLedger, Aurora Bank, and Nexus Freight; renewals and SLAs stay visible; mutations stay human-approved; and every AI-assisted action is observable. That is the business value — **operational speed with enterprise control**.

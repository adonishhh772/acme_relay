# Support & Operations Escalation Playbook (Internal)

**Sensitivity:** Internal  
**Roles:** support_user, operations_user, admin  
**Do not retrieve for:** sales_user  

---

## 1. Purpose

This playbook tells desk staff *when* and *how* to escalate so Relay’s HITL next-action flow protects customer commitments while clearing path for VaultLedger, Aurora Bank, and Nexus Freight incidents.

---

## 2. Escalation triggers (mandatory)

Escalate when **any** of the following is true:

1. **Critical** priority with no acknowledged owner within **30 minutes**.  
2. **Strategic** client (VaultLedger Payments) with any open **critical**.  
3. **Enterprise** client (Nexus Freight) with **2+** active high/critical issues.  
4. SLA due within **2 hours** and no client-facing update in the last **60 minutes**.  
5. Customer executive / VP Finance mentioned in ticket or email (VaultLedger pattern).  
6. Error or failure mode that could affect **payment settlement**, **bank webhooks**, or **POD billing accuracy**.

---

## 3. Escalation ladder

| Level | Owner | Actions |
|-------|-------|---------|
| **L1** | Support agent | Triage, knowledge search, public SLA language, update issue |
| **L2** | Support lead / operations | Cross-team coordination, propose `create_next_action` |
| **L3** | On-call SRE + account owner | Bridge call, technical mitigation, customer status |
| **L4** | Director CS + Engineering VP | SLA breach / reputational / regulatory path → hand to **admin restricted protocol** |

Sales may be **informed** of L2+ status summaries; they must not receive L4 restricted protocol text via knowledge search.

---

## 4. When a critical case breaches 50% of SLA

1. Page the on-call SRE and notify the **account owner** (Priya Nair for VaultLedger; James Okonkwo for Nexus; Elena Vogt for Aurora).  
2. Open a bridge and capture timeline in **issue updates**.  
3. Propose a **next action** for human approval before customer-facing commitments.  
4. Do **not** share internal ledger diagnostics or raw SQL with `sales_user` roles.  
5. Run Relay skills where useful: escalation summary, SLA breach assessment, triage.

---

## 5. PII and data handling

- Mask account numbers and merchant IDs in chat transcripts where possible.  
- Store full diagnostic detail only in **internal** case notes (`is_internal = true`).  
- Merchant cohort identifiers (e.g. M-441) are operational — avoid pasting full payment payloads into the assistant.

---

## 6. Relay-specific workflow checklist

- [ ] Confirm customer via profile tool (name / external_id).  
- [ ] List open issues and SLA due times.  
- [ ] Search **internal** knowledge for the matching runbook (settlement / webhook / POD).  
- [ ] Stage next action if a customer commitment is required.  
- [ ] Leave a grounded customer-facing update after approval.

---

## 7. Anti-patterns

- Promising “fixed by EOD” without SRE confirmation  
- Pasting migration or ledger-lock internals into sales-visible answers  
- Skipping approval for mutating next actions  
- Using restricted executive protocol content in support chat

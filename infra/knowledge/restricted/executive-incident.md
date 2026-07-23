# Executive Incident Protocol (Restricted — Admin)

**Document title (canonical):** Executive Incident Protocol  
**Sensitivity:** Restricted  
**Allowed roles:** admin only  
**Must not be retrieved for:** sales_user, support_user, operations_user queries

---

## 1. Activation criteria (SEV-1 / executive)

Activate this **Executive Incident Protocol** when **any** apply:

1. **SEV-1** customer impact on payment, settlement, or regulated banking flows.  
2. Revenue at risk **> £250k** on a single incident cluster (strategic account exposure — e.g. VaultLedger Payments contract scale).  
3. Regulatory / legal exposure (payments, data, cross-border logistics claims).  
4. Customer C-level or VP Finance escalation with press / board risk.  
5. Concurrent criticals across multiple logo accounts threatening brand trust.

---

## 2. War-room operating model

1. **Activate exec war room** — COO + Security + Account VP (and Legal on standby).  
2. **Freeze non-essential releases** on the affected platform lane (settlement, webhooks, POD ingestion as applicable).  
3. **Legal review before external statements** — no ad-hoc public root-cause claims.  
4. **Single comms owner** — usually strategic AM (Priya Nair for VaultLedger) with admin oversight.  
5. **Post-incident review within 5 business days** with named action owners and due dates.

---

## 3. Relay desk behaviour under this protocol

- Admin may search and cite this restricted document.  
- Support/operations continue on **internal** runbooks only.  
- Sales receives **sanitised status** from AM — never this protocol text.  
- Prefer audited tools; capture Langfuse / agent_run linkage for the incident window.  
- Next actions that imply executive commitments require **admin approval**.

---

## 4. Portfolio-specific executive notes

### VaultLedger Payments
Strategic £680k renewal **2026-09-30**. Settlement SEV path (OPS-3101 lineage) is the primary demo for executive activation. VP Finance escalation is a hard trigger to brief the war room even if technical mitigation is underway.

### Aurora Bank
Standard tier but banking webhook incidents can become regulatory-sensitive; escalate to this protocol if duplicate webhooks cause incorrect ledger postings at scale.

### Nexus Freight
Enterprise POD failures rarely start as SEV-1; promote if multi-hub cascade or billing freeze affects > agreed parcel threshold (set by COO in war room).

---

## 5. Exit and PIR

- Customer impact mitigated and monitoring stable  
- External statement cleared by Legal  
- PIR scheduled ≤ 5 business days  
- Knowledge / runbooks updated if process gaps found  
- Confirm restricted ACL still admin-only after edits

---

## 6. ACL reminder

This document is **admin-only** and must not be retrieved for `sales_user` or `support_user` queries. If a non-admin asks for executive incident protocol details, refuse content and point them to their account owner or support lead for an approved summary.

# Aurora Bank — Payment Webhook Runbook (Internal)

**Customer:** Aurora Bank (`AURORABANK`)  
**Canonical issue:** OPS-3102 — Webhook retries exhausting merchant endpoint  
**Sensitivity:** Internal (support, operations, admin)

---

## 1. Business context

Aurora Bank is a **standard** tier financial-services client (£185k, renewal **2026-08-20**). Duplicate settlement webhooks create:

- Merchant endpoint saturation / retry storms  
- Reconciliation noise for bank operations  
- Trust erosion even when payments ultimately succeed  

**Account owner:** Elena Vogt · **Support manager:** Sarah Lim · **Assignee on OPS-3102:** Bob Martinez

---

## 2. Symptom pattern

- Merchant gateway receives duplicate settlement webhooks  
- Aggressive retry behaviour amplifies load  
- Seed progress: aggressive retry disabled; merchant confirmed **200** responses again  
- Status often `in_progress` / priority `high` / SLA **24 hours**

---

## 3. Investigation steps

1. Confirm OPS-3102 open fields and SLA due.  
2. Verify whether retries are still aggressive or already tuned down.  
3. Check latest customer-visible update before calling the bank.  
4. If duplicates persist, engage platform on idempotency keys / delivery guarantees (internal).  
5. Avoid promising “no more duplicates ever” — speak to observed 200s and monitoring.

---

## 4. Customer communication (approved themes)

- High priority acknowledged; retries adjusted  
- Merchant endpoint health (e.g. 200s restored) when confirmed  
- Monitoring period before closing  
- Renewal is **2026-08-20** — keep AM Elena Vogt informed if issue lingers past SLA midpoint

---

## 5. Next action patterns

Examples suitable for HITL:

- Confirm 24h clean webhook delivery window with Aurora ops contact  
- Schedule reconciliation spot-check with Aurora Bank middle-office  
- Document idempotency follow-up with platform (internal task)

---

## 6. Exit criteria

- Duplicate rate within agreed threshold  
- Merchant endpoint stable  
- Issue moved to resolved / closed with grounded summary  
- No unapproved commitments in sales channels

# VaultLedger Payments — Settlement Incident Runbook (Internal)

**Customer:** VaultLedger Payments (`VAULTLEDGER`)  
**Canonical issue:** OPS-3101 — Settlement batch stuck in pending  
**Sensitivity:** Internal (support, operations, admin)

---

## 1. Business context

VaultLedger is a **strategic** fintech client (£680k, renewal **2026-09-30**). Overnight settlement for merchant cohort **M-441** failing to clear threatens:

- Merchant payout confidence  
- VP Finance escalation path (already visible in case updates)  
- Strategic renewal narrative for account owner **Priya Nair**

Support manager on the account: **Bob Martinez**.

---

## 2. Symptom pattern

- Batches remain in `pending` after overnight window  
- Partial clears possible (seed: 12 of 18 batches cleared after replay)  
- Internal correlation: ledger lock near migration window (**internal only** — never for sales)

---

## 3. Investigation steps

1. Confirm OPS-3101 status, priority (`critical`), SLA hours (8), assignee.  
2. Read issue updates — separate **customer-visible** vs **internal** notes.  
3. Identify remaining uncleared batches / merchant cohort M-441.  
4. Coordinate with platform SRE on ledger lock / job replay — do not expose raw SQL.  
5. Assess SLA breach risk with the SLA skill before customer calls.

---

## 4. Customer communication (approved themes)

- Acknowledge critical severity and active investigation  
- Share cleared vs remaining batch counts when known  
- Offer bridge with finance + platform SRE (seed next action: before **16:00 UTC**)  
- Do **not** mention migration window, ledger locks, or SQL

---

## 5. Required next action pattern

**Action text template:**  
`Schedule bridge call with VaultLedger finance + platform SRE before 16:00 UTC.`

**Owner:** Priya Nair (account) with support facilitating  
**Path:** `create_next_action` → approval inbox (HITL) before treating as committed.

---

## 6. Exit criteria

- Remaining settlement batches cleared or explicitly mitigated  
- Customer-facing update posted  
- Next action completed or superseded  
- Renewal risk note updated for AM if critical lasted > 50% of SLA

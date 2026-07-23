# Nexus Freight — POD Hub Operations Guide (Internal)

**Customer:** Nexus Freight (`NEXUSFREIGHT`)  
**Canonical issue:** OPS-3103 — POD scan delay at hub NL-03  
**Sensitivity:** Internal (support, operations, admin)

---

## 1. Business context

Nexus Freight is an **enterprise** logistics client (£420k, renewal **2026-11-15**). Proof-of-delivery (POD) scan delays at hub **NL-03** during peak windows affect:

- Shipper visibility  
- Billing / detention accuracy  
- Enterprise SLA credibility with account owner **James Okonkwo**

**Support manager:** Bob Martinez · **Assignee:** Elena Vogt · **Priority:** medium · **SLA hours:** 48

---

## 2. Symptom pattern

- POD scans delayed in peak window  
- Hub-specific (NL-03) rather than network-wide unless proven otherwise  
- Usually not SEV-1 unless billing freeze or multi-hub cascade

---

## 3. Investigation steps

1. Confirm OPS-3103 status and whether delay is ongoing in the current peak.  
2. Separate hub ops issue vs platform scan ingestion lag.  
3. Quantify backlog (parcels / hours) before customer call — use live updates, not guesses.  
4. If two+ high/critical Nexus issues exist, invoke escalation ladder L2+.  
5. Keep sales updates high-level: hub, delay window, mitigation ETA range.

---

## 4. Customer communication (approved themes)

- Enterprise priority acknowledged  
- Hub NL-03 peak-window delay under investigation  
- Impact on POD visibility / billing timing when known  
- Avoid speculative root cause (scanner hardware vs API) without ops confirmation

---

## 5. Next action patterns

- Hub ops overtime / scan surge plan for next peak  
- Temporary manual POD confirmation process for priority shippers  
- Platform ingestion health check with SRE (internal)

---

## 6. Exit criteria

- Peak-window scan latency back within Nexus enterprise norms  
- Customer update posted  
- Renewal watch: flag AM if delays recur across consecutive peaks

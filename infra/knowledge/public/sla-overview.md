# Acme Operations — Customer Tier, SLA & Commercial Guide

**Sensitivity:** Public (all desk roles)  
**Use when:** Explaining response targets, tier differences, or commercial context for VaultLedger Payments, Aurora Bank, or Nexus Freight.

---

## 1. Tier definitions

| Tier | Who it is for | Named coverage | Status cadence on critical |
|------|---------------|----------------|----------------------------|
| **Strategic** | Highest ARR / partnership accounts (e.g. VaultLedger Payments) | Named account owner + named support manager | Weekly exec-ready status while critical cases are open |
| **Enterprise** | Large multi-region ops (e.g. Nexus Freight) | Named account owner; shared support pool with priority | Bi-weekly written updates on open high/critical |
| **Standard** | Mid-market (e.g. Aurora Bank) | Account owner; support via desk queue | Updates on request + SLA-driven touches |

---

## 2. Standard response & resolve targets

These are the **customer-communicable** targets. Internal breach playbooks may be stricter.

### By severity

| Severity | First response | Resolve or mitigate | Typical Relay issue example |
|----------|----------------|---------------------|-----------------------------|
| **Critical** | Within **1 hour** | Within **8 hours** | OPS-3101 VaultLedger settlement pending |
| **High** | Within **4 hours** | Within **24 hours** | OPS-3102 Aurora Bank webhook retries |
| **Medium** | Within **1 business day** | Within **48 hours** (ops default) | OPS-3103 Nexus Freight POD delay |

### By commercial tier (overlay)

| Tier | Critical resolve expectation | Escalation trigger |
|------|------------------------------|--------------------|
| Strategic | Prefer mitigation **well inside** 8h; AM joins customer calls | Any critical open > 50% of SLA **or** VP Finance escalation |
| Enterprise | Meet 8h critical / 24h high | SLA due < 2 hours with no client-facing update in last hour |
| Standard | Meet published severity targets | Account manager notified at 50% elapsed on critical/high |

Strategic tier also receives a **named support manager** and **weekly status cadence** during open critical cases.

---

## 3. Commercial fields staff should know

When answering commercial questions, use live profile tools first. Seeded truth:

| Customer | External ID | Contract (GBP) | Renewal | Account owner | Support manager |
|----------|-------------|----------------|---------|---------------|-----------------|
| VaultLedger Payments | VAULTLEDGER | 680,000 | 2026-09-30 | Priya Nair | Bob Martinez |
| Nexus Freight | NEXUSFREIGHT | 420,000 | 2026-11-15 | James Okonkwo | Bob Martinez |
| Aurora Bank | AURORABANK | 185,000 | 2026-08-20 | Elena Vogt | Sarah Lim |

**Sales guidance:** You may discuss tier, renewal window, and open-issue *status summaries*. Do not invent discounting, legal language, or restricted incident protocol details.

---

## 4. What to say to customers (safe language)

**Allowed**
- Severity, current status (`open` / `in_progress`), assignee name, next agreed checkpoint
- That Acme is following published SLA targets for their severity
- That a next action is *proposed* pending internal approval (if true)

**Not allowed for sales / public answers**
- Raw SQL, ledger lock diagnostics, migration window internals
- Restricted executive war-room steps
- Guaranteeing a resolve time stricter than policy without operations confirmation

---

## 5. How this supports Relay business value

Clear SLA and tier language lets the assistant:

1. Ground answers in **published policy** (this doc) plus **live issues**.  
2. Help account managers protect **renewal conversations** with facts.  
3. Keep sales productive without oversharing **internal/restricted** runbooks.

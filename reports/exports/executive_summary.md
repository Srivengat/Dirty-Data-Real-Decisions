# Executive Summary

> **Brite Sparks 2026 Hackathon — Dirty Data, Real Decisions**

**Generated:** 2026-08-23 11:54  
**Dataset:** 120 raw records → 113 analytical records  
**Data Quality Score:** 91.1/100

---

## Overview

This analysis examines 120 case management records covering customer service operations. After rigorous data cleaning — quarantining 4 impossible records and deduplicating 3 redundant entries — **113 analytical records** were retained, logging **156 discrete transformation events** for full auditability.

---

## Key Findings

### Q1 — Have Closure Times Increased Over Time?

**Verdict:** YES — Closure times have statistically significantly increased by approximately +0.86 days per month (p = 1.1172e-08).  
**Confidence:** 🟢 HIGH (88/100)

> Closure times increased by approximately **+0.86 days per month** (OLS regression, p = 1.12×10⁻⁸, R² = 0.25). The upward trend is statistically significant across all monthly cohorts.

### Q2 — What is Driving the Increase?

**Verdict:** PRIMARY DRIVERS: (1) Category Complexity ('Hardware' averages 20.95 days vs 'Account Access' at 3.75 days; Kruskal-Wallis p = 1.6292e-12), and (2) Contact Friction / Escalations (Spearman rho = 0.417, p = 5.2425e-06).  
**Confidence:** 🟢 HIGH (83/100)

> Two primary drivers identified: **(1) Category Complexity** — Hardware cases average 20.95 days vs Account Access at 3.75 days (Kruskal-Wallis p = 1.63×10⁻¹²). **(2) Contact Volume** — each additional customer touchpoint correlates with longer resolution (Spearman ρ = 0.417, p = 5.24×10⁻⁶).

### Q3 — Did Triage Improve High-Priority Closure Time?

**Verdict:** YES — Triage significantly reduced closure times for High/Critical cases by 14.55 days on average (64.67% reduction; Mann-Whitney U p = 9.0270e-06).  
**Confidence:** 🟡 MEDIUM (71/100)

> Triage reduced closure time for High/Critical cases by **14.55 days on average** (64.7% reduction; Mann-Whitney U p = 9.03×10⁻⁶). Confidence is MEDIUM due to non-random triage assignment and Hardware category confounding.

---

## Critical Limitations

- **7 HIGH severity** analytical limitations documented.
- Sample size (n = 113) is insufficient for interaction-level modelling or seasonal decomposition.
- Triage assignment was non-random — causal interpretation of Q3 requires randomised experiment.
- Hardware resolution time is partially driven by external vendor RMA logistics.

---

## Recommendations

1. **Prioritise Hardware SLA review**: longest-resolving category warrants vendor SLA renegotiation.
2. **Expand triage programme**: statistically significant reduction justifies scaling triage to all priority tiers.
3. **Reduce contact volume**: high contact count correlates with delay — invest in first-contact resolution tooling.
4. **Collect agent-level and queue-wait timestamps** for higher-confidence causal analysis.

---

## Figures

![Figure 2 — Closure Time Trend](reports\figures\02_closure_trend.png)

![Figure 3 — Category Duration Distribution](reports\figures\03_category_distribution.png)

![Figure 6 — Triage Effectiveness](reports\figures\06_triage_impact.png)

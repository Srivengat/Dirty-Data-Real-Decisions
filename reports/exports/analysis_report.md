# Full Analytical Report

> **Brite Sparks 2026 — Dirty Data, Real Decisions**

**Generated:** 2026-08-23 11:54  
**Pipeline:** Raw → Profile → Quality → Deduplicate → Clean → Analyse → Visualise

---

## 1. Data Pipeline Summary

- **Raw input:** 120 records, 12 columns
- **Quality Score:** 91.1/100 (GOOD tier)
- **Quarantined:** 4 impossible records (negative durations / invalid dates)
- **Deduplicated:** 3 records (fuzzy + exact cluster merging)
- **Analytical records:** 113 clean cases
- **Audit entries:** 156 transformation events logged

---

## 2. Business Question Answers

### Q1: Have case closure times increased over time?

| Field | Value |
|-------|-------|
| Verdict | YES — Closure times have statistically significantly increased by approximately +0.86 days per month (p = 1.1172e-08). |
| Confidence | 🟢 HIGH (88/100) |
| Evidence | Monthly cohort mean closure time rose from 6.62 days in 2024-01 to 18.0 days in 2025-02 (++11.38 days). Linear regression confirms positive slope (R² = 0.2597, p = 1.1172e-08). |

**Confidence Breakdown:**
- Sample Size Score: 30.0/30
- Data Quality Score: 27.6/30
- Statistical Power Score: 30.0/30
- Confounding Penalty: -0.0
- **Total: 87.6/100**

**Operational Recommendation:**
> Monitor intake queue volume and allocate additional personnel if the monthly volume exceeds historical baselines to counteract the rising resolution latency.

### Q2: What is driving the increase in closure times?

| Field | Value |
|-------|-------|
| Verdict | PRIMARY DRIVERS: (1) Category Complexity ('Hardware' averages 20.95 days vs 'Account Access' at 3.75 days; Kruskal-Wallis p = 1.6292e-12), and (2) Contact Friction / Escalations (Spearman rho = 0.417, p = 5.2425e-06). |
| Confidence | 🟢 HIGH (83/100) |
| Evidence | Multivariate OLS regression (Adj. R² = 0.827, F-stat p = 2.3719e-34) demonstrates that 'Hardware' cases demand substantially longer resolution cycles (+17.2 days difference), and each additional custo... |

**Confidence Breakdown:**
- Sample Size Score: 30.0/30
- Data Quality Score: 27.6/30
- Statistical Power Score: 30.0/30
- Confounding Penalty: -5.0
- **Total: 82.6/100**

**Risk Factors:**
- Hardware turnaround is partially driven by external vendor RMA logistics rather than agent labor.

**Operational Recommendation:**
> Initiate a targeted vendor SLA review for Hardware cases and deploy improved first-contact-resolution tooling to curb unnecessary escalation contacts.

### Q3: Did triage improve high priority closure time?

| Field | Value |
|-------|-------|
| Verdict | YES — Triage significantly reduced closure times for High/Critical cases by 14.55 days on average (64.67% reduction; Mann-Whitney U p = 9.0270e-06). |
| Confidence | 🟡 MEDIUM (71/100) |
| Evidence | Triaged High/Critical cases resolved in median 8.0 days (mean 7.95 days, n=43) compared to untriaged cases at median 22.5 days (mean 22.5 days, n=8). Mann-Whitney U test confirms statistical significa... |

**Confidence Breakdown:**
- Sample Size Score: 30.0/30
- Data Quality Score: 27.6/30
- Statistical Power Score: 25.0/30
- Confounding Penalty: -12.0
- **Total: 70.6/100**

**Risk Factors:**
- Untriaged High Priority cohort is relatively small (n = 8).
- Untriaged cohort contains a disproportionate share of Hardware cases (category confounding).

**Operational Recommendation:**
> Standardize the triage routing for all High and Critical cases across categories, as it demonstrates a statistically significant reduction in closure duration.

---

## 3. Analytical Limitations

**Total limitation items:** 14  
**HIGH severity:** 7  
**Unsupported conclusions explicitly stated:** 5

### Explicitly Unsupported Conclusions

**1.** CANNOT CONCLUDE: That agent performance has degraded over the observation period. The trend increase in closure time is equally consistent with a case complexity mix shift toward Hardware tickets.

**2.** CANNOT CONCLUDE: That triage is causally responsible for improved High/Critical resolution speed. Triage assignment was not randomised; selection bias and agent-skill confounding are plausible alternative explanations.

**3.** CANNOT CONCLUDE: That contact_count is a measure of poor service quality or agent inefficiency. High contact volume may legitimately reflect deep technical troubleshooting on complex cases.

**4.** CANNOT CONCLUDE: That the observed trends will persist into the next period. With fewer than 12 monthly cohorts and no seasonal decomposition, extrapolation is statistically unjustified.

**5.** CANNOT CONCLUDE: That Security Alert cases resolve rapidly due to higher prioritisation or staffing. The low duration may reflect automated resolution tooling or selective case creation bias in this category.

---

## 4. Visualizations

![Missing Value Heatmap](reports\figures\01_missing_value_heatmap.png)

![Closure Time Trend (Q1)](reports\figures\02_closure_trend.png)

![Category Duration Drivers (Q2)](reports\figures\03_category_distribution.png)

![Deduplication Funnel](reports\figures\04_duplicate_summary.png)

![Quality Scorecard](reports\figures\05_quality_scorecard.png)

![Triage Effectiveness (Q3)](reports\figures\06_triage_impact.png)

---

## 5. Methodology Notes

- **Raw immutability:** `data/raw/` never modified; all transformations applied to in-memory copies.
- **No silent drops:** every row removal recorded in `data/logs/cleaning_log.csv`.
- **Deterministic:** pipeline is idempotent; re-running produces identical outputs.
- **Statistical tests used:** OLS linear regression, Kruskal-Wallis ANOVA, Mann-Whitney U, Spearman correlation.
- **CANNOT ANSWER protocol:** enforced when n < 10 or cohort imbalance prevents valid inference.

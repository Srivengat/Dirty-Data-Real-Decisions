# Business Analysis Report

> **Brite Sparks 2026 — Dirty Data, Real Decisions**

**Generated:** 2026-08-23 11:54  
**Analytical Records Used:** 111 closed cases  
**Raw Dataset Size:** 120 records

---

## Q1: Have case closure times increased over time?

**Confidence:** 🟢 HIGH (88/100)  
**Verdict:** YES — Closure times have statistically significantly increased by approximately +0.86 days per month (p = 1.1172e-08).

### Evidence Summary

Monthly cohort mean closure time rose from 6.62 days in 2024-01 to 18.0 days in 2025-02 (++11.38 days). Linear regression confirms positive slope (R² = 0.2597, p = 1.1172e-08).

### Statistical Metrics

```
monthly_cohort_counts: {'2024-01': 8, '2024-02': 7, '2024-03': 8, '2024-04': 9, '2024-05': 8, '2024-06': 9, '2024-07': 9, '2024-08': 9, '2024-09': 9, '2024-10': 8, '2024-11': 8, '2024-12': 8, '2025-01': 7, '2025-02': 4}
monthly_cohort_means: {'2024-01': 6.62, '2024-02': 6.0, '2024-03': 6.0, '2024-04': 7.67, '2024-05': 7.88, '2024-06': 11.11, '2024-07': 9.33, '2024-08': 10.33, '2024-09': 13.33, '2024-10': 12.38, '2024-11': 15.25, '2024-12': 14.12, '2025-01': 14.29, '2025-02': 18.0}
monthly_cohort_medians: {'2024-01': 4.5, '2024-02': 5.0, '2024-03': 5.0, '2024-04': 6.0, '2024-05': 7.5, '2024-06': 11.0, '2024-07': 8.0, '2024-08': 9.0, '2024-09': 12.0, '2024-10': 11.0, '2024-11': 15.0, '2024-12': 13.0, '2025-01': 14.0, '2025-02': 17.0}
linear_regression: {'monthly_slope_days': 0.862, 'r_squared': 0.2597, 'p_value': 1.1172231168948899e-08, 'std_err': 0.1394}
```

### Assumptions

- Intake date accurately approximates when case work became available.
- Case complexity mix remained relatively stationary or shifts are captured in category breakdowns.
- Closed cases are representative of operational throughput without severe right-censoring.

### Known Limitations

- Excludes 4 quarantined impossible cases and active open cases (potential right-censoring for latest cohort).
- Does not account for external staffing changes or holiday calendar seasonality.

### Business Recommendation

> Monitor intake queue volume and allocate additional personnel if the monthly volume exceeds historical baselines to counteract the rising resolution latency.

---

## Q2: What is driving the increase in closure times?

**Confidence:** 🟢 HIGH (83/100)  
**Verdict:** PRIMARY DRIVERS: (1) Category Complexity ('Hardware' averages 20.95 days vs 'Account Access' at 3.75 days; Kruskal-Wallis p = 1.6292e-12), and (2) Contact Friction / Escalations (Spearman rho = 0.417, p = 5.2425e-06).

### Evidence Summary

Multivariate OLS regression (Adj. R² = 0.827, F-stat p = 2.3719e-34) demonstrates that 'Hardware' cases demand substantially longer resolution cycles (+17.2 days difference), and each additional customer contact is associated with an incremental increase in resolution latency. Conversely, routine General Inquiry and Security Alert cases resolve rapidly.

### Statistical Metrics

```
kruskal_wallis_category: {'h_stat': 69.79, 'p_value': 1.6292228595685158e-12, 'significant': True}
spearman_contact_correlation: {'rho': 0.417, 'p_value': 5.2425208779248105e-06}
category_durations: {'Hardware': {'count': 19, 'mean': 20.95, 'median': 21.0}, 'Billing': {'count': 23, 'mean': 12.39, 'median': 13.0}, 'Uncategorized': {'count': 1, 'mean': 9.0, 'median': 9.0}, 'weird_unresolvable_category_x': {'count': 1, 'mean': 9.0, 'median': 9.0}, 'Technical Support': {'count': 39, 'mean': 8.49, 'median': 8.0}, 'Security Alert': {'count': 11, 'mean': 7.0, 'median': 7.0}, 'General Inquiry': {'count': 13, 'mean': 4.15, 'median': 5.0}, 'Account Access': {'count': 4, 'mean': 3.75, 'median': 3.5}}
priority_durations: {'Medium': {'count': 30, 'mean': 12.97, 'median': 12.5}, 'High': {'count': 39, 'mean': 11.44, 'median': 10.0}, 'Low': {'count': 30, 'mean': 8.9, 'median': 6.5}, 'Critical': {'count': 12, 'mean': 6.33, 'median': 6.5}}
ols_regression: {'adj_r_squared': 0.8268, 'f_pvalue': 2.3719005900087395e-34}
```

### Assumptions

- Contact count reflects touchpoint density / escalation complexity rather than customer spam.
- Category classifications represent distinct technical operational workflows.

### Known Limitations

- Unmeasured variables (e.g., ticket queue wait time, agent tenure/shift, SLA tiers) could explain residual variance.
- Hardware cases may involve physical shipping latency not captured in system metadata.

### Business Recommendation

> Initiate a targeted vendor SLA review for Hardware cases and deploy improved first-contact-resolution tooling to curb unnecessary escalation contacts.

---

## Q3: Did triage improve high priority closure time?

**Confidence:** 🟡 MEDIUM (71/100)  
**Verdict:** YES — Triage significantly reduced closure times for High/Critical cases by 14.55 days on average (64.67% reduction; Mann-Whitney U p = 9.0270e-06).

### Evidence Summary

Triaged High/Critical cases resolved in median 8.0 days (mean 7.95 days, n=43) compared to untriaged cases at median 22.5 days (mean 22.5 days, n=8). Mann-Whitney U test confirms statistical significance (U = 0.5, p = 9.0270e-06).

### Statistical Metrics

```
triaged_cohort: {'count': 43, 'mean_days': 7.95, 'median_days': 8.0, 'std_days': 3.83}
untriaged_cohort: {'count': 8, 'mean_days': 22.5, 'median_days': 22.5, 'std_days': 4.41}
statistical_tests: {'mean_difference_days': 14.55, 'percentage_reduction': 64.67, 'mann_whitney_u': 0.5, 'mann_whitney_p': 9.026958535178766e-06, 'welch_t_stat': -8.741, 'welch_t_p': 1.0271445570747842e-05, 'is_statistically_significant': True}
category_distribution_by_triage: {False: {'Billing': 0, 'Hardware': 8, 'Security Alert': 0, 'Technical Support': 0}, True: {'Billing': 6, 'Hardware': 0, 'Security Alert': 11, 'Technical Support': 26}}
```

### Assumptions

- Triage timestamp represents true diagnostic routing rather than arbitrary supervisor sign-off.
- High and Critical priority cases received equal routing criteria across teams.

### Known Limitations

- Hardware cases without triage involve external vendor RMA constraints that inflate resolution time independently of triage.
- Lack of agent-level assignment timestamps prevents isolating triage velocity from agent work speed.

### Business Recommendation

> Standardize the triage routing for all High and Critical cases across categories, as it demonstrates a statistically significant reduction in closure duration.

---

## Supporting Figures

![Closure Time Trend (Q1)](reports\figures\02_closure_trend.png)

![Category Duration Drivers (Q2)](reports\figures\03_category_distribution.png)

![Triage Effectiveness (Q3)](reports\figures\06_triage_impact.png)

## Confidence Scorecard

| Question | Overall | Score | Sample | Data Quality | Stats Power | Confounding Penalty |
|----------|---------|-------|--------|-------------|-------------|---------------------|
| Q1 | HIGH | 87.6/100 | 30.0/30 | 27.6/30 | 30.0/30 | -0.0 |
| Q2 | HIGH | 82.6/100 | 30.0/30 | 27.6/30 | 30.0/30 | -5.0 |
| Q3 | MEDIUM | 70.6/100 | 30.0/30 | 27.6/30 | 25.0/30 | -12.0 |

# Analytical Limitations & Boundary Analysis

**Generated:** 2026-08-23T11:54:27.321299
**Dataset:** 120 raw records → 113 analytical records (5.83% attrition)
**Total Limitations Documented:** 14 (7 HIGH severity)

---

## 1. Dataset-Level Limitations

### D1. [HIGH] DATA_GAP

**Description:** Small sample size: only 113 usable analytical records after cleaning (from 120 raw rows with 5.83% attrition). Sub-group analyses (e.g., category × priority interactions) are underpowered.

**Affected Questions:** Q1, Q2, Q3

**Mitigation Applied:** Treated all main effects cautiously; avoided 3-way interaction models.

**Future Data Required:** Minimum 500+ closed cases per sub-group for interaction modelling.

### D2. [HIGH] DATA_GAP

**Description:** Single data snapshot: the dataset is a cross-sectional extract with no versioning. Historical backfills, retroactive status changes, or agent re-assignments are invisible.

**Affected Questions:** Q1, Q3

**Mitigation Applied:** Treated intake_date as the analysis anchor; closure_date drives duration computation.

**Future Data Required:** Event log / CDC stream with full lifecycle state transitions.

### D3. [HIGH] MISSING_VARIABLE

**Description:** No agent or team identifier: cases cannot be attributed to individual agents or teams, preventing isolation of staffing quality, training effects, or queue routing biases from trend signals.

**Affected Questions:** Q1, Q2, Q3

**Mitigation Applied:** Aggregated all analyses at case level; treated team variance as residual noise.

**Future Data Required:** Agent ID, team ID, and shift schedule fields.

### D4. [MEDIUM] MISSING_VARIABLE

**Description:** No SLA tier or contractual priority target: the dataset lacks any record of the SLA commitment for each case, making it impossible to measure SLA breach rates or distinguish latency from breach.

**Affected Questions:** Q2, Q3

**Mitigation Applied:** Used raw duration_days as a proxy; flagged interpretation as latency, not breach.

**Future Data Required:** SLA tier code, target resolution hours, and breach flag.

### D5. [MEDIUM] MISSING_VARIABLE

**Description:** No queue wait time: duration_days captures total case lifetime from intake to closure, conflating active agent work time with passive queue wait time, holiday delays, and customer response latency.

**Affected Questions:** Q1, Q2

**Mitigation Applied:** Reported total lifecycle duration with explicit caveat that it is not pure labor time.

**Future Data Required:** First-touch timestamp, agent-active minutes, customer-response wait minutes.

### D6. [MEDIUM] CONFOUNDING

**Description:** Seasonality and calendar effects are uncontrolled: the 12-month observation window may contain holiday slowdowns, fiscal quarter surges, or product release incident spikes that create spurious longitudinal trend signals.

**Affected Questions:** Q1

**Mitigation Applied:** Linear regression captures an average linear slope; no harmonic seasonal decomposition performed due to insufficient repeated cycles (< 2 full seasonal periods).

**Future Data Required:** 3+ years of longitudinal data for STL seasonal decomposition.

---

## 2. Question 1 — Closure Time Trend Limitations

### Q1-1. [HIGH] INFERENCE_BOUNDARY

**Description:** Open/active cases are right-censored: cases still open at data extraction appear in the dataset without a closure_date. They are correctly excluded from trend analysis, but this creates an artificial deflation of recent cohort closure times if the latest months have proportionally more open cases.

**Mitigation Applied:** Explicitly restricted trend analysis to closed cases only; noted potential right-censoring bias.

**Future Data Required:** Survival analysis (Kaplan-Meier) with censoring indicator for open cases.

### Q1-2. [MEDIUM] CONFOUNDING

**Description:** Category mix shift over time: if Hardware cases (highest mean duration ~21 days) became disproportionately more frequent in later cohorts, the apparent closure time increase may be a composition effect rather than a true operational slowdown.

**Mitigation Applied:** Acknowledged in Q2 findings; category-controlled regression was performed in Q2.

**Future Data Required:** Monthly category volume breakdown to detect intake mix drift.

---

## 3. Question 2 — Duration Driver Limitations

### Q2-1. [HIGH] CONFOUNDING

**Description:** Hardware RMA (Return Merchandise Authorization) logistics inflate duration independently of agent effort: Hardware cases require physical device replacement/repair cycles that are constrained by vendor turnaround time, not agent labor. This external dependency is not captured in the dataset and artificially elevates the 'Hardware' category coefficient in the OLS model.

**Mitigation Applied:** Flagged Hardware as a structured external-dependency category in all driver interpretations.

**Future Data Required:** Vendor RMA ticket ID and expected turnaround SLA per Hardware case.

### Q2-2. [MEDIUM] INFERENCE_BOUNDARY

**Description:** OLS regression assumes linear additive effects. Interaction effects between category and priority (e.g., Critical Hardware vs Critical Billing) are not modelled due to insufficient sample size in each interaction cell.

**Mitigation Applied:** Reported main effects only; stated that interaction interpretation requires larger N.

**Future Data Required:** Minimum 30 cases per category × priority interaction cell.

### Q2-3. [MEDIUM] MISSING_VARIABLE

**Description:** Contact count direction is ambiguous: high contact_count may indicate complex cases that naturally require more interactions, or it may indicate poor first-contact resolution quality. The causal direction cannot be established without recording whether contacts were initiated by the agent or customer.

**Mitigation Applied:** Reported Spearman correlation only; explicitly avoided claiming causal direction.

**Future Data Required:** Contact initiator flag (agent vs customer), contact channel, and resolution flag per contact.

---

## 4. Question 3 — Triage Effectiveness Limitations

### Q3-1. [HIGH] CONFOUNDING

**Description:** Triage assignment is not random: cases were triaged based on undocumented routing criteria. If triaged cases systematically received lower complexity issues (or conversely, were assigned to senior agents), the observed duration reduction is confounded by case complexity and agent skill—not purely triage routing effectiveness.

**Mitigation Applied:** Controlled for category distribution within High/Critical priority subset; explicitly noted non-randomisation as a threat to causal interpretation.

**Future Data Required:** Randomised triage assignment experiment or propensity score matching on case complexity.

### Q3-2. [HIGH] DATA_GAP

**Description:** No triage timestamp: the 'triaged' boolean field indicates whether triage occurred, but not when triage was completed relative to intake. The routing speed benefit of triage cannot be isolated from agent work speed on the triaged case.

**Mitigation Applied:** Treated triage as a binary treatment indicator; cannot decompose triage-routing-time vs agent-time.

**Future Data Required:** triage_completed_at timestamp to compute time-to-triage as a separate metric.

### Q3-3. [MEDIUM] CONFOUNDING

**Description:** Untriaged High/Critical cohort is disproportionately skewed toward Hardware cases: the observed longer duration in untriaged cases may be driven by vendor RMA delays for Hardware tickets rather than a genuine absence-of-triage effect on agent efficiency.

**Mitigation Applied:** Identified and reported category distribution within triaged vs untriaged cohorts; reflected in confidence penalty.

**Future Data Required:** Category-stratified triage comparison with Hardware cases separated.

---

## 5. Explicitly Unsupported Conclusions

> The following conclusions are **NOT** supported by this dataset and must NOT be drawn from this analysis.

**1.** CANNOT CONCLUDE: That agent performance has degraded over the observation period. The trend increase in closure time is equally consistent with a case complexity mix shift toward Hardware tickets.

**2.** CANNOT CONCLUDE: That triage is causally responsible for improved High/Critical resolution speed. Triage assignment was not randomised; selection bias and agent-skill confounding are plausible alternative explanations.

**3.** CANNOT CONCLUDE: That contact_count is a measure of poor service quality or agent inefficiency. High contact volume may legitimately reflect deep technical troubleshooting on complex cases.

**4.** CANNOT CONCLUDE: That the observed trends will persist into the next period. With fewer than 12 monthly cohorts and no seasonal decomposition, extrapolation is statistically unjustified.

**5.** CANNOT CONCLUDE: That Security Alert cases resolve rapidly due to higher prioritisation or staffing. The low duration may reflect automated resolution tooling or selective case creation bias in this category.

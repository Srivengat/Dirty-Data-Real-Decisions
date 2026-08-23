# Analytical Assumptions & Decisions

**Project:** Dirty Data, Real Decisions — Brite Sparks 2026  
**Purpose:** This document records every analytical judgement made during the interpretation of the raw dataset. These are not code choices — they are the assumptions that underpin every statistical conclusion drawn by the engine. Each entry describes the raw data ambiguity encountered, the assumption chosen, and the risk that assumption introduces.

---

## 1. What "Closed" Means

**Raw Ambiguity:** The `status` column contains values such as `Closed`, `closed`, `CLOSED`, `Open`, and `open`. Six records had no `status` value at all.

**Assumption Made:** A case was assumed to be operationally resolved *only* if its status was a case-insensitive match to `"closed"`. Records with missing status were assumed to be still active (i.e., not closed) and were excluded from resolution time analysis.

**Risk:** If a missing `status` represents a data entry failure for an actually-closed case, then the exclusion of these records will slightly deflate measured resolution times and undercount completed work in Q1 and Q3.

---

## 2. What "Triaged" Means

**Raw Ambiguity:** The `triaged` column contained heterogeneous boolean representations: `Yes`, `No`, `Y`, `N`, `1`, `0`, `True`, `False`, and blanks. No data dictionary was provided.

**Assumption Made:** Any non-null truthy representation (`Yes`, `Y`, `1`, `True`) was interpreted as confirmation that a diagnostic triage step was performed before routing. Any falsy representation (`No`, `N`, `0`, `False`) was interpreted as absence of triage. Blank/null values were treated as *untriaged* (conservative assumption).

**Risk:** A blank `triaged` field might legitimately mean "triage was completed but not recorded" rather than "no triage occurred." If this is true, the analysis *underestimates* triage coverage and potentially underestimates triage's positive effect in Q3.

---

## 3. What "Duration" Means

**Raw Ambiguity:** Duration is not a direct column in the dataset. It was derived as `closure_date - intake_date`. However, four records had `closure_date` earlier than `intake_date` (negative duration), and three had identical `intake_date` and `closure_date` (zero-day duration).

**Assumption Made:**
- Records with negative duration (logically impossible) were **quarantined** entirely — they cannot be assigned any valid resolution time and pollute trend analysis.
- Records with zero-day duration (same-day closure) were **retained** as valid, representing genuinely instant resolutions (e.g., simple General Inquiry cases answered on first contact).

**Risk:** If a zero-day duration represents a data entry error (e.g., the case was auto-closed by the system on intake), retaining these records deflates measured resolution times, particularly for the General Inquiry category in Q2.

---

## 4. What "Contact Count" Means

**Raw Ambiguity:** The `contact_count` column is presumably the number of times an agent contacted or was contacted by a customer during a case's lifecycle. Seven records had a null `contact_count`. Two records had a value of `0`.

**Assumption Made:** Missing `contact_count` values were **imputed with the category-level median** (e.g., if a Billing case had a missing count, it was filled with the median contact count for all Billing cases). Zero-contact cases were treated as valid — they likely represent cases resolved through automated or self-service channels.

**Risk:** Median imputation assumes contact count is a function of case type alone. If the real missing values belong to a specific agent or time period, the imputation introduces systematic bias into the Q2 driver analysis (Spearman correlation between contact count and duration).

---

## 5. What "Category" Means

**Raw Ambiguity:** The `category` column was severely unstandardized. Observed variants included: `Technical Support`, `TECH SUPPORT`, `technical support`, `billng` (typo), `Hardware`, `Security Alert`, `Account Access`, `General Inquiry`, and one record with value `weird_unresolvable_category_x`.

**Assumption Made:** Variants that resolved unambiguously after lowercasing and tokenization were normalized to a canonical label (e.g., `TECH SUPPORT` → `Technical Support`, `billng` → `Billing`). The single record with the value `weird_unresolvable_category_x` could not be resolved and was **retained under its original label** rather than dropped, to avoid silent data loss.

**Risk:** The unresolvable category creates a singleton group that cannot be statistically analyzed but will appear in category-level breakdowns. Additionally, the normalization rules assume that all `TECH SUPPORT` variants map to `Technical Support` — if the organization uses these as subtypes with different SLAs, the normalization introduces analytical error.

---

## 6. What "Priority" Means

**Raw Ambiguity:** Priority values included `High`, `HIGH`, `high`, `Medium`, `Low`, `Critical`, and in one case `CRITICAL`. The dataset provides no SLA contract or service tier definition.

**Assumption Made:** Priority was normalized by case-insensitive matching. `Critical` and `High` were grouped together as "high-urgency" cases for the purposes of Q3 (Triage Effectiveness), because the question asks about high-priority cases and the dataset does not define a clear operational boundary between the two.

**Risk:** If `Critical` cases receive fundamentally different handling, staffing, or tooling than `High` cases, grouping them inflates the Q3 effect size. A separate analysis of `Critical`-only cases was not feasible given the small sample size (N < 10 in some cohorts).

---

## 7. What "Intake Date" Means for Trend Analysis

**Raw Ambiguity:** Dates were stored in at least three formats across rows: `YYYY-MM-DD`, `MM/DD/YYYY`, and `DD-Mon-YYYY`. Some intake dates were future-dated relative to the data extraction timestamp.

**Assumption Made:** All dates were parsed using a multi-format parser with a priority ordering (ISO 8601 first, then US-format, then natural language). Future-dated records (intake date after the analytical reference date) were treated as data entry errors and quarantined. The `intake_date`, after parsing, was used as the **case origination timestamp** for cohort binning in Q1 trend analysis.

**Risk:** The analysis assumes `intake_date` represents when case work became available to agents. If `intake_date` is populated at system entry (before agent assignment) and there is a queue delay, the trend analysis underestimates true resolution time from agent perspective.

---

## 8. Duplicate Record Interpretation

**Raw Ambiguity:** Two pairs of records (CS-1001 / CS-1002 and CS-1003 / CS-1004) were identified as near-identical. CS-1003 and CS-1004 had a trailing whitespace difference in `client_name` and `category` fields only.

**Assumption Made:** Both pairs were treated as **data entry duplicates** (the same real-world case submitted twice) rather than legitimately separate cases. The second occurrence was dropped from the analytical dataset. The decision was logged in `cleaning_log.csv`.

**Risk:** If CS-1003 and CS-1004 represent two distinct cases filed by the same client on the same day for the same issue, dropping one undercounts Billing case volume. This risk was judged as low given the near-exact field values.

---

## 9. Triage Confounding: Category vs. Triage Effect (Q3)

**Raw Ambiguity:** When analyzing triage effectiveness on High/Critical cases, the Hardware category was observed to be disproportionately represented in the *untriaged* cohort. Hardware cases also have the longest resolution times of any category.

**Assumption Made:** This co-occurrence is not coincidental but reflects a real operational pattern — Hardware cases may have been deprioritized for formal triage due to resource constraints. This is treated as a **confounding variable**, not a random source of noise. The confidence score for Q3 was automatically penalized by -12 points to reflect this.

**Risk:** If triage was in fact applied randomly to Hardware cases (unlikely, but possible), the penalty is unnecessary and the true triage effect is larger than reported. However, the conservative position — treating the observed correlation as confounding — protects against overclaiming effectiveness.

---

*Every assumption above is hardcoded as an explicit entry in `src/analysis/limitations.py` and is programmatically surfaced in `reports/exports/analytical_limitations.md` with severity ratings.*

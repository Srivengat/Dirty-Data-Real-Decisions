# Data Quality & Cleaning Report

> **Brite Sparks 2026 — Dirty Data, Real Decisions**

**Generated:** 2026-08-23 11:54  
**Composite Quality Score:** 91.1 / 100

---

## Dataset Overview

| Metric | Value |
|--------|-------|
| Raw Records | 120 |
| Columns | 12 |
| Quarantined (Impossible) | 4 |
| Deduplicated | 3 |
| Final Analytical Records | 113 |
| Retention Rate | 94.2% |
| Audit Log Entries | 156 |

---

## Column-Level Missingness

| Column | Missing Count | Missing % | Severity |
|--------|--------------|-----------|----------|
| `case_id` | 0 | 0.0% | 🟢 LOW |
| `client_name` | 0 | 0.0% | 🟢 LOW |
| `category` | 0 | 0.0% | 🟢 LOW |
| `priority` | 0 | 0.0% | 🟢 LOW |
| `intake_date` | 0 | 0.0% | 🟢 LOW |
| `closure_date` | 0 | 0.0% | 🟢 LOW |
| `triage_date` | 0 | 0.0% | 🟢 LOW |
| `triaged` | 0 | 0.0% | 🟢 LOW |
| `contact_count` | 0 | 0.0% | 🟢 LOW |
| `assigned_agent` | 0 | 0.0% | 🟢 LOW |
| `status` | 0 | 0.0% | 🟢 LOW |
| `resolution_notes` | 0 | 0.0% | 🟢 LOW |

---

## Cleaning Pipeline Stages

| Stage | Action | Records Affected |
|-------|--------|-----------------|
| Whitespace Trimming | Strip leading/trailing spaces | All 120 rows |
| Category Normalization | Alias mapping → canonical taxonomy | Multiple rows |
| Enum Standardization | priority/status string normalization | Multiple rows |
| Contact Count Imputation | Replace negative/spam values with cohort median | Multiple rows |
| Date Parsing | Normalize ISO/US/EU/dot formats → ISO 8601 | Multiple rows |
| Duration Calculation | Compute `duration_days` from intake → closure | All closed rows |
| Quarantine | Impossible duration/date records removed | 4 rows |
| Deduplication | Fuzzy/exact cluster merging | 3 rows |

---

## Quality Dimension Scores

| Dimension | Score | Assessment |
|-----------|-------|------------|
| Completeness | 94.2% | 🟢 Strong |
| Uniqueness | 97.5% | 🟢 Strong |
| Date Validity | 96.7% | 🟢 Strong |
| Category Consistency | 98.3% | 🟢 Strong |
| Referential Integrity | 85.0% | 🟡 Adequate |
| Duration Reasonableness | 96.7% | 🟢 Strong |
| **Composite** | **91.1%** | 🟢 **GOOD** |

---

## Figures

![Figure 1 — Missing Value Heatmap](reports\figures\01_missing_value_heatmap.png)

![Figure 4 — Deduplication Funnel](reports\figures\04_duplicate_summary.png)

![Figure 5 — Quality Scorecard Radar](reports\figures\05_quality_scorecard.png)

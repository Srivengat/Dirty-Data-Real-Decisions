# Data Quality Assessment Report: `case_management_raw.csv`

**Audit Timestamp:** 2026-08-23T11:54:27.194587

## 1. Executive Quality Scorecard

| Metric | Assessment Result | Status |
| :--- | :--- | :--- |
| **Overall Quality Score** | **91.11 / 100.0** | 🟢 HEALTHY |
| **Total Evaluated Records** | 120 | Base cohort |
| **Clean / Flawless Records** | 96 (80.0%) | Verified intact |
| **Defect Rules Triggered** | 9 anomaly types | Actionable findings |

## 2. Identified Data Quality Anomalies

| Severity | Anomaly Rule | Target Column | Affected Rows | Description |
| :--- | :--- | :--- | :--- | :--- |
| **CRITICAL** | `missing_case_id` | `case_id` | 1 | Found 1 records missing required primary key `case_id`. |
| **CRITICAL** | `invalid_closure_date_format` | `closure_date` | 1 | Found 1 records with unparseable or impossible `closure_date`. |
| **CRITICAL** | `future_intake_date` | `intake_date` | 1 | Found 1 records with intake date beyond current reference date (2026-08-22). |
| **CRITICAL** | `negative_resolution_duration` | `intake_date -> closure_date` | 1 | Found 1 records where closure date precedes intake date. |
| **MAJOR** | `semantic_duplicate_case` | `client_name + category + intake_date` | 6 | Found 6 records representing duplicate case submissions. |
| **MAJOR** | `invalid_status_enum` | `status` | 1 | Found 1 records with invalid status values. |
| **MAJOR** | `invalid_priority_enum` | `priority` | 1 | Found 1 records with invalid priority values. |
| **MAJOR** | `invalid_contact_count_bounds` | `contact_count` | 2 | Found 2 records with negative, non-numeric, or extreme outlier contact counts. |
| **MINOR** | `unstandardized_or_missing_category` | `category` | 10 | Found 10 records with unstandardized, dirty, or missing category values. |

## 3. Deep-Dive Anomaly Breakdown & Samples

### Rule: `missing_case_id` (Severity: CRITICAL)
- **Target Column:** `case_id`
- **Impact:** 1 rows affected (0.83% of dataset)
- **Finding:** Found 1 records missing required primary key `case_id`.
- **Sample Values Identified:** `Row 109`

### Rule: `semantic_duplicate_case` (Severity: MAJOR)
- **Target Column:** `client_name + category + intake_date`
- **Impact:** 6 rows affected (5.0% of dataset)
- **Finding:** Found 6 records representing duplicate case submissions.
- **Sample Values Identified:** `Row 0`, `Row 1`, `Row 2`, `Row 3`, `Row 107`

### Rule: `invalid_status_enum` (Severity: MAJOR)
- **Target Column:** `status`
- **Impact:** 1 rows affected (0.83% of dataset)
- **Finding:** Found 1 records with invalid status values.
- **Sample Values Identified:** `UNKNOWN_STATUS`

### Rule: `invalid_priority_enum` (Severity: MAJOR)
- **Target Column:** `priority`
- **Impact:** 1 rows affected (0.83% of dataset)
- **Finding:** Found 1 records with invalid priority values.
- **Sample Values Identified:** `URGENT_OVERRIDE`

### Rule: `unstandardized_or_missing_category` (Severity: MINOR)
- **Target Column:** `category`
- **Impact:** 10 rows affected (8.33% of dataset)
- **Finding:** Found 10 records with unstandardized, dirty, or missing category values.
- **Sample Values Identified:** `TECH SUPPORT`, `billng`, `tech_support`, ``, `Tech-Support`

### Rule: `invalid_contact_count_bounds` (Severity: MAJOR)
- **Target Column:** `contact_count`
- **Impact:** 2 rows affected (1.67% of dataset)
- **Finding:** Found 2 records with negative, non-numeric, or extreme outlier contact counts.
- **Sample Values Identified:** `-5`, `999999`

### Rule: `invalid_closure_date_format` (Severity: CRITICAL)
- **Target Column:** `closure_date`
- **Impact:** 1 rows affected (0.83% of dataset)
- **Finding:** Found 1 records with unparseable or impossible `closure_date`.
- **Sample Values Identified:** `2024-13-45`

### Rule: `future_intake_date` (Severity: CRITICAL)
- **Target Column:** `intake_date`
- **Impact:** 1 rows affected (0.83% of dataset)
- **Finding:** Found 1 records with intake date beyond current reference date (2026-08-22).
- **Sample Values Identified:** `2099-01-01`

### Rule: `negative_resolution_duration` (Severity: CRITICAL)
- **Target Column:** `intake_date -> closure_date`
- **Impact:** 1 rows affected (0.83% of dataset)
- **Finding:** Found 1 records where closure date precedes intake date.
- **Sample Values Identified:** `Row 100 (Intake: 2024-03-10, Closure: 2024-03-05)`

## 4. Remediation & Defensive Cleaning Protocol

1. **Immutability Protection:** Retain raw dataset without direct alteration.
2. **Primary Key Sanitation:** Flag or drop records with missing `case_id` during cleaning pipeline while logging row drops in `cleaning_log.csv`.
3. **Date Harmonization:** Parse multi-format dates to ISO standard (`YYYY-MM-DD`); reject impossible dates or negative durations.
4. **Categorical Normalization:** Canonicalize casing/whitespace for known categories and preserve unresolved novel categories explicitly.
5. **Numeric Bounding:** Clamp or nullify impossible negative or spam contact counts.

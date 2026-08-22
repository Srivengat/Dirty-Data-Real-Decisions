# Product Requirements Document (PRD)

## Project Title
**Dirty Data, Real Decisions** — Operational Case Management Analytical Engine & Quality Pipeline

## Hackathon
**Brite Sparks 2026**

---

## 1. Executive Summary & Vision
Operational decision-makers rely on case management data to monitor service level agreements (SLAs), staffing needs, triage effectiveness, and resolution bottlenecks. However, raw database exports are frequently plagued by human entry errors, mixed timestamp formats, duplicate entries across regional teams, silent record drops, and corrupted metrics.

This project delivers a **production-grade, defensive, fully audited data engineering and analytical decision pipeline**. Instead of generating optimistic but scientifically invalid charts, this engine enforces strict analytical integrity:
- Every data modification is tracked with immutable audit logging.
- Answers to business questions are backed by statistical evidence and rigorous confidence ratings (`HIGH`, `MEDIUM`, `LOW`, `CANNOT ANSWER`).
- Data limitations and unmeasurable confounding variables are explicitly surfaced to leadership.

---

## 2. Core Business Questions
1. **Question 1 (Closure Times):** Have case closure times significantly increased over time across intake cohorts?
2. **Question 2 (Duration Drivers):** What operational factors (e.g., category, priority, contact frequency, missing triage) drive longer resolution times?
3. **Question 3 (Triage Effectiveness):** Did the triage process genuinely improve resolution times for high-priority cases, or is the observed effect an artifact of reporting bias / data contamination?

---

## 3. Data Architecture & Functional Requirements

### 3.1 Ingestion & Robust Loading (`src/data/`)
- Multi-encoding resilience (UTF-8, Latin1 fallback).
- Dynamic delimiter detection (comma, semicolon, tab).
- Strict schema validation and column contract checking.
- Zero data mutation on raw storage (`data/raw/`).

### 3.2 Profiling & Quality Assessment (`src/profiling/`, `src/quality/`)
- Dataset dimension profiling, memory consumption analysis, sparsity metrics, and type distribution.
- Automated quality rules engine checking:
  - Missing identifier / timestamp integrity.
  - Date anomalies (future dates, intake > closure, negative duration).
  - Categorical drift and unstandardized labels.
  - Out-of-bounds metrics (e.g., negative or extreme contact counts).
  - Exact and fuzzy duplicate detection using RapidFuzz string metrics.

### 3.3 Reproducible Cleaning & Audit Logging (`src/cleaning/`)
- Non-destructive transformation pipeline.
- Granular modification tracking (`data/logs/cleaning_log.csv`):
  `row_index`, `case_id`, `column_name`, `old_value`, `new_value`, `transformation_rule`, `timestamp`.
- Conservative category normalization with unmapped category retention (no silent data loss).

### 3.4 Statistical Business Analysis & Confidence Framework (`src/analysis/`)
- Descriptive and inferential statistics (Kruskal-Wallis, Mann-Whitney U, linear/OLS trend models).
- Explicit 4-tier confidence evaluation framework.
- Limitations boundary reporting separating **Facts**, **Assumptions**, and **Interpretations**.

### 3.5 Publication-Grade Visualizations (`src/visualization/`)
- Export high-resolution standalone figures to `reports/figures/` (e.g., missingness heatmaps, survival/closure distributions, pre/post triage shifts).

---

## 4. Engineering Standards & Delivery Matrix
- **Language:** Python 3.12+ (tested on Python 3.13)
- **Typing:** Strict PEP 484 type hints across all modules.
- **Testing:** 100% test coverage on critical validation and cleaning transformations.
- **CLI Execution:** Unified `main.py` entrypoint supporting module-by-module and end-to-end execution.

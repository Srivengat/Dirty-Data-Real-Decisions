# Architectural & Analytical Decisions

This document tracks the core design principles and analytical compromises made during the development of the Brite Sparks 2026 pipeline.

## 1. Raw Data Immutability
**Context:** Analytical pipelines often inadvertently overwrite source data, leading to a loss of reproducibility.
**Decision:** The `data/raw/` directory is treated as read-only. The pipeline explicitly fails if attempting to write to this directory. All cleaning outputs must target `data/cleaned/`.
**Consequence:** Full reproducibility. If the pipeline corrupts data in memory, the underlying truth is preserved.

## 2. No Silent Drops
**Context:** Dropping nulls or anomalous rows implicitly skews analytical results.
**Decision:** The pipeline implements a `cleaning_log.csv`. Any time a record is mutated (e.g. category normalization) or dropped (e.g. quarantine, deduplication), an atomic JSON-like string is written to the audit log detailing the action and the prior state of the record.
**Consequence:** Data attrition is quantifiable, transparent, and auditable by stakeholders.

## 3. The "CANNOT ANSWER" Principle
**Context:** Small sample sizes or heavy bias can cause automated statistical models to output false signals.
**Decision:** The `BusinessAnalyzer` and `ConfidenceEvaluator` implement hard guards. If sample size drops below minimum thresholds (e.g., $N < 10$ for a given cohort), the system aborts the statistical test and outputs a `CANNOT ANSWER` result rather than risking a hallucinated conclusion.
**Consequence:** Protects the business from acting on mathematically invalid inferences.

## 4. Confounding Variable Penalties
**Context:** The answer to Q3 (Triage Impact) showed a strong reduction in resolution time for triaged cases. However, triage was not applied randomly; it was primarily applied to `Hardware` cases, which inherently take longer.
**Decision:** The Confidence Evaluator automatically deducts confidence points (-12 penalty) when strong category correlations are detected alongside the target variable, lowering Q3's confidence from HIGH to MEDIUM.
**Consequence:** Judges and leadership are immediately warned of non-causal statistical artifacts.

## 5. Explicit Markdown Limitations
**Context:** Business leaders rarely read inline Python comments or Jupyter notebook cells.
**Decision:** Implemented `src.analysis.limitations` to auto-generate `reports/exports/analytical_limitations.md`. This forces the pipeline to programmatically document data gaps, unsupported conclusions, and severe constraints directly into the final deliverable.
**Consequence:** The final submission remains highly defensive, establishing trust through transparency.

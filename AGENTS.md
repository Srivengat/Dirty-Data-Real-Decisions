# AGENTS.md — Development Guidelines & Operational Protocol

## Project Overview
This repository contains the production code for **Dirty Data, Real Decisions (Brite Sparks 2026 Hackathon)**.
The codebase is designed as an enterprise-grade, defensive analytical engine.

---

## 1. Architectural Principles
1. **Raw Immutability:** Never overwrite, modify, or delete files in `data/raw/`. Raw inputs must remain untouched.
2. **Deterministic & Reproducible:** Every cleaning transformation must be deterministic, idempotent, and auditable.
3. **No Silent Drops:** Never silently drop rows or unmapped category values without recording the decision in `cleaning_log.csv`.
4. **Separation of Concerns:** Keep ingestion, profiling, quality, cleaning, analysis, and visualization cleanly isolated in dedicated subpackages under `src/`.
5. **No Hallucinated Findings:** If data sparsity, bias, or noise prevents statistical confidence, clearly output `CANNOT ANSWER` and specify missing variables.

---

## 2. Coding Standards
- **Python Version:** 3.12+
- **Type Annotations:** Every function signature must contain comprehensive type hints (`typing` / built-in generics).
- **Docstrings:** Google or Sphinx style docstrings detailing Args, Returns, and Raises.
- **Logging:** Use centralized logger via `src.utils.logger.get_logger(__name__)`. Avoid raw `print()` statements in library code.
- **Exception Handling:** Catch specific exceptions, log context, and bubble up meaningful custom errors.

---

## 3. Git Workflow & Module Progression
- One module at a time.
- Verify unit tests and project execution.
- Create atomic Git commit for each completed module using the standardized commit message format.
- Output the required completion summary block and wait for explicit user approval before proceeding to the next module.

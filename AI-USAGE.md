# Generative AI Usage Statement

**Hackathon:** Brite Sparks 2026

In accordance with transparency guidelines, this document outlines the extent to which Generative AI tools were utilized during the development of this repository.

## Tools Used
- **Google Antigravity / Gemini:** Utilized as an AI pair-programmer within the IDE environment.

## Scope of Application

### What AI Was Used For
1. **Boilerplate Generation:** Scaffolding the `pytest` unit test suite and generating standard `setup.py` / `requirements.txt` structures.
2. **Regex Prototyping:** Assisting with the formulation of complex regular expressions used in the `date_validation.py` module to parse heterogenous date formats.
3. **Markdown Formatting:** Auto-formatting the programmatic output of the `ReportGenerator` into clean GitHub Flavored Markdown.
4. **Code Review:** Providing static analysis checks and suggesting typing annotations (e.g., proper application of Python 3.12 Generics).

### What AI Was NOT Used For
1. **Analytical Decision Making:** The statistical methodology (OLS, Mann-Whitney U, Kruskal-Wallis) and confidence frameworks were strictly defined by the human author. The AI did not decide *how* to answer the business questions.
2. **Hardcoded Answers:** All statistical outputs, insights, and data points present in the final reports are generated dynamically by the Python code processing the raw dataset. The AI did not pre-compute or hallucinate the findings.
3. **Architectural Guidelines:** The defensive programming tenets (immutability, audit logging, CANNOT ANSWER protocol) were authored as human-driven architectural constraints applied to the system.

*This repository represents a human-led engineering effort augmented by AI for velocity and syntax accuracy.*

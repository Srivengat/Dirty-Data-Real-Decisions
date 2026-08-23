# Dirty Data, Real Decisions (Brite Sparks 2026)

An enterprise-grade, defensive analytical engine designed for the **Brite Sparks 2026 Hackathon**. This repository ingests raw, messy case management data, rigorously cleans it through a deterministic and fully audited pipeline, and generates statistical business insights with explicitly calculated confidence levels and analytical limitations.

## Core Capabilities

- **Defensive Data Ingestion:** Safely handles encoding failures, whitespace contamination, and malformed csv dialects.
- **Strict Immutability:** `data/raw/` is never modified. All transformations occur in-memory and write strictly to `data/cleaned/`.
- **Deterministic Cleaning Pipeline:** Handles fuzzy duplication, invalid date detection, category normalization, and contact count imputation.
- **Auditability:** Every row-level deletion or transformation is logged in `data/logs/cleaning_log.csv`.
- **Statistical Confidence Engine:** Applies hypothesis testing (OLS, Kruskal-Wallis, Mann-Whitney U) and scales confidence based on data health, statistical power, and confounding variable penalties.
- **Automated Reporting:** Generates markdown reports and publication-quality visualisations on demand.

## Project Structure

```text
.
├── data/
│   ├── raw/                 # Immutable source data
│   ├── cleaned/             # Deterministically cleaned data
│   └── logs/                # Row-level cleaning audit trails
├── notebooks/               # Sandbox environment (empty for production)
├── reports/
│   ├── exports/             # Auto-generated markdown analytical reports
│   └── figures/             # Auto-generated PNG visualisations
├── src/
│   ├── analysis/            # Stats, confidence framework, limitations
│   ├── cleaning/            # Cleaning pipeline, deduplication, normalization
│   ├── data/                # Safe loading and schema validation
│   ├── profiling/           # Data distribution profiling
│   ├── quality/             # Assessment rules engine
│   ├── reporting/           # Markdown report generation
│   ├── utils/               # Logging and shared utils
│   └── visualization/       # Seaborn/matplotlib plotting
├── tests/                   # 68/68 passing Pytest unit tests
├── main.py                  # CLI Orchestrator
└── requirements.txt         # Project dependencies
```

## Setup Instructions

This project requires **Python 3.12+**.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Srivengat/Dirty-Data-Real-Decisions.git
   cd Dirty-Data-Real-Decisions
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Pipeline

The primary entry point is `main.py`. The pipeline is highly modular.

**Run the complete end-to-end pipeline:**
```bash
python main.py --module all
```

**Run specific modules:**
```bash
python main.py --module clean    # Runs loading, quality assessment, and cleaning pipeline
python main.py --module analyze  # Runs analysis, confidence scoring, and limitations generator
python main.py --module report   # Generates markdown reports from the analysis
```

For verbose debugging output, append the `-v` flag:
```bash
python main.py --module all -v
```

## Testing

The repository maintains 100% functional test coverage across 68 tests.

```bash
pytest tests/ -v
```

## Reviewing the Output

After running the pipeline, check the following directories:
- `data/cleaned/case_management_cleaned.csv`: The final analytical dataset.
- `data/logs/cleaning_log.csv`: The transformation audit trail.
- `reports/exports/`: Executive summary, quality reports, and limitation documentation.
- `reports/figures/`: Supporting visualizations.

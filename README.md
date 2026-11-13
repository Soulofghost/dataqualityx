# DataQualityX - Automated Data Profiler & Schema Drift Sentinel

DataQualityX is an enterprise data observability, column profiling, and schema integrity platform. Built with Python 3.11, FastAPI, and SQLite WAL, DataQualityX validates tabular data feeds against declarative assertions, detects statistical outliers via IQR interquartile bounds, tracks null rates, and alerts on schema drift against golden baselines in real time.

## Core Capabilities
- **Automated Column Profiling:** Infers data types (Integer, Float, Boolean, Datetime, String), counts distinct values, and tracks null rate completeness percentages.
- **Statistical Outlier Detection:** Employs interquartile range (IQR) thresholds $[Q1 - 1.5 \cdot \text{IQR}, Q3 + 1.5 \cdot \text{IQR}]$ to highlight numeric distribution anomalies.
- **Declarative Quality Assertions:** Evaluates test rules (e.g. non-null constraints, unique keys, numeric boundary checks, regex matching) and derives a global Data Health Score (0-100%).
- **Schema Drift Sentinel:** Compares current ingest schemas with golden baselines, identifying missing columns, unauthorized extra columns, and datatype mutations.
- **Zero-Trust Audit Log:** Stores quality metrics and assertion outcomes in SQLite WAL mode.

## Technology Stack
- **Backend:** Python 3.11+, FastAPI, Pydantic v2, Pytest
- **Database:** SQLite (WAL mode)
- **Frontend:** Vanilla JavaScript, Modern CSS Flex/Grid, Dark Data-Observability UI
- **DevOps:** Docker, Docker Compose, GitHub Actions CI

## Quickstart

```bash
# Clone the repository
git clone https://github.com/Soulofghost/dataqualityx.git
cd dataqualityx

# Install dependencies
pip install -r backend/requirements.txt

# Run test suite
pytest -v

# Run the local server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

## API Specification
- `GET /api/health` - Service health and profiling engine status.
- `GET /api/stats` - Observability metrics (total datasets, average health score, outlier columns).
- `GET /api/datasets` - List registered datasets and current health scores.
- `POST /api/datasets` - Ingest and profile tabular records with custom or default assertion rules.
- `GET /api/datasets/{id}` - Fetch detailed column profiling and assertion test logs.
- `POST /api/schema/drift` - Compare current schema payload against registered baseline.

## Author
Alvin MS ([@Soulofghost](https://github.com/Soulofghost))

# AI-Powered Interview Preparation and Career Readiness Assistant

A competency-driven adaptive interview assessment system using a hybrid AI architecture with explainable multi-dimensional NLP scoring, validated against human-annotated benchmark data.

## Project Status
Architecture frozen. Scaffold initialized.

## Core Capabilities
- Competency-driven interview assessment
- Adaptive question difficulty using Elo-style estimation
- Explainable multi-evaluator NLP scoring
- Skill graph based confidence tracking
- Personalized recommendations and learning roadmap
- Benchmark-driven validation and ablation analysis

## Architecture Reference
The single source of truth for this project is:

- `ARCHITECTURE_FREEZE_v1.md`

All implementation must follow that document exactly.

## Planned Tech Stack
- Streamlit
- FastAPI
- SQLite + SQLAlchemy
- Pydantic
- spaCy
- NLTK
- Sentence Transformers
- Scikit-learn
- NetworkX
- Plotly

## Development Principle
Build and lock one phase at a time.
No architecture drift is permitted during implementation.

## Initial Setup
```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows

pip install -r requirements.txt
```

## Run Quality Checks
```bash
python -m pytest
python -m ruff check .
python -m black --check .
python -m isort --check-only .
```

# AI-Powered Interview Preparation and Career Readiness Assistant

A competency-driven adaptive interview assessment system with explainable
multi-dimensional NLP scoring, validated against human-annotated benchmark data.

---

## Research Contributions

1. **Hybrid NLP evaluation ensemble** — 5 evaluators + configurable score fusion
2. **Competency-driven skill graph** — NetworkX graph with Elo-style adaptive difficulty
3. **Explainable rubric-based scoring** — every score has auditable per-dimension evidence
4. **Benchmark validation** — MAE, RMSE, and Pearson R vs human-annotated ground truth
5. **Ablation study** — each evaluator's contribution measured and reported

---

## Quick Start

```bash
# 1. Clone and set up virtual environment
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# 3. Configure environment
cp .env.example .env
# Edit .env and set SECRET_KEY

# 4. Initialise database and seed data
python database/db_setup.py
python database/seed_data.py

# 5. Run benchmark validation
python scripts/run_full_validation.py

# 6. Run all tests
python scripts/run_all_tests.py

# 7. Start backend (Terminal 1)
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload

# 8. Start frontend (Terminal 2)
streamlit run app.py
```

---

## Architecture

```
Streamlit Frontend
      │ HTTP
      ▼
FastAPI Backend  (Routes → Services → AI Core)
      │
      ├── AI Core  ← evaluation, skill graph, recommendations, resume
      ├── Services ← business orchestration
      └── Database ← SQLAlchemy ORM (SQLite)
```

---

## Documentation

| Document | Location |
|----------|----------|
| AI/ML Design | [docs/AI_ML_DESIGN.md](docs/AI_ML_DESIGN.md) |
| Software Architecture | [docs/SOFTWARE_ARCHITECTURE.md](docs/SOFTWARE_ARCHITECTURE.md) |
| Database Model | [docs/DATABASE_MODEL.md](docs/DATABASE_MODEL.md) |
| AI Governance | [docs/AI_GOVERNANCE.md](docs/AI_GOVERNANCE.md) |
| Error Analysis | [docs/ERROR_ANALYSIS_REPORT.md](docs/ERROR_ANALYSIS_REPORT.md) |
| Ablation Study | [docs/ABLATION_STUDY_REPORT.md](docs/ABLATION_STUDY_REPORT.md) |
| Full Project Report | [docs/PROJECT_REPORT.md](docs/PROJECT_REPORT.md) |

---

## Validation

```bash
# Run all tests (grouped by module)
python scripts/run_all_tests.py

# Run benchmark + ablation + error analysis
python scripts/run_full_validation.py

# Generate complete final report
python scripts/generate_final_report.py

# Resume pipeline integration test
python scripts/test_resume_pipeline_integration.py
```

---

## Known Limitations

- Concept coverage depends on ontology completeness (see AI_GOVERNANCE.md)
- Benchmark dataset is small (17 annotated answers) — results are indicative
- Non-native English speakers may score lower on communication dimensions
- HR questions are harder to evaluate automatically than technical questions

Full limitation and bias documentation: [docs/AI_GOVERNANCE.md](docs/AI_GOVERNANCE.md)

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit |
| Backend | FastAPI + JWT |
| Database | SQLite via SQLAlchemy |
| NLP | spaCy + NLTK |
| Embeddings | Sentence Transformers (all-MiniLM-L6-v2) |
| Skill Graph | NetworkX |
| ML | Scikit-learn |
| Validation | Pydantic v2 |
| Testing | pytest |

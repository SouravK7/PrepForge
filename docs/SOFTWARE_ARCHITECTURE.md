# Software Architecture Document
## AI-Powered Interview Preparation and Career Readiness Assistant
**Version:** 1.0.0  

---

## 1. Architecture Overview

This system follows a layered architecture where AI pipelines are
the core and all other components serve them.

```
┌─────────────────────────────────────────────────────────┐
│                  Streamlit Frontend                     │
└─────────────────────────────────────────────────────────┘
                          │ HTTP (requests)
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  FastAPI Backend                        │
│            (Routes → Services → AI Core)               │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
│   AI Core    │  │   Database   │  │    Services      │
│              │  │              │  │                  │
│ evaluation   │  │ SQLAlchemy   │  │ interview svc    │
│ skill graph  │  │ repositories │  │ evaluation svc   │
│ recommender  │  │ SQLite       │  │ competency svc   │
│ resume intel │  │              │  │ analytics svc    │
└──────────────┘  └──────────────┘  └──────────────────┘
```

---

## 2. Layer Responsibilities

### Frontend (Streamlit)
- Presents AI outputs to users
- Calls FastAPI backend via HTTP
- Manages session state (auth token, interview state)
- **No AI logic**
- **No database access**

### Backend (FastAPI)
- Receives HTTP requests
- Validates input with Pydantic
- Calls service layer
- Returns structured JSON responses
- JWT authentication and dependency injection
- **No AI logic**
- **No SQL queries**

### Service Layer
- Orchestrates AI pipelines and repositories
- Contains all business logic
- **No ML code**
- **No raw SQL**

### AI Core
- All ML and NLP processing
- **No database access**
- **No business logic**
- All inputs/outputs via typed Pydantic schemas

### Database Layer
- SQLAlchemy ORM models
- Repository pattern (all queries inside repositories)
- **No AI logic**
- **No business logic**

---

## 3. Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend | Streamlit | 1.32+ |
| Backend | FastAPI | 0.110+ |
| Database | SQLite via SQLAlchemy | 2.0+ |
| Validation | Pydantic v2 | 2.6+ |
| Auth | JWT (python-jose) | 3.3+ |
| Core NLP | spaCy + NLTK | 3.7+ / 3.8+ |
| Embeddings | Sentence Transformers | 2.5+ |
| ML | Scikit-learn | 1.4+ |
| Graph | NetworkX | 3.2+ |
| Visualization | Plotly | 5.19+ |
| Resume | pdfplumber + python-docx | Latest |
| Testing | pytest | 8.0+ |

---

## 4. Folder Structure

```
interview_assistant/
├── ai_core/               ← AI/ML pipelines
│   ├── shared/            ← NLP infrastructure (models, embeddings, text)
│   ├── evaluation_pipeline/  ← 5 evaluators + fusion + explainability
│   ├── skill_pipeline/       ← Competency graph + Elo + gap analysis
│   ├── recommendation_pipeline/ ← Roadmap + resource matching
│   ├── resume_pipeline/      ← Resume parsing + skill extraction
│   └── question_pipeline/    ← Question selection + adaptive difficulty
├── schemas/               ← Pydantic data contracts (only source of truth)
├── configs/               ← YAML configuration (no hardcoded values)
├── data/                  ← Knowledge assets (competencies, questions, rubrics)
├── database/              ← ORM models + repository methods
├── services/              ← Business orchestration layer
├── api/                   ← FastAPI routes + middleware
├── frontend/              ← Streamlit pages + components
├── benchmark/             ← Scientific validation framework
├── tests/                 ← Test suite
└── docs/                  ← Project documentation
```

---

## 5. API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /api/auth/register | ✗ | Create account |
| POST | /api/auth/login | ✗ | Login and receive JWT |
| GET | /api/auth/me | ✓ | Get current user profile |
| POST | /api/interview/start | ✓ | Start interview session |
| POST | /api/interview/submit-answer | ✓ | Submit and evaluate answer |
| POST | /api/interview/next-question | ✓ | Get adaptive next question |
| POST | /api/interview/complete | ✓ | Finalize session |
| GET | /api/interview/history | ✓ | Session history |
| GET | /api/evaluation/session/{id} | ✓ | Session evaluations |
| GET | /api/competencies/graph | ✓ | Skill graph |
| GET | /api/competencies/gaps | ✓ | Skill gaps for role |
| GET | /api/competencies/readiness | ✓ | Readiness percentage |
| POST | /api/recommendations/generate | ✓ | Generate learning roadmap |
| GET | /api/recommendations/ | ✓ | Get saved recommendations |
| GET | /api/analytics/dashboard | ✓ | Dashboard statistics |
| POST | /api/benchmark/run | ✓ | Run benchmark validation |
| POST | /api/benchmark/ablation | ✓ | Run ablation study |

---

## 6. Data Flow: Answer Evaluation

```
User submits answer via Streamlit
    ↓
POST /api/interview/submit-answer  (FastAPI route)
    ↓
InterviewService.submit_answer()
    ↓
AnswerRepository.create()          → saves raw answer to DB
    ↓
EvaluationOrchestrator.evaluate()
    ↓
[SemanticEvaluator, ConceptEvaluator, CommunicationEvaluator,
 EvidenceEvaluator, ReasoningEvaluator] → 5 dimension scores
    ↓
ScoreFusion.fuse()                 → weighted final score
    ↓
ExplainabilityEngine               → human-readable reasons
    ↓
EvaluationRepository.create_from_output() → saves to DB
    ↓
CompetencyScoreRepository.upsert() → updates skill Elo
    ↓
SubmitAnswerResponse                → returned to frontend
    ↓
Streamlit displays scores, grade, concepts, improvement tip
```

---

## 7. Design Decisions

### 7.1 Why SQLite?
Zero configuration, portable single-file database. Appropriate for
an academic capstone with a single concurrent user. The SQLAlchemy ORM
makes migration to PostgreSQL a one-line change (DATABASE_URL).

### 7.2 Why Streamlit?
Fastest path from AI pipeline to interactive UI. Streamlit's reactive
model suits the sequential interview flow (question → answer → result).

### 7.3 Why Repository Pattern?
Separates SQL queries from business logic. Services never write SQL.
Makes unit testing trivial (mock the repository, not the database).

### 7.4 Why Pydantic v2?
Type-safe inter-layer communication. All data crossing layer boundaries
is validated. No silent type mismatches between AI outputs and API responses.

### 7.5 Why Configurable Weights?
Evaluation weights are in `configs/scoring_weights.yaml`, not in code.
Changing question type weights for research requires no code change,
only YAML edit and restart.

---

## 8. Coding Standards

- Python 3.10+ throughout
- Type hints required on all function signatures
- Google-style docstrings on all classes and public methods
- No raw SQL outside `database/repositories.py`
- No ML code outside `ai_core/`
- No business logic in `api/routes/`
- All inter-module data passed via Pydantic schemas
- All tunable values in YAML configs, not hardcoded

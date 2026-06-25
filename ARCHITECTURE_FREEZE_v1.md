# ARCHITECTURE_FREEZE_v1.md
# AI-Powered Interview Preparation and Career Readiness Assistant
# Version: 1.0.0
# Status: FROZEN
# Date: 2025
# ─────────────────────────────────────────────────────────────────
# This document is the single source of truth for this project.
# No architectural changes are permitted during implementation.
# If a design conflict is discovered during coding,
# report it. Do not modify this document or the architecture.
# ─────────────────────────────────────────────────────────────────

---

# 1. PROJECT VISION

## 1.1 Title
AI-Powered Interview Preparation and Career Readiness Assistant

## 1.2 One-Line Description
A competency-driven adaptive interview assessment system
using a hybrid AI architecture with explainable multi-dimensional
NLP scoring, validated against human-annotated benchmark data.

## 1.3 Core Philosophy
The interface exists to serve the AI.
The AI exists to serve the competency model.
The competency model exists to serve the user.

## 1.4 Research Contributions
This project makes the following original contributions:

Contribution 1:
  A competency-driven assessment model that replaces
  question-centric interview evaluation with a
  structured competency graph that evolves across sessions.

Contribution 2:
  A hybrid NLP evaluation ensemble combining
  semantic similarity, concept coverage, communication
  quality, evidence detection, and reasoning depth,
  outperforming semantic-similarity-only baselines.

Contribution 3:
  An Elo-style adaptive skill estimation engine that
  dynamically adjusts question difficulty based on
  demonstrated competency confidence.

Contribution 4:
  Explainable rubric-based scoring with auditable
  evidence per evaluation criterion, making every
  score traceable to observable answer content.

Contribution 5:
  A benchmark validation study comparing AI evaluation
  scores against human-annotated ground truth using
  MAE, RMSE, and Pearson/Spearman correlation metrics.

---

# 2. HYBRID AI ARCHITECTURE

## 2.1 Architecture Type
Hybrid AI System combining:

  Layer 1: Statistical NLP
    - Sentence Transformers for semantic similarity
    - TF-IDF for keyword relevance
    - Cosine similarity for answer comparison

  Layer 2: Rule-Based Reasoning
    - Concept coverage checking against ontology
    - Rubric-based scoring criteria
    - Required concept matching per question

  Layer 3: Knowledge Graph
    - Competency graph with confidence scores
    - Skill dependency mapping
    - Ontology-based skill normalization

  Layer 4: ML Models
    - Scikit-learn for recommendation ranking
    - Elo rating system for adaptive difficulty
    - Content-based filtering for resources

  Layer 5: LLM (Optional Enhancement)
    - Follow-up question generation
    - HR answer qualitative feedback
    - Resume parsing assistance

## 2.2 Core Design Principles

Principle 1: AI First
  Every module exists to serve the AI pipeline.
  The UI is built last.
  The database serves the AI, not the other way around.

Principle 2: Competency Central
  Every component updates, reads, or depends on
  the competency model.
  Questions are temporary.
  Competencies are permanent.

Principle 3: Explainability Required
  Every score must have a human-readable reason.
  No mysterious numbers.
  Every evaluation criterion must reference
  observable evidence in the answer.

Principle 4: Ensemble Over Monolith
  No single evaluator does everything.
  Each evaluator has one responsibility.
  Score fusion combines them with configurable weights.

Principle 5: Configuration Driven
  No hardcoded weights, roles, or thresholds.
  All tunable values live in YAML config files.

Principle 6: Benchmark Driven
  The evaluator is not done when it is built.
  It is done when it passes the benchmark targets.

---

# 3. FINAL FOLDER STRUCTURE

```
interview_assistant/
│
├── ARCHITECTURE_FREEZE_v1.md          ← This file
├── app.py                             ← Streamlit entry point
├── api.py                             ← FastAPI entry point
├── requirements.txt                   ← All dependencies
├── pyproject.toml                     ← Project metadata
├── .env.example                       ← Environment template
├── .gitignore                         ← Git ignore rules
├── README.md                          ← Project overview
│
├── ai_core/                           ← HEART OF THE PROJECT
│   ├── __init__.py
│   │
│   ├── shared/                        ← Shared AI infrastructure
│   │   ├── __init__.py
│   │   ├── model_manager.py           ← Singleton model loader
│   │   ├── text_processor.py          ← NLP preprocessing
│   │   ├── embedding_service.py       ← Embedding generation
│   │   ├── embedding_cache.py         ← Embedding cache
│   │   ├── similarity.py              ← Similarity calculations
│   │   ├── config_loader.py           ← YAML config reader
│   │   └── ai_logger.py               ← AI decision logger
│   │
│   ├── evaluation_pipeline/           ← Evaluation ensemble
│   │   ├── __init__.py
│   │   ├── base_evaluator.py          ← Abstract base class
│   │   ├── semantic_evaluator.py      ← Semantic similarity
│   │   ├── concept_evaluator.py       ← Concept coverage
│   │   ├── communication_evaluator.py ← Grammar and clarity
│   │   ├── evidence_evaluator.py      ← Examples detection
│   │   ├── reasoning_evaluator.py     ← Depth and logic
│   │   ├── score_fusion.py            ← Weighted combination
│   │   ├── explainability.py          ← Score explanation
│   │   └── evaluation_orchestrator.py ← Orchestrates pipeline
│   │
│   ├── skill_pipeline/                ← Competency tracking
│   │   ├── __init__.py
│   │   ├── competency_graph.py        ← Knowledge graph
│   │   ├── confidence_updater.py      ← Update skill scores
│   │   ├── elo_estimator.py           ← Adaptive difficulty
│   │   └── skill_gap_analyzer.py      ← Gap identification
│   │
│   ├── recommendation_pipeline/       ← Personalized roadmap
│   │   ├── __init__.py
│   │   ├── resource_matcher.py        ← Match resources to gaps
│   │   ├── roadmap_generator.py       ← Weekly learning plan
│   │   ├── practice_generator.py      ← Practice questions
│   │   └── recommender.py             ← Orchestrates pipeline
│   │
│   ├── resume_pipeline/               ← Resume intelligence
│   │   ├── __init__.py
│   │   ├── resume_parser.py           ← Extract raw text
│   │   ├── skill_extractor.py         ← NLP skill extraction
│   │   ├── skill_normalizer.py        ← Normalize skill names
│   │   ├── resume_confidence.py       ← Resume quality score
│   │   └── resume_question_mapper.py  ← Map skills to questions
│   │
│   └── question_pipeline/             ← Question generation
│       ├── __init__.py
│       ├── question_selector.py       ← Role-based selection
│       ├── adaptive_selector.py       ← Difficulty-adaptive
│       └── followup_generator.py      ← Context follow-ups
│
├── schemas/                           ← Pydantic data contracts
│   ├── __init__.py
│   ├── competency_schema.py
│   ├── question_schema.py
│   ├── rubric_schema.py
│   ├── answer_schema.py
│   ├── evaluation_schema.py
│   ├── recommendation_schema.py
│   ├── benchmark_schema.py
│   ├── resume_schema.py
│   └── report_schema.py
│
├── configs/                           ← YAML configuration files
│   ├── models.yaml
│   ├── scoring_weights.yaml
│   ├── roles.yaml
│   ├── competencies.yaml
│   ├── rubrics.yaml
│   ├── success_criteria.yaml
│   └── app_config.yaml
│
├── data/                              ← Knowledge assets
│   ├── competencies/
│   │   ├── software_engineer.json
│   │   ├── data_analyst.json
│   │   └── ai_engineer.json
│   ├── questions/
│   │   ├── software_engineer.json
│   │   ├── data_analyst.json
│   │   └── ai_engineer.json
│   ├── rubrics/
│   │   ├── technical_rubrics.json
│   │   └── hr_rubrics.json
│   ├── resources/
│   │   └── learning_resources.json
│   └── benchmark/
│       ├── oop_benchmark_v1.json
│       ├── sql_benchmark_v1.json
│       └── hr_benchmark_v1.json
│
├── database/                          ← Data persistence layer
│   ├── __init__.py
│   ├── db_setup.py                    ← Schema creation
│   ├── models.py                      ← SQLAlchemy models
│   ├── repositories.py                ← CRUD operations
│   └── seed_data.py                   ← Initial data loader
│
├── services/                          ← Business logic layer
│   ├── __init__.py
│   ├── interview_service.py           ← Interview orchestration
│   ├── evaluation_service.py          ← Evaluation orchestration
│   ├── competency_service.py          ← Competency management
│   ├── recommendation_service.py      ← Recommendation logic
│   ├── resume_service.py              ← Resume processing
│   ├── analytics_service.py           ← Performance analytics
│   └── report_service.py              ← Report generation
│
├── api/                               ← FastAPI backend
│   ├── __init__.py
│   ├── main.py                        ← FastAPI app
│   ├── dependencies.py                ← Shared dependencies
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── interview_routes.py
│   │   ├── evaluation_routes.py
│   │   ├── recommendation_routes.py
│   │   ├── resume_routes.py
│   │   └── analytics_routes.py
│   └── middleware/
│       ├── __init__.py
│       └── error_handler.py
│
├── frontend/                          ← Streamlit UI
│   ├── __init__.py
│   ├── streamlit_app.py               ← Main Streamlit app
│   ├── pages/
│   │   ├── home.py
│   │   ├── interview.py
│   │   ├── results.py
│   │   ├── skill_map.py
│   │   ├── recommendations.py
│   │   ├── resume_upload.py
│   │   └── benchmark_dashboard.py
│   └── components/
│       ├── score_cards.py
│       ├── charts.py
│       ├── rubric_view.py
│       └── sidebar.py
│
├── benchmark/                         ← Scientific validation
│   ├── __init__.py
│   ├── run_benchmark.py               ← Main benchmark runner
│   ├── metrics.py                     ← MAE, RMSE, Pearson
│   ├── ablation_runner.py             ← Ablation study
│   ├── error_analysis.py              ← Error analysis
│   └── reports/                       ← Generated reports
│
├── prompts/                           ← LLM prompt templates
│   ├── v1/
│   │   ├── evaluate_technical.md
│   │   ├── evaluate_hr.md
│   │   ├── generate_followup.md
│   │   └── parse_resume.md
│
├── tests/                             ← Test suite
│   ├── __init__.py
│   ├── test_semantic_evaluator.py
│   ├── test_concept_evaluator.py
│   ├── test_score_fusion.py
│   ├── test_competency_graph.py
│   ├── test_elo_estimator.py
│   ├── test_recommendation.py
│   └── test_resume_parser.py
│
├── logs/                              ← AI decision logs
│   └── ai_decisions.log
│
├── models/                            ← Saved/cached ML models
│   └── cache/
│
└── docs/                              ← Project documentation
    ├── AI_GOVERNANCE.md
    ├── AI_ML_DESIGN.md
    ├── SOFTWARE_ARCHITECTURE.md
    └── DATABASE_MODEL.md
```

---

# 4. TECHNOLOGY STACK

| Layer | Technology | Justification |
|---|---|---|
| Frontend | Streamlit | Fast UI for AI demos |
| Backend API | FastAPI | Async, typed, auto-docs |
| Database | SQLite via SQLAlchemy | Zero config, demo-ready |
| Validation | Pydantic v2 | Type-safe data contracts |
| Core NLP | spaCy + NLTK | Production NLP pipeline |
| Embeddings | Sentence Transformers | Semantic understanding |
| ML Models | Scikit-learn | Recommendations, ranking |
| Skill Graph | NetworkX | Graph operations |
| Visualization | Plotly | Interactive charts |
| Resume Parsing | pdfplumber + python-docx | Multi-format support |
| Config | PyYAML | Configuration management |
| Testing | pytest | Test suite |
| Optional LLM | HuggingFace / OpenAI | Enhanced generation |

---

# 5. DOMAIN MODEL

## 5.1 Competency Structure

A Competency is the central unit of this system.
Questions serve competencies.
Evaluations update competencies.
Recommendations target competencies.

```
Competency {
  id:                 string      (unique identifier)
  name:               string      (human readable name)
  description:        string      (what this competency covers)
  parent_id:          string|null (parent competency for hierarchy)
  children:           list[str]   (child competency ids)
  role_relevance:     dict        (role -> weight 0.0-1.0)
  difficulty_level:   string      (beginner/intermediate/advanced)
  required_concepts:  list[str]   (concepts that must be known)
  related_resources:  list[str]   (resource ids)
  confidence_score:   float       (0.0 - 1.0, updated per answer)
  evidence_count:     int         (number of times assessed)
  elo_rating:         float       (adaptive difficulty rating)
  last_assessed:      datetime|null
  improvement_trend:  float       (positive = improving)
}
```

## 5.2 Competency Hierarchy Example

```
Software Engineering
├── Programming Fundamentals
│   ├── OOP Concepts
│   │   ├── Classes and Objects
│   │   ├── Inheritance
│   │   ├── Polymorphism
│   │   └── Encapsulation
│   └── Data Structures
│       ├── Arrays
│       ├── Linked Lists
│       ├── Trees
│       └── Hash Maps
├── Database Systems
│   ├── SQL Fundamentals
│   │   ├── Joins
│   │   ├── Aggregations
│   │   └── Indexes
│   └── Database Design
│       ├── Normalization
│       └── ER Diagrams
└── System Design
    ├── REST APIs
    ├── Scalability
    └── Design Patterns
```

## 5.3 Question Structure

```
Question {
  id:                 string
  competency_id:      string        (which competency this tests)
  question_text:      string
  question_type:      string        (technical | hr)
  difficulty:         string        (beginner | intermediate | advanced)
  elo_difficulty:     float         (numeric difficulty for Elo)
  category:           string
  required_concepts:  list[str]     (must be in answer)
  optional_concepts:  list[str]     (bonus if in answer)
  sample_answer:      string        (reference answer)
  rubric_id:          string        (which rubric to apply)
  follow_up_hints:    list[str]     (potential follow-up directions)
  role_tags:          list[str]     (which roles this applies to)
}
```

## 5.4 Rubric Structure

```
Rubric {
  id:                 string
  name:               string
  question_type:      string        (technical | hr)
  criteria: [
    {
      name:           string
      weight:         float
      description:    string
      scoring_guide: {
        0-25:         string        (poor answer indicators)
        26-50:        string        (below average indicators)
        51-75:        string        (average answer indicators)
        76-100:       string        (excellent answer indicators)
      }
    }
  ]
}
```

## 5.5 Evaluation Structure

```
Evaluation {
  id:                   string
  session_id:           string
  answer_id:            string
  competency_id:        string
  question_id:          string

  scores: {
    semantic:           float       (0-100)
    concept:            float       (0-100)
    communication:      float       (0-100)
    evidence:           float       (0-100)
    reasoning:          float       (0-100)
    weighted_final:     float       (0-100)
  }

  grade:                string      (A/B/C/D/F)
  readiness_level:      string      (excellent/good/average/poor)

  evidence: {
    matched_concepts:   list[str]
    missing_concepts:   list[str]
    detected_examples:  list[str]
    grammar_issues:     list[str]
    strengths:          list[str]
    weaknesses:         list[str]
  }

  explanation: {
    semantic_reason:    string
    concept_reason:     string
    communication_reason: string
    evidence_reason:    string
    reasoning_reason:   string
    overall_summary:    string
    improvement_tip:    string
  }

  competency_delta:     float       (change in confidence)
  evaluated_at:         datetime
}
```

---

# 6. EVALUATION ENSEMBLE DESIGN

## 6.1 Pipeline Flow

```
User Answer (string)
      │
      ▼
TextProcessor
  - Tokenize
  - Lemmatize
  - Remove stopwords
  - POS tagging
      │
      ▼
EmbeddingService
  - Generate answer embedding
  - Load from cache if seen
      │
      ├─────────────────────────────────────┐
      ▼                                     ▼
SemanticEvaluator                   ConceptEvaluator
  - Cosine similarity                 - Check required concepts
  - vs sample answer embedding        - Check optional concepts
  - Score: 0-100                      - Coverage percentage
                                      - Score: 0-100
      │                                     │
      ▼                                     ▼
CommunicationEvaluator              EvidenceEvaluator
  - Grammar check (spaCy)             - Example detection
  - Sentence structure                - Real-world reference
  - Fluency scoring                   - Specific case mentions
  - Technical term usage              - Score: 0-100
  - Score: 0-100
      │                                     │
      └──────────────┬──────────────────────┘
                     ▼
             ReasoningEvaluator
               - Logical structure
               - Argument coherence
               - Depth of explanation
               - Score: 0-100
                     │
                     ▼
               ScoreFusion
               - Apply weights from scoring_weights.yaml
               - Separate weights for technical vs HR
               - Produce weighted_final_score
                     │
                     ▼
              Explainability
               - Generate reason per dimension
               - Highlight matched concepts
               - Highlight missing concepts
               - Generate improvement tip
                     │
                     ▼
           EvaluationOutput (Pydantic Schema)
```

## 6.2 Scoring Weights

Technical Questions:
```
  concept_coverage:     0.35
  semantic_similarity:  0.20
  reasoning_depth:      0.20
  evidence_examples:    0.15
  communication:        0.10
```

HR Questions:
```
  semantic_similarity:  0.25
  communication:        0.25
  evidence_examples:    0.25
  reasoning_depth:      0.15
  concept_coverage:     0.10
```

These weights are stored in configs/scoring_weights.yaml.
They must not be hardcoded in Python files.

## 6.3 Grade Boundaries

```
  90-100:   A  (Excellent)
  75-89:    B  (Good)
  60-74:    C  (Average)
  40-59:    D  (Below Average)
  0-39:     F  (Poor)
```

---

# 7. ADAPTIVE ENGINE DESIGN

## 7.1 Elo-Style Skill Estimation

Each competency has an Elo rating.
Each question has an Elo difficulty.
After each answer, ratings are updated.

Formulas:
```
expected_score = 1 / (1 + 10 ^ ((question_elo - skill_elo) / 400))
actual_score   = normalized answer score (0.0 to 1.0)
new_skill_elo  = old_skill_elo + K * (actual_score - expected_score)

K = 32 (standard K-factor)
```

Starting Elo values:
```
  Beginner questions:     900
  Intermediate questions: 1200
  Advanced questions:     1500
  Expert questions:       1800

  New user skill rating:  1000
```

## 7.2 Difficulty Adjustment Logic

```
  If skill_elo >= 1400:   select Advanced or Expert questions
  If skill_elo 1100-1399: select Intermediate questions
  If skill_elo < 1100:    select Beginner questions
```

## 7.3 Interview Phase Blueprint

```
  Phase 1: Introduction (1-2 HR questions)
  Phase 2: Resume Verification (1-2 questions from resume skills)
  Phase 3: Core Technical (4-5 adaptive technical questions)
  Phase 4: Scenario Based (1-2 applied questions)
  Phase 5: Behavioral (1-2 HR behavioral questions)
  Phase 6: Closing (1 HR motivation question)
```

---

# 8. SKILL GRAPH DESIGN

## 8.1 Graph Structure

Nodes: Competencies
Edges: Dependency relationships (prerequisite)

```
  Node properties:
    - competency_id
    - confidence_score (0.0-1.0)
    - elo_rating
    - evidence_count
    - last_assessed

  Edge properties:
    - relationship_type (prerequisite | related | advanced_of)
    - strength (0.0-1.0)
```

## 8.2 Confidence Update Formula

```
  new_confidence = old_confidence + learning_rate * (score - old_confidence)
  learning_rate  = 0.3 (tunable in configs/app_config.yaml)
```

## 8.3 Skill Gap Identification

```
  gap = required_confidence - current_confidence
  priority = gap * role_relevance_weight

  Priority tiers:
    High:   gap >= 0.4
    Medium: gap 0.2-0.39
    Low:    gap < 0.2
```

---

# 9. DATABASE SCHEMA

## Tables

### users
```
  id              INTEGER PRIMARY KEY
  username        TEXT UNIQUE NOT NULL
  email           TEXT UNIQUE NOT NULL
  password_hash   TEXT NOT NULL
  full_name       TEXT
  target_role     TEXT
  experience_level TEXT
  created_at      TIMESTAMP
  updated_at      TIMESTAMP
```

### competency_scores
```
  id              INTEGER PRIMARY KEY
  user_id         INTEGER FK users
  competency_id   TEXT NOT NULL
  confidence      REAL DEFAULT 0.0
  elo_rating      REAL DEFAULT 1000.0
  evidence_count  INTEGER DEFAULT 0
  last_assessed   TIMESTAMP
  improvement_trend REAL DEFAULT 0.0
```

### sessions
```
  id              INTEGER PRIMARY KEY
  user_id         INTEGER FK users
  job_role        TEXT NOT NULL
  difficulty      TEXT
  status          TEXT DEFAULT 'in_progress'
  overall_score   REAL DEFAULT 0.0
  readiness_level TEXT
  started_at      TIMESTAMP
  completed_at    TIMESTAMP
```

### questions_asked
```
  id              INTEGER PRIMARY KEY
  session_id      INTEGER FK sessions
  question_id     TEXT NOT NULL
  competency_id   TEXT NOT NULL
  phase           TEXT
  asked_at        TIMESTAMP
```

### answers
```
  id              INTEGER PRIMARY KEY
  session_id      INTEGER FK sessions
  user_id         INTEGER FK users
  question_id     TEXT NOT NULL
  competency_id   TEXT NOT NULL
  answer_text     TEXT NOT NULL
  time_taken      INTEGER
  submitted_at    TIMESTAMP
```

### evaluations
```
  id                    INTEGER PRIMARY KEY
  answer_id             INTEGER FK answers
  session_id            INTEGER FK sessions
  user_id               INTEGER FK users
  semantic_score        REAL
  concept_score         REAL
  communication_score   REAL
  evidence_score        REAL
  reasoning_score       REAL
  weighted_final        REAL
  grade                 TEXT
  matched_concepts      TEXT (JSON)
  missing_concepts      TEXT (JSON)
  strengths             TEXT (JSON)
  weaknesses            TEXT (JSON)
  explanation           TEXT (JSON)
  competency_delta      REAL
  evaluated_at          TIMESTAMP
```

### recommendations
```
  id              INTEGER PRIMARY KEY
  user_id         INTEGER FK users
  session_id      INTEGER FK sessions
  competency_id   TEXT
  title           TEXT
  description     TEXT
  resource_url    TEXT
  resource_type   TEXT
  priority        TEXT
  week_number     INTEGER
  is_completed    INTEGER DEFAULT 0
  created_at      TIMESTAMP
```

### resumes
```
  id                    INTEGER PRIMARY KEY
  user_id               INTEGER FK users
  file_name             TEXT
  raw_text              TEXT
  extracted_skills      TEXT (JSON)
  extracted_education   TEXT (JSON)
  extracted_experience  TEXT (JSON)
  resume_quality_score  REAL
  parsed_at             TIMESTAMP
```

### benchmark_results
```
  id              INTEGER PRIMARY KEY
  run_id          TEXT
  experiment_name TEXT
  question_id     TEXT
  answer_type     TEXT
  human_score     REAL
  ai_score        REAL
  absolute_error  REAL
  run_at          TIMESTAMP
```

### ai_decision_logs
```
  id              INTEGER PRIMARY KEY
  session_id      TEXT
  decision_type   TEXT
  input_summary   TEXT
  output_summary  TEXT
  reasoning       TEXT
  confidence      REAL
  logged_at       TIMESTAMP
```

---

# 10. API ENDPOINTS

```
POST   /api/auth/register
POST   /api/auth/login

POST   /api/interview/start
POST   /api/interview/answer
GET    /api/interview/next-question/{session_id}
GET    /api/interview/session/{session_id}/results
GET    /api/interview/history/{user_id}

POST   /api/resume/upload
GET    /api/resume/{user_id}

GET    /api/competencies/{user_id}
GET    /api/competencies/{user_id}/gaps
GET    /api/competencies/{user_id}/graph

GET    /api/recommendations/{user_id}
GET    /api/recommendations/{user_id}/roadmap

GET    /api/analytics/{user_id}/dashboard
GET    /api/analytics/{user_id}/progress

POST   /api/benchmark/run
GET    /api/benchmark/results/{run_id}
```

---

# 11. BENCHMARK AND VALIDATION PLAN

## 11.1 Dataset Structure

Per question in benchmark dataset:
```
{
  "question_id": string,
  "question_text": string,
  "competency_id": string,
  "required_concepts": list,
  "answers": [
    {
      "type": "poor | average | good | excellent",
      "text": string,
      "human_score": float (0-100),
      "annotator_scores": list[float],
      "notes": string
    }
  ]
}
```

## 11.2 Evaluation Metrics

```
  MAE    = mean(|ai_score - human_score|)
  RMSE   = sqrt(mean((ai_score - human_score)^2))
  Pearson R  = linear correlation
  Spearman R = rank correlation
```

## 11.3 Success Criteria

```
  Concept Evaluator alone:   Pearson R >= 0.80
  Full Ensemble:             Pearson R >= 0.85
  Full Ensemble:             MAE <= 12 points
  Resume Parser:             Skill extraction >= 80% accuracy
  Adaptive Engine:           Convergence within 5 sessions
  API Response Time:         <= 500ms without LLM
  API Response Time:         <= 2000ms with LLM
```

## 11.4 Ablation Study Plan

```
  Experiment 1: Semantic only
  Experiment 2: Semantic + Concept
  Experiment 3: Semantic + Concept + Evidence
  Experiment 4: Semantic + Concept + Evidence + Communication
  Experiment 5: Full Ensemble (all evaluators)

  Report: Pearson R and MAE for each experiment.
  Goal: Demonstrate each evaluator adds measurable value.
```

## 11.5 Error Analysis Plan

```
  After benchmark run, group errors by:
    - Question type (technical vs HR)
    - Competency category
    - Answer type (poor/average/good/excellent)
    - Score range

  Identify:
    - Where AI consistently over-scores
    - Where AI consistently under-scores
    - Pattern in largest errors

  Document findings in:
    docs/ERROR_ANALYSIS_REPORT.md
```

---

# 12. CODING STANDARDS

## 12.1 Python Standards
```
  Python version:       3.10+
  Type hints:           Required on all functions
  Docstrings:           Google style on all classes and functions
  Line length:          88 characters (Black formatter)
  Imports:              Sorted (isort)
```

## 12.2 File Naming
```
  Python files:         snake_case.py
  Classes:              PascalCase
  Functions:            snake_case
  Constants:            UPPER_SNAKE_CASE
  Config keys:          snake_case
```

## 12.3 AI Module Rules
```
  - No AI module loads models directly
  - All models loaded through ModelManager only
  - No business logic in AI pipeline files
  - No database calls in AI pipeline files
  - All inputs and outputs use Pydantic schemas
  - All AI decisions logged through AILogger
```

## 12.4 Service Layer Rules
```
  - Services orchestrate AI pipelines and repositories
  - Services do not contain ML logic
  - Services do not contain SQL queries directly
  - Services use repositories for data access
```

## 12.5 API Rules
```
  - Routes only call services
  - Routes do not contain business logic
  - All request/response bodies use Pydantic schemas
  - All errors return structured JSON responses
```

---

# 13. PHASE LOCK RULES

```
Phase 0:  Architecture Design          ← LOCKED (this document)

Phase 1:  Project Scaffold             ← Unlock after folder
          Requirements                   structure confirmed

Phase 2:  Schemas and Configs          ← Unlock after schemas
                                         pass validation tests

Phase 3:  AI Shared Infrastructure     ← Unlock after model
                                         loading confirmed

Phase 4:  Evaluation Ensemble          ← Unlock after POC
                                         produces valid scores

Phase 5:  Benchmark Validation         ← Unlock after Pearson
                                         R >= 0.80 achieved

Phase 6:  Skill Graph and Adaptive     ← Unlock after Phase 5
          Engine

Phase 7:  Recommendation Engine        ← Unlock after Phase 6

Phase 8:  Resume Intelligence          ← Unlock after Phase 7

Phase 9:  Database Layer               ← Unlock after Phase 8

Phase 10: Service Layer                ← Unlock after Phase 9

Phase 11: FastAPI Backend              ← Unlock after Phase 10

Phase 12: Streamlit Frontend           ← Unlock after Phase 11

Phase 13: Final Polish and Docs        ← Unlock after Phase 12
```

---

# 14. AI GOVERNANCE

## 14.1 Known Limitations
```
  - Short answers may be unfairly penalized by
    completeness scoring
  - Non-native English speakers may receive lower
    communication scores due to grammar weighting
  - Semantic similarity cannot verify factual accuracy
  - Concept coverage depends on quality of the ontology
  - System may not handle highly creative but correct
    answers that use different terminology
```

## 14.2 Bias Considerations
```
  - Grammar scoring may disadvantage non-native speakers
  - Question bank may reflect specific cultural contexts
  - Sample answers define the scoring ceiling
  - Elo rating may disadvantage users who start with
    harder questions by chance
```

## 14.3 Privacy
```
  - User answers are stored locally in SQLite
  - No answer data is sent to external APIs by default
  - Resume data is processed locally
  - LLM integration is optional and opt-in only
```

## 14.4 Human Oversight
```
  - AI scores should be treated as guidance only
  - Not as definitive evaluation of candidate capability
  - Human review recommended for high-stakes decisions
  - Users should be informed of AI limitations
```

## 14.5 Explainability Commitment
```
  - Every score has a documented reason
  - Users can see exactly what concepts were evaluated
  - No hidden scoring criteria
  - All evaluation rubrics are visible to users
```

---

# 15. ENVIRONMENT VARIABLES

```
# .env.example

APP_NAME=AI Interview Assistant
APP_VERSION=1.0.0
DEBUG=True

DATABASE_URL=sqlite:///interview_assistant.db

SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

OPENAI_API_KEY=optional
USE_LLM=False
LLM_PROVIDER=openai

EMBEDDING_MODEL=all-MiniLM-L6-v2
SPACY_MODEL=en_core_web_sm

LOG_LEVEL=INFO
LOG_FILE=logs/ai_decisions.log

DATA_VERSION=v1
BENCHMARK_VERSION=v1
MODEL_VERSION=1.0.0
```

---

# END OF ARCHITECTURE_FREEZE_v1.md
# Status: FROZEN
# No modifications permitted during implementation.
# Report conflicts. Do not change architecture.

# Database and Knowledge Model
## AI-Powered Interview Preparation and Career Readiness Assistant
**Version:** 1.0.0  

---

## 1. Database Overview

The system uses SQLite via SQLAlchemy ORM.

SQLite was chosen because:
- Zero configuration — no separate server process required
- Appropriate for single-instance academic deployment
- Easy to demo and test (single `.db` file)
- Fully portable across operating systems

For production scale, the SQLAlchemy ORM allows migration to PostgreSQL
by changing only the `DATABASE_URL` environment variable.

---

## 2. Entity Relationship

```
users
  │
  ├── sessions ──── answers ──── evaluations
  │
  ├── competency_scores
  │
  ├── recommendations
  │
  └── resumes

benchmark_runs    (standalone — not user-scoped)
ai_decision_logs  (standalone — audit trail)
```

---

## 3. Table Definitions

### `users`
Stores user accounts and hashed authentication credentials.
Primary entity. Every other user-scoped table references this.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer PK | Auto-increment primary key |
| username | String (unique) | Login identifier |
| email | String (unique) | Email address |
| hashed_password | String | bcrypt hash |
| full_name | String | Display name |
| target_role | String | Job role being prepared for |
| experience_level | String | fresher / junior / mid / senior |
| created_at | DateTime | Account creation timestamp |
| last_login | DateTime | Last successful login |

---

### `sessions`
One record per interview session.
Stores aggregate scores after session completion.

| Column | Type | Description |
|--------|------|-------------|
| id | String (UUID) | Unique session identifier |
| user_id | FK → users | Session owner |
| job_role | String | Role being practiced |
| difficulty | String | beginner / intermediate / advanced |
| total_questions | Integer | Planned question count |
| answered_questions | Integer | Actual answers submitted |
| overall_score | Float | Average evaluation score |
| technical_score | Float | Average technical question score |
| hr_score | Float | Average HR question score |
| readiness_level | String | poor / below_average / average / good / excellent |
| status | String | in_progress / completed / abandoned |
| started_at | DateTime | Session start time |
| completed_at | DateTime | Session completion time |

---

### `answers`
One record per submitted answer.
Raw answer text is stored for audit and potential future training.

| Column | Type | Description |
|--------|------|-------------|
| id | String (UUID) | Unique answer identifier |
| session_id | FK → sessions | Parent session |
| user_id | FK → users | Answer author |
| question_id | String | Question identifier from question bank |
| competency_id | String | Competency being assessed |
| question_text | String | The question as asked |
| user_answer | Text | The user's full answer text |
| question_type | String | technical / hr |
| time_taken | Integer | Seconds taken to answer |
| submitted_at | DateTime | Answer submission timestamp |

---

### `evaluations`
One record per evaluated answer.
Stores all 5 dimension scores, grade, concept evidence, and explanation.

| Column | Type | Description |
|--------|------|-------------|
| id | String (UUID) | Unique evaluation identifier |
| answer_id | FK → answers | Evaluated answer |
| session_id | FK → sessions | Parent session |
| user_id | FK → users | Evaluated user |
| competency_id | String | Competency assessed |
| semantic_score | Float | Semantic similarity score (0–100) |
| concept_score | Float | Concept coverage score (0–100) |
| communication_score | Float | Communication quality score (0–100) |
| evidence_score | Float | Evidence/examples score (0–100) |
| reasoning_score | Float | Reasoning depth score (0–100) |
| weighted_final | Float | Weighted fusion final score (0–100) |
| grade | String | A / B / C / D / F |
| readiness_level | String | poor / below_average / average / good / excellent |
| matched_concepts | JSON | List of matched concept strings |
| missing_concepts | JSON | List of missing concept strings |
| strengths | JSON | List of detected strengths |
| weaknesses | JSON | List of detected weaknesses |
| improvement_tip | String | Single highest-impact improvement tip |
| explanation | JSON | Per-dimension human-readable reasons |
| evaluated_at | DateTime | Evaluation timestamp |

---

### `competency_scores`
One record per (user, competency) pair.
Updated after every evaluation that touches this competency.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer PK | Auto-increment |
| user_id | FK → users | Score owner |
| competency_id | String | Competency identifier |
| confidence | Float | Current confidence 0.0–1.0 |
| elo_rating | Float | Current Elo rating |
| evidence_count | Integer | Total answers assessed |
| improvement_trend | Float | Positive = improving |
| last_assessed | DateTime | Most recent assessment time |

---

### `recommendations`
One record per learning recommendation.
Generated from skill gaps. Tracks completion status.

| Column | Type | Description |
|--------|------|-------------|
| id | String (UUID) | Unique recommendation identifier |
| user_id | FK → users | Recommendation recipient |
| session_id | String | Source session |
| competency_id | String | Targeted competency gap |
| competency_name | String | Human-readable competency name |
| title | String | Resource or action title |
| description | String | What to do and why |
| resource_url | String | Link to learning resource |
| resource_type | String | video / article / course / practice |
| priority | String | high / medium / low |
| week_number | Integer | Week in learning roadmap |
| estimated_hours | Float | Estimated study hours |
| is_completed | Boolean | Whether user marked done |
| created_at | DateTime | Recommendation creation time |
| completed_at | DateTime | Completion timestamp if done |

---

### `resumes`
Stores parsed resume data for a user.
One active resume per user at a time.

| Column | Type | Description |
|--------|------|-------------|
| id | String (UUID) | Unique resume identifier |
| user_id | FK → users | Resume owner |
| file_name | String | Original uploaded filename |
| raw_text | Text | Full extracted resume text |
| extracted_skills | JSON | List of ExtractedSkill dicts |
| competency_ids | JSON | Competency IDs detected from skills |
| quality_score | Float | Resume quality score 0–100 |
| parsed_at | DateTime | Parsing timestamp |

---

### `benchmark_runs`
Stores benchmark validation results.
Tracks MAE, RMSE, Pearson R, and Spearman R per run.

| Column | Type | Description |
|--------|------|-------------|
| id | String (UUID) | Run identifier |
| benchmark_name | String | Benchmark dataset name |
| pearson_r | Float | Pearson correlation coefficient |
| spearman_r | Float | Spearman rank correlation |
| mae | Float | Mean Absolute Error |
| rmse | Float | Root Mean Squared Error |
| total_answers | Integer | Number of answers evaluated |
| run_at | DateTime | Run timestamp |
| report_path | String | Path to saved report JSON |

---

### `ai_decision_logs`
Audit log of all significant AI decisions.
Used for transparency, debugging, and future analysis.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer PK | Auto-increment |
| session_id | String | Related session |
| user_id | Integer | Related user |
| decision_type | String | evaluation / question_selection / elo_update |
| input_summary | JSON | Key inputs that triggered the decision |
| output_summary | JSON | Key outputs of the decision |
| confidence | Float | Model confidence if available |
| logged_at | DateTime | Decision timestamp |

---

## 4. Knowledge Assets

### Competency Ontology (`data/competencies/`)

JSON files per role defining:
- Competency hierarchy (parent/children relationships)
- Required concepts per competency
- Role relevance weights per job title
- Elo difficulty ratings

Available roles: `software_engineer.json`, `data_analyst.json`, `ai_engineer.json`

### Question Bank (`data/questions/`)

JSON files per role with interview questions containing:
- Linked competency ID
- Required and optional concepts
- Sample answer for semantic comparison
- Rubric ID and follow-up hints
- Elo difficulty rating

### Rubrics (`data/rubrics/`)

JSON files defining evaluation criteria per question type.
Technical and HR rubrics have different criterion weights.
Each criterion has observable score band indicators.

### Benchmark Dataset (`data/benchmark/`)

Human-annotated answer sets for validation.
Each question has poor, below-average, average, good, and excellent answers.
Each answer has a human score from multiple annotators.

Files: `oop_benchmark_v1.json`, `sql_benchmark_v1.json`, `hr_benchmark_v1.json`

### Learning Resources (`data/resources/`)

Curated learning resources indexed by competency ID.
Used by the recommendation engine.

File: `learning_resources.json`

---

## 5. Data Versioning

```yaml
# configs/app_config.yaml
data_version:      "v1"
benchmark_version: "v1"
model_version:     "1.0.0"
```

Changing these values invalidates cached benchmark results
and forces a fresh run when the system detects a version mismatch.

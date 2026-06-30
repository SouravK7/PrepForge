# AI/ML Design Document
## AI-Powered Interview Preparation and Career Readiness Assistant
**Version:** 1.0.0  
**Status:** Final  

---

## 1. System Overview

This system is a competency-driven adaptive interview assessment platform.
It evaluates interview answers using a hybrid AI architecture combining
statistical NLP, rule-based reasoning, and knowledge graph-based skill tracking.

The central design principle is that every score must be explainable,
every recommendation must be traceable to a competency gap,
and every evaluation claim must be validated against human judgment.

---

## 2. Research Contributions

### Contribution 1: Hybrid Evaluation Ensemble
A multi-dimensional NLP evaluation pipeline combining five independent
evaluators with configurable weighted fusion. This outperforms
semantic-similarity-only baselines as demonstrated by the ablation study.

### Contribution 2: Competency-Driven Assessment Model
A knowledge graph of competencies replaces question-centric evaluation.
Every answer updates competency confidence scores. Recommendations
target specific competency gaps rather than vague topic areas.

### Contribution 3: Elo-Style Adaptive Difficulty
An Elo rating system adjusts question difficulty based on demonstrated
competency performance. This produces more accurate readiness estimates
than fixed-difficulty interview systems.

### Contribution 4: Explainable Rubric-Based Scoring
Every score dimension is traceable to observable evidence in the answer.
Users see exactly which concepts were found, which were missing,
and a specific actionable improvement tip.

### Contribution 5: Benchmark Validation
The evaluation ensemble is validated against a human-annotated benchmark
dataset. Agreement metrics (MAE, RMSE, Pearson R) are reported.

---

## 3. Hybrid AI Architecture

```
Layer 1: Statistical NLP
  - Sentence Transformers (all-MiniLM-L6-v2)
  - Cosine similarity for semantic comparison
  - TF-IDF for keyword relevance

Layer 2: Rule-Based Reasoning
  - Required concept coverage checking
  - Evidence signal pattern matching
  - Grammar structure analysis via spaCy

Layer 3: Knowledge Graph
  - NetworkX competency graph
  - Elo-style confidence propagation
  - Skill dependency mapping

Layer 4: ML Models
  - Scikit-learn for recommendation ranking
  - Content-based resource filtering
  - Elo rating for adaptive difficulty
```

The hybrid approach is intentional. Pure ML models require large labeled
datasets which are unavailable for this domain. Pure rule-based systems
cannot capture semantic meaning. The hybrid combines the strengths of both.

---

## 4. Evaluation Ensemble Design

### 4.1 Evaluators

| Evaluator | Method | Dimension |
|-----------|--------|-----------|
| SemanticEvaluator | Sentence Transformers cosine similarity | Answer relevance |
| ConceptEvaluator | Ontology-based concept matching | Required concept coverage |
| CommunicationEvaluator | spaCy POS analysis + pattern matching | Clarity and grammar |
| EvidenceEvaluator | Signal phrase detection + tech keywords | Real-world examples |
| ReasoningEvaluator | Causal/comparative signal detection | Logical depth |

### 4.2 Scoring Weights

**Technical Questions:**
```
Concept Coverage:      35%
Semantic Relevance:    20%
Reasoning Depth:       20%
Evidence/Examples:     15%
Communication:         10%
```

**HR Questions:**
```
Semantic Relevance:    25%
Communication:         25%
Evidence/Examples:     25%
Reasoning Depth:       15%
Concept Coverage:      10%
```

Weights are stored in `configs/scoring_weights.yaml`.
They are not hardcoded. Different question types use different profiles.

### 4.3 Why These Weights?

Technical questions are scored with concept coverage highest because
in a technical interview, covering the required concepts is the primary
measure of competence. Communication matters less than accuracy.

HR questions are scored with communication and evidence equally weighted
with semantic relevance because behavioral questions reward delivery,
specificity, and structure as much as topic coverage.

### 4.4 Grade Boundaries

| Grade | Score Range | Meaning |
|-------|-------------|---------|
| A | 90–100 | Excellent — Ready |
| B | 75–89 | Good — Nearly Ready |
| C | 60–74 | Average — Needs Practice |
| D | 40–59 | Below Average — Significant Gaps |
| F | 0–39 | Poor — Fundamental Review Needed |

---

## 5. Adaptive Engine Design

### 5.1 Elo Rating System

Every competency has an Elo rating. Every question has a difficulty Elo.
After each answer, the user's skill Elo is updated.

**Formula:**
```
expected_score = 1 / (1 + 10 ^ ((question_elo - skill_elo) / 400))
new_skill_elo  = old_elo + K * (actual_score - expected_score)
K = 32
```

**Starting Values:**
```
New user skill Elo:        1000
Beginner question Elo:     900
Intermediate question Elo: 1200
Advanced question Elo:     1500
Expert question Elo:       1800
```

### 5.2 Difficulty Selection

```
Elo >= 1400:   Select Advanced questions
Elo 1100-1399: Select Intermediate questions
Elo < 1100:    Select Beginner questions
```

### 5.3 Competency Confidence Update

```
new_confidence = old_confidence + learning_rate * (score - old_confidence)
learning_rate  = 0.3
```

This is an exponential moving average. A single poor answer does not
collapse a well-established competency. Multiple poor answers do.

---

## 6. Skill Graph Design

### 6.1 Graph Structure

```
Nodes: Competencies (with confidence score and Elo rating)
Edges: Dependency relationships (prerequisite / related / advanced_of)
```

### 6.2 Confidence Colors

```
Green:  confidence >= 0.7  (interview ready)
Yellow: confidence 0.4–0.69 (developing)
Red:    confidence < 0.4   (needs work)
```

### 6.3 Competency Hierarchy Example

```
Software Engineering
├── Object Oriented Programming
│   ├── Classes and Objects
│   ├── Inheritance
│   ├── Polymorphism
│   └── Encapsulation
├── Database Systems
│   ├── SQL Fundamentals
│   └── Database Design
└── System Design
    ├── Scalability
    └── Design Patterns
```

---

## 7. NLP Models Used

| Model | Source | Purpose |
|-------|--------|---------|
| all-MiniLM-L6-v2 | Sentence Transformers | Semantic embedding |
| en_core_web_sm | spaCy | POS tagging, NER, syntax |
| NLTK punkt | NLTK | Tokenization |
| NLTK stopwords | NLTK | Stopword removal |
| NLTK wordnet | NLTK | Lemmatization |

All models are pretrained. No custom model training is performed
in this version. The Elo system and concept coverage are the
primary AI contributions beyond model application.

---

## 8. Inference Pipeline

```
User Answer
    ↓
TextProcessor (spaCy)
    ↓
EmbeddingService (Sentence Transformers + Cache)
    ↓
Five Evaluators (parallel conceptually, sequential in code)
    ↓
ScoreFusion (config-driven weighted combination)
    ↓
ExplainabilityEngine (human-readable reasons)
    ↓
CompetencyUpdater (Elo + confidence update)
    ↓
EvaluationOutput (Pydantic schema)
```

Target latency: under 500 ms without LLM, under 2000 ms with LLM.

---

## 9. Resume Intelligence Pipeline

```
Resume File (PDF/DOCX/TXT)
    ↓
ResumeParser (pdfplumber / python-docx)
    ↓
SkillExtractor (keyword matching + spaCy NER + pattern matching)
    ↓
SkillNormalizer (abbreviation map + canonical forms)
    ↓
ResumeConfidenceAnalyzer (buzzword detection + quality scoring)
    ↓
ResumeQuestionMapper (skill → competency → question mapping)
    ↓
ResumeParseResult (Pydantic schema)
```

---

## 10. Benchmark Validation Design

### 10.1 Dataset

Human-annotated answers across three competency categories:
- OOP concepts (2 questions, 9 annotated answers)
- SQL JOIN types (1 question, 4 annotated answers)
- HR Behavioral (1 question, 4 annotated answers)

Each answer has:
- An assigned quality tier: poor, below_average, average, good, excellent
- A human score from multiple annotators
- Annotator notes

### 10.2 Metrics

```
MAE       = mean(|ai_score - human_score|)
RMSE      = sqrt(mean((ai_score - human_score)^2))
Pearson R = linear correlation coefficient
Spearman R = rank correlation coefficient
```

### 10.3 Success Criteria

```
Full ensemble Pearson R:  >= 0.85
Full ensemble MAE:        <= 12 points
```

### 10.4 Ablation Study

Five experiments progressively adding evaluators to measure
individual contribution. Results documented in
`docs/ABLATION_STUDY_REPORT.md`.

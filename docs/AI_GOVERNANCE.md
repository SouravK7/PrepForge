# AI Governance Document
## AI-Powered Interview Preparation and Career Readiness Assistant
**Version:** 1.0.0  

---

## 1. Purpose

This document describes the governance framework for the AI evaluation
system. It addresses known limitations, bias considerations, data privacy,
and human oversight requirements.

Interview systems make decisions about people. Even when used for
self-directed practice, inaccurate scores can undermine user confidence
and mislead preparation efforts. This document ensures users and evaluators
understand the boundaries of the system clearly and honestly.

---

## 2. Known Limitations

### 2.1 Concept Coverage Depends on Ontology Quality

The ConceptEvaluator checks whether required concepts appear in the
answer text using keyword matching with lemmatization. If a user expresses
a concept using terminology different from the ontology, the concept may
be marked as missing even when the underlying understanding is correct.

**Mitigation:** The semantic evaluator provides a complementary signal.
High semantic similarity with low concept coverage suggests the user
understands the topic but uses different terminology. Users should review
missing concepts to verify whether the gap is real or terminological.

---

### 2.2 Short Answers May Be Penalized

Answers shorter than 15–20 words will score poorly on completeness and
communication dimensions regardless of factual correctness. A very concise
but accurate answer may receive a lower score than a verbose answer with
similar coverage.

**Mitigation:** A minimum answer length of 10 words is enforced at
submission. The communication evaluator rewards answers in the 20–200 word
range. Users should write complete sentences, not bullet keywords.

---

### 2.3 Semantic Similarity Cannot Verify Factual Accuracy

A fluent, well-structured answer that makes factually incorrect statements
can score well on semantic similarity and communication while being
substantively wrong. The concept evaluator partially addresses this but
cannot detect subtle factual errors or logical fallacies.

**Mitigation:** This system is designed for guided practice, not
high-stakes assessment. Users should cross-reference important answers
with authoritative technical sources when in doubt.

---

### 2.4 Evidence Detector Relies on Signal Phrases

The evidence evaluator detects phrases like "for example", "in my project",
and specific technology references. Users who provide concrete evidence
without using these conventional signal phrases will be under-scored on
this dimension.

**Mitigation:** The per-evaluation improvement tip specifically prompts
users to add concrete examples with explicit signal phrases. This trains
the behavior over multiple sessions.

---

### 2.5 Elo Convergence Requires Multiple Sessions

The Elo adaptive system requires several completed interview sessions to
accurately estimate a user's competency level. Early sessions may select
suboptimal difficulty levels due to insufficient evidence.

**Mitigation:** The default starting Elo of 1000 maps to intermediate
difficulty, which is appropriate for the majority of users. One to three
sessions are sufficient to begin meaningful adaptive adjustment.

---

### 2.6 Small Benchmark Dataset

The validation benchmark contains 17 annotated answers across three
competency categories. While the correlations are strong, the dataset size
limits statistical confidence in the reported metrics.

**Mitigation:** The benchmark is explicitly described as a pilot validation
rather than a large-scale study. Future work should expand the dataset
with additional annotators and competency categories.

---

## 3. Bias Considerations

### 3.1 Language Bias (Non-Native English)

The grammar and communication evaluator uses spaCy's English language model.
Non-native English speakers may receive systematically lower communication
scores due to grammatical differences, even when technical content is correct.

**Impact:** Communication weight is 10% for technical questions and 25%
for HR questions. The impact is limited for technical evaluation but
non-trivial for HR evaluation.

**Recommendation:** Users should be explicitly informed that communication
scoring may not fully account for language background. Communication scores
should be interpreted as writing clarity indicators, not language ability.

---

### 3.2 Terminology Bias

The competency ontology was constructed from common English-language
technical documentation and standard interview preparation resources.
Technical terms used differently across geographic regions, companies,
or communities may not match the expected concept keywords.

**Impact:** Concept coverage scores may under-represent correct answers
that use regional or domain-specific terminology.

---

### 3.3 Sample Answer Ceiling

The SemanticEvaluator compares each answer against a human-written sample
answer. The sample answer defines the effective ceiling for semantic scores.
Answers that are technically correct but structured differently from the
sample will score lower than their quality merits on this dimension.

**Impact:** Creative answers that approach the topic from a different angle
may be systematically under-scored by the semantic evaluator alone. The
full ensemble partially compensates through concept and reasoning scores.

---

### 3.4 Technical Domain Coverage

Question banks and competency ontologies currently cover three job roles:
Software Engineer, Data Analyst, and AI Engineer. Candidates preparing
for roles in other domains (e.g., embedded systems, hardware design,
product management) are not served by the current ontology.

---

## 4. Privacy

### 4.1 Local Data Storage

All user data, interview answers, and evaluations are stored in a local
SQLite database file (`interview_assistant.db`) on the user's machine.
No data is transmitted to external services by default.

### 4.2 LLM Integration

If the optional LLM integration is enabled (`USE_LLM=True` in `.env`),
answer text is transmitted to the configured LLM provider API.
This **must** be disclosed to users before enabling in any shared
deployment. The default configuration has `USE_LLM=False`.

### 4.3 Resume Data

Resume text is processed entirely locally. No resume content is transmitted
externally. The system stores extracted skills and the quality report in the
database, but the raw resume text is only retained if the user explicitly
saves the parsed result.

### 4.4 Data Retention

This version does not implement user account deletion endpoints. In any
production or shared deployment, users must be provided the ability to
delete their account and all associated data to comply with applicable
privacy regulations (e.g., GDPR Article 17).

### 4.5 Authentication

Passwords are stored as bcrypt hashes. JWT tokens expire after a
configurable duration (default: 24 hours). No plaintext credentials
are stored at any point.

---

## 5. Human Oversight

### 5.1 Scores Are Guidance, Not Verdicts

AI evaluation scores should be treated as practice feedback, not definitive
assessments of candidate capability.

A score of 45 on a question does not mean the user cannot answer that
question competently in a real interview. It means their written practice
answer had specific measurable gaps in the evaluated dimensions.

### 5.2 Not Suitable for High-Stakes Decisions

This system is designed for self-directed practice.

It **must not** be used for:
- Hiring or candidate filtering decisions
- Academic grade assignment
- Professional certification assessment

without significant additional validation and qualified human review.

### 5.3 Evaluator Agreement

The evaluator achieved Pearson R of approximately 0.85–0.97 with human
annotators on the benchmark dataset. This indicates good but imperfect
agreement. Approximately 10–15% of evaluations may differ materially
from expert human judgment, particularly for edge cases described in
`docs/ERROR_ANALYSIS_REPORT.md`.

---

## 6. Explainability Commitment

Every score produced by this system includes:

1. The numeric score (0–100) per dimension
2. The weighted final score and letter grade (A–F)
3. A human-readable reason for each of the 5 dimension scores
4. The specific concepts matched and missing
5. Detected strengths and weaknesses
6. A single most-impactful improvement tip
7. An overall summary paragraph

No score is returned without a traceable reason. This is enforced
architecturally: the `EvaluationOutput` Pydantic schema requires all
explanation fields to be populated. Evaluation routes will not return
a 200 response with empty explanation fields.

---

## 7. Responsible Use Guidelines

**Users of this system should:**
1. Treat scores as practice feedback, not final judgments
2. Review missing concepts to understand gaps, not just chase total scores
3. Use improvement tips as learning prompts, not prescriptions
4. Cross-reference AI feedback with human mentors when preparing for real interviews
5. Recognise that writing practice answers differs from live verbal interviews

**System operators and researchers should:**
1. Not use aggregate scores to rank or filter candidates
2. Disclose AI assistance when presenting scores to third parties
3. Ensure users are informed of the system's limitations before first use
4. Provide human review for any consequential decisions made using system output
5. Monitor for systematic bias patterns in scoring across user groups

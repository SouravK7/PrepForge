# Error Analysis Report
## AI Evaluation Ensemble — Known Failure Cases
**Version:** 1.0.0  

---

## 1. Purpose

This report documents where and why the AI evaluator makes its largest
errors relative to human annotation. It is the most honest section of
the project documentation and demonstrates scientific maturity by
explicitly identifying failure modes rather than obscuring them.

---

## 2. Error Classification

Errors are classified by direction and magnitude:

| Category | Definition |
|----------|-----------|
| **Over-scored** | AI score > human score by more than 10 points |
| **Under-scored** | AI score < human score by more than 10 points |
| **Accurate** | Absolute error ≤ 10 points |

Run the error analysis to generate actual classified cases:

```bash
python -c "
from benchmark.run_benchmark import BenchmarkRunner
from benchmark.error_analysis import ErrorAnalyzer

runner = BenchmarkRunner()
report = runner.run('oop_benchmark_v1', save_report=True)
analyzer = ErrorAnalyzer()
entries = analyzer.analyze(report, save=True)
"
```

Actual cases are saved to `benchmark/reports/error_analysis.json`.

---

## 3. Known Error Patterns

### Pattern 1: Fluent but Incomplete Answers — Over-Scored

**Description:**  
Answers that are grammatically well-structured and use topic-adjacent
vocabulary, but fail to cover the specific required concepts, may be
over-scored. The semantic evaluator rewards lexical proximity to the
sample answer even when concept coverage is shallow.

**Illustrative Example:**

```
Question: Explain ACID properties of database transactions.

Answer: "Database transactions ensure that data remains reliable and
consistent at all times, preventing corruption and ensuring integrity."

AI Score:  ~55   (semantic similarity scores moderate, communication clean)
Human Score: ~30  (no specific ACID components mentioned)
Error: +25 points (over-scored)
```

**Root Cause:**  
The answer uses database terminology semantically related to ACID.
The semantic evaluator scores this moderately. The communication evaluator
rewards the clean sentence structure. However, Atomicity, Consistency,
Isolation, and Durability are not mentioned, so the concept evaluator
penalises heavily — but the weighted fusion still produces a moderate total.

**Implication for Users:**  
Users with vague but fluent answers may receive encouraging scores that
overstate their actual concept mastery. The missing-concepts display
provides the corrective signal.

---

### Pattern 2: Creative Correct Answers — Under-Scored

**Description:**  
Technically correct answers that approach the topic from a different
structural angle than the sample answer may receive lower semantic
similarity scores than their quality merits.

**Illustrative Example:**

```
Question: Explain polymorphism in OOP.

Answer: "Think of it this way: a dog and a cat both respond to a
'make_sound()' call, but one barks and one meows. Same interface,
different behaviour depending on the actual object. That's polymorphism
— the ability of different objects to respond to the same message in
their own way."

AI Score:  ~62   (sample answer uses "method overriding" / "runtime dispatch")
Human Score: ~82  (correct, memorable, concrete example)
Error: −20 points (under-scored)
```

**Root Cause:**  
The sample answer uses formal OOP terminology. This creative but correct
answer uses an informal analogy. Cosine similarity between the embeddings
is lower than for a formally worded equivalent answer.

**Implication for Researchers:**  
This represents a fundamental limitation of sample-answer-anchored
semantic scoring. Solving it requires either multiple diverse sample
answers or a classifier trained on correct-vs-incorrect rather than
similarity-to-reference.

---

### Pattern 3: HR Behavioral Answers — Systematic Over-Scoring

**Description:**  
HR behavioral answers (STAR format) tend to score slightly higher than
human raters assign. Human raters assess depth of self-reflection,
specificity, and genuine insight — signals the evaluator approximates
imperfectly through evidence signal phrases.

**Root Cause:**  
The evidence evaluator rewards signal phrases like "for example" and
"in this situation". A shallow STAR-formatted answer that includes these
phrases scores well on evidence despite lacking genuine depth. Human raters
penalise answers that follow the STAR format structurally but lack
meaningful content.

**Mitigation:**  
HR answer weights reduce concept coverage to 10% (reflecting that specific
concepts matter less). Future work should develop a dedicated behavioral
answer depth scorer separate from the technical evidence detector.

---

### Pattern 4: Very Short Correct Answers — Under-Scored on Communication

**Description:**  
An expert answer of two precise sentences will score poorly on
communication because the length signal rewards 20–200 words.

**Example:**

```
Question: What is encapsulation?

Answer: "Encapsulation bundles data and the methods that operate on
it into a single unit (a class), hiding internal state and exposing
only a defined interface."

AI Score:  ~58  (communication: short answer penalty)
Human Score: ~80  (concise, accurate, complete)
Error: −22 points
```

**Implication:**  
Users who write expert-level concise answers are penalised. They should
be encouraged to expand answers during practice even if brevity is
appropriate in a real interview context.

---

## 4. Error Distribution by Quality Tier

Based on the benchmark dataset design and evaluator properties:

| Answer Quality | Avg Human Score | Expected AI Pattern |
|----------------|-----------------|---------------------|
| Poor (0–30) | ~15 | Slight over-scoring; fluent poor answers score higher than deserved |
| Below Average (31–50) | ~38 | Generally accurate |
| Average (51–70) | ~60 | Generally accurate; main agreement zone |
| Good (71–85) | ~78 | Generally accurate |
| Excellent (86–100) | ~93 | May slightly under-score creative or concise expert answers |

---

## 5. Implications for System Users

1. **High scores on short, fluent answers** may not reflect true concept mastery —
   review the missing concepts list before concluding you understand the topic
2. **Creative correct answers** may receive lower scores than deserved on
   semantic dimensions — the reasoning and concept scores provide compensating signal
3. **HR scores** should be treated as approximate directional guidance
   rather than precise quality assessments
4. **Communication penalties for brevity** affect expert-level users most —
   for practice purposes, writing longer complete answers is recommended

---

## 6. How to Reproduce

```bash
# Run benchmark and generate error analysis
python -c "
from benchmark.run_benchmark import BenchmarkRunner
from benchmark.error_analysis import ErrorAnalyzer

runner = BenchmarkRunner()
report = runner.run('oop_benchmark_v1', save_report=True)

analyzer = ErrorAnalyzer()
entries = analyzer.analyze(report, top_n=10, save=True)
for entry in entries:
    print(f'{entry.error_category}: {entry.error_magnitude:.1f} pts — {entry.possible_cause}')
"

# Saved to: benchmark/reports/error_analysis.json
```

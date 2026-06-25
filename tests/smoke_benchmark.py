"""Quick smoke test: run benchmark answers through the evaluation pipeline."""
import json
from schemas.answer_schema import AnswerInput
from schemas.question_schema import QuestionType
from ai_core.evaluation_pipeline.evaluation_orchestrator import EvaluationOrchestrator

with open("data/benchmark/oop_benchmark_v1.json") as f:
    bench = json.load(f)

orch = EvaluationOrchestrator()

for ans in bench["answers"]:
    ai = AnswerInput(
        session_id=1,
        user_id=1,
        question_id=bench["question_id"],
        competency_id=bench["competency_id"],
        question_text=bench["question_text"],
        question_type=QuestionType.TECHNICAL,
        sample_answer=bench["sample_answer"],
        required_concepts=bench["required_concepts"],
        rubric_id="rubric_technical_standard",
        user_answer=ans["answer_text"],
    )
    result = orch.evaluate(ai)
    human = ans["human_score"]
    ai_score = result.scores.weighted_final
    delta = abs(human - ai_score)
    print(
        f'{ans["answer_type"]:10s} | '
        f'Human: {human:3d} | '
        f'AI: {ai_score:6.1f} | '
        f'Delta: {delta:5.1f} | '
        f'Grade: {result.grade.value}'
    )

print("\nAll benchmark answers processed successfully.")

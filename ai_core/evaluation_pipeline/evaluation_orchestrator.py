"""
Evaluation orchestrator.

Coordinates the full evaluation pipeline:
    AnswerInput
        → 5 parallel evaluators
        → ScoreFusion
        → ExplainabilityEngine
        → EvaluationOutput

This is the single entry point for evaluating any answer.
Call EvaluationOrchestrator.evaluate(answer_input) to get
a complete EvaluationOutput with all scores, grades,
evidence, and explanations.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from ai_core.evaluation_pipeline.communication_evaluator import CommunicationEvaluator
from ai_core.evaluation_pipeline.concept_evaluator import ConceptEvaluator
from ai_core.evaluation_pipeline.evidence_evaluator import EvidenceEvaluator
from ai_core.evaluation_pipeline.explainability import ExplainabilityEngine
from ai_core.evaluation_pipeline.reasoning_evaluator import ReasoningEvaluator
from ai_core.evaluation_pipeline.score_fusion import FusionInput, ScoreFusion
from ai_core.evaluation_pipeline.semantic_evaluator import SemanticEvaluator
from ai_core.shared.ai_logger import ai_logger
from schemas.answer_schema import AnswerInput
from schemas.evaluation_schema import EvaluationOutput


class EvaluationOrchestrator:
    """
    Orchestrates the complete evaluation ensemble.

    Instantiates all evaluators, runs them in sequence,
    fuses scores, generates explanations, and returns
    a complete EvaluationOutput.

    Usage:
        orchestrator = EvaluationOrchestrator()
        result = orchestrator.evaluate(answer_input)
    """

    def __init__(self) -> None:
        """Initialise all evaluators and supporting engines."""
        self._semantic = SemanticEvaluator()
        self._concept = ConceptEvaluator()
        self._communication = CommunicationEvaluator()
        self._evidence = EvidenceEvaluator()
        self._reasoning = ReasoningEvaluator()
        self._fusion = ScoreFusion()
        self._explainability = ExplainabilityEngine()

    def evaluate(self, answer_input: AnswerInput) -> EvaluationOutput:
        """
        Run the full evaluation pipeline on a single answer.

        Args:
            answer_input: Complete answer context from the user.

        Returns:
            EvaluationOutput with scores, grade, evidence, and explanations.
        """
        evaluation_id = str(uuid.uuid4())

        ai_logger.log_decision(
            decision_type="evaluation_started",
            context={
                "evaluation_id": evaluation_id,
                "question_id": answer_input.question_id,
                "question_type": answer_input.question_type.value,
                "user_id": answer_input.user_id,
                "session_id": answer_input.session_id,
                "answer_length": len(answer_input.user_answer.split()),
            },
            output={},
            reasoning="Starting evaluation pipeline for answer",
        )

        # --- Step 1: Run all 5 evaluators ---
        semantic_dim = self._semantic.evaluate(answer_input)
        concept_dim = self._concept.evaluate(answer_input)
        communication_dim = self._communication.evaluate(answer_input)
        evidence_dim = self._evidence.evaluate(answer_input)
        reasoning_dim = self._reasoning.evaluate(answer_input)

        # --- Step 2: Fuse scores ---
        fusion_input = FusionInput(
            semantic=semantic_dim,
            concept=concept_dim,
            communication=communication_dim,
            evidence=evidence_dim,
            reasoning=reasoning_dim,
            question_type=answer_input.question_type,
        )

        scores = self._fusion.fuse(fusion_input)
        grade = self._fusion.get_grade(scores.weighted_final)
        readiness = self._fusion.get_readiness(scores.weighted_final)

        # --- Step 3: Build explanations and evidence ---
        explanation = self._explainability.build_explanation(
            fusion_input=fusion_input,
            grade=grade,
            readiness=readiness,
            weighted_final=scores.weighted_final,
        )

        evidence = self._explainability.build_evidence(
            concept_dim=concept_dim,
            communication_dim=communication_dim,
            evidence_dim=evidence_dim,
            reasoning_dim=reasoning_dim,
            semantic_dim=semantic_dim,
        )

        # --- Step 4: Compute competency confidence delta ---
        # Normalized score (0.0-1.0) drives a learning-rate-based update.
        # The delta itself is stored; actual update happens in skill_pipeline.
        normalized_score = scores.weighted_final / 100.0
        competency_delta = 0.3 * (normalized_score - 0.5)  # learning_rate * (score - midpoint)

        ai_logger.log_decision(
            decision_type="evaluation_complete",
            context={"evaluation_id": evaluation_id},
            output={
                "weighted_final": scores.weighted_final,
                "grade": grade.value,
                "readiness": readiness.value,
                "competency_delta": round(competency_delta, 4),
                "semantic": scores.semantic,
                "concept": scores.concept,
                "communication": scores.communication,
                "evidence": scores.evidence,
                "reasoning": scores.reasoning,
            },
            reasoning="All evaluators complete, scores fused",
        )

        return EvaluationOutput(
            id=evaluation_id,
            session_id=answer_input.session_id,
            answer_id=0,  # Populated by service layer after DB persist
            user_id=answer_input.user_id,
            competency_id=answer_input.competency_id,
            question_id=answer_input.question_id,
            scores=scores,
            grade=grade,
            readiness_level=readiness,
            evidence=evidence,
            explanation=explanation,
            competency_delta=round(competency_delta, 4),
            evaluated_at=datetime.utcnow(),
        )

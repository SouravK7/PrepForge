"""
Evaluation service.

Orchestrates the evaluation ensemble, persists results,
and updates competency scores.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from ai_core.evaluation_pipeline import EvaluationOrchestrator
from ai_core.skill_pipeline import ConfidenceUpdater, EloEstimator
from database.repositories import (
    AnswerRepository,
    EvaluationRepository,
    CompetencyScoreRepository,
)
from schemas.answer_schema import AnswerInput
from schemas.competency_schema import CompetencyScore as ScoreSchema, CompetencyUpdate
from schemas.evaluation_schema import (
    EvaluationOutput,
    EvaluationScores,
    EvaluationEvidence,
    EvaluationExplanation,
    GradeEnum,
    ReadinessEnum,
)


@dataclass
class EvaluationResult:
    """
    Complete result of evaluating one answer.

    Attributes:
        evaluation: Full evaluation output from ensemble.
        answer_id: Database ID of the saved answer.
        competency_update: How competency confidence changed.
    """

    evaluation: EvaluationOutput
    answer_id: int
    competency_update: CompetencyUpdate


class EvaluationService:
    """
    Orchestrates answer evaluation and persistence.

    Flow:
        1. Save answer to database
        2. Run evaluation ensemble
        3. Save evaluation to database
        4. Update competency confidence
        5. Update Elo rating
        6. Return complete result
    """

    def __init__(self, db_session: Session) -> None:
        """
        Initialize with database session.

        Args:
            db_session: SQLAlchemy database session.
        """
        self._db = db_session
        self._answer_repo = AnswerRepository(db_session)
        self._eval_repo = EvaluationRepository(db_session)
        self._competency_repo = CompetencyScoreRepository(db_session)
        self._orchestrator = EvaluationOrchestrator()
        self._updater = ConfidenceUpdater()
        self._elo = EloEstimator()

    def evaluate_answer(
        self,
        answer_input: AnswerInput,
        question_elo: float = 1200.0,
    ) -> EvaluationResult:
        """
        Evaluate a user answer end to end.

        Args:
            answer_input: Complete answer context from the user.
            question_elo: Elo difficulty of the question answered.

        Returns:
            EvaluationResult with evaluation, answer_id, and update.

        Raises:
            ValueError: If answer is empty or invalid.
        """
        # Step 1: Save raw answer
        answer_record = self._answer_repo.create(
            session_id=answer_input.session_id,
            user_id=answer_input.user_id,
            question_id=answer_input.question_id,
            competency_id=answer_input.competency_id,
            question_text=answer_input.question_text,
            question_type=answer_input.question_type.value,
            answer_text=answer_input.user_answer,
            time_taken=answer_input.time_taken,
        )

        # Step 2: Run evaluation ensemble
        evaluation = self._orchestrator.evaluate(answer_input)

        # Step 3: Set database answer ID on evaluation
        evaluation.answer_id = answer_record.id

        # Step 4: Save evaluation to database
        self._eval_repo.create_from_output(evaluation, answer_record.id)

        # Step 5: Get or initialise competency score
        current_score = self._competency_repo.get_by_user_and_competency(
            answer_input.user_id,
            answer_input.competency_id,
        )

        if current_score is None:
            current_schema = self._updater.create_initial_score(
                user_id=answer_input.user_id,
                competency_id=answer_input.competency_id,
            )
        else:
            current_schema = ScoreSchema(
                user_id=current_score.user_id,
                competency_id=current_score.competency_id,
                confidence=current_score.confidence,
                elo_rating=current_score.elo_rating,
                evidence_count=current_score.evidence_count,
                improvement_trend=current_score.improvement_trend,
                last_assessed=current_score.last_assessed,
            )

        # Update confidence via EMA
        updated_schema, update_record = self._updater.update(
            current_schema,
            evaluation_score=evaluation.scores.weighted_final,
        )

        # Update Elo rating
        new_elo, _ = self._elo.update_elo(
            current_score=updated_schema,
            question_elo=question_elo,
            actual_performance=evaluation.scores.weighted_final / 100.0,
        )
        updated_schema.elo_rating = new_elo

        # Rebuild update record with final Elo
        final_update = CompetencyUpdate(
            competency_id=update_record.competency_id,
            old_confidence=update_record.old_confidence,
            new_confidence=update_record.new_confidence,
            old_elo=update_record.old_elo,
            new_elo=new_elo,
            evidence_added=update_record.evidence_added,
            delta=update_record.delta,
        )

        # Step 6: Persist updated competency score
        self._competency_repo.upsert(updated_schema)

        return EvaluationResult(
            evaluation=evaluation,
            answer_id=answer_record.id,
            competency_update=final_update,
        )

    def get_session_evaluations(
        self,
        session_id: int,
    ) -> list[EvaluationOutput]:
        """
        Get all evaluations for a session.

        Args:
            session_id: Target interview session.

        Returns:
            List of EvaluationOutput schemas.
        """
        records = self._eval_repo.get_session_evaluations(session_id)
        return [self._record_to_schema(r) for r in records]

    def _record_to_schema(self, record) -> EvaluationOutput:
        """
        Convert database EvaluationRecord to EvaluationOutput schema.

        Args:
            record: EvaluationRecord from database.

        Returns:
            EvaluationOutput Pydantic schema.
        """
        explanation_data: dict = {}
        if record.explanation:
            try:
                explanation_data = json.loads(record.explanation)
            except Exception:
                pass

        return EvaluationOutput(
            id=str(record.id),
            session_id=record.session_id,
            answer_id=record.answer_id,
            user_id=record.user_id,
            competency_id=record.competency_id,
            question_id=record.question_id,
            scores=EvaluationScores(
                semantic=record.semantic_score or 0.0,
                concept=record.concept_score or 0.0,
                communication=record.communication_score or 0.0,
                evidence=record.evidence_score or 0.0,
                reasoning=record.reasoning_score or 0.0,
                weighted_final=record.weighted_final or 0.0,
            ),
            grade=GradeEnum(record.grade or "F"),
            readiness_level=ReadinessEnum(
                record.readiness_level or "poor"
            ),
            evidence=EvaluationEvidence(
                matched_concepts=json.loads(record.matched_concepts or "[]"),
                missing_concepts=json.loads(record.missing_concepts or "[]"),
                strengths=json.loads(record.strengths or "[]"),
                weaknesses=json.loads(record.weaknesses or "[]"),
            ),
            explanation=EvaluationExplanation(
                semantic_reason=explanation_data.get("semantic_reason", ""),
                concept_reason=explanation_data.get("concept_reason", ""),
                communication_reason=explanation_data.get("communication_reason", ""),
                evidence_reason=explanation_data.get("evidence_reason", ""),
                reasoning_reason=explanation_data.get("reasoning_reason", ""),
                overall_summary=explanation_data.get("overall_summary", ""),
                improvement_tip=explanation_data.get("improvement_tip", ""),
            ),
            competency_delta=record.competency_delta or 0.0,
            evaluated_at=record.evaluated_at or datetime.utcnow(),
        )

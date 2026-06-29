"""
Evaluation routes.

Endpoints for retrieving evaluation history and details.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db
from database.models import User
from services.evaluation_service import EvaluationService

router = APIRouter()


@router.get(
    "/session/{session_id}",
    summary="Get all evaluations for a session",
)
def get_session_evaluations(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    Get all AI evaluations for a completed session.

    Args:
        session_id: Target session ID.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        List of evaluation dicts with all scores and explanations.
    """
    service = EvaluationService(db)
    evaluations = service.get_session_evaluations(session_id)

    return [
        {
            "id": ev.id,
            "question_id": ev.question_id,
            "competency_id": ev.competency_id,
            "scores": {
                "semantic": ev.scores.semantic,
                "concept": ev.scores.concept,
                "communication": ev.scores.communication,
                "evidence": ev.scores.evidence,
                "reasoning": ev.scores.reasoning,
                "weighted_final": ev.scores.weighted_final,
            },
            "grade": ev.grade.value,
            "readiness_level": ev.readiness_level.value,
            "matched_concepts": ev.evidence.matched_concepts,
            "missing_concepts": ev.evidence.missing_concepts,
            "strengths": ev.evidence.strengths,
            "weaknesses": ev.evidence.weaknesses,
            "overall_summary": ev.explanation.overall_summary,
            "improvement_tip": ev.explanation.improvement_tip,
            "competency_delta": ev.competency_delta,
            "evaluated_at": ev.evaluated_at.isoformat(),
        }
        for ev in evaluations
    ]


@router.get(
    "/competency/{competency_id}/averages",
    summary="Get average scores for a competency",
)
def get_competency_averages(
    competency_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Get average evaluation scores for one competency.

    Args:
        competency_id: Target competency.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        Dict with average scores per dimension.
    """
    from database.repositories import EvaluationRepository

    repo = EvaluationRepository(db)
    averages = repo.get_average_scores_by_competency(
        current_user.id, competency_id
    )

    if not averages:
        return {"message": "No evaluations found for this competency"}

    return averages

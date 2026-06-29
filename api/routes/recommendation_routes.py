"""
Recommendation routes.

Endpoints for generating and managing learning recommendations.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db
from database.models import User
from services.recommendation_service import RecommendationService
from services.competency_service import CompetencyService

router = APIRouter()


class GenerateRecommendationsRequest(BaseModel):
    """Request to generate recommendations."""

    session_id: int
    target_role: str = Field(default="Software Engineer")
    max_weeks: int = Field(default=6, ge=1, le=12)


@router.post(
    "/generate",
    summary="Generate personalized learning recommendations",
)
def generate_recommendations(
    request: GenerateRecommendationsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Generate and save personalized learning recommendations.

    Analyzes skill gaps and creates a week-by-week roadmap.

    Args:
        request: Generation parameters.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        Dict with roadmap and top resources.
    """
    competency_service = CompetencyService(db)
    rec_service = RecommendationService(db)

    gaps = competency_service.get_skill_gaps(
        user_id=current_user.id,
        job_role=request.target_role,
    )

    output = rec_service.generate_and_save(
        user_id=current_user.id,
        session_id=request.session_id,
        gaps=gaps,
        target_role=request.target_role,
    )

    return {
        "total_weeks": output.roadmap.total_weeks,
        "estimated_readiness_date": output.roadmap.estimated_readiness_date,
        "weekly_plans": [
            {
                "week_number": plan.week_number,
                "focus_competency": plan.focus_competency_name,
                "goal": plan.goal,
                "estimated_hours": plan.estimated_hours,
                "recommendations": [
                    {
                        "title": rec.title,
                        "description": rec.description,
                        "resource_url": rec.resource.url if rec.resource else None,
                        "resource_type": rec.resource.resource_type.value if rec.resource else None,
                        "priority": rec.priority,
                        "estimated_hours": rec.estimated_hours,
                    }
                    for rec in plan.recommendations
                ],
            }
            for plan in output.roadmap.weekly_plans
        ],
        "top_resources": [
            {
                "title": res.title,
                "url": res.url,
                "type": res.resource_type.value,
                "difficulty": res.difficulty,
                "description": res.description,
            }
            for res in output.top_resources
        ],
        "gap_count": len(gaps),
    }


@router.get(
    "/",
    summary="Get saved recommendations",
)
def get_recommendations(
    completed: bool | None = None,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    Get saved learning recommendations for current user.

    Args:
        completed: Filter by completion status.
        limit: Maximum to return.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        List of recommendation dicts.
    """
    service = RecommendationService(db)
    return service.get_user_recommendations(
        user_id=current_user.id,
        completed=completed,
        limit=limit,
    )


@router.put(
    "/{recommendation_id}/complete",
    summary="Mark recommendation as completed",
)
def mark_completed(
    recommendation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Mark a learning recommendation as completed.

    Args:
        recommendation_id: Target recommendation.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        Success confirmation.

    Raises:
        HTTPException 404: If recommendation not found.
    """
    service = RecommendationService(db)
    success = service.mark_completed(recommendation_id, current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found.",
        )

    return {"success": True, "recommendation_id": recommendation_id}


@router.get(
    "/next-steps",
    summary="Get immediate next step recommendations",
)
def get_next_steps(
    target_role: str = "Software Engineer",
    top_n: int = 3,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    Get immediate next step recommendations.

    Args:
        target_role: Target job role.
        top_n: Number of steps to return.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        List of immediate recommendation dicts.
    """
    competency_service = CompetencyService(db)
    rec_service = RecommendationService(db)

    gaps = competency_service.get_skill_gaps(
        user_id=current_user.id,
        job_role=target_role,
        top_n=top_n,
    )

    steps = rec_service.get_next_steps(
        user_id=current_user.id,
        session_id=0,
        gaps=gaps,
        top_n=top_n,
    )

    return [
        {
            "competency_id": s.competency_id,
            "competency_name": s.competency_name,
            "title": s.title,
            "description": s.description,
            "resource_url": s.resource.url if s.resource else None,
            "priority": s.priority,
            "estimated_hours": s.estimated_hours,
        }
        for s in steps
    ]

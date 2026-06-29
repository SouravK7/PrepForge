"""
Analytics routes.

Dashboard statistics and performance trend endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db
from database.models import User
from services.analytics_service import AnalyticsService

router = APIRouter()


@router.get(
    "/dashboard",
    summary="Get complete dashboard statistics",
)
def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Get all dashboard statistics for the current user.

    Args:
        current_user: Authenticated user.
        db: Database session.

    Returns:
        Dict with overview, trends, and competency data.
    """
    service = AnalyticsService(db)
    return service.get_dashboard_stats(current_user.id)


@router.get(
    "/score-trend",
    summary="Get score trend for chart",
)
def get_score_trend(
    job_role: str | None = None,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    Get score trend data for line chart visualization.

    Args:
        job_role: Filter by role if provided.
        limit: Maximum data points.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        List of score data points.
    """
    service = AnalyticsService(db)
    return service.get_score_trend(
        user_id=current_user.id,
        job_role=job_role,
        limit=limit,
    )


@router.get(
    "/competency-radar",
    summary="Get competency radar chart data",
)
def get_competency_radar(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Get competency scores formatted for radar chart.

    Args:
        current_user: Authenticated user.
        db: Database session.

    Returns:
        Dict with labels and values for radar chart.
    """
    service = AnalyticsService(db)
    return service.get_competency_radar_data(current_user.id)

"""
Competency routes.

Skill graph and gap analysis endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db
from database.models import User
from services.competency_service import CompetencyService

router = APIRouter()


@router.get(
    "/graph",
    summary="Get skill confidence graph",
)
def get_skill_graph(
    job_role: str = "Software Engineer",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Get the skill confidence graph for visualization.

    Args:
        job_role: Target job role.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        SkillGraph with nodes and edges.
    """
    service = CompetencyService(db)
    graph = service.get_skill_graph(current_user.id, job_role)

    return {
        "nodes": [
            {
                "id": n.id,
                "label": n.label,
                "confidence": n.confidence,
                "color": n.color,
                "size": n.size,
                "parent": n.parent,
            }
            for n in graph.nodes
        ],
        "edges": [
            {
                "source": e.source,
                "target": e.target,
                "relationship": e.relationship,
                "strength": e.strength,
            }
            for e in graph.edges
        ],
    }


@router.get(
    "/gaps",
    summary="Get prioritized skill gaps",
)
def get_skill_gaps(
    job_role: str = "Software Engineer",
    top_n: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    Get prioritized skill gaps for the current user.

    Args:
        job_role: Target job role.
        top_n: Maximum gaps to return.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        List of gap dicts sorted by priority.
    """
    service = CompetencyService(db)
    gaps = service.get_skill_gaps(current_user.id, job_role, top_n)

    return [
        {
            "competency_id": g.competency_id,
            "competency_name": g.competency_name,
            "current_confidence": g.current_confidence,
            "gap": g.gap,
            "priority": g.priority.value,
            "role_relevance": g.role_relevance,
            "recommended_action": g.recommended_action,
        }
        for g in gaps
    ]


@router.get(
    "/readiness",
    summary="Get overall interview readiness",
)
def get_readiness(
    job_role: str = "Software Engineer",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Get overall interview readiness percentage.

    Args:
        job_role: Target job role.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        Dict with readiness percentage and label.
    """
    service = CompetencyService(db)
    readiness = service.get_overall_readiness(current_user.id, job_role)

    if readiness >= 85:
        label = "Excellent"
    elif readiness >= 70:
        label = "Good"
    elif readiness >= 50:
        label = "Average"
    else:
        label = "Needs Work"

    return {
        "readiness_percentage": readiness,
        "readiness_label": label,
        "job_role": job_role,
    }


@router.get(
    "/scores",
    summary="Get all competency scores",
)
def get_scores(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    Get all competency confidence scores for the user.

    Args:
        current_user: Authenticated user.
        db: Database session.

    Returns:
        List of competency score dicts.
    """
    service = CompetencyService(db)
    scores = service.get_user_scores(current_user.id)

    return [
        {
            "competency_id": comp_id,
            "confidence": round(score.confidence * 100, 1),
            "elo_rating": score.elo_rating,
            "evidence_count": score.evidence_count,
            "improvement_trend": score.improvement_trend,
            "last_assessed": (
                score.last_assessed.isoformat()
                if score.last_assessed
                else None
            ),
        }
        for comp_id, score in scores.items()
    ]

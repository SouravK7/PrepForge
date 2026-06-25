"""
Report schemas.

Output contracts for session summaries and interview reports.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from schemas.competency_schema import CompetencyGap
from schemas.evaluation_schema import EvaluationOutput, ReadinessEnum
from schemas.recommendation_schema import LearningRoadmap


class SessionSummary(BaseModel):
    """
    High-level summary of a completed interview session.

    Used in history views and dashboard displays.
    """

    model_config = ConfigDict(frozen=True)

    session_id: int = Field(..., description="Session identifier")
    user_id: int = Field(..., description="User who completed session")
    job_role: str = Field(..., description="Target job role")
    overall_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Weighted average score across all answers",
    )
    readiness_level: ReadinessEnum = Field(
        ...,
        description="Overall interview readiness assessment",
    )
    technical_score: Optional[float] = Field(
        default=None,
        description="Average score on technical questions",
    )
    hr_score: Optional[float] = Field(
        default=None,
        description="Average score on HR questions",
    )
    total_questions: int = Field(..., description="Number of questions answered")
    duration_minutes: int = Field(
        default=0,
        description="Total session duration in minutes",
    )
    started_at: datetime = Field(..., description="Session start time")
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Session completion time",
    )
    top_strengths: list[str] = Field(
        default_factory=list,
        description="Top 3 demonstrated strengths",
    )
    top_weaknesses: list[str] = Field(
        default_factory=list,
        description="Top 3 identified weaknesses",
    )


class InterviewReport(BaseModel):
    """
    Complete interview report for a finished session.

    Contains full evaluation details, competency updates,
    skill gaps, and personalized recommendations.
    Rendered in the results page and optionally exported as PDF.
    """

    model_config = ConfigDict(frozen=False)

    session_summary: SessionSummary = Field(
        ...,
        description="High-level session summary",
    )
    evaluations: list[EvaluationOutput] = Field(
        ...,
        description="Full evaluation details per question",
    )
    skill_gaps: list[CompetencyGap] = Field(
        default_factory=list,
        description="Identified competency gaps from this session",
    )
    roadmap: Optional[LearningRoadmap] = Field(
        default=None,
        description="Personalized learning roadmap generated from gaps",
    )
    generated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this report was generated",
    )

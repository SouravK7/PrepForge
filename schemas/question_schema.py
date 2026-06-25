"""
Question schemas.

Every question maps to exactly one competency.
Questions have Elo difficulty ratings for the adaptive engine.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class QuestionType(str, Enum):
    """Interview question category."""

    TECHNICAL = "technical"
    HR = "hr"


class DifficultyLevel(str, Enum):
    """Question difficulty levels."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class InterviewPhase(str, Enum):
    """Phases in the structured interview blueprint."""

    INTRODUCTION = "introduction"
    RESUME_VERIFICATION = "resume_verification"
    CORE_TECHNICAL = "core_technical"
    SCENARIO = "scenario"
    BEHAVIORAL = "behavioral"
    CLOSING = "closing"


class Question(BaseModel):
    """
    Represents a single interview question.

    Every question is linked to exactly one competency.
    Required concepts define what must appear in a correct answer.
    The Elo difficulty rating is used by the adaptive engine.
    """

    model_config = ConfigDict(frozen=True)

    id: str = Field(..., description="Unique question identifier")
    competency_id: str = Field(
        ...,
        description="Which competency this question assesses",
    )
    question_text: str = Field(..., description="The interview question text")
    question_type: QuestionType = Field(
        ...,
        description="technical or hr",
    )
    difficulty: DifficultyLevel = Field(
        ...,
        description="Difficulty level label",
    )
    elo_difficulty: float = Field(
        default=1200.0,
        description="Numeric Elo difficulty rating for adaptive engine",
    )
    category: str = Field(
        ...,
        description="Topic category e.g. OOP, SQL, Behavioral",
    )
    required_concepts: list[str] = Field(
        default_factory=list,
        description="Concepts that must appear in a correct answer",
    )
    optional_concepts: list[str] = Field(
        default_factory=list,
        description="Bonus concepts that improve the answer score",
    )
    sample_answer: str = Field(
        ...,
        description="Reference answer used for semantic comparison",
    )
    rubric_id: str = Field(
        ...,
        description="Which rubric to apply when evaluating answers",
    )
    follow_up_hints: list[str] = Field(
        default_factory=list,
        description="Potential directions for adaptive follow-up questions",
    )
    role_tags: list[str] = Field(
        default_factory=list,
        description="Which job roles this question applies to",
    )


class SessionQuestion(BaseModel):
    """
    Represents a question as it appears during an active interview session.

    Includes session-specific context such as phase and display index.
    """

    model_config = ConfigDict(frozen=True)

    session_id: int = Field(..., description="Active interview session id")
    question: Question = Field(..., description="The question being asked")
    phase: InterviewPhase = Field(
        ...,
        description="Which interview phase this question belongs to",
    )
    display_index: int = Field(
        ...,
        description="Question number shown to user (1-based)",
    )
    is_follow_up: bool = Field(
        default=False,
        description="True if this was adaptively generated as a follow-up",
    )
    previous_answer_reference: Optional[str] = Field(
        default=None,
        description="If follow-up, reference to what triggered it",
    )

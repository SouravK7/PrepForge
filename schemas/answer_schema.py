"""
Answer schemas.

Typed contracts for user answers entering the evaluation pipeline.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from schemas.question_schema import QuestionType


class AnswerInput(BaseModel):
    """
    Input schema for a user answer entering the evaluation pipeline.

    This is the entry point to the evaluation ensemble.
    All evaluators receive this schema as input.
    """

    model_config = ConfigDict(frozen=True)

    session_id: int = Field(..., description="Active interview session id")
    user_id: int = Field(..., description="User submitting this answer")
    question_id: str = Field(..., description="Question being answered")
    competency_id: str = Field(
        ...,
        description="Competency this answer will update",
    )
    question_text: str = Field(..., description="The question that was asked")
    question_type: QuestionType = Field(
        ...,
        description="technical or hr determines scoring weights",
    )
    sample_answer: str = Field(
        ...,
        description="Reference answer for semantic comparison",
    )
    required_concepts: list[str] = Field(
        ...,
        description="Concepts that must appear in a correct answer",
    )
    optional_concepts: list[str] = Field(
        default_factory=list,
        description="Bonus concepts that improve the score",
    )
    rubric_id: str = Field(
        ...,
        description="Which rubric to apply for evaluation",
    )
    user_answer: str = Field(
        ...,
        min_length=1,
        description="The raw text answer provided by the user",
    )
    time_taken: int = Field(
        default=0,
        ge=0,
        description="Seconds taken to answer",
    )
    submitted_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the answer was submitted",
    )


class AnswerRecord(BaseModel):
    """
    A persisted answer record stored in the database.

    Created after AnswerInput is saved to the answers table.
    """

    model_config = ConfigDict(frozen=True)

    id: int = Field(..., description="Database primary key")
    session_id: int = Field(..., description="Session this answer belongs to")
    user_id: int = Field(..., description="User who submitted this answer")
    question_id: str = Field(..., description="Question that was answered")
    competency_id: str = Field(..., description="Competency being assessed")
    answer_text: str = Field(..., description="Raw answer text")
    time_taken: int = Field(..., description="Seconds taken to answer")
    submitted_at: datetime = Field(..., description="Submission timestamp")

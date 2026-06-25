"""
Rubric schemas.

Rubrics define the evaluation criteria for each question type.
Every criterion has observable scoring indicators per score band.
This makes all evaluation auditable and explainable.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class RubricType(str, Enum):
    """Which question type this rubric applies to."""

    TECHNICAL = "technical"
    HR = "hr"


class ScoringGuide(BaseModel):
    """
    Score band indicators for a single rubric criterion.

    Each band describes observable evidence that places
    an answer within that score range.
    """

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    poor: str = Field(
        ...,
        alias="0-25",
        description="Observable indicators for score 0-25",
    )
    below_average: str = Field(
        ...,
        alias="26-50",
        description="Observable indicators for score 26-50",
    )
    average: str = Field(
        ...,
        alias="51-75",
        description="Observable indicators for score 51-75",
    )
    excellent: str = Field(
        ...,
        alias="76-100",
        description="Observable indicators for score 76-100",
    )


class RubricCriterion(BaseModel):
    """
    A single evaluation criterion within a rubric.

    Each criterion has a weight, description, and scoring guide
    with observable indicators per score band.
    """

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., description="Criterion name e.g. Concept Coverage")
    weight: float = Field(
        ...,
        gt=0.0,
        le=1.0,
        description="Contribution weight to final score 0.0-1.0",
    )
    description: str = Field(
        ...,
        description="What this criterion measures",
    )
    scoring_guide: dict[str, str] = Field(
        ...,
        description="Score band to observable indicator mapping",
    )


class Rubric(BaseModel):
    """
    A complete evaluation rubric for a question type.

    Rubrics ensure every evaluation is consistent, auditable,
    and explainable. The sum of criterion weights must equal 1.0.
    """

    model_config = ConfigDict(frozen=True)

    id: str = Field(..., description="Unique rubric identifier")
    name: str = Field(..., description="Rubric name")
    rubric_type: RubricType = Field(
        ...,
        description="technical or hr",
    )
    criteria: list[RubricCriterion] = Field(
        ...,
        min_length=1,
        description="List of evaluation criteria. Weights must sum to 1.0",
    )
    description: str = Field(
        default="",
        description="What this rubric is designed to evaluate",
    )

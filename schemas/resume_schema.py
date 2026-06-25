"""
Resume schemas.

Output contracts from the resume intelligence pipeline.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ExtractedSkill(BaseModel):
    """A single skill extracted from a resume."""

    model_config = ConfigDict(frozen=True)

    raw_text: str = Field(..., description="Original text from resume")
    normalized: str = Field(..., description="Normalized skill name e.g. JavaScript")
    competency_id: Optional[str] = Field(
        default=None,
        description="Matched competency id if found in ontology",
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Extraction confidence 0.0-1.0",
    )
    source_section: str = Field(
        default="unknown",
        description="Which resume section this came from",
    )


class ExtractedEducation(BaseModel):
    """Education record extracted from a resume."""

    model_config = ConfigDict(frozen=True)

    degree: str = Field(default="", description="Degree name")
    institution: str = Field(default="", description="Institution name")
    field_of_study: str = Field(default="", description="Field of study")
    year: Optional[str] = Field(default=None, description="Graduation year")


class ExtractedExperience(BaseModel):
    """Work experience record extracted from a resume."""

    model_config = ConfigDict(frozen=True)

    title: str = Field(default="", description="Job title")
    company: str = Field(default="", description="Company name")
    duration: str = Field(default="", description="Duration e.g. 2021-2023")
    description: str = Field(default="", description="Role description")
    skills_mentioned: list[str] = Field(
        default_factory=list,
        description="Skills mentioned in this role",
    )


class ResumeConfidenceReport(BaseModel):
    """
    AI-generated quality assessment of a resume.

    Detects potential issues like buzzword overuse or
    missing project descriptions that may indicate exaggeration.
    """

    model_config = ConfigDict(frozen=True)

    overall_quality_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Overall resume quality 0-100",
    )
    buzzword_count: int = Field(
        default=0,
        description="Number of generic buzzwords detected",
    )
    flagged_buzzwords: list[str] = Field(
        default_factory=list,
        description="Specific buzzwords flagged",
    )
    missing_descriptions: list[str] = Field(
        default_factory=list,
        description="Projects or roles with missing descriptions",
    )
    skill_claim_gaps: list[str] = Field(
        default_factory=list,
        description="Skills claimed but not supported by experience",
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Specific suggestions to improve the resume",
    )


class ResumeParseResult(BaseModel):
    """
    Complete result from parsing and analyzing a resume.

    Output of the resume intelligence pipeline.
    Used to customize question selection for the interview.
    """

    model_config = ConfigDict(frozen=False)

    user_id: int = Field(..., description="User this resume belongs to")
    file_name: str = Field(..., description="Original file name")
    raw_text: str = Field(..., description="Full extracted raw text")
    skills: list[ExtractedSkill] = Field(
        default_factory=list,
        description="All extracted and normalized skills",
    )
    education: list[ExtractedEducation] = Field(
        default_factory=list,
        description="Education records",
    )
    experience: list[ExtractedExperience] = Field(
        default_factory=list,
        description="Work experience records",
    )
    projects: list[str] = Field(
        default_factory=list,
        description="Project names and descriptions",
    )
    certifications: list[str] = Field(
        default_factory=list,
        description="Certifications mentioned",
    )
    confidence_report: Optional[ResumeConfidenceReport] = Field(
        default=None,
        description="Resume quality and confidence analysis",
    )
    competency_ids_detected: list[str] = Field(
        default_factory=list,
        description="Competency ids matched from extracted skills",
    )
    parsed_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When parsing was completed",
    )

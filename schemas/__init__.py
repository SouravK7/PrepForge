"""
Schemas package.

All Pydantic data contracts for the AI Interview Assistant.
Every pipeline, service, and API route communicates
through these typed schemas only.
No raw dictionaries are passed between modules.
"""

from schemas.answer_schema import AnswerInput, AnswerRecord
from schemas.benchmark_schema import (
    AblationResult,
    BenchmarkAnswer,
    BenchmarkQuestion,
    BenchmarkResult,
    BenchmarkRunReport,
    ErrorAnalysisEntry,
)
from schemas.competency_schema import (
    Competency,
    CompetencyGap,
    CompetencyScore,
    CompetencyUpdate,
    SkillGraph,
    SkillGraphEdge,
    SkillGraphNode,
)
from schemas.evaluation_schema import (
    EvaluationEvidence,
    EvaluationExplanation,
    EvaluationOutput,
    EvaluationScores,
    GradeEnum,
    ReadinessEnum,
)
from schemas.question_schema import (
    DifficultyLevel,
    InterviewPhase,
    Question,
    QuestionType,
    SessionQuestion,
)
from schemas.recommendation_schema import (
    LearningRoadmap,
    Recommendation,
    Resource,
    WeeklyPlan,
)
from schemas.report_schema import (
    InterviewReport,
    SessionSummary,
)
from schemas.resume_schema import (
    ExtractedEducation,
    ExtractedExperience,
    ExtractedSkill,
    ResumeConfidenceReport,
    ResumeParseResult,
)
from schemas.rubric_schema import (
    Rubric,
    RubricCriterion,
    RubricType,
    ScoringGuide,
)

__all__ = [
    # Answer
    "AnswerInput",
    "AnswerRecord",
    # Benchmark
    "BenchmarkAnswer",
    "BenchmarkQuestion",
    "BenchmarkResult",
    "BenchmarkRunReport",
    "AblationResult",
    "ErrorAnalysisEntry",
    # Competency
    "Competency",
    "CompetencyScore",
    "CompetencyUpdate",
    "CompetencyGap",
    "SkillGraphNode",
    "SkillGraphEdge",
    "SkillGraph",
    # Evaluation
    "EvaluationScores",
    "EvaluationEvidence",
    "EvaluationExplanation",
    "EvaluationOutput",
    "GradeEnum",
    "ReadinessEnum",
    # Question
    "Question",
    "QuestionType",
    "DifficultyLevel",
    "InterviewPhase",
    "SessionQuestion",
    # Recommendation
    "Resource",
    "Recommendation",
    "WeeklyPlan",
    "LearningRoadmap",
    # Report
    "SessionSummary",
    "InterviewReport",
    # Resume
    "ResumeParseResult",
    "ExtractedSkill",
    "ExtractedEducation",
    "ExtractedExperience",
    "ResumeConfidenceReport",
    # Rubric
    "ScoringGuide",
    "RubricCriterion",
    "Rubric",
    "RubricType",
]

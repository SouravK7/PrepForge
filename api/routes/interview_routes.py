"""
Interview session routes.

Manages interview lifecycle: start, next question, submit answer, complete.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db
from database.models import User
from services.interview_service import InterviewService
from services.evaluation_service import EvaluationService
from schemas.answer_schema import AnswerInput
from schemas.question_schema import QuestionType

router = APIRouter()


# ─── Request / Response Models ────────────────────────────────

class StartSessionRequest(BaseModel):
    """Request to start a new interview session."""

    job_role: str = Field(default="Software Engineer")
    difficulty: str = Field(default="intermediate")
    experience_level: str = Field(default="")
    total_questions: int = Field(default=10, ge=3, le=20)


class StartSessionResponse(BaseModel):
    """Response after session starts."""

    session_id: int
    job_role: str
    blueprint: list[dict]
    first_question: dict | None


class NextQuestionRequest(BaseModel):
    """Request for the next adaptive question."""

    session_id: int
    asked_question_ids: list[str] = Field(default_factory=list)
    last_score: float | None = None
    last_competency_id: str | None = None
    question_number: int = Field(default=1, ge=1)
    total_questions: int = Field(default=10, ge=1)


class NextQuestionResponse(BaseModel):
    """Response with next question."""

    question: dict | None
    phase: str
    question_number: int
    total_questions: int
    is_complete: bool


class SubmitAnswerRequest(BaseModel):
    """Request to submit an answer."""

    session_id: int
    question_id: str
    competency_id: str
    question_text: str
    question_type: str = Field(default="technical")
    sample_answer: str
    required_concepts: list[str] = Field(default_factory=list)
    optional_concepts: list[str] = Field(default_factory=list)
    rubric_id: str = Field(default="rubric_technical_standard")
    user_answer: str = Field(..., min_length=1)
    time_taken: int = Field(default=0, ge=0)
    question_elo: float = Field(default=1200.0)


class SubmitAnswerResponse(BaseModel):
    """Response after answer submission."""

    answer_id: int
    session_id: int
    scores: dict
    grade: str
    readiness_level: str
    matched_concepts: list[str]
    missing_concepts: list[str]
    strengths: list[str]
    weaknesses: list[str]
    explanation: dict
    improvement_tip: str
    competency_delta: float


class CompleteSessionRequest(BaseModel):
    """Request to complete a session."""

    session_id: int
    evaluation_scores: list[float]
    technical_scores: list[float] = Field(default_factory=list)
    hr_scores: list[float] = Field(default_factory=list)
    answered_questions: int


class SessionHistoryResponse(BaseModel):
    """Session history item."""

    session_id: int
    job_role: str
    overall_score: float
    readiness_level: str
    answered_questions: int
    completed_at: str


# ─── Routes ──────────────────────────────────────────────────

@router.post(
    "/start",
    response_model=StartSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new interview session",
)
def start_session(
    request: StartSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StartSessionResponse:
    """
    Start a new adaptive interview session.

    Creates a session record, generates the interview blueprint,
    and returns the first question.

    Args:
        request: Session configuration.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        StartSessionResponse with session_id and first question.
    """
    service = InterviewService(db)
    result = service.start_session(
        user_id=current_user.id,
        job_role=request.job_role,
        difficulty=request.difficulty,
        experience_level=request.experience_level,
        total_questions=request.total_questions,
    )

    first_q = None
    if result.first_question:
        first_q = {
            "id": result.first_question.id,
            "question_text": result.first_question.question_text,
            "question_type": result.first_question.question_type.value,
            "difficulty": result.first_question.difficulty.value,
            "competency_id": result.first_question.competency_id,
            "required_concepts": result.first_question.required_concepts,
            "sample_answer": result.first_question.sample_answer,
            "rubric_id": result.first_question.rubric_id,
            "elo_difficulty": result.first_question.elo_difficulty,
        }

    return StartSessionResponse(
        session_id=result.session_id,
        job_role=result.job_role,
        blueprint=result.blueprint,
        first_question=first_q,
    )


@router.post(
    "/next-question",
    response_model=NextQuestionResponse,
    summary="Get the next adaptive interview question",
)
def get_next_question(
    request: NextQuestionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NextQuestionResponse:
    """
    Get the next adaptively selected question.

    Uses Elo ratings to select appropriate difficulty.

    Args:
        request: Current session context.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        NextQuestionResponse with next question or completion signal.
    """
    service = InterviewService(db)
    result = service.get_next_question(
        session_id=request.session_id,
        user_id=current_user.id,
        job_role=current_user.target_role or "Software Engineer",
        asked_question_ids=request.asked_question_ids,
        last_score=request.last_score,
        last_competency_id=request.last_competency_id,
        question_number=request.question_number,
        total_questions=request.total_questions,
    )

    question_dict = None
    if result.question:
        question_dict = {
            "id": result.question.id,
            "question_text": result.question.question_text,
            "question_type": result.question.question_type.value,
            "difficulty": result.question.difficulty.value,
            "competency_id": result.question.competency_id,
            "required_concepts": result.question.required_concepts,
            "sample_answer": result.question.sample_answer,
            "rubric_id": result.question.rubric_id,
            "elo_difficulty": result.question.elo_difficulty,
        }

    return NextQuestionResponse(
        question=question_dict,
        phase=result.phase.value,
        question_number=result.question_number,
        total_questions=result.total_questions,
        is_complete=result.is_complete,
    )


@router.post(
    "/submit-answer",
    response_model=SubmitAnswerResponse,
    summary="Submit an answer and receive AI evaluation",
)
def submit_answer(
    request: SubmitAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SubmitAnswerResponse:
    """
    Submit an answer and receive complete AI evaluation.

    Runs the full evaluation ensemble and returns explainable scores.

    Args:
        request: Answer submission with full question context.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        SubmitAnswerResponse with all scores and explanations.

    Raises:
        HTTPException 400: If answer is empty.
    """
    if not request.user_answer.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Answer cannot be empty.",
        )

    answer_input = AnswerInput(
        session_id=request.session_id,
        user_id=current_user.id,
        question_id=request.question_id,
        competency_id=request.competency_id,
        question_text=request.question_text,
        question_type=QuestionType(request.question_type),
        sample_answer=request.sample_answer,
        required_concepts=request.required_concepts,
        optional_concepts=request.optional_concepts,
        rubric_id=request.rubric_id,
        user_answer=request.user_answer,
        time_taken=request.time_taken,
    )

    service = EvaluationService(db)
    result = service.evaluate_answer(answer_input, request.question_elo)

    ev = result.evaluation

    return SubmitAnswerResponse(
        answer_id=result.answer_id,
        session_id=ev.session_id,
        scores={
            "semantic": ev.scores.semantic,
            "concept": ev.scores.concept,
            "communication": ev.scores.communication,
            "evidence": ev.scores.evidence,
            "reasoning": ev.scores.reasoning,
            "weighted_final": ev.scores.weighted_final,
        },
        grade=ev.grade.value,
        readiness_level=ev.readiness_level.value,
        matched_concepts=ev.evidence.matched_concepts,
        missing_concepts=ev.evidence.missing_concepts,
        strengths=ev.evidence.strengths,
        weaknesses=ev.evidence.weaknesses,
        explanation={
            "semantic_reason": ev.explanation.semantic_reason,
            "concept_reason": ev.explanation.concept_reason,
            "communication_reason": ev.explanation.communication_reason,
            "evidence_reason": ev.explanation.evidence_reason,
            "reasoning_reason": ev.explanation.reasoning_reason,
            "overall_summary": ev.explanation.overall_summary,
        },
        improvement_tip=ev.explanation.improvement_tip,
        competency_delta=ev.competency_delta,
    )


@router.post(
    "/complete",
    summary="Complete an interview session",
)
def complete_session(
    request: CompleteSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Mark an interview session as completed.

    Computes final scores and updates the session record.

    Args:
        request: Final session data.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        Final session summary dict.
    """
    service = InterviewService(db)
    return service.complete_session(
        session_id=request.session_id,
        evaluation_scores=request.evaluation_scores,
        technical_scores=request.technical_scores,
        hr_scores=request.hr_scores,
        answered_questions=request.answered_questions,
    )


@router.get(
    "/history",
    summary="Get interview session history",
)
def get_history(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    Get completed session history for the current user.

    Args:
        limit: Maximum sessions to return.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        List of session summary dicts.
    """
    service = InterviewService(db)
    return service.get_session_history(current_user.id, limit)


@router.get(
    "/session/{session_id}",
    summary="Get session details",
)
def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Get details of a specific session.

    Args:
        session_id: Target session ID.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        Session summary dict.

    Raises:
        HTTPException 404: If session not found.
    """
    from services.report_service import ReportService

    service = ReportService(db)
    summary = service.get_session_summary(session_id)

    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found.",
        )

    # Note: ReportService.get_session_summary returns a SessionSummary schema
    # Pydantic models need to be dumped to dict for FastAPI response
    return summary.model_dump()

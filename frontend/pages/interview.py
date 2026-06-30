"""
Interview simulation page.

Core interview experience: adaptive questions,
answer submission, and real-time evaluation display.
"""

from __future__ import annotations

import time

import streamlit as st
from frontend.session_state import get_api_client, require_auth, reset_interview_state
from frontend.components.score_cards import grade_card, dimension_scores_table, concept_tags
from frontend.components.rubric_view import (
    show_explanation_card,
    show_improvement_tip,
    show_strengths_weaknesses,
)
from frontend.components.charts import dimension_bar_chart

ROLES = [
    "Software Engineer",
    "Data Analyst",
    "AI Engineer",
    "Web Developer",
    "Data Scientist",
]

DIFFICULTIES = ["beginner", "intermediate", "advanced"]


def render() -> None:
    """Render the interview simulation page."""
    if not require_auth():
        return

    if st.session_state.get("interview_complete"):
        _render_session_complete()
        return

    if not st.session_state.get("interview_active"):
        _render_setup()
    else:
        _render_interview()


def _render_setup() -> None:
    """Render interview setup configuration."""
    st.markdown("# Interview Setup")
    st.markdown("Configure your adaptive practice interview session.")
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        default_role = st.session_state.get("target_role", "Software Engineer")
        role_index = ROLES.index(default_role) if default_role in ROLES else 0
        job_role = st.selectbox("Target Job Role", ROLES, index=role_index,
                                key="setup_role")
        difficulty = st.selectbox("Difficulty Level", DIFFICULTIES, index=1,
                                  key="setup_difficulty")

    with col2:
        total_questions = st.slider(
            "Number of Questions", min_value=3, max_value=15, value=10,
            key="setup_total",
        )
        st.markdown("**Interview Blueprint**")
        st.caption(
            "Introduction (1) → Resume Check (1) → "
            "Core Technical (5+) → Behavioral (1) → Closing (1)"
        )

    st.markdown("---")

    if st.button("Start Interview", use_container_width=True, type="primary",
                 key="btn_start_interview"):
        _start_interview(job_role, difficulty, total_questions)


def _start_interview(job_role: str, difficulty: str, total_questions: int) -> None:
    """Start a new interview session via API."""
    client = get_api_client()
    reset_interview_state()

    try:
        with st.spinner("Starting your interview..."):
            result = client.start_session(
                job_role=job_role,
                difficulty=difficulty,
                total_questions=total_questions,
            )

        st.session_state.session_id = result["session_id"]
        st.session_state.total_questions = total_questions
        st.session_state.question_number = 1
        st.session_state.interview_active = True

        if result.get("first_question"):
            st.session_state.current_question = result["first_question"]
            st.session_state.asked_question_ids.append(
                result["first_question"]["id"]
            )

        st.rerun()

    except ValueError as e:
        st.error(f"Failed to start interview: {e}")


def _render_interview() -> None:
    """Render the active interview interface."""
    q_num = st.session_state.get("question_number", 1)
    total = st.session_state.get("total_questions", 10)
    question = st.session_state.get("current_question")

    # Progress indicator
    progress = min(q_num / total, 1.0)
    st.progress(progress)
    st.caption(f"Question {q_num} of {total}")
    st.markdown("---")

    if not question:
        st.warning("Loading next question...")
        _load_next_question()
        return

    # Question context tags
    q_type = question.get("question_type", "technical").upper()
    difficulty = question.get("difficulty", "").title()
    competency = (
        question.get("competency_id", "")
        .replace("comp_se_", "").replace("comp_da_", "").replace("comp_ai_", "")
        .replace("_", " ").title()
    )

    st.markdown(
        f"""
        <div style="
            background:#f8f9fa;
            border-left:5px solid #3498db;
            padding:16px 20px;
            border-radius:6px;
            margin-bottom:16px;
        ">
            <div style="font-size:11px;color:#888;margin-bottom:8px;">
                [{q_type}] &nbsp;|&nbsp; {difficulty} &nbsp;|&nbsp; {competency}
            </div>
            <div style="font-size:17px;font-weight:600;color:#2c3e50;line-height:1.5;">
                {question.get("question_text", "")}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not st.session_state.get("answer_submitted"):
        if st.session_state.get("time_started") is None:
            st.session_state.time_started = time.time()

        answer = st.text_area(
            "Your Answer",
            height=180,
            placeholder=(
                "Type your answer here. Be clear, specific, "
                "and include examples where possible..."
            ),
            key=f"answer_input_{q_num}",
        )

        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("Submit Answer", use_container_width=True,
                         type="primary", key=f"btn_submit_{q_num}"):
                if not answer.strip():
                    st.warning("Please write an answer before submitting.")
                else:
                    _submit_answer(question, answer)
        with col2:
            if st.button("Skip Question", use_container_width=True,
                         key=f"btn_skip_{q_num}"):
                _move_to_next_question()
    else:
        _show_evaluation_result()


def _submit_answer(question: dict, answer: str) -> None:
    """Submit an answer to the API and display evaluation."""
    client = get_api_client()
    time_taken = int(
        time.time() - (st.session_state.get("time_started") or time.time())
    )

    answer_data = {
        "session_id": st.session_state.session_id,
        "question_id": question["id"],
        "competency_id": question["competency_id"],
        "question_text": question["question_text"],
        "question_type": question["question_type"],
        "sample_answer": question.get("sample_answer", ""),
        "required_concepts": question.get("required_concepts", []),
        "optional_concepts": question.get("optional_concepts", []),
        "rubric_id": question.get("rubric_id", "rubric_technical_standard"),
        "user_answer": answer,
        "time_taken": time_taken,
        "question_elo": question.get("elo_difficulty", 1200.0),
    }

    try:
        with st.spinner("Evaluating your answer with AI..."):
            result = client.submit_answer(answer_data)

        # Store evaluation in session state
        st.session_state.last_evaluation = result
        st.session_state.answer_submitted = True

        score = result["scores"]["weighted_final"]
        st.session_state.evaluation_scores.append(score)

        q_type = question.get("question_type", "technical")
        if q_type == "technical":
            st.session_state.technical_scores.append(score)
        else:
            st.session_state.hr_scores.append(score)

        # Store evaluation for results page
        result["question_text"] = question["question_text"]
        result["question_type"] = q_type
        result["question_number"] = st.session_state.question_number
        st.session_state.session_evaluations.append(result)

        st.rerun()

    except ValueError as e:
        st.error(f"Evaluation failed: {e}")


def _show_evaluation_result() -> None:
    """Display the last evaluation result inline."""
    ev = st.session_state.get("last_evaluation")
    if not ev:
        return

    scores = ev.get("scores", {})
    final_score = scores.get("weighted_final", 0)
    grade = ev.get("grade", "F")
    readiness = ev.get("readiness_level", "poor")

    st.markdown("---")
    st.markdown("### AI Evaluation")

    col_grade, col_scores = st.columns([1, 2])

    with col_grade:
        grade_card(grade, readiness, final_score)

    with col_scores:
        dimension_scores_table(scores)

    st.markdown("---")
    concept_tags(
        matched=ev.get("matched_concepts", []),
        missing=ev.get("missing_concepts", []),
    )

    show_strengths_weaknesses(
        strengths=ev.get("strengths", []),
        weaknesses=ev.get("weaknesses", []),
    )

    show_improvement_tip(ev.get("improvement_tip", ""))

    with st.expander("Score Explanations"):
        show_explanation_card(ev.get("explanation", {}))

    st.markdown("---")

    q_num = st.session_state.get("question_number", 1)
    total = st.session_state.get("total_questions", 10)

    if q_num >= total:
        if st.button("Finish Interview & View Results", use_container_width=True,
                     type="primary", key="btn_finish"):
            _finish_session()
    else:
        if st.button("Next Question", use_container_width=True,
                     type="primary", key=f"btn_next_{q_num}"):
            _move_to_next_question()


def _move_to_next_question() -> None:
    """Advance to the next question."""
    q_num = st.session_state.get("question_number", 1)
    total = st.session_state.get("total_questions", 10)

    if q_num >= total:
        _finish_session()
        return

    st.session_state.question_number = q_num + 1
    st.session_state.answer_submitted = False
    st.session_state.last_evaluation = None
    st.session_state.time_started = None
    st.session_state.current_question = None
    _load_next_question()


def _load_next_question() -> None:
    """Load the next adaptive question from the API."""
    client = get_api_client()
    q_num = st.session_state.get("question_number", 1)

    # Get last score and competency for adaptive selection
    eval_scores = st.session_state.get("evaluation_scores", [])
    session_evals = st.session_state.get("session_evaluations", [])
    last_score = eval_scores[-1] if eval_scores else None
    last_comp = None
    if session_evals:
        last_comp = session_evals[-1].get("competency_id")

    try:
        result = client.get_next_question(
            session_id=st.session_state.session_id,
            asked_question_ids=st.session_state.asked_question_ids,
            last_score=last_score,
            last_competency_id=last_comp,
            question_number=q_num,
            total_questions=st.session_state.total_questions,
        )

        if result.get("is_complete") or not result.get("question"):
            _finish_session()
            return

        question = result["question"]
        st.session_state.current_question = question
        st.session_state.asked_question_ids.append(question["id"])
        st.rerun()

    except ValueError as e:
        st.error(f"Failed to load question: {e}")


def _finish_session() -> None:
    """Complete the session and navigate to results."""
    client = get_api_client()

    try:
        with st.spinner("Saving your session..."):
            client.complete_session(
                session_id=st.session_state.session_id,
                evaluation_scores=st.session_state.evaluation_scores,
                technical_scores=st.session_state.technical_scores,
                hr_scores=st.session_state.hr_scores,
                answered_questions=len(st.session_state.evaluation_scores),
            )
    except ValueError:
        pass  # Non-fatal — local state is still valid

    st.session_state.interview_active = False
    st.session_state.interview_complete = True
    st.rerun()


def _render_session_complete() -> None:
    """Render session complete screen with summary."""
    scores = st.session_state.get("evaluation_scores", [])
    overall = sum(scores) / len(scores) if scores else 0.0

    st.markdown("# Interview Complete!")
    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Questions Answered", len(scores))
    with col2:
        st.metric("Overall Score", f"{overall:.1f}")
    with col3:
        tech = st.session_state.get("technical_scores", [])
        tech_avg = sum(tech) / len(tech) if tech else 0
        st.metric("Technical Score", f"{tech_avg:.1f}")

    st.markdown("---")

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("View Full Results", use_container_width=True,
                     type="primary", key="btn_view_results"):
            st.session_state.current_page = "results"
            st.rerun()

    with col_b:
        if st.button("Start New Interview", use_container_width=True,
                     key="btn_new_interview"):
            reset_interview_state()
            st.rerun()

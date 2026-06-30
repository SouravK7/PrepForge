"""
Results page.

Displays the full session report after an interview completes.
Shows per-question evaluations with all scores and explanations.
"""

from __future__ import annotations

import streamlit as st
from frontend.session_state import get_api_client, require_auth, reset_interview_state
from frontend.components.score_cards import (
    grade_card,
    dimension_scores_table,
    concept_tags,
    readiness_gauge,
)
from frontend.components.charts import dimension_bar_chart, score_trend_chart
from frontend.components.rubric_view import (
    show_explanation_card,
    show_improvement_tip,
    show_strengths_weaknesses,
)


def render() -> None:
    """Render the session results page."""
    if not require_auth():
        return

    st.markdown("# Session Results")
    st.markdown("---")

    session_id = st.session_state.get("session_id")
    evaluations = st.session_state.get("session_evaluations", [])
    scores = st.session_state.get("evaluation_scores", [])

    if not scores and not session_id:
        st.info("No completed session. Start an interview first.")
        if st.button("Start Interview", key="results_start"):
            st.session_state.current_page = "interview"
            st.rerun()
        return

    # ── Overview metrics ────────────────────────────────────────
    overall = sum(scores) / len(scores) if scores else 0.0
    tech_scores = st.session_state.get("technical_scores", [])
    hr_scores = st.session_state.get("hr_scores", [])
    tech_avg = sum(tech_scores) / len(tech_scores) if tech_scores else 0.0
    hr_avg = sum(hr_scores) / len(hr_scores) if hr_scores else 0.0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Overall Score", f"{overall:.1f}")
    with col2:
        st.metric("Technical", f"{tech_avg:.1f}")
    with col3:
        st.metric("HR / Behavioral", f"{hr_avg:.1f}")
    with col4:
        st.metric("Questions", len(scores))

    st.markdown("---")

    # ── Try to load session readiness from API ───────────────────
    client = get_api_client()
    role = st.session_state.get("target_role", "Software Engineer")

    col_readiness, col_chart = st.columns([1, 2])
    with col_readiness:
        try:
            r = client.get_readiness(role)
            readiness_gauge(r.get("readiness_percentage", 0), f"{role} Readiness")
        except ValueError:
            readiness_gauge(overall, "Session Score")

    with col_chart:
        try:
            trend = client.get_score_trend(limit=10)
            score_trend_chart(trend)
        except ValueError:
            pass

    # ── Per-question evaluation breakdown ───────────────────────
    st.markdown("---")
    st.markdown("## Question-by-Question Breakdown")

    if not evaluations:
        # Try to fetch from API
        if session_id:
            try:
                evaluations = client.get_session_evaluations(session_id)
            except ValueError:
                pass

    if evaluations:
        for i, ev in enumerate(evaluations, 1):
            q_text = ev.get("question_text", f"Question {i}")
            q_type = ev.get("question_type", "technical").upper()
            ev_scores = ev.get("scores", {})
            final = ev_scores.get("weighted_final", 0)
            grade = ev.get("grade", "F")
            readiness = ev.get("readiness_level", "poor")

            with st.expander(
                f"Q{i} [{q_type}] — Score: {final:.1f}  |  Grade: {grade}  "
                f"|  {readiness.replace('_', ' ').title()}",
                expanded=(i == 1),
            ):
                st.markdown(f"**{q_text}**")
                st.markdown("---")

                col_g, col_s = st.columns([1, 2])
                with col_g:
                    grade_card(grade, readiness, final)
                with col_s:
                    dimension_scores_table(ev_scores)

                dimension_bar_chart(ev_scores)

                concept_tags(
                    matched=ev.get("matched_concepts", []),
                    missing=ev.get("missing_concepts", []),
                )

                show_strengths_weaknesses(
                    strengths=ev.get("strengths", []),
                    weaknesses=ev.get("weaknesses", []),
                )

                show_improvement_tip(ev.get("improvement_tip", ""))

                explanation = ev.get("explanation", {})
                if explanation:
                    show_explanation_card(explanation)
    else:
        st.info("Evaluation details not available for this session.")

    # ── Post-session actions ─────────────────────────────────────
    st.markdown("---")
    st.markdown("### What's Next?")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        if st.button("Generate Learning Plan", use_container_width=True,
                     type="primary", key="results_gen_recs"):
            _generate_recommendations()

    with col_b:
        if st.button("View Skill Map", use_container_width=True,
                     key="results_skillmap"):
            st.session_state.current_page = "skill_map"
            st.rerun()

    with col_c:
        if st.button("Start New Interview", use_container_width=True,
                     key="results_new_interview"):
            reset_interview_state()
            st.session_state.current_page = "interview"
            st.rerun()


def _generate_recommendations() -> None:
    """Generate recommendations for the completed session."""
    client = get_api_client()
    session_id = st.session_state.get("session_id")
    role = st.session_state.get("target_role", "Software Engineer")

    if not session_id:
        st.warning("Session ID not available.")
        return

    try:
        with st.spinner("Generating your personalized learning plan..."):
            client.generate_recommendations(
                session_id=session_id,
                target_role=role,
            )
        st.success("Learning plan generated!")
        st.session_state.current_page = "recommendations"
        st.rerun()
    except ValueError as e:
        st.error(f"Could not generate recommendations: {e}")

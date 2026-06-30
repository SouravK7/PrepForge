"""
Skill map page.

Visualizes the user's skill confidence graph
with competency nodes and gap priorities.
"""

from __future__ import annotations

import streamlit as st
from frontend.session_state import get_api_client, require_auth
from frontend.components.charts import (
    competency_radar_chart,
    skill_confidence_bar,
)
from frontend.components.score_cards import readiness_gauge

ROLES = [
    "Software Engineer",
    "Data Analyst",
    "AI Engineer",
    "Web Developer",
    "Data Scientist",
]


def render() -> None:
    """Render the skill map page."""
    if not require_auth():
        return

    client = get_api_client()
    default_role = st.session_state.get("target_role", "Software Engineer")

    st.markdown("# Skill Map")
    st.markdown("*Your competency confidence levels and skill gaps*")
    st.markdown("---")

    role_index = ROLES.index(default_role) if default_role in ROLES else 0
    job_role = st.selectbox("Select Role", ROLES, index=role_index,
                            key="skillmap_role")

    st.markdown("---")

    # ── Readiness gauge ─────────────────────────────────────────
    try:
        readiness_data = client.get_readiness(job_role)
        col_gauge, col_meta = st.columns([1, 2])
        with col_gauge:
            readiness_gauge(
                readiness_data.get("readiness_percentage", 0),
                f"{job_role} Readiness",
            )
        with col_meta:
            label = readiness_data.get("readiness_label", "")
            pct = readiness_data.get("readiness_percentage", 0)
            st.markdown(f"### {label}")
            st.write(
                f"You are **{pct:.1f}%** ready for a **{job_role}** interview. "
                "The radar chart below shows how your confidence is distributed "
                "across key competencies."
            )
    except ValueError:
        st.info("Complete an interview to populate your skill map.")

    st.markdown("---")

    # ── Radar chart from analytics ───────────────────────────────
    try:
        radar = client.get_competency_radar()
        labels = radar.get("labels", [])
        values = radar.get("values", [])
        if labels and values:
            competency_radar_chart(labels, values)
    except ValueError:
        pass

    # ── Confidence bar chart ─────────────────────────────────────
    try:
        scores = client.get_competency_scores()
        if scores:
            skill_confidence_bar(scores)
    except ValueError:
        pass

    # ── Skill gaps table ─────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Prioritized Skill Gaps")

    try:
        gaps = client.get_skill_gaps(job_role, top_n=10)
        if gaps:
            priority_icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}

            for gap in gaps:
                icon = priority_icons.get(gap.get("priority", "low"), "⚪")
                name = gap.get("competency_name", "Unknown")
                confidence = gap.get("current_confidence", 0) * 100
                gap_val = gap.get("gap", 0) * 100
                action = gap.get("recommended_action", "")
                relevance = gap.get("role_relevance", 0)

                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"**{icon} {name}**")
                    st.caption(action)
                with col2:
                    st.metric("Confidence", f"{confidence:.0f}%")
                with col3:
                    st.metric("Gap", f"{gap_val:.0f}%")
                st.markdown("---")
        else:
            st.success(
                "No skill gaps detected. You meet the readiness threshold "
                "for all key competencies!"
            )
    except ValueError as e:
        st.error(str(e))

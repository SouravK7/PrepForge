"""
Recommendations page.

Displays personalized learning roadmap, weekly plans,
and resource links generated from skill gaps.
"""

from __future__ import annotations

import streamlit as st
from frontend.session_state import get_api_client, require_auth

ROLES = [
    "Software Engineer",
    "Data Analyst",
    "AI Engineer",
    "Web Developer",
    "Data Scientist",
]


def render() -> None:
    """Render the recommendations page."""
    if not require_auth():
        return

    client = get_api_client()
    role = st.session_state.get("target_role", "Software Engineer")

    st.markdown("# Learning Recommendations")
    st.markdown("*Personalized study plan based on your skill gaps*")
    st.markdown("---")

    tab_saved, tab_generate = st.tabs(["My Recommendations", "Generate New Plan"])

    with tab_saved:
        _render_saved_recommendations(client)

    with tab_generate:
        _render_generate_plan(client, role)


def _render_saved_recommendations(client) -> None:
    """Render saved recommendations with completion tracking."""
    st.markdown("### Your Learning Plan")

    filter_col, _ = st.columns([1, 2])
    with filter_col:
        show_filter = st.selectbox(
            "Filter",
            ["All", "Pending", "Completed"],
            key="rec_filter",
        )

    completed_filter = None
    if show_filter == "Pending":
        completed_filter = False
    elif show_filter == "Completed":
        completed_filter = True

    try:
        recs = client.get_recommendations(completed=completed_filter)

        if not recs:
            st.info(
                "No recommendations yet. "
                "Complete an interview, then generate your plan."
            )
            return

        # Group by week
        by_week: dict[int, list] = {}
        for rec in recs:
            week = rec.get("week_number", 1)
            by_week.setdefault(week, []).append(rec)

        for week_num in sorted(by_week.keys()):
            week_recs = by_week[week_num]
            total = len(week_recs)
            completed = sum(1 for r in week_recs if r.get("is_completed"))

            st.markdown(
                f"### Week {week_num} &nbsp; "
                f"<span style='font-size:13px;color:#888;'>"
                f"{completed}/{total} completed</span>",
                unsafe_allow_html=True,
            )

            for rec in week_recs:
                _render_recommendation_card(client, rec)

    except ValueError as e:
        st.error(str(e))


def _render_recommendation_card(client, rec: dict) -> None:
    """Render a single recommendation card with completion button."""
    rec_id = rec.get("id")
    title = rec.get("title", "")
    description = rec.get("description", "")
    resource_url = rec.get("resource_url", "")
    resource_type = rec.get("resource_type", "")
    priority = rec.get("priority", "medium")
    hours = rec.get("estimated_hours", 0)
    is_completed = rec.get("is_completed", False)
    competency = rec.get("competency_name", "")

    priority_icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}
    icon = priority_icons.get(priority, "⚪")
    status_icon = "✅" if is_completed else "📖"

    with st.container():
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(
                f"**{status_icon} {title}** {icon}",
            )
            if competency:
                st.caption(f"Skill: {competency}")
            st.write(description)
            if resource_url:
                type_label = resource_type.replace("_", " ").title() if resource_type else "Resource"
                st.markdown(f"[{type_label} — Open]({resource_url})")
            if hours:
                st.caption(f"Estimated: {hours}h")
        with col2:
            if not is_completed and rec_id:
                if st.button("Done", key=f"rec_done_{rec_id}"):
                    try:
                        client.mark_recommendation_completed(rec_id)
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
        st.markdown("---")


def _render_generate_plan(client, role: str) -> None:
    """Render generate new recommendation plan form."""
    st.markdown("### Generate New Learning Plan")
    st.write(
        "This analyzes your current skill gaps and creates a "
        "personalized week-by-week study roadmap."
    )

    session_id = st.session_state.get("session_id")

    role_index = ROLES.index(role) if role in ROLES else 0
    selected_role = st.selectbox(
        "Target Role", ROLES, index=role_index, key="gen_rec_role"
    )
    max_weeks = st.slider(
        "Plan Duration (weeks)", min_value=2, max_value=12, value=6,
        key="gen_rec_weeks"
    )

    if not session_id:
        st.info("You need to complete at least one interview session first.")
        if st.button("Start Interview", key="rec_start_interview"):
            st.session_state.current_page = "interview"
            st.rerun()
        return

    if st.button(
        "Generate Plan",
        use_container_width=True,
        type="primary",
        key="btn_gen_plan",
    ):
        try:
            with st.spinner("Analyzing your skill gaps and generating your plan..."):
                result = client.generate_recommendations(
                    session_id=session_id,
                    target_role=selected_role,
                    max_weeks=max_weeks,
                )

            st.success(
                f"Learning plan generated! {result.get('gap_count', 0)} gaps addressed "
                f"across {result.get('total_weeks', max_weeks)} weeks."
            )

            # Preview the roadmap
            weekly_plans = result.get("weekly_plans", [])
            if weekly_plans:
                st.markdown("---")
                st.markdown("### Your Roadmap Preview")
                for plan in weekly_plans:
                    week_num = plan.get("week_number", 1)
                    focus = plan.get("focus_competency", "")
                    goal = plan.get("goal", "")
                    hours = plan.get("estimated_hours", 0)

                    with st.expander(
                        f"Week {week_num}: {focus} ({hours}h)",
                        expanded=(week_num == 1),
                    ):
                        if goal:
                            st.write(f"**Goal:** {goal}")
                        for rec in plan.get("recommendations", []):
                            r_title = rec.get("title", "")
                            r_url = rec.get("resource_url", "")
                            r_type = rec.get("resource_type", "")
                            r_hours = rec.get("estimated_hours", 0)
                            priority = rec.get("priority", "medium")
                            p_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "")
                            link = f"[{r_type.replace('_', ' ').title()}]({r_url})" if r_url else ""
                            st.markdown(
                                f"- {p_icon} **{r_title}** ({r_hours}h) {link}"
                            )

            st.rerun()

        except ValueError as e:
            st.error(str(e))

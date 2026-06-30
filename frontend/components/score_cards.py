"""
Score card UI components.

Reusable components for displaying AI evaluation scores.
"""

from __future__ import annotations

import streamlit as st


def score_badge(score: float, label: str = "") -> None:
    """
    Display a colored score badge.

    Args:
        score: Score value 0-100.
        label: Optional label text.
    """
    if score >= 85:
        color = "#2ecc71"
        bg = "#d5f5e3"
        grade = "Excellent"
    elif score >= 70:
        color = "#3498db"
        bg = "#d6eaf8"
        grade = "Good"
    elif score >= 50:
        color = "#f39c12"
        bg = "#fef9e7"
        grade = "Average"
    else:
        color = "#e74c3c"
        bg = "#fadbd8"
        grade = "Needs Work"

    st.markdown(
        f"""
        <div style="
            background-color: {bg};
            border-left: 4px solid {color};
            padding: 12px 16px;
            border-radius: 6px;
            margin: 4px 0;
        ">
            <span style="color: {color}; font-size: 24px; font-weight: bold;">
                {score:.1f}
            </span>
            <span style="color: #666; font-size: 14px; margin-left: 8px;">
                / 100 &nbsp; {grade}
            </span>
            {f'<div style="color: #444; font-size: 13px; margin-top: 4px;">{label}</div>' if label else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def dimension_scores_table(scores: dict) -> None:
    """
    Display all dimension scores as progress bars.

    Args:
        scores: Dict of dimension name to score value.
    """
    st.markdown("**Score Breakdown**")

    for dimension, score in scores.items():
        if dimension == "weighted_final":
            continue

        label = dimension.replace("_", " ").title()

        if score >= 75:
            bar_color = "#2ecc71"
        elif score >= 50:
            bar_color = "#f39c12"
        else:
            bar_color = "#e74c3c"

        bar_width = int(score)

        st.markdown(
            f"""
            <div style="margin: 6px 0;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                    <span style="font-size: 13px; color: #444;">{label}</span>
                    <span style="font-size: 13px; font-weight: bold; color: #333;">{score:.1f}</span>
                </div>
                <div style="background: #ecf0f1; border-radius: 4px; height: 8px;">
                    <div style="
                        background: {bar_color};
                        width: {bar_width}%;
                        height: 8px;
                        border-radius: 4px;
                    "></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def readiness_gauge(percentage: float, label: str = "Interview Readiness") -> None:
    """
    Display a readiness percentage as a visual gauge.

    Args:
        percentage: Readiness 0-100.
        label: Gauge label.
    """
    if percentage >= 85:
        color = "#2ecc71"
        status = "Excellent"
    elif percentage >= 70:
        color = "#3498db"
        status = "Good"
    elif percentage >= 50:
        color = "#f39c12"
        status = "Average"
    else:
        color = "#e74c3c"
        status = "Needs Work"

    st.markdown(
        f"""
        <div style="
            text-align: center;
            padding: 20px;
            border: 2px solid {color};
            border-radius: 12px;
            background: white;
        ">
            <div style="font-size: 48px; font-weight: bold; color: {color};">
                {percentage:.1f}%
            </div>
            <div style="font-size: 18px; color: {color}; font-weight: 600;">
                {status}
            </div>
            <div style="font-size: 13px; color: #666; margin-top: 4px;">
                {label}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def concept_tags(matched: list[str], missing: list[str]) -> None:
    """
    Display matched and missing concepts as tags.

    Args:
        matched: Concepts found in answer.
        missing: Concepts absent from answer.
    """
    if matched:
        st.markdown("**Concepts Covered** ✅")
        tags_html = " ".join([
            f'<span style="background:#d5f5e3;color:#1e8449;padding:3px 10px;border-radius:12px;'
            f'font-size:12px;margin:2px;display:inline-block;">{c}</span>'
            for c in matched
        ])
        st.markdown(tags_html, unsafe_allow_html=True)

    if missing:
        st.markdown("**Concepts Missing** ❌")
        tags_html = " ".join([
            f'<span style="background:#fadbd8;color:#c0392b;padding:3px 10px;border-radius:12px;'
            f'font-size:12px;margin:2px;display:inline-block;">{c}</span>'
            for c in missing
        ])
        st.markdown(tags_html, unsafe_allow_html=True)


def grade_card(grade: str, readiness: str, final_score: float) -> None:
    """
    Display grade card with final score.

    Args:
        grade: Letter grade A-F.
        readiness: Readiness level string.
        final_score: Weighted final score.
    """
    colors = {
        "A": "#2ecc71", "B": "#3498db",
        "C": "#f39c12", "D": "#e67e22", "F": "#e74c3c",
    }
    color = colors.get(grade, "#95a5a6")

    st.markdown(
        f"""
        <div style="
            text-align: center;
            background: white;
            border: 3px solid {color};
            border-radius: 12px;
            padding: 20px;
        ">
            <div style="font-size: 64px; font-weight: bold; color: {color};">
                {grade}
            </div>
            <div style="font-size: 22px; font-weight: bold; color: #2c3e50;">
                {final_score:.1f} / 100
            </div>
            <div style="font-size: 14px; color: #666; margin-top: 6px;">
                {readiness.replace("_", " ").title()}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

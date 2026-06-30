"""
Chart components using Plotly.

Reusable chart functions for the analytics dashboard.
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st


def score_trend_chart(trend_data: list[dict]) -> None:
    """
    Render score trend line chart.

    Args:
        trend_data: List of dicts with date and score keys.
    """
    if not trend_data:
        st.info("No session data yet. Complete interviews to see your trend.")
        return

    dates = [d.get("date", "") for d in trend_data]
    scores = [d.get("score", 0) for d in trend_data]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=scores,
        mode="lines+markers",
        line=dict(color="#3498db", width=2),
        marker=dict(size=8, color="#3498db"),
        name="Score",
    ))
    fig.add_hline(y=70, line_dash="dash", line_color="#2ecc71",
                  annotation_text="Good (70)")
    fig.add_hline(y=85, line_dash="dash", line_color="#27ae60",
                  annotation_text="Excellent (85)")
    fig.update_layout(
        title="Score Trend Over Sessions",
        xaxis_title="Session Date",
        yaxis_title="Score",
        yaxis=dict(range=[0, 105]),
        height=350,
        showlegend=False,
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#ecf0f1")
    fig.update_yaxes(showgrid=True, gridcolor="#ecf0f1")
    st.plotly_chart(fig, use_container_width=True)


def competency_radar_chart(labels: list[str], values: list[float]) -> None:
    """
    Render competency radar chart.

    Args:
        labels: Competency names.
        values: Confidence percentages.
    """
    if not labels or not values:
        st.info("No competency data yet. Complete an interview to see your skill map.")
        return

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=labels + [labels[0]],
        fill="toself",
        fillcolor="rgba(52, 152, 219, 0.2)",
        line=dict(color="#3498db", width=2),
        name="Current Level",
    ))
    fig.add_trace(go.Scatterpolar(
        r=[70] * (len(labels) + 1),
        theta=labels + [labels[0]],
        line=dict(color="#2ecc71", width=1, dash="dash"),
        name="Target (70%)",
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100], ticksuffix="%")),
        showlegend=True,
        height=400,
        title="Competency Confidence Radar",
    )
    st.plotly_chart(fig, use_container_width=True)


def dimension_bar_chart(scores: dict) -> None:
    """
    Render evaluation dimension bar chart.

    Args:
        scores: Dict of dimension name to score.
    """
    filtered = {k: v for k, v in scores.items() if k != "weighted_final"}
    if not filtered:
        return

    labels = [k.replace("_", " ").title() for k in filtered.keys()]
    values = list(filtered.values())
    colors = [
        "#2ecc71" if v >= 75 else "#f39c12" if v >= 50 else "#e74c3c"
        for v in values
    ]

    fig = go.Figure(go.Bar(
        x=labels,
        y=values,
        marker_color=colors,
        text=[f"{v:.1f}" for v in values],
        textposition="outside",
    ))
    fig.update_layout(
        title="Evaluation Dimension Scores",
        yaxis=dict(range=[0, 110]),
        height=350,
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
    )
    fig.update_yaxes(showgrid=True, gridcolor="#ecf0f1")
    st.plotly_chart(fig, use_container_width=True)


def skill_confidence_bar(competency_scores: list[dict]) -> None:
    """
    Render horizontal bar chart of competency confidence scores.

    Args:
        competency_scores: List of score dicts with competency_id and confidence.
    """
    if not competency_scores:
        st.info("No competency scores yet.")
        return

    labels = [
        s.get("competency_id", "")
        .replace("comp_se_", "").replace("comp_da_", "").replace("comp_ai_", "")
        .replace("_", " ").title()
        for s in competency_scores
    ]
    values = [s.get("confidence", 0) for s in competency_scores]
    colors = [
        "#2ecc71" if v >= 70 else "#f39c12" if v >= 40 else "#e74c3c"
        for v in values
    ]

    fig = go.Figure(go.Bar(
        x=values,
        y=labels,
        orientation="h",
        marker_color=colors,
        text=[f"{v:.1f}%" for v in values],
        textposition="outside",
    ))
    fig.update_layout(
        title="Competency Confidence Scores",
        xaxis=dict(range=[0, 120], title="Confidence %"),
        height=max(300, len(labels) * 35),
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
    )
    fig.add_vline(x=70, line_dash="dash", line_color="#2ecc71",
                  annotation_text="Target 70%")
    st.plotly_chart(fig, use_container_width=True)


def session_overview_metrics(overview: dict) -> None:
    """
    Display overview metrics in a column layout.

    Args:
        overview: Dict with total_sessions, avg_score, best_score, improvement.
    """
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Sessions Completed", overview.get("total_sessions", 0))
    with col2:
        avg = overview.get("avg_score", 0)
        st.metric("Average Score", f"{avg:.1f}")
    with col3:
        best = overview.get("best_score", 0)
        st.metric("Best Score", f"{best:.1f}")
    with col4:
        improvement = overview.get("improvement", 0)
        st.metric(
            "Improvement",
            f"{abs(improvement):.1f}",
            delta=f"{improvement:+.1f}" if improvement != 0 else None,
        )

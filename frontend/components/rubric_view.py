"""
Rubric display component.

Shows evaluation rubric criteria and scores
to make evaluation transparent and auditable.
"""

from __future__ import annotations

import streamlit as st


def show_explanation_card(explanation: dict) -> None:
    """
    Display explainability card for one evaluation.

    Shows why each score was assigned.

    Args:
        explanation: Dict with reason strings per dimension.
    """
    st.markdown("### Score Explanations")

    dimensions = [
        ("Semantic Relevance", "semantic_reason"),
        ("Concept Coverage", "concept_reason"),
        ("Communication", "communication_reason"),
        ("Evidence & Examples", "evidence_reason"),
        ("Reasoning Depth", "reasoning_reason"),
    ]

    for label, key in dimensions:
        reason = explanation.get(key, "")
        if reason:
            with st.expander(label, expanded=False):
                st.write(reason)

    summary = explanation.get("overall_summary", "")
    if summary:
        st.markdown("### Overall Summary")
        st.info(summary)


def show_improvement_tip(tip: str) -> None:
    """
    Display the most impactful improvement tip.

    Args:
        tip: Single improvement recommendation string.
    """
    if tip:
        st.markdown("### Most Impactful Improvement")
        st.success(tip)


def show_strengths_weaknesses(
    strengths: list[str],
    weaknesses: list[str],
) -> None:
    """
    Display strengths and weaknesses columns.

    Args:
        strengths: List of strength strings.
        weaknesses: List of weakness strings.
    """
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Strengths**")
        if strengths:
            for s in strengths:
                st.markdown(f"- {s}")
        else:
            st.caption("No significant strengths detected.")

    with col2:
        st.markdown("**Weaknesses**")
        if weaknesses:
            for w in weaknesses:
                st.markdown(f"- {w}")
        else:
            st.caption("No significant weaknesses detected.")

"""
Main Streamlit application entry point.

This file is intentionally minimal during scaffold initialization.
UI pages and components will be implemented in later phases.
"""

import streamlit as st


def main() -> None:
    """Render the initial scaffold landing page."""
    st.set_page_config(
        page_title="AI Interview Assistant",
        page_icon="🎯",
        layout="wide",
    )

    st.title("AI-Powered Interview Preparation Assistant")
    st.info("Project scaffold initialized successfully.")
    st.write(
        "Frontend pages, interview workflows, analytics dashboards, "
        "and AI visualizations will be implemented in later steps."
    )


if __name__ == "__main__":
    main()

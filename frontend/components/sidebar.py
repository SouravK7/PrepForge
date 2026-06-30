"""
Sidebar navigation component.
"""

from __future__ import annotations

import streamlit as st
from frontend.session_state import is_authenticated, logout


def render_sidebar() -> str:
    """
    Render the sidebar navigation.

    Returns:
        Selected page name.
    """
    with st.sidebar:
        st.markdown("# PrepForge AI")
        st.markdown("*Interview Preparation*")
        st.markdown("---")

        if is_authenticated():
            username = st.session_state.get("username", "User")
            role = st.session_state.get("target_role", "")
            st.markdown(f"**{username}**")
            if role:
                st.caption(f"Target: {role}")
            st.markdown("---")

            pages = {
                "Home": "home",
                "Start Interview": "interview",
                "Dashboard": "dashboard",
                "Skill Map": "skill_map",
                "Recommendations": "recommendations",
            }

            selected = st.session_state.get("current_page", "home")

            for label, page in pages.items():
                is_selected = selected == page
                if st.button(
                    label,
                    use_container_width=True,
                    type="primary" if is_selected else "secondary",
                    key=f"nav_{page}",
                ):
                    st.session_state.current_page = page
                    st.rerun()

            st.markdown("---")
            if st.button("Logout", use_container_width=True, key="nav_logout"):
                logout()
                st.rerun()

        else:
            if st.button(
                "Login / Register",
                use_container_width=True,
                type="primary",
                key="nav_auth",
            ):
                st.session_state.current_page = "auth"
                st.rerun()

        st.markdown("---")
        st.caption("PrepForge AI v1.0")

    return st.session_state.get("current_page", "home")

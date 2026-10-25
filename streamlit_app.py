"""
Aegis Foundation - Application Entrypoint
Implements Streamlit Dynamic Navigation (st.navigation + st.Page) for statutory role isolation.
"""

import sys
import os

# Ensure local packages are resolvable
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from core.db import seed_foundation
from views.public import render_landing_and_login, logout
from views.college import college_page
from views.officer import officer_page, render_audit_trail_view

# Streamlit Page Configuration
st.set_page_config(
    page_title="Aegis - AICTE Regulatory Validation",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize and seed database if not already done
seed_foundation()

# Initialize session state
if "user" not in st.session_state:
    st.session_state["user"] = None

user = st.session_state["user"]

# Build Dynamic Navigation based on authenticated role
if user is None:
    # Public & Unauthenticated visitors: ONLY public gateway is mounted
    public_page = st.Page(render_landing_and_login, title="Aegis Gateway", icon="🏛️", default=True)
    nav = st.navigation([public_page])

elif user.get("role") == "COLLEGE_REPRESENTATIVE":
    # College Representative: ONLY College views are mounted
    college_portal = st.Page(college_page, title="Institutional Portal", icon="🎓", default=True)
    logout_page = st.Page(logout, title="Sign Out", icon="🚪")
    nav = st.navigation({
        "Institution Workspace": [college_portal],
        "Session": [logout_page]
    })

elif user.get("role") == "AICTE_SCRUTINY_OFFICER":
    # AICTE Scrutiny Officer: ONLY Officer views and Audit Log are mounted
    officer_portal = st.Page(officer_page, title="Scrutiny Queue", icon="⚖️", default=True)
    audit_page = st.Page(render_audit_trail_view, title="Statutory Audit Log", icon="📜")
    logout_page = st.Page(logout, title="Sign Out", icon="🚪")
    nav = st.navigation({
        "AICTE Scrutiny Panel": [officer_portal, audit_page],
        "Session": [logout_page]
    })

else:
    # Unknown role fallback
    st.error("Unknown user role. Session terminated.")
    st.session_state.clear()
    st.rerun()

# Run active routed page
nav.run()

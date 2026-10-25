"""
Aegis Foundation - Screen A: Public Landing Page
Directly implements Wireframe 1 (AICTE Portal):
- Top header with AICTE Portal badge & profile indicator
- Background visual relating to higher education governance & academic quality
- Concise explanation of statutory scrutiny purpose
- Two prominent, equally clear entry points: COLLEGE LOGIN and SCRUTINY OFFICER LOGIN
"""

import streamlit as st
from core.auth import AuthService
from views.theme import render_header, render_footer, apply_custom_css


def render_landing_and_login():
    """Renders Screen A matching Wireframe 1."""
    apply_custom_css()

    # Top Header matching Wireframe 1 (AICTE Portal badge on left, circle icon on right)
    render_header(
        portal_title="AICTE Portal",
        badge_label="National Regulatory Gateway",
        subtitle="Council for Technical Education — Statutory Scrutiny Platform"
    )

    # Background Banner Visual (Higher Education / Academic Governance Architecture)
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.96) 0%, rgba(30, 58, 138, 0.92) 100%),
                    repeating-linear-gradient(45deg, rgba(255,255,255,0.02) 0px, rgba(255,255,255,0.02) 2px, transparent 2px, transparent 8px);
        border: 1px solid #1E293B;
        border-radius: 10px;
        padding: 28px 32px;
        color: #FFFFFF;
        margin-bottom: 24px;
        box-shadow: 0 4px 12px rgba(15,23,42,0.08);
    ">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
            <span style="font-size: 1.1rem;">🏛️</span>
            <span style="font-size: 0.78rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: #93C5FD;">
                Statutory Regulatory Scrutiny & Document Verification
            </span>
        </div>
        <h2 style="color: #FFFFFF; font-size: 1.75rem; margin: 0 0 10px 0; font-weight: 700; letter-spacing: -0.01em;">
            Aegis Institutional Compliance System
        </h2>
        <p style="color: #E2E8F0; font-size: 0.95rem; line-height: 1.55; max-width: 900px; margin: 0;">
            A national decision-support platform assisting statutory scrutiny committees and accredited technical colleges in verifying approval dossiers, inspecting document authenticity, cross-checking structural integrity, and managing regulatory clarification workflows.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize public view state
    if "public_login_role" not in st.session_state:
        st.session_state["public_login_role"] = "college"

    current_role = st.session_state["public_login_role"]

    # Two prominent entry point cards matching Wireframe 1
    col_college_card, col_officer_card = st.columns(2)

    with col_college_card:
        is_active = current_role == "college"
        active_border = "border: 2px solid #2563EB; background: #EFF6FF;" if is_active else "border: 1px solid #E2E8F0; background: #FFFFFF;"
        st.markdown(f"""
        <div style="{active_border} border-radius: 10px; padding: 20px; min-height: 140px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 1.6rem;">🎓</span>
                <span style="font-size: 0.72rem; font-weight: 700; color: #1E40AF; background: #DBEAFE; padding: 3px 8px; border-radius: 4px;">
                    INSTITUTIONAL ACCESS
                </span>
            </div>
            <div style="font-size: 1.2rem; font-weight: 700; color: #0F172A; text-transform: uppercase; margin-bottom: 4px;">
                COLLEGE LOGIN
            </div>
            <p style="font-size: 0.84rem; color: #475569; margin: 0;">
                Accredited technical institutions, university departments, principals, and authorized registrars.
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Select College Representative Login", key="btn_select_college", use_container_width=True, type="primary" if is_active else "secondary"):
            st.session_state["public_login_role"] = "college"
            st.rerun()

    with col_officer_card:
        is_active = current_role == "officer"
        active_border = "border: 2px solid #2563EB; background: #EFF6FF;" if is_active else "border: 1px solid #E2E8F0; background: #FFFFFF;"
        st.markdown(f"""
        <div style="{active_border} border-radius: 10px; padding: 20px; min-height: 140px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 1.6rem;">⚖️</span>
                <span style="font-size: 0.72rem; font-weight: 700; color: #1E40AF; background: #DBEAFE; padding: 3px 8px; border-radius: 4px;">
                    REGULATORY DIRECTORATE
                </span>
            </div>
            <div style="font-size: 1.2rem; font-weight: 700; color: #0F172A; text-transform: uppercase; margin-bottom: 4px;">
                SCRUTINY OFFICER LOGIN
            </div>
            <p style="font-size: 0.84rem; color: #475569; margin: 0;">
                AICTE evaluation officers, scrutiny committees, and authorized statutory reviewers.
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Select Scrutiny Officer Login", key="btn_select_officer", use_container_width=True, type="primary" if is_active else "secondary"):
            st.session_state["public_login_role"] = "officer"
            st.rerun()

    st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)

    # Render Active Login Portal Form below
    if current_role == "college":
        with st.container(border=True):
            st.markdown("### 🎓 Institutional Representative Authentication")
            st.caption("Sign in with your registered college email and statutory password.")

            with st.form("college_login_form"):
                email = st.text_input("Institutional Email", placeholder="principal@apextech.edu", key="college_email")
                password = st.text_input("Password", type="password", key="college_pw")
                submit = st.form_submit_button("Sign In to College Portal", use_container_width=True, type="primary")

                if submit:
                    user = AuthService.authenticate(email, password, expected_role="COLLEGE_REPRESENTATIVE")
                    if user:
                        st.session_state["user"] = user
                        st.session_state["college_view"] = "dashboard"
                        st.success(f"Authenticated as {user['name']}. Redirecting...")
                        st.rerun()
                    else:
                        st.error("Invalid credentials or unauthorized role. Please check your login details.")

            st.caption("Provisioned Dev Credentials: `principal@apextech.edu` (Apex Tech) · `registrar@beacon.ac.in` (Beacon College)")

    else:
        with st.container(border=True):
            st.markdown("### ⚖️ AICTE Scrutiny Directorate Authentication")
            st.caption("Sign in with your official AICTE scrutiny officer credentials.")

            with st.form("officer_login_form"):
                email = st.text_input("Official AICTE Email", placeholder="admin@aicte.gov.in", key="officer_email")
                password = st.text_input("Password", type="password", key="officer_pw")
                submit = st.form_submit_button("Sign In to Scrutiny Panel", use_container_width=True, type="primary")

                if submit:
                    user = AuthService.authenticate(email, password, expected_role="AICTE_SCRUTINY_OFFICER")
                    if user:
                        st.session_state["user"] = user
                        st.session_state["officer_view"] = "dashboard"
                        st.success(f"Authenticated as {user['name']}. Redirecting...")
                        st.rerun()
                    else:
                        st.error("Invalid credentials or unauthorized officer role.")

            st.caption("Provisioned Dev Credentials: `admin@aicte.gov.in` (AICTE Directorate)")

    render_footer()


def logout():
    """Clears session and redirects to public gateway."""
    st.session_state.clear()
    st.rerun()

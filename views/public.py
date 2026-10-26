"""
Aegis Foundation - Screen A: Public Landing Page & Dual Authentication Gateway
Directly implements Wireframe 1 (AICTE Portal) with modern governance aesthetics:
- Top government header with AICTE Portal badge & profile indicator
- Explanatory regulatory workflow banner (APH 2026-27 compliance mandate)
- 3-Phase scrutiny roadmap (Preparation -> Deterministic Pre-Check -> Officer Adjudication)
- Quick-fill demo credentials for seamless evaluator testing
- Two prominent entry points: COLLEGE LOGIN and SCRUTINY OFFICER LOGIN
"""

import streamlit as st
from core.auth import AuthService
from views.theme import render_header, render_footer, apply_custom_css
from core.scenarios import load_scenario_deficient, load_scenario_clean, load_scenario_clarification


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
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.96) 0%, rgba(30, 58, 138, 0.94) 100%),
                    repeating-linear-gradient(45deg, rgba(255,255,255,0.02) 0px, rgba(255,255,255,0.02) 2px, transparent 2px, transparent 8px);
        border: 1px solid #1E293B;
        border-radius: 10px;
        padding: 28px 32px;
        color: #FFFFFF;
        margin-bottom: 24px;
        box-shadow: 0 4px 14px rgba(15,23,42,0.10);
    ">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
            <span style="font-size: 1.15rem;">🏛️</span>
            <span style="font-size: 0.76rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: #93C5FD;">
                Statutory Regulatory Scrutiny & Approval Workflow · APH 2026-27
            </span>
        </div>
        <h2 style="color: #FFFFFF; font-size: 1.85rem; margin: 0 0 10px 0; font-weight: 700; letter-spacing: -0.01em;">
            Aegis Institutional Compliance & Scrutiny Platform
        </h2>
        <p style="color: #E2E8F0; font-size: 0.95rem; line-height: 1.6; max-width: 960px; margin: 0 0 18px 0;">
            A national administrative decision-support platform assisting statutory scrutiny committees and accredited technical colleges in verifying approval dossiers, auditing PDF structural integrity, reconciling cross-document land surveys, and executing auditable clarification workflows.
        </p>

        <!-- 3-Phase Scrutiny Architecture Pill Ribbon -->
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; border-top: 1px solid rgba(255,255,255,0.12); padding-top: 14px;">
            <div style="display: flex; align-items: flex-start; gap: 10px;">
                <span style="background: rgba(37,99,235,0.3); border: 1px solid #3B82F6; color: #93C5FD; border-radius: 50%; width: 22px; height: 22px; display: flex; align-items: center; justify-content: center; font-size: 0.72rem; font-weight: 700; flex-shrink: 0;">1</span>
                <div>
                    <div style="font-size: 0.82rem; font-weight: 600; color: #FFFFFF;">Dossier Assembly</div>
                    <div style="font-size: 0.74rem; color: #94A3B8;">Mandatory checklist uploads per category</div>
                </div>
            </div>
            <div style="display: flex; align-items: flex-start; gap: 10px;">
                <span style="background: rgba(16,185,129,0.3); border: 1px solid #10B981; color: #6EE7B7; border-radius: 50%; width: 22px; height: 22px; display: flex; align-items: center; justify-content: center; font-size: 0.72rem; font-weight: 700; flex-shrink: 0;">2</span>
                <div>
                    <div style="font-size: 0.82rem; font-weight: 600; color: #FFFFFF;">Deterministic Rule Pre-Check</div>
                    <div style="font-size: 0.74rem; color: #94A3B8;">7-field explainable findings without fake AI</div>
                </div>
            </div>
            <div style="display: flex; align-items: flex-start; gap: 10px;">
                <span style="background: rgba(245,158,11,0.3); border: 1px solid #F59E0B; color: #FCD34D; border-radius: 50%; width: 22px; height: 22px; display: flex; align-items: center; justify-content: center; font-size: 0.72rem; font-weight: 700; flex-shrink: 0;">3</span>
                <div>
                    <div style="font-size: 0.82rem; font-weight: 600; color: #FFFFFF;">Human Directorate Scrutiny</div>
                    <div style="font-size: 0.74rem; color: #94A3B8;">Official clarification & statutory orders</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Quick Simulation Suite on Landing Page
    with st.expander("🎯 One-Click Live Evaluation Scenarios (For SIH Judges & Evaluators)", expanded=False):
        st.markdown("Instantly initialize and inspect authentic regulatory compliance scenarios without manual form entry:")
        c_p1, c_p2, c_p3 = st.columns(3)
        with c_p1:
            st.markdown("**Scenario 1: Deficient Application**")
            st.caption("Building plan naming anomaly & pending municipal demarcation. Generates 7-field findings.")
            if st.button("▶ Evaluate Deficient Dossier", key="pub_btn_load_sc1", use_container_width=True):
                res = load_scenario_deficient()
                officer = AuthService.authenticate("admin@aicte.gov.in", "AegisAdmin@2026#Secure", expected_role="AICTE_SCRUTINY_OFFICER")
                st.session_state["user"] = officer
                st.session_state["officer_view"] = "review"
                st.session_state["active_app_id"] = res["application_id"]
                st.query_params["view"] = "review"
                st.query_params["app_id"] = res["application_id"]
                st.rerun()

        with c_p2:
            st.markdown("**Scenario 2: Clean Compliance Dossier**")
            st.caption("100% compliant application with all 4 mandatory documents passing all rule checks.")
            if st.button("▶ Evaluate Clean Dossier", key="pub_btn_load_sc2", use_container_width=True):
                res = load_scenario_clean()
                officer = AuthService.authenticate("admin@aicte.gov.in", "AegisAdmin@2026#Secure", expected_role="AICTE_SCRUTINY_OFFICER")
                st.session_state["user"] = officer
                st.session_state["officer_view"] = "review"
                st.session_state["active_app_id"] = res["application_id"]
                st.query_params["view"] = "review"
                st.query_params["app_id"] = res["application_id"]
                st.rerun()

        with c_p3:
            st.markdown("**Scenario 3: Active Clarification Round**")
            st.caption("Application undergoing formal clarification request with pending surveyor proof.")
            if st.button("▶ Evaluate Clarification Response", key="pub_btn_load_sc3", use_container_width=True):
                res = load_scenario_clarification()
                college = AuthService.authenticate("principal@apextech.edu", "ApexPrincipal@2026#Secure", expected_role="COLLEGE_REPRESENTATIVE")
                st.session_state["user"] = college
                st.session_state["college_view"] = "notifications"
                st.query_params["view"] = "notifications"
                st.rerun()

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
        <div style="{active_border} border-radius: 10px; padding: 22px; min-height: 145px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
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
        <div style="{active_border} border-radius: 10px; padding: 22px; min-height: 145px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
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
                AICTE evaluation officers, scrutiny committees, regional officers, and authorized reviewers.
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

            # Quick-Fill Evaluator Buttons
            st.markdown("<div style='margin-bottom: 10px;'><strong>⚡ Quick Fill Demo Credentials:</strong></div>", unsafe_allow_html=True)
            c_fill1, c_fill2 = st.columns(2)
            with c_fill1:
                if st.button("Use Apex Tech (principal@apextech.edu)", key="btn_fill_apex", use_container_width=True):
                    st.session_state["auto_email"] = "principal@apextech.edu"
                    st.session_state["auto_pw"] = "ApexPrincipal@2026#Secure"
            with c_fill2:
                if st.button("Use Beacon College (registrar@beacon.ac.in)", key="btn_fill_beacon", use_container_width=True):
                    st.session_state["auto_email"] = "registrar@beacon.ac.in"
                    st.session_state["auto_pw"] = "BeaconRegistrar@2026#Secure"

            init_email = st.session_state.pop("auto_email", "")
            init_pw = st.session_state.pop("auto_pw", "")

            with st.form("college_login_form"):
                email = st.text_input("Institutional Email", value=init_email, placeholder="principal@apextech.edu", key="college_email")
                password = st.text_input("Password", value=init_pw, type="password", key="college_pw")
                submit = st.form_submit_button("Sign In to College Portal", use_container_width=True, type="primary")

                if submit:
                    user = AuthService.authenticate(email, password, expected_role="COLLEGE_REPRESENTATIVE")
                    if user:
                        st.session_state["user"] = user
                        st.session_state["college_view"] = "dashboard"
                        st.query_params["view"] = "dashboard"
                        st.success(f"Authenticated as {user['name']}. Redirecting...")
                        st.rerun()
                    else:
                        st.error("Invalid credentials or unauthorized role. Please check your login details.")

            st.caption("Provisioned Dev Credentials: `principal@apextech.edu` (Apex Tech) · `registrar@beacon.ac.in` (Beacon College)")

    else:
        with st.container(border=True):
            st.markdown("### ⚖️ AICTE Scrutiny Directorate Authentication")
            st.caption("Sign in with your official AICTE scrutiny officer credentials.")

            # Quick-Fill Evaluator Button
            st.markdown("<div style='margin-bottom: 10px;'><strong>⚡ Quick Fill Demo Credentials:</strong></div>", unsafe_allow_html=True)
            if st.button("Use AICTE Officer (admin@aicte.gov.in)", key="btn_fill_officer", use_container_width=True):
                st.session_state["auto_officer_email"] = "admin@aicte.gov.in"
                st.session_state["auto_officer_pw"] = "AegisAdmin@2026#Secure"

            init_off_email = st.session_state.pop("auto_officer_email", "")
            init_off_pw = st.session_state.pop("auto_officer_pw", "")

            with st.form("officer_login_form"):
                email = st.text_input("Official AICTE Email", value=init_off_email, placeholder="admin@aicte.gov.in", key="officer_email")
                password = st.text_input("Password", value=init_off_pw, type="password", key="officer_pw")
                submit = st.form_submit_button("Sign In to Scrutiny Panel", use_container_width=True, type="primary")

                if submit:
                    user = AuthService.authenticate(email, password, expected_role="AICTE_SCRUTINY_OFFICER")
                    if user:
                        st.session_state["user"] = user
                        st.session_state["officer_view"] = "dashboard"
                        st.query_params["view"] = "dashboard"
                        st.success(f"Authenticated as {user['name']}. Redirecting...")
                        st.rerun()
                    else:
                        st.error("Invalid credentials or unauthorized officer role.")

            st.caption("Provisioned Dev Credentials: `admin@aicte.gov.in` (AICTE Directorate)")

    render_footer()


def logout():
    """Clears session and redirects to public gateway."""
    st.session_state.clear()
    st.query_params.clear()
    st.rerun()

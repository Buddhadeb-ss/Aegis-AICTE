"""
Aegis Foundation - Scrutiny Officer Views
Directly implements Wireframes 2, 4, and 5:
- Screen C (Wireframe 2): Scrutiny Officer Dashboard with APPLICATIONS and LOGS cards.
- Screen D (Wireframe 4): Scrutiny Officer Application Queue with two-panel layout (list on left, selected details + AI approval status on right).
- Screen E (Wireframe 5): Individual Application Review with application header, college name, context/why, AI check (PASS/FAIL/SUS), attached documents cards, and APPROVE/REJECT decision controls.
"""

import os
import json
import streamlit as st
from core.auth import ApplicationService
from core.audit import get_audit_events
from views.theme import render_header, render_footer, apply_custom_css
from views.validation_view import (
    render_application_verdict,
    render_decision_oriented_results,
    render_validation_summary_badge
)


def render_officer_dashboard(user, apps):
    """Screen C (Wireframe 2) - Scrutiny Officer Portal with 2 prominent cards."""
    pending_apps = [a for a in apps if a.get("status") in ["SUBMITTED", "UNDER_SCRUTINY"]]
    total_events = len(get_audit_events(limit=500))

    banner_html = (
        '<div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 18px 24px; margin-bottom: 24px;">'
        '<div style="display: flex; justify-content: space-between; align-items: center;">'
        '<div>'
        '<h2 style="font-size: 1.35rem; color: #0F172A; margin: 0 0 4px 0; font-weight: 700;">AICTE Central Scrutiny Directorate</h2>'
        f'<div style="font-size: 0.85rem; color: #64748B;">Jurisdiction: <strong>National Technical Approval Scrutiny</strong> · Authorized Scrutiny Officer: <strong>{user.get("name")}</strong> ({user.get("email")})</div>'
        '</div>'
        '<div><span style="font-size: 0.75rem; text-transform: uppercase; font-weight: 700; color: #1E40AF; background: #DBEAFE; padding: 4px 10px; border-radius: 4px;">Approval Process Cycle 2026-27</span></div>'
        '</div></div>'
    )
    st.markdown(banner_html, unsafe_allow_html=True)

    # Three prominent cards (APPLICATIONS, ADD APPLICATION, and LOGS)
    col_apps, col_new, col_logs = st.columns(3)

    with col_apps:
        st.markdown(f"""
        <div class="wf-card">
            <div>
                <div class="wf-card-icon">📂</div>
                <div class="wf-card-title">APPLICATIONS</div>
                <p class="wf-card-desc">
                    Central scrutiny queue across all technical institutions. Inspect submitted approval dossiers and verify compliance.
                </p>
            </div>
            <div class="wf-card-meta">
                <span>Active Scrutiny Queue</span>
                <span style="color: #2563EB; font-weight: 700;">{len(pending_apps)} Pending / {len(apps)} Total</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Scrutiny Queue →", key="card_btn_apps", use_container_width=True, type="primary"):
            st.session_state["officer_view"] = "queue"
            st.rerun()

    with col_new:
        st.markdown(f"""
        <div class="wf-card">
            <div>
                <div class="wf-card-icon">➕</div>
                <div class="wf-card-title">ADD APPLICATION</div>
                <p class="wf-card-desc">
                    Register a new institutional dossier directly for scrutiny on behalf of an applicant college or university.
                </p>
            </div>
            <div class="wf-card-meta">
                <span>Direct Officer Intake</span>
                <span style="color: #166534; font-weight: 700;">Instant Submission</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("➕ Register New Application →", key="card_btn_new_app", use_container_width=True):
            st.session_state["officer_view"] = "create_app"
            st.rerun()

    with col_logs:
        st.markdown(f"""
        <div class="wf-card">
            <div>
                <div class="wf-card-icon">📜</div>
                <div class="wf-card-title">LOGS</div>
                <p class="wf-card-desc">
                    Statutory immutable audit trail. Comprehensive chronological record of all actions, uploads, and regulatory orders.
                </p>
            </div>
            <div class="wf-card-meta">
                <span>Audit Trail Records</span>
                <span style="color: #2563EB; font-weight: 700;">{total_events} Recorded Events</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Inspect Audit Log →", key="card_btn_logs", use_container_width=True):
            st.session_state["officer_view"] = "logs"
            st.rerun()

    # Recent submissions summary
    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
    st.markdown("### 📋 Recent Scrutiny Submissions")

    if not apps:
        st.info("No applications submitted in the system.")
    else:
        for a in apps[:4]:
            with st.container(border=True):
                ca, cb, cc, cd = st.columns([2.5, 1.2, 1.2, 1.2])
                with ca:
                    st.markdown(f"**{a['institution_name']}** (`{a['institution_code']}`)")
                    st.caption(f"App No: **{a['application_number']}** · Cat: {a['category']} · Docs: {a['doc_count']}")
                with cb:
                    st.markdown(f"Status: **{a['status']}**")
                with cc:
                    st.caption(f"Created: {a['created_at'][:10]}")
                with cd:
                    if st.button("Inspect Queue →", key=f"rec_dash_{a['id']}", use_container_width=True):
                        st.session_state["officer_selected_app_id"] = a["id"]
                        st.session_state["officer_view"] = "queue"
                        st.rerun()


def render_officer_queue_twopanel(user, apps):
    """Screen D (Wireframe 4) - Two-panel queue layout."""
    c_back, c_title, c_add = st.columns([1, 3.2, 1.4])
    with c_back:
        if st.button("← Back to Portal", key="btn_queue_back", use_container_width=True):
            st.session_state["officer_view"] = "dashboard"
            st.rerun()
    with c_title:
        st.markdown("## ⚖️ APPLICATIONS (Scrutiny Queue)")
    with c_add:
        if st.button("➕ Add Application", key="btn_queue_add_app", type="primary", use_container_width=True):
            st.session_state["officer_view"] = "create_app"
            st.rerun()

    # Filter and Sort Bar (Wireframe 4: SORT BY)
    col_sort, col_filter, col_search = st.columns([1.2, 1.2, 1.6])
    with col_sort:
        sort_by = st.selectbox(
            "SORT BY",
            ["Submission Date (Newest first)", "Submission Date (Oldest first)", "Institution Name (A-Z)", "Status"],
            key="queue_sort_by"
        )
    with col_filter:
        status_filter = st.selectbox(
            "FILTER BY STATUS",
            ["ALL", "SUBMITTED", "UNDER_SCRUTINY", "CLARIFICATION_REQUESTED", "APPROVED", "REJECTED"],
            key="queue_status_filter"
        )
    with col_search:
        search_query = st.text_input("Search Institution / Application No.", placeholder="Apex Tech, AICTE-2026...", key="queue_search")

    # Filter and sort apps
    filtered = list(apps)
    if status_filter != "ALL":
        filtered = [a for a in filtered if a["status"] == status_filter]
    if search_query.strip():
        q = search_query.lower()
        filtered = [a for a in filtered if q in a["institution_name"].lower() or q in a["application_number"].lower() or q in a.get("institution_code", "").lower()]

    if "Newest" in sort_by:
        filtered.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    elif "Oldest" in sort_by:
        filtered.sort(key=lambda x: x.get("created_at", ""))
    elif "Institution" in sort_by:
        filtered.sort(key=lambda x: x.get("institution_name", "").lower())
    elif "Status" in sort_by:
        filtered.sort(key=lambda x: x.get("status", ""))

    if not filtered:
        st.info("No applications match the selected filter criteria.")
        return

    # Default selected application
    selected_id = st.session_state.get("officer_selected_app_id")
    if not selected_id or not any(a["id"] == selected_id for a in filtered):
        selected_id = filtered[0]["id"]
        st.session_state["officer_selected_app_id"] = selected_id

    st.markdown("---")

    # Wireframe 4: Two-Panel Layout (Left: Application List, Right: Corresponding Details & AI Assessment)
    col_list, col_details = st.columns([1.1, 1.4])

    # LEFT PANEL: Application List
    with col_list:
        st.markdown(f"### Queue List ({len(filtered)})")
        for a in filtered:
            is_active = a["id"] == selected_id
            active_class = "queue-item-active" if is_active else ""
            status = a["status"]
            badge_class = f"badge badge-{status.lower()}"

            st.markdown(f"""
            <div class="queue-item {active_class}">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 4px;">
                    <div style="font-weight: 700; color: #0F172A; font-size: 0.95rem;">{a['application_number']}</div>
                    <span class="{badge_class}">{status}</span>
                </div>
                <div style="font-size: 0.88rem; color: #1E3A8A; font-weight: 600; margin-bottom: 2px;">
                    {a['institution_name']}
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.76rem; color: #64748B;">
                    <span>Code: {a['institution_code']}</span>
                    <span>Docs: {a['doc_count']} · {a['created_at'][:10]}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if not is_active:
                if st.button(f"Select Application →", key=f"sel_{a['id']}", use_container_width=True):
                    st.session_state["officer_selected_app_id"] = a["id"]
                    st.rerun()

    # RIGHT PANEL: Selected Application Details & AI Approval Status
    with col_details:
        st.markdown("### Selected Application Details")
        try:
            packet = ApplicationService.get_application_details(selected_id, user)
            sel_app = packet["application"]
            sel_docs = packet["documents"]

            with st.container(border=True):
                st.markdown(f"#### 🏛️ {sel_app['institution_name']}")
                st.caption(f"Application No: **`{sel_app['application_number']}`** · Permanent Code: `{sel_app['institution_code']}` · State: `{sel_app.get('state', 'N/A')}`")

                # Status pill
                s = sel_app["status"]
                b_class = f"badge badge-{s.lower()}"
                st.markdown(f"Current Status: <span class='{b_class}'>{s}</span> · Category: **{sel_app['category'].replace('_', ' ')}** · Academic Year: **{sel_app['academic_year']}**", unsafe_allow_html=True)

                if sel_app.get("notes"):
                    st.markdown(f"**Institutional Remarks:** {sel_app['notes']}")

                st.markdown("---")

                # Wireframe 4 requirement: "SHOW THE CORRESPONDING DETAILS OF THE APPLICATION AND ALSO IF THE AI APPROVES THE DOCUMENTS OR OFFICER CHECK IS REQUIRED"
                st.markdown("#### 📋 Document Verification Summary")

                val_sum = packet.get("validation_summary", {})
                render_application_verdict(val_sum, mandatory_count=len(packet.get("mandatory_checklist", [])))

                st.markdown("---")
                st.markdown(f"#### 📄 Submitted Documents ({len(sel_docs)} uploaded)")

                if sel_docs:
                    app_assessments = val_sum.get("app_assessments") or {}
                    compact_docs = app_assessments.get("compact_documents", [])
                    c_status_map = {cd["filename"]: cd.get("simple_status", "Clear") for cd in compact_docs}

                    for d in sel_docs:
                        col_d1, col_d2 = st.columns([2, 1])
                        with col_d1:
                            st.write(f"📄 **{d['document_type'].replace('_', ' ')}** (`{d['filename']}`)")
                        with col_d2:
                            s_st = c_status_map.get(d["filename"], "Clear")
                            if s_st == "Issue":
                                st.markdown('<span class="badge badge-issue">Issue</span>', unsafe_allow_html=True)
                            elif s_st == "Review":
                                st.markdown('<span class="badge badge-review">Review</span>', unsafe_allow_html=True)
                            elif s_st == "Incomplete":
                                st.markdown('<span class="badge badge-incomplete">Incomplete</span>', unsafe_allow_html=True)
                            else:
                                st.markdown('<span class="badge badge-clear">Clear</span>', unsafe_allow_html=True)
                else:
                    st.info("No documents uploaded yet.")

                st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)

                # Direct Scrutiny Determination Controls (Approve / Reject)
                st.markdown("#### ⚖️ Scrutiny Determination")
                current_status = sel_app["status"]

                if current_status == "APPROVED":
                    st.success("✅ **APPLICATION APPROVED** · Official Scrutiny Order Confirmed.")
                    if sel_app.get("notes"):
                        st.caption(f"Remarks: {sel_app['notes']}")
                    if st.button("Re-open Scrutiny / Change Determination", key=f"reopen_{sel_app['id']}", use_container_width=True):
                        ApplicationService.record_decision(selected_id, user, "UNDER_SCRUTINY", "Reopened for re-evaluation")
                        st.rerun()
                elif current_status == "REJECTED":
                    st.error("❌ **APPLICATION REJECTED** · Application Deficient / Disapproved.")
                    if sel_app.get("notes"):
                        st.caption(f"Remarks: {sel_app['notes']}")
                    if st.button("Re-open Scrutiny / Change Determination", key=f"reopen_{sel_app['id']}", use_container_width=True):
                        ApplicationService.record_decision(selected_id, user, "UNDER_SCRUTINY", "Reopened for re-evaluation")
                        st.rerun()
                else:
                    dec_notes = st.text_input(
                        "Scrutiny Remarks / Rejection Justification",
                        value="",
                        placeholder="Required for rejection, optional for approval...",
                        key=f"dec_notes_{sel_app['id']}"
                    )
                    c_appr, c_rej = st.columns(2)
                    with c_appr:
                        if st.button("✅ APPROVE", key=f"btn_appr_{sel_app['id']}", type="primary", use_container_width=True):
                            appr_note = dec_notes.strip() or "Compliance verified per APH 2026-27 statutory norms."
                            ApplicationService.record_decision(selected_id, user, "APPROVED", appr_note)
                            st.success(f"Application {sel_app['application_number']} APPROVED!")
                            st.rerun()
                    with c_rej:
                        if st.button("❌ REJECT", key=f"btn_rej_{sel_app['id']}", use_container_width=True):
                            if not dec_notes.strip():
                                st.error("Please enter a specific reason or statutory justification before rejecting.")
                            else:
                                ApplicationService.record_decision(selected_id, user, "REJECTED", dec_notes.strip())
                                st.error(f"Application {sel_app['application_number']} REJECTED.")
                                st.rerun()

                st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
                # Navigation button to Screen E (Individual Review)
                if st.button("Open Full Detailed Review →", key="btn_open_indiv_review", use_container_width=True):
                    st.session_state["officer_active_app_id"] = selected_id
                    st.session_state["officer_view"] = "review"
                    st.rerun()

        except KeyError:
            st.error("Selected application not found.")


def render_officer_create_application(user):
    """Allows a scrutiny officer to register an institutional application directly."""
    c_back, c_title = st.columns([1, 4])
    with c_back:
        if st.button("← Back to Queue", key="btn_create_app_back", use_container_width=True):
            st.session_state["officer_view"] = "queue"
            st.rerun()
    with c_title:
        st.markdown("## ➕ Register New Institutional Application")
        st.caption("Initiate a statutory approval application dossier directly into the scrutiny queue.")

    institutions = ApplicationService.get_all_institutions()
    if not institutions:
        st.error("No institutions registered in the master records.")
        return

    inst_options = {f"{i['name']} ({i['code']})": i["id"] for i in institutions}

    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            chosen_inst_label = st.selectbox("Sponsoring Institution", list(inst_options.keys()), key="officer_new_inst")
            chosen_inst_id = inst_options[chosen_inst_label]

            category = st.selectbox(
                "Application Category",
                ["NEW_TECHNICAL_INSTITUTION", "EXTENSION_OF_APPROVAL", "CHANGE_INTAKE"],
                key="officer_new_cat"
            )

        with col2:
            academic_year = st.selectbox(
                "Target Academic Session",
                ["2026-2027", "2027-2028"],
                key="officer_new_year"
            )

            initial_status = st.selectbox(
                "Initial Status",
                ["SUBMITTED", "UNDER_SCRUTINY", "DRAFT"],
                help="SUBMITTED will immediately place this application in the active scrutiny queue.",
                key="officer_new_status"
            )

        notes = st.text_area(
            "Officer Registration Remarks (Optional)",
            value="Application dossier registered via Central Scrutiny Officer console.",
            key="officer_new_notes"
        )

        col_sub, _ = st.columns([1.5, 3])
        with col_sub:
            if st.button("🚀 Register Application for Scrutiny", type="primary", use_container_width=True, key="btn_officer_submit_app"):
                try:
                    new_app = ApplicationService.create_application(
                        institution_id=chosen_inst_id,
                        category=category,
                        academic_year=academic_year,
                        actor=user["email"],
                        notes=notes,
                        initial_status=initial_status
                    )
                    st.success(f"Application `{new_app['application_number']}` created successfully!")
                    st.session_state["officer_selected_app_id"] = new_app["id"]
                    st.session_state["officer_view"] = "queue"
                    st.rerun()
                except Exception as e:
                    st.error(f"Error creating application: {str(e)}")


def render_individual_review(user):
    """Screen E (Wireframe 5) - Individual Application Review."""
    app_id = st.session_state.get("officer_active_app_id")

    c_back, c_title = st.columns([1, 4])
    with c_back:
        if st.button("← Back to Application Queue", key="btn_review_back", use_container_width=True):
            st.session_state["officer_view"] = "queue"
            st.rerun()

    if not app_id:
        st.info("No application selected for review.")
        return

    try:
        packet = ApplicationService.get_application_details(app_id, user)
    except KeyError:
        st.error(f"Application record '{app_id}' not found.")
        st.session_state["officer_view"] = "queue"
        st.rerun()
        return

    app = packet["application"]
    docs = packet["documents"]
    clarifs = packet["clarifications"]

    with c_title:
        # Wireframe 5 Header: APPLICATION identifier & COLLEGE NAME
        st.markdown(f"## APPLICATION: `{app['application_number']}`")

    st.markdown(f"""
    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px 20px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 1.25rem; font-weight: 700; color: #0F172A;">
                    COLLEGE NAME: {app['institution_name']}
                </div>
                <div style="font-size: 0.85rem; color: #64748B;">
                    Permanent Code: <code>{app['institution_code']}</code> · State: <strong>{app.get('state', 'N/A')}</strong> · City: <strong>{app.get('city', 'N/A')}</strong>
                </div>
            </div>
            <div>
                <span class="badge badge-{app['status'].lower()}">{app['status']}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Wireframe 5: Main 2-Column Split (Left: DETAILS & CONTEXT, Right: AI CHECK PASS/FAIL/SUS)
    col_context, col_aicheck = st.columns([1.3, 1])

    with col_context:
        with st.container(border=True):
            st.markdown("### 📋 DETAILS OF THE APPLICATION AND CONTEXT AND WHY")
            st.write(f"**Application Category:** `{app['category'].replace('_', ' ')}`")
            st.write(f"**Academic Session:** `{app['academic_year']}`")
            st.write(f"**Regulatory Framework:** Approval Process Handbook (APH 2026-27), AICTE Act 1987")
            st.write(f"**Submission Date:** `{app['created_at']}`")
            st.write(f"**Institutional Representative:** `{app['institution_name']}` Representative")

            if app.get("notes"):
                st.markdown(f"**Institutional Remarks / Justification:**")
                st.info(app["notes"])
            else:
                st.caption("No custom remarks submitted by the institutional representative.")

    with col_aicheck:
        with st.container(border=True):
            st.markdown("### 📋 Document Verification")
            render_application_verdict(packet.get("validation_summary", {}), mandatory_count=len(packet.get("mandatory_checklist", [])))

    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)

    # Wireframe 5: ATTACHED DOCUMENTS & Decision-Oriented Document Validation Results
    st.markdown("### 📄 ATTACHED DOCUMENTS & VALIDATION RESULTS")
    render_decision_oriented_results(packet, user)

    st.markdown("---")

    # Wireframe 5: APPROVE / REJECT Controls & Clarification Workflow
    st.markdown("### ⚖️ REGULATORY ACTION: APPROVE / REJECT / CLARIFY")

    tab_decision, tab_clarif = st.tabs(["⚖️ Record Statutory Scrutiny Outcome (Approve/Reject)", "💬 Request Regulatory Clarification"])

    # Tab 1: APPROVE / REJECT
    with tab_decision:
        current_status = app["status"]
        if current_status == "APPROVED":
            st.success("✅ **APPLICATION APPROVED** · Official Scrutiny Order Confirmed.")
            if app.get("notes"):
                st.caption(f"Official Remarks: {app['notes']}")
            if st.button("Re-open Scrutiny / Change Determination", key="reopen_review_btn", use_container_width=True):
                ApplicationService.record_decision(app_id, user, "UNDER_SCRUTINY", "Reopened for re-evaluation")
                st.rerun()
        elif current_status == "REJECTED":
            st.error("❌ **APPLICATION REJECTED** · Application Deficient / Disapproved.")
            if app.get("notes"):
                st.caption(f"Official Remarks: {app['notes']}")
            if st.button("Re-open Scrutiny / Change Determination", key="reopen_review_btn", use_container_width=True):
                ApplicationService.record_decision(app_id, user, "UNDER_SCRUTINY", "Reopened for re-evaluation")
                st.rerun()
        else:
            st.markdown("Record official scrutiny determination for this institutional dossier:")
            order_notes = st.text_input(
                "Official Scrutiny Remarks / Rejection Justification",
                value="",
                placeholder="Required for rejection, optional for approval...",
                key="order_notes_review"
            )
            col_d_appr, col_d_rej = st.columns(2)
            with col_d_appr:
                if st.button("✅ APPROVE APPLICATION", key="btn_review_approve", type="primary", use_container_width=True):
                    appr_notes = order_notes.strip() or "Compliance verified per APH 2026-27 statutory norms."
                    ApplicationService.record_decision(app_id, user, "APPROVED", appr_notes)
                    st.success(f"Application {app['application_number']} APPROVED!")
                    st.rerun()
            with col_d_rej:
                if st.button("❌ REJECT APPLICATION", key="btn_review_reject", use_container_width=True):
                    if not order_notes.strip():
                        st.error("Please enter a specific reason or statutory justification for rejecting the application.")
                    else:
                        ApplicationService.record_decision(app_id, user, "REJECTED", order_notes.strip())
                        st.error(f"Application {app['application_number']} REJECTED.")
                        st.rerun()

    # Tab 2: Clarification Workflow
    with tab_clarif:
        st.markdown("#### Clarification History & Action Items")
        if clarifs:
            for cl in clarifs:
                with st.container(border=True):
                    st.markdown(f"**Clarification ID:** `{cl['id']}` · Status: **{cl['status']}** · Issued: {cl['created_at'][:19]}")
                    st.info(f"**Officer Question:** {cl['question_text']}")
                    if cl["status"] == "RESOLVED":
                        st.success(f"**College Response:** {cl['response_text']}")
                        if cl.get("response_documents"):
                            st.write(f"**Evidence Attached:** {cl['response_documents']}")
                    else:
                        st.warning("Awaiting response from institutional applicant.")
        else:
            st.info("No clarifications have been requested for this application.")

        if app["status"] not in ["APPROVED", "REJECTED"]:
            st.markdown("---")
            st.markdown("#### Issue Regulatory Clarification Request")
            with st.form("request_clarif_wireframe5"):
                q_text = st.text_area("Specify the deficiency or required clarification")
                req_doc_desc = st.text_input("Requested Supporting Evidence / Documents (Optional)")
                send_clr = st.form_submit_button("Issue Statutory Clarification Request", use_container_width=True)

                if send_clr:
                    if not q_text.strip():
                        st.error("Please enter the specific clarification question.")
                    else:
                        try:
                            ApplicationService.request_clarification(app_id, user, q_text, req_doc_desc)
                            st.success("Clarification request issued to college representative!")
                            st.rerun()
                        except ValueError as ve:
                            st.error(str(ve))


def render_audit_trail_view():
    """Audit Trail View (Accessible from Card 2: LOGS or Navigation)."""
    user = st.session_state.get("user")
    render_header(
        portal_title="Scrutiny Officer Portal",
        badge_label="Statutory Audit Trail",
        subtitle="Chronological Immutable Compliance Record",
        user=user
    )

    c_back, c_title = st.columns([1, 4])
    with c_back:
        if st.button("← Back to Officer Portal", key="btn_audit_back", use_container_width=True):
            st.session_state["officer_view"] = "dashboard"
            st.rerun()

    with c_title:
        st.markdown("## 📜 Statutory Audit Log & Regulatory Traceability")

    st.caption("Immutable chronological record of all authentication, submission, and review events.")

    events = get_audit_events(limit=150)
    if not events:
        st.info("No audit events recorded.")
        render_footer()
        return

    for ev in events:
        with st.container(border=True):
            col1, col2, col3 = st.columns([1.5, 2, 1])
            with col1:
                st.markdown(f"**{ev['event_type']}**")
                st.caption(f"Entity: `{ev['entity_type']}:{ev['entity_id']}`")
            with col2:
                details = ev.get("details_json")
                if details:
                    st.code(details, language="json")
            with col3:
                st.caption(f"Actor: **{ev['actor']}**")
                st.caption(f"{ev['created_at'][:19]}")

    render_footer()


def officer_page():
    """Main Scrutiny Officer Portal Entrypoint implementing Wireframes 2, 4, and 5."""
    user = st.session_state.get("user")
    if not user:
        st.error("Session terminated.")
        return

    # Top Header matching Wireframes
    render_header(
        portal_title="Scrutiny Officer Portal",
        badge_label="Regulatory Directorate",
        subtitle="AICTE Central Scrutiny Directorate · National Jurisdiction",
        user=user
    )

    apps = ApplicationService.get_applications_for_user(user)
    view = st.session_state.get("officer_view", "dashboard")

    if view == "queue":
        render_officer_queue_twopanel(user, apps)
    elif view == "create_app":
        render_officer_create_application(user)
    elif view == "review":
        render_individual_review(user)
    elif view == "logs":
        render_audit_trail_view()
    else:
        render_officer_dashboard(user, apps)

    render_footer()

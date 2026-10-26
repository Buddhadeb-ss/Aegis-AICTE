"""
Aegis Foundation - Scrutiny Officer Views
Directly implements Wireframes 2, 4, and 5 with complete governance capabilities:
- Screen C (Wireframe 2): Scrutiny Officer Dashboard with live metrics ribbon, queue statistics, and quick intake.
- Screen D (Wireframe 4): Scrutiny Officer Application Queue with two-panel layout (list on left, selected details + AI approval status on right).
- Screen E (Wireframe 5): Individual Application Review with application header, college name, context/why, AI check, attached documents cards, APPROVE/REJECT decision controls, and exportable scrutiny report.
- Statutory Audit Log Explorer and Direct Officer Intake.
"""

import os
import json
import streamlit as st
from datetime import datetime
from typing import Dict, Any, List
from core.auth import ApplicationService
from core.audit import get_audit_events
from views.theme import (
    render_header,
    render_footer,
    apply_custom_css,
    render_breadcrumbs,
    render_metrics_ribbon,
    render_empty_state,
    render_status_badge
)
from views.validation_view import (
    render_application_verdict,
    render_decision_oriented_results,
    render_validation_summary_badge
)


def generate_scrutiny_summary_report(packet: Dict[str, Any], officer_user: Dict[str, Any]) -> str:
    """Generates an exportable, formatted statutory scrutiny summary report."""
    app = packet["application"]
    docs = packet.get("documents", [])
    val_sum = packet.get("validation_summary", {})
    clarifs = packet.get("clarifications", [])

    lines = []
    lines.append("=" * 78)
    lines.append("ALL INDIA COUNCIL FOR TECHNICAL EDUCATION (AICTE)")
    lines.append("CENTRAL SCRUTINY DIRECTORATE — PRELIMINARY DOSSIER SCRUTINY REPORT")
    lines.append(f"Approval Process Cycle: 2026-2027 · Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 78)
    lines.append("")
    lines.append("1. INSTITUTIONAL IDENTIFICATION")
    lines.append(f"   Institution Name : {app.get('institution_name', 'N/A')}")
    lines.append(f"   Permanent AICTE ID: {app.get('institution_code', 'N/A')}")
    lines.append(f"   Location         : {app.get('city', 'N/A')}, {app.get('state', 'N/A')}")
    lines.append(f"   Application No.  : {app.get('application_number', 'N/A')}")
    lines.append(f"   Category         : {app.get('category', 'N/A').replace('_', ' ')}")
    lines.append(f"   Academic Session : {app.get('academic_year', 'N/A')}")
    lines.append(f"   Current Status   : {app.get('status', 'N/A')}")
    lines.append(f"   Reviewing Officer: {officer_user.get('name', 'Scrutiny Officer')} ({officer_user.get('email', 'AICTE')})")
    lines.append("")
    lines.append("2. STATUTORY DOCUMENT INVENTORY & COMPLETENESS")
    mandatory = packet.get("mandatory_checklist", [])
    lines.append(f"   Mandatory Requirements: {len(mandatory)} document types")
    lines.append(f"   Uploaded Documents    : {len(docs)} documents ({packet.get('completeness_pct', 0)}% complete)")
    if packet.get("missing_documents"):
        lines.append(f"   Missing Requirements  : {', '.join(packet['missing_documents'])}")
    else:
        lines.append("   Missing Requirements  : NONE (All mandatory items uploaded)")
    lines.append("")
    lines.append("   SUBMITTED DOCUMENTS LIST:")
    for i, d in enumerate(docs, 1):
        lines.append(f"   [{i}] {d['document_type']} — {d['filename']} ({d['file_size']} bytes)")
        lines.append(f"       SHA-256 Hash: {d.get('sha256_hash', 'N/A')}")
        v_run = d.get("validation_run") or {}
        lines.append(f"       Preliminary Check Result: {v_run.get('status', 'PENDING')}")
    lines.append("")
    lines.append("3. DETERMINISTIC VALIDATION FINDINGS SUMMARY")
    lines.append(f"   Overall Dossier State: {val_sum.get('overall_status', 'UNDER_SCRUTINY')}")
    findings = val_sum.get("findings", [])
    if findings:
        lines.append(f"   Recorded Findings ({len(findings)} items):")
        for j, f in enumerate(findings, 1):
            lines.append(f"   Finding #{j}:")
            lines.append(f"     - Document        : {f.get('document', f.get('file', 'N/A'))}")
            lines.append(f"     - Expected        : {f.get('expected', 'Statutory requirement')}")
            lines.append(f"     - Detected        : {f.get('finding', f.get('problem', 'N/A'))}")
            lines.append(f"     - Observed Evidence: {f.get('evidence', 'N/A')}")
            lines.append(f"     - Statutory Impact: {f.get('why_it_matters', 'Regulatory compliance')}")
            lines.append(f"     - Action Required : {f.get('recommended_action', f.get('action', 'N/A'))}")
    else:
        lines.append("   No critical technical discrepancies identified by rule checks.")
    lines.append("")
    lines.append("4. STATUTORY CLARIFICATION HISTORY")
    if clarifs:
        for k, cl in enumerate(clarifs, 1):
            lines.append(f"   Clarification #{k} [{cl['id']}] — Status: {cl['status']}")
            lines.append(f"     - Officer Inquiry  : {cl['question_text']}")
            lines.append(f"     - College Response : {cl.get('response_text', 'Pending Response')}")
            if cl.get("response_documents"):
                lines.append(f"     - Attached Proof   : {cl['response_documents']}")
    else:
        lines.append("   No formal clarification notices issued.")
    lines.append("")
    lines.append("5. OFFICIAL SCRUTINY DETERMINATION")
    lines.append(f"   Determination Outcome : {app.get('status')}")
    lines.append(f"   Officer Statutory Note: {app.get('notes', 'None recorded.')}")
    lines.append("")
    lines.append("=" * 78)
    lines.append("STATUTORY DISCLAIMER: This automated preliminary scrutiny report provides technical")
    lines.append("decision-support based on deterministic verification rules per AICTE APH 2026-27.")
    lines.append("Final regulatory approval or disapproval is rendered exclusively by the competent authority.")
    lines.append("=" * 78)

    return "\n".join(lines)


def render_officer_dashboard(user: Dict[str, Any], apps: List[Dict[str, Any]]):
    """Screen C (Wireframe 2) - Scrutiny Officer Portal with live metrics ribbon and prominent cards."""
    pending_apps = [a for a in apps if a.get("status") in ["SUBMITTED", "UNDER_SCRUTINY"]]
    clarif_apps = [a for a in apps if a.get("status") == "CLARIFICATION_REQUESTED"]
    concluded_apps = [a for a in apps if a.get("status") in ["APPROVED", "REJECTED"]]
    total_events = len(get_audit_events(limit=500))

    banner_html = (
        '<div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 18px 24px; margin-bottom: 20px;">'
        '<div style="display: flex; justify-content: space-between; align-items: center;">'
        '<div>'
        '<h2 style="font-size: 1.35rem; color: #0F172A; margin: 0 0 4px 0; font-weight: 700;">AICTE Central Scrutiny Directorate</h2>'
        f'<div style="font-size: 0.85rem; color: #64748B;">Jurisdiction: <strong>National Technical Approval Scrutiny</strong> · Authorized Scrutiny Officer: <strong>{user.get("name")}</strong> ({user.get("email")})</div>'
        '</div>'
        '<div><span style="font-size: 0.75rem; text-transform: uppercase; font-weight: 700; color: #1E40AF; background: #DBEAFE; padding: 4px 10px; border-radius: 4px;">Approval Process Cycle 2026-27</span></div>'
        '</div></div>'
    )
    st.markdown(banner_html, unsafe_allow_html=True)

    # Directorate Metrics Ribbon
    metrics_data = [
        {"label": "Queue Total", "value": len(apps), "icon": "📂", "sub": "Total institutional dossiers", "color": "#0F172A"},
        {"label": "Awaiting Review", "value": len(pending_apps), "icon": "⏳", "sub": "Actionable scrutiny items", "color": "#2563EB"},
        {"label": "In Clarification", "value": len(clarif_apps), "icon": "💬", "sub": "Awaiting college proofs", "color": "#B45309" if clarif_apps else "#64748B"},
        {"label": "Concluded", "value": len(concluded_apps), "icon": "⚖️", "sub": "Approved / Disapproved", "color": "#15803D" if concluded_apps else "#64748B"},
        {"label": "Audit Events", "value": total_events, "icon": "📜", "sub": "Immutable trail records", "color": "#475569"},
    ]
    render_metrics_ribbon(metrics_data)

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
            st.query_params["view"] = "queue"
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
            st.query_params["view"] = "create_app"
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
            st.query_params["view"] = "logs"
            st.rerun()

    # Recent submissions summary
    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
    st.markdown("### 📋 Recent Scrutiny Submissions")

    if not apps:
        render_empty_state(
            icon="📂",
            title="Queue Empty",
            description="No technical institution applications are currently on record."
        )
    else:
        for a in apps[:4]:
            with st.container(border=True):
                ca, cb, cc, cd = st.columns([2.5, 1.2, 1.2, 1.2])
                with ca:
                    st.markdown(f"**{a['institution_name']}** (`{a['institution_code']}`)")
                    st.caption(f"App No: **{a['application_number']}** · Cat: {a['category'].replace('_', ' ')} · Docs: {a['doc_count']}")
                with cb:
                    st.markdown(render_status_badge(a["status"]), unsafe_allow_html=True)
                with cc:
                    st.caption(f"Created: {a['created_at'][:10]}")
                with cd:
                    if st.button("Inspect Queue →", key=f"rec_dash_{a['id']}", use_container_width=True):
                        st.session_state["officer_selected_app_id"] = a["id"]
                        st.session_state["officer_view"] = "queue"
                        st.query_params["view"] = "queue"
                        st.rerun()


def render_officer_queue_twopanel(user: Dict[str, Any], apps: List[Dict[str, Any]]):
    """Screen D (Wireframe 4) - Two-panel queue layout with live search and filter."""
    render_breadcrumbs([
        {"label": "Central Scrutiny Directorate", "icon": "🏛️"},
        {"label": "Scrutiny Queue", "icon": "⚖️", "active": True}
    ])
    c_back, c_title, c_add = st.columns([1.2, 3.2, 1.4])
    with c_back:
        if st.button("← Back to Portal", key="btn_queue_back", use_container_width=True):
            st.session_state["officer_view"] = "dashboard"
            st.query_params["view"] = "dashboard"
            st.rerun()
    with c_title:
        st.markdown("## ⚖️ APPLICATIONS (Scrutiny Queue)")
    with c_add:
        if st.button("➕ Add Application", key="btn_queue_add_app", type="primary", use_container_width=True):
            st.session_state["officer_view"] = "create_app"
            st.query_params["view"] = "create_app"
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
        render_empty_state(
            icon="🔍",
            title="No Matching Applications",
            description="No applications match your selected filter or search criteria."
        )
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

            st.markdown(f"""
            <div class="queue-item {active_class}">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 4px;">
                    <div style="font-weight: 700; color: #0F172A; font-size: 0.95rem;">{a['application_number']}</div>
                    {render_status_badge(status)}
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
                st.markdown(f"Current Status: {render_status_badge(s)} · Category: **{sel_app['category'].replace('_', ' ')}** · Academic Year: **{sel_app['academic_year']}**", unsafe_allow_html=True)

                if sel_app.get("notes"):
                    st.markdown(f"**Institutional Remarks:** {sel_app['notes']}")

                st.markdown("---")
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
                    st.query_params["view"] = "review"
                    st.query_params["app_id"] = selected_id
                    st.rerun()

        except KeyError:
            st.error("Selected application not found.")


def render_create_app_officer_intake(user: Dict[str, Any]):
    """Direct Officer Intake (Wireframe Screen C Card 2 Intake)."""
    render_breadcrumbs([
        {"label": "Central Scrutiny Directorate", "icon": "🏛️"},
        {"label": "Scrutiny Queue", "icon": "⚖️"},
        {"label": "Direct Officer Intake", "icon": "➕", "active": True}
    ])
    c_back, c_title = st.columns([1.2, 4])
    with c_back:
        if st.button("← Back to Scrutiny Queue", key="btn_intake_back", use_container_width=True):
            st.session_state["officer_view"] = "queue"
            st.query_params["view"] = "queue"
            st.rerun()
    with c_title:
        st.markdown("## ➕ Direct Officer Intake Registration")

    institutions = ApplicationService.get_all_institutions()
    inst_options = {f"{inst['name']} ({inst['code']})": inst['id'] for inst in institutions}

    with st.form("officer_create_app_form"):
        selected_inst_label = st.selectbox("Applicant Institution", list(inst_options.keys()))
        target_inst_id = inst_options[selected_inst_label]

        category = st.selectbox(
            "Application Category",
            ["NEW_TECHNICAL_INSTITUTION", "EXTENSION_OF_APPROVAL"],
            format_func=lambda x: "New Technical Institution (Approval Process Handbook)" if x == "NEW_TECHNICAL_INSTITUTION" else "Extension of Approval (EoA - Existing Approved Technical College)"
        )
        academic_year = st.selectbox("Academic Year", ["2026-2027", "2027-2028"])
        intake_notes = st.text_area("Officer Intake Notes / Authorization Reference", placeholder="Authority order reference, regional council recommendation...")

        submit = st.form_submit_button("Register Application into Scrutiny Queue", use_container_width=True, type="primary")

        if submit:
            res = ApplicationService.create_application(
                institution_or_user=user,
                institution_id=target_inst_id,
                category=category,
                academic_year=academic_year,
                actor=user["email"],
                notes=intake_notes,
                initial_status="SUBMITTED"
            )
            st.session_state["officer_selected_app_id"] = res["id"]
            st.session_state["officer_view"] = "queue"
            st.query_params["view"] = "queue"
            st.success(f"Application `{res['application_number']}` successfully onboarded into Scrutiny Queue!")
            st.rerun()


def render_individual_review(user: Dict[str, Any]):
    """Screen E (Wireframe 5) - Full Detailed Application Scrutiny & Determination Workspace."""
    app_id = st.session_state.get("officer_active_app_id") or st.query_params.get("app_id")

    if not app_id:
        render_breadcrumbs([
            {"label": "Central Scrutiny Directorate", "icon": "🏛️"},
            {"label": "Detailed Review", "icon": "🔍", "active": True}
        ])
        st.info("No application selected for detailed scrutiny.")
        if st.button("← Back to Scrutiny Queue", key="btn_review_empty_back"):
            st.session_state["officer_view"] = "queue"
            st.query_params["view"] = "queue"
            st.rerun()
        return

    try:
        packet = ApplicationService.get_application_details(app_id, user)
    except KeyError:
        st.error(f"Application `{app_id}` not found.")
        st.session_state["officer_view"] = "queue"
        st.query_params["view"] = "queue"
        st.rerun()
        return

    app = packet["application"]
    docs = packet["documents"]
    clarifs = packet["clarifications"]

    render_breadcrumbs([
        {"label": "Central Scrutiny Directorate", "icon": "🏛️"},
        {"label": "Scrutiny Queue", "icon": "⚖️"},
        {"label": f"Review {app['application_number']}", "icon": "🔍", "active": True}
    ])

    c_back, c_title = st.columns([1.2, 4])
    with c_back:
        if st.button("← Back to Application Queue", key="btn_review_back", use_container_width=True):
            st.session_state["officer_view"] = "queue"
            st.query_params["view"] = "queue"
            if "app_id" in st.query_params:
                del st.query_params["app_id"]
            st.rerun()

    with c_title:
        st.markdown(f"## APPLICATION: `{app['application_number']}`")

    # Header Card
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
                {render_status_badge(app['status'])}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2-Column Split: Context & Verification Overview
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

    # Wireframe 5: ATTACHED DOCUMENTS & Validation Results
    st.markdown("### 📄 ATTACHED DOCUMENTS & VALIDATION RESULTS")
    render_decision_oriented_results(packet, user)

    st.markdown("---")

    # Wireframe 5: APPROVE / REJECT Controls, Clarification Workflow, Immutable Timeline & Export
    st.markdown("### ⚖️ REGULATORY ACTION: APPROVE / REJECT / CLARIFY")

    tab_decision, tab_clarif, tab_timeline, tab_export = st.tabs([
        "⚖️ Record Statutory Scrutiny Outcome",
        "💬 Clarification Workflow",
        "📜 Dossier Regulatory Timeline",
        "📄 Export Scrutiny Summary"
    ])

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

    # Tab 3: Timeline & Audit History
    with tab_timeline:
        st.markdown("#### Chronological Dossier Audit Trail")
        timeline = packet.get("audit_trail", [])
        if timeline:
            for ev in timeline:
                ev_type = ev.get("event_type", "EVENT")
                ev_time = ev.get("created_at", "")[:19].replace("T", " ")
                ev_actor = ev.get("actor", "System")
                details = {}
                if ev.get("details_json"):
                    try:
                        details = json.loads(ev["details_json"])
                    except Exception:
                        details = {}

                with st.container(border=True):
                    col_ev_badge, col_ev_meta = st.columns([1.5, 3])
                    with col_ev_badge:
                        st.markdown(f"**{ev_type.replace('_', ' ')}**")
                        st.caption(f"🕒 {ev_time}")
                    with col_ev_meta:
                        st.markdown(f"**Actor:** `{ev_actor}`")
                        if details.get("outcome"):
                            st.write(f"Determination: **{details['outcome']}**")
                        if details.get("notes"):
                            st.info(f"Justification: {details['notes']}")
                        if details.get("question"):
                            st.info(f"Clarification Issued: {details['question']}")
                        if details.get("response"):
                            st.success(f"Response: {details['response']}")
                        if details.get("filename"):
                            st.write(f"Document: `{details['filename']}`")
        else:
            st.info("No audit events recorded for this application dossier.")

    # Tab 4: Export Scrutiny Summary Report
    with tab_export:
        st.markdown("#### 📄 Statutory Scrutiny Summary Export")
        st.caption("Generate a structured, formal Preliminary Scrutiny Summary Report for regulatory recordkeeping.")

        report_txt = generate_scrutiny_summary_report(packet, user)
        with st.expander("👁️ Preview Scrutiny Summary Report", expanded=False):
            st.code(report_txt, language="text")

        c_dl1, c_dl2 = st.columns(2)
        with c_dl1:
            st.download_button(
                label="⬇️ Download Scrutiny Report (.txt)",
                data=report_txt,
                file_name=f"AICTE_Scrutiny_{app['application_number']}.txt",
                mime="text/plain",
                use_container_width=True,
                type="primary"
            )
        with c_dl2:
            st.caption("Official statutory artifact generated under AICTE Approval Process Handbook (APH 2026-27).")


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
            st.query_params["view"] = "dashboard"
            st.rerun()

    with c_title:
        st.markdown("## 📜 Statutory Audit Log & Regulatory Traceability")

    st.caption("Immutable chronological record of all authentication, submission, and review events.")

    events = get_audit_events(limit=200)
    if not events:
        render_empty_state(
            icon="📜",
            title="Audit Trail Clean",
            description="No compliance events have been recorded in the persistent ledger."
        )
        return

    # Filter by search
    q_search = st.text_input("🔍 Search Audit Records by Actor, Event Type, or Target ID", placeholder="principal@, DOCUMENT_UPLOADED, app_...")
    filtered_events = events
    if q_search.strip():
        qs = q_search.strip().lower()
        filtered_events = [e for e in events if qs in e["event_type"].lower() or qs in e["actor"].lower() or qs in e["entity_id"].lower()]

    st.markdown(f"**Showing {len(filtered_events)} audit events:**")

    for ev in filtered_events:
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([1.8, 1.8, 1.2, 2.2])
            with c1:
                st.markdown(f"**{ev['event_type']}**")
                st.caption(f"ID: `{ev['id']}`")
            with c2:
                st.markdown(f"Target: `{ev['entity_type']}` (`{ev['entity_id']}`)")
                st.caption(f"Actor: **{ev['actor']}**")
            with c3:
                st.caption(f"🕒 {ev['created_at'][:19].replace('T', ' ')}")
            with c4:
                if ev.get("details_json"):
                    try:
                        det = json.loads(ev["details_json"])
                        det_preview = ", ".join(f"{k}: {v}" for k, v in det.items() if v)[:70]
                        st.caption(det_preview or "No extra details")
                    except Exception:
                        st.caption(ev["details_json"][:70])


def officer_page():
    """Main Scrutiny Officer Portal Entrypoint implementing Wireframe 2, 4, 5."""
    user = st.session_state.get("user")
    if not user:
        st.error("Session terminated. Please return to the public login portal.")
        return

    # Top Header matching Wireframe 2
    render_header(
        portal_title="Scrutiny Officer Portal",
        badge_label="Directorate Scrutiny Console",
        subtitle=f"Central Technical Scrutiny Directorate · Officer: {user.get('name')}",
        user=user
    )

    apps = ApplicationService.get_applications_for_user(user)

    # Synchronize view and active_app_id with st.query_params
    qp_view = st.query_params.get("view")
    if qp_view and "officer_view" not in st.session_state:
        st.session_state["officer_view"] = qp_view
    elif "officer_view" in st.session_state:
        st.query_params["view"] = st.session_state["officer_view"]

    qp_app_id = st.query_params.get("app_id")
    if qp_app_id and "officer_active_app_id" not in st.session_state:
        st.session_state["officer_active_app_id"] = qp_app_id
    elif "officer_active_app_id" in st.session_state:
        st.query_params["app_id"] = st.session_state["officer_active_app_id"]

    view = st.session_state.get("officer_view", "dashboard")

    # Routing
    if view == "queue":
        render_officer_queue_twopanel(user, apps)
    elif view == "create_app":
        render_create_app_officer_intake(user)
    elif view == "review":
        render_individual_review(user)
    elif view == "logs":
        render_audit_trail_view()
    else:
        render_officer_dashboard(user, apps)

    render_footer()

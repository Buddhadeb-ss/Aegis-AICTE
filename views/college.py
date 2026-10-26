"""
Aegis Foundation - Screen B: College Representative Portal
Comprehensive Institutional Compliance & Application Scrutiny System:
- Top Header with institutional permanent ID, accreditation badge, and user pill
- Dynamic metrics ribbon (Total dossiers, Drafts, In Review, Action Required, Concluded)
- Three prominent navigation cards (APPLY, APPLICATION STATUS, NOTIFICATIONS)
- Multi-step application creation wizard (Details -> Checklist -> Uploads -> Submission)
- Robust application management with live search, status filters, and sorting
- Comprehensive document workspace with versioning, live pre-check, and replacements
- Chronological dossier audit timeline and clarification response round-trip
"""

import os
import time
import json
import streamlit as st
from typing import Dict, Any, List
from core.auth import ApplicationService, MANDATORY_DOCUMENTS
from views.theme import (
    render_header,
    render_footer,
    apply_custom_css,
    render_breadcrumbs,
    render_metrics_ribbon,
    render_wizard_step_bar,
    render_empty_state,
    render_status_badge,
    render_compliance_pillar_meter,
    render_version_differential_card
)
from views.validation_view import render_applicant_feedback_panel
from views.inspector import render_pdf_inspector_ui


def render_college_dashboard(user: Dict[str, Any], apps: List[Dict[str, Any]], notifications: List[Dict[str, Any]]):
    """Main dashboard displaying live metrics ribbon and the 3 prominent navigation cards."""
    open_inquiries = [n for n in notifications if n.get("status") == "OPEN"]
    active_drafts = [a for a in apps if a.get("status") == "DRAFT"]
    submitted_apps = [a for a in apps if a.get("status") in ["SUBMITTED", "UNDER_SCRUTINY"]]
    concluded_apps = [a for a in apps if a.get("status") in ["APPROVED", "REJECTED"]]

    # Directorate Context Banner
    banner_html = (
        '<div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 18px 24px; margin-bottom: 20px;">'
        '<div style="display: flex; justify-content: space-between; align-items: center;">'
        '<div>'
        f'<h2 style="font-size: 1.35rem; color: #0F172A; margin: 0 0 4px 0; font-weight: 700;">{user.get("institution_name", "Institutional Workspace")}</h2>'
        f'<div style="font-size: 0.85rem; color: #64748B;">Permanent ID: <code style="color: #1E3A8A; font-weight: 600;">{user.get("institution_code", user.get("institution_id"))}</code> · Authorized Representative: <strong>{user.get("name")}</strong> ({user.get("email")})</div>'
        '</div>'
        '<div style="text-align: right;"><span style="font-size: 0.75rem; text-transform: uppercase; font-weight: 700; color: #1E40AF; background: #DBEAFE; padding: 4px 10px; border-radius: 4px;">Approval Cycle 2026-27</span></div>'
        '</div></div>'
    )
    st.markdown(banner_html, unsafe_allow_html=True)

    # Metrics Ribbon (Dynamic Data Grounded in Real SQLite Records)
    metrics_data = [
        {"label": "Total Applications", "value": len(apps), "icon": "📂", "sub": "Institutional dossiers", "color": "#0F172A"},
        {"label": "Active Drafts", "value": len(active_drafts), "icon": "📝", "sub": "Incomplete authoring", "color": "#2563EB"},
        {"label": "Under Scrutiny", "value": len(submitted_apps), "icon": "⚖️", "sub": "Directorate review", "color": "#1E40AF"},
        {"label": "Action Required", "value": len(open_inquiries), "icon": "⚠️", "sub": "Clarification notices", "color": "#B45309" if open_inquiries else "#64748B"},
        {"label": "Concluded", "value": len(concluded_apps), "icon": "✅", "sub": "Approved / Decided", "color": "#15803D" if concluded_apps else "#64748B"},
    ]
    render_metrics_ribbon(metrics_data)

    # 3 Prominent Navigation Cards (Wireframe 3 Standard)
    c_apply, c_status, c_notify = st.columns(3)

    with c_apply:
        st.markdown(f"""
        <div class="wf-card">
            <div>
                <div class="wf-card-icon">📝</div>
                <div class="wf-card-title">APPLY</div>
                <p class="wf-card-desc">
                    Initiate new statutory approval application or continue an existing draft. Upload mandatory proofs and save progress.
                </p>
            </div>
            <div class="wf-card-meta">
                <span>{'Draft in progress' if active_drafts else 'Ready to apply'}</span>
                <span style="color: #2563EB; font-weight: 700;">{len(active_drafts)} Drafts</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Application (Apply) →", key="card_btn_apply", use_container_width=True, type="primary"):
            st.session_state["college_view"] = "apply"
            st.query_params["view"] = "apply"
            st.rerun()

    with c_status:
        st.markdown(f"""
        <div class="wf-card">
            <div>
                <div class="wf-card-icon">📊</div>
                <div class="wf-card-title">APPLICATION STATUS</div>
                <p class="wf-card-desc">
                    Track submitted regulatory dossiers, check completeness status, review scrutiny stages, and inspect outcomes.
                </p>
            </div>
            <div class="wf-card-meta">
                <span>Applications on Record</span>
                <span style="color: #2563EB; font-weight: 700;">{len(apps)} Total</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Check Application Status →", key="card_btn_status", use_container_width=True, type="primary"):
            st.session_state["college_view"] = "status"
            st.query_params["view"] = "status"
            st.rerun()

    with c_notify:
        alert_style = "color: #B45309; font-weight: 700;" if open_inquiries else "color: #15803D; font-weight: 700;"
        st.markdown(f"""
        <div class="wf-card">
            <div>
                <div class="wf-card-icon">🔔</div>
                <div class="wf-card-title">NOTIFICATIONS</div>
                <p class="wf-card-desc">
                    View official deficiency notices, statutory clarification inquiries issued by Scrutiny Officers, and submit evidence.
                </p>
            </div>
            <div class="wf-card-meta">
                <span>Active Clarifications</span>
                <span style="{alert_style}">{'⚠️ ' + str(len(open_inquiries)) + ' Action Required' if open_inquiries else 'All Resolved'}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("View Notifications →", key="card_btn_notify", use_container_width=True, type="primary"):
            st.session_state["college_view"] = "notifications"
            st.query_params["view"] = "notifications"
            st.rerun()

    # 4-Pillar Statutory Compliance Gauge
    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
    st.markdown("### 🏛️ Institutional Compliance Pillars (APH 2026-27 Norms)")
    latest_app_id = apps[0]["id"] if apps else None
    latest_docs = []
    mandatory_reqs = MANDATORY_DOCUMENTS["NEW_TECHNICAL_INSTITUTION"]
    if latest_app_id:
        try:
            pkt = ApplicationService.get_application_details(latest_app_id, user)
            latest_docs = pkt.get("documents", [])
            mandatory_reqs = pkt.get("mandatory_checklist", mandatory_reqs)
        except Exception:
            latest_docs = []
    render_compliance_pillar_meter(latest_docs, mandatory_reqs)

    # Recent Overview Section
    st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)
    st.markdown("### 📋 Institutional Dossier Activity")

    if not apps:
        render_empty_state(
            icon="📂",
            title="No Applications Initiated",
            description="Your institution has not initiated any approval applications for the 2026-27 cycle. Click the Apply card above to start your application dossier."
        )
    else:
        for a in apps[:4]:
            with st.container(border=True):
                ca, cb, cc, cd = st.columns([2.6, 1.2, 1.2, 1.2])
                with ca:
                    st.markdown(f"**{a['application_number']}** — *{a['category'].replace('_', ' ')}*")
                    st.caption(f"Academic Year: {a['academic_year']} · Documents: {a['doc_count']}")
                with cb:
                    st.markdown(render_status_badge(a["status"]), unsafe_allow_html=True)
                with cc:
                    if a.get("open_clarifications", 0) > 0:
                        st.warning(f"⚠️ {a['open_clarifications']} Action Items")
                    else:
                        st.caption("No pending inquiries")
                with cd:
                    if st.button("Open Dossier →", key=f"dash_open_{a['id']}", use_container_width=True):
                        st.session_state["active_app_id"] = a["id"]
                        st.session_state["college_view"] = "dossier_detail"
                        st.query_params["view"] = "dossier_detail"
                        st.query_params["app_id"] = a["id"]
                        st.rerun()


def render_apply_view(user: Dict[str, Any], apps: List[Dict[str, Any]]):
    """View for Card 1 (APPLY) - Multi-step wizard to create or continue active draft."""
    render_breadcrumbs([
        {"label": "Institutional Workspace", "icon": "🎓"},
        {"label": "Apply & Draft Application", "icon": "📝", "active": True}
    ])

    c_back, c_title = st.columns([1.2, 4])
    with c_back:
        if st.button("← Back to Dashboard", key="btn_apply_back", use_container_width=True):
            st.session_state["college_view"] = "dashboard"
            st.query_params["view"] = "dashboard"
            st.rerun()
    with c_title:
        st.markdown("## 📝 Statutory Approval Application Authoring")

    # Wizard step state
    if "wizard_step" not in st.session_state:
        st.session_state["wizard_step"] = 0

    wizard_steps = [
        "1. Details & Category",
        "2. Mandatory Checklist",
        "3. Document Uploads",
        "4. Review & Submission"
    ]
    render_wizard_step_bar(wizard_steps, st.session_state["wizard_step"])

    active_drafts = [a for a in apps if a.get("status") == "DRAFT"]

    if active_drafts:
        d_app = active_drafts[0]
        st.info(f"📌 Active In-Progress Draft: **`{d_app['application_number']}`** ({d_app['category'].replace('_', ' ')})")
        col_c1, col_c2 = st.columns([1, 1.2])
        with col_c1:
            if st.button("Resume Active Draft Workspace →", key="btn_cont_draft", use_container_width=True, type="primary"):
                st.session_state["active_app_id"] = d_app["id"]
                st.session_state["college_view"] = "dossier_detail"
                st.query_params["view"] = "dossier_detail"
                st.query_params["app_id"] = d_app["id"]
                st.rerun()
        with col_c2:
            st.caption("You can continue uploading statutory documents or submit the active draft for scrutiny.")
        st.markdown("---")

    # Wizard Step 0: Category & Details
    if st.session_state["wizard_step"] == 0:
        st.markdown("### Step 1: Institutional Approval Framework & Category")
        with st.form("create_new_application_form"):
            category = st.selectbox(
                "Regulatory Application Category",
                ["NEW_TECHNICAL_INSTITUTION", "EXTENSION_OF_APPROVAL"],
                format_func=lambda x: "New Technical Institution (Initial AICTE Approval Process)" if x == "NEW_TECHNICAL_INSTITUTION" else "Extension of Approval (EoA - Existing Approved Technical College)"
            )
            academic_year = st.selectbox("Academic Year / Session", ["2026-2027", "2027-2028"])
            notes = st.text_area(
                "Institutional Remarks & Justification (Optional)",
                placeholder="Specify campus location, proposed academic departments, intake capacity, or statutory justification..."
            )
            sub_next = st.form_submit_button("Save & Proceed to Document Checklist →", use_container_width=True, type="primary")

            if sub_next:
                res = ApplicationService.create_application(
                    institution_or_user=user,
                    category=category,
                    academic_year=academic_year,
                    notes=notes
                )
                st.session_state["active_app_id"] = res["id"]
                st.session_state["wizard_step"] = 1
                st.session_state["college_view"] = "dossier_detail"
                st.query_params["view"] = "dossier_detail"
                st.query_params["app_id"] = res["id"]
                st.success(f"Application Draft `{res['application_number']}` initialized successfully!")
                st.rerun()


def render_status_view(user: Dict[str, Any], apps: List[Dict[str, Any]]):
    """View for Card 2 (APPLICATION STATUS) - Searchable, filterable management table."""
    render_breadcrumbs([
        {"label": "Institutional Workspace", "icon": "🎓"},
        {"label": "Application Status & Management", "icon": "📊", "active": True}
    ])
    c_back, c_title = st.columns([1.2, 4])
    with c_back:
        if st.button("← Back to Dashboard", key="btn_status_back", use_container_width=True):
            st.session_state["college_view"] = "dashboard"
            st.query_params["view"] = "dashboard"
            st.rerun()
    with c_title:
        st.markdown("## 📊 Institutional Application Management")

    if not apps:
        render_empty_state(
            icon="📊",
            title="No Records Found",
            description="Your institution does not have any recorded applications. Use the Apply module to initiate a submission."
        )
        return

    # Filter & Search Bar
    col_search, col_filter, col_sort = st.columns([1.8, 1.2, 1.2])
    with col_search:
        search_q = st.text_input("🔍 Search by Application No. or Category", placeholder="AICTE-2026, New Technical...", key="status_search")
    with col_filter:
        status_flt = st.selectbox("Filter Status", ["ALL", "DRAFT", "SUBMITTED", "UNDER_SCRUTINY", "CLARIFICATION_REQUESTED", "APPROVED", "REJECTED"], key="status_filter")
    with col_sort:
        sort_flt = st.selectbox("Sort Order", ["Newest First", "Oldest First", "Status"], key="status_sort")

    # Apply Filtering & Sorting
    filtered_apps = list(apps)
    if status_flt != "ALL":
        filtered_apps = [a for a in filtered_apps if a["status"] == status_flt]
    if search_q.strip():
        sq = search_q.strip().lower()
        filtered_apps = [a for a in filtered_apps if sq in a["application_number"].lower() or sq in a["category"].lower() or sq in (a.get("notes") or "").lower()]

    if sort_flt == "Newest First":
        filtered_apps.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    elif sort_flt == "Oldest First":
        filtered_apps.sort(key=lambda x: x.get("created_at", ""))
    elif sort_flt == "Status":
        filtered_apps.sort(key=lambda x: x.get("status", ""))

    st.markdown(f"**Found {len(filtered_apps)} matching applications:**")

    for a in filtered_apps:
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([2.5, 1.3, 1.2, 1.2])
            with col1:
                st.markdown(f"**Application Reference:** `{a['application_number']}`")
                st.caption(f"Category: **{a['category'].replace('_', ' ')}** · Session: **{a['academic_year']}**")
                if a.get("notes"):
                    st.caption(f"Remarks: {a['notes'][:90]}...")
            with col2:
                st.markdown(render_status_badge(a["status"]), unsafe_allow_html=True)
                # Completeness calculation
                mandatory_reqs = MANDATORY_DOCUMENTS.get(a["category"], MANDATORY_DOCUMENTS["NEW_TECHNICAL_INSTITUTION"])
                doc_pct = min(100, int((a.get("doc_count", 0) / max(len(mandatory_reqs), 1)) * 100))
                st.caption(f"Documents: {a.get('doc_count', 0)} of {len(mandatory_reqs)} ({doc_pct}%)")
            with col3:
                st.caption(f"Created: {a['created_at'][:10]}")
                if a.get("open_clarifications", 0) > 0:
                    st.warning(f"⚠️ {a['open_clarifications']} Action Items")
                else:
                    st.caption("Compliant / In Scrutiny")
            with col4:
                btn_label = "Continue Draft →" if a["status"] == "DRAFT" else "Inspect Dossier →"
                if st.button(btn_label, key=f"status_open_{a['id']}", use_container_width=True):
                    st.session_state["active_app_id"] = a["id"]
                    st.session_state["college_view"] = "dossier_detail"
                    st.query_params["view"] = "dossier_detail"
                    st.query_params["app_id"] = a["id"]
                    st.rerun()


def render_notifications_view(user: Dict[str, Any], notifications: List[Dict[str, Any]]):
    """View for Card 3 (NOTIFICATIONS) - Clarification requests and official notices."""
    render_breadcrumbs([
        {"label": "Institutional Workspace", "icon": "🎓"},
        {"label": "Regulatory Notifications & Clarifications", "icon": "🔔", "active": True}
    ])
    c_back, c_title = st.columns([1.2, 4])
    with c_back:
        if st.button("← Back to Dashboard", key="btn_notif_back", use_container_width=True):
            st.session_state["college_view"] = "dashboard"
            st.query_params["view"] = "dashboard"
            st.rerun()
    with c_title:
        st.markdown("## 🔔 Regulatory Inquiries & Clarification Notices")

    if not notifications:
        render_empty_state(
            icon="✅",
            title="All Clear — No Pending Inquiries",
            description="Your institution has no outstanding statutory clarification notices or deficiency items. All submitted dossiers are in order."
        )
        return

    open_inquiries = [n for n in notifications if n.get("status") == "OPEN"]
    resolved_inquiries = [n for n in notifications if n.get("status") != "OPEN"]

    if open_inquiries:
        st.warning(f"### ⚠️ Action Required: {len(open_inquiries)} Pending Statutory Clarification(s)")
        for cl in open_inquiries:
            with st.container(border=True):
                st.markdown(f"**Application Reference:** `{cl.get('application_number')}` · Inquiry ID: `{cl['id']}` · Issued: {cl['created_at'][:19]}")
                st.markdown(f"**Officer Question ({cl.get('requested_by')}):**")
                st.info(cl["question_text"])
                if cl.get("requested_documents"):
                    st.write(f"**Required Evidence / Documentation:** `{cl['requested_documents']}`")

                with st.form(f"resp_form_{cl['id']}"):
                    response_text = st.text_area("Your Written Clarification Response", key=f"txt_{cl['id']}", placeholder="Explain statutory rectification or evidence...")
                    add_doc_note = st.text_input("Attached Document Description / Reference (Optional)", key=f"note_{cl['id']}")
                    clarif_file = st.file_uploader("Upload Supplementary Evidence Document (PDF or image, max 15MB)", type=["pdf", "png", "jpg", "jpeg"], key=f"cfile_{cl['id']}")
                    send_resp = st.form_submit_button("Submit Clarification Response to AICTE", use_container_width=True, type="primary")

                    if send_resp:
                        if not response_text.strip():
                            st.error("Please enter your clarification response before submitting.")
                        else:
                            try:
                                supp_file = None
                                if clarif_file is not None:
                                    supp_file = {"filename": clarif_file.name, "bytes": clarif_file.read()}
                                ApplicationService.respond_clarification(
                                    cl["id"],
                                    user,
                                    response_text,
                                    response_docs=add_doc_note,
                                    supplementary_file=supp_file
                                )
                                st.success("Clarification response recorded and application resubmitted for scrutiny!")
                                st.rerun()
                            except ValueError as ve:
                                st.error(str(ve))

    if resolved_inquiries:
        st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
        st.markdown("### 📜 Clarification History (Resolved)")
        for cl in resolved_inquiries:
            with st.container(border=True):
                st.markdown(f"**Inquiry ID:** `{cl['id']}` · Application: `{cl.get('application_number')}` · Status: **{cl['status']}**")
                st.caption(f"Question: {cl['question_text']}")
                st.success(f"**Institution Response:** {cl.get('response_text')}")
                if cl.get("response_documents"):
                    st.caption(f"Attached Proof: {cl['response_documents']}")


def render_dossier_detail(user: Dict[str, Any]):
    """Full application dossier workspace (document management, live pre-check, and final submission)."""
    app_id = st.session_state.get("active_app_id") or st.query_params.get("app_id")

    if not app_id:
        render_breadcrumbs([
            {"label": "Institutional Workspace", "icon": "🎓"},
            {"label": "Application Status", "icon": "📊"},
            {"label": "Dossier Detail", "icon": "📄", "active": True}
        ])
        st.info("No active dossier selected.")
        if st.button("← Back to Applications", key="btn_dossier_empty_back"):
            st.session_state["college_view"] = "status"
            st.query_params["view"] = "status"
            st.rerun()
        return

    try:
        packet = ApplicationService.get_application_details(app_id, user)
    except (PermissionError, KeyError) as e:
        st.error(f"Access error: {str(e)}. Returning to dashboard.")
        st.session_state.pop("active_app_id", None)
        st.session_state["college_view"] = "dashboard"
        st.query_params["view"] = "dashboard"
        if "app_id" in st.query_params:
            del st.query_params["app_id"]
        st.rerun()
        return

    app = packet["application"]
    docs = packet["documents"]
    clarifs = packet["clarifications"]

    render_breadcrumbs([
        {"label": "Institutional Workspace", "icon": "🎓"},
        {"label": "Application Status", "icon": "📊"},
        {"label": f"Dossier {app['application_number']}", "icon": "📄", "active": True}
    ])

    c_back, c_title = st.columns([1.2, 4])
    with c_back:
        if st.button("← Back to Applications", key="btn_dossier_back", use_container_width=True):
            st.session_state["college_view"] = "status"
            st.query_params["view"] = "status"
            if "app_id" in st.query_params:
                del st.query_params["app_id"]
            st.rerun()

    with c_title:
        st.markdown(f"## Dossier: `{app['application_number']}`")

    # Header Card
    st.markdown(f"""
    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px 20px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <strong>Status:</strong> {render_status_badge(app['status'])} · 
                <strong>Category:</strong> {app['category'].replace('_', ' ')} · 
                <strong>Academic Year:</strong> {app['academic_year']}
            </div>
            <div>
                <strong>Institution:</strong> {app['institution_name']} ({app['institution_code']})
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Document Completeness & Submission Readiness Gauge
    st.markdown("### Statutory Document Checklist")
    pct = packet["completeness_pct"]
    st.progress(pct / 100.0, text=f"Statutory Completeness: {pct}% ({len(docs)} of {len(packet['mandatory_checklist'])} required documents uploaded)")

    if packet["missing_documents"]:
        missing_fmt = [m.replace("_", " ").title() for m in packet["missing_documents"]]
        st.error(f"📋 **Submission Incomplete:** Missing mandatory documents: **{', '.join(missing_fmt)}**. Please upload all required items below to unlock formal submission.")
    else:
        st.success("✅ **Ready for Scrutiny:** All mandatory statutory documents uploaded and verified. You may proceed with formal submission below.")

    # Document Upload Section (available if in DRAFT or CLARIFICATION_REQUESTED)
    if app["status"] in ["DRAFT", "CLARIFICATION_REQUESTED"]:
        with st.expander("📤 Upload / Replace Statutory Document", expanded=True):
            with st.form("upload_doc_form", clear_on_submit=True):
                doc_type = st.selectbox("Select Regulatory Document Type", packet["mandatory_checklist"], format_func=lambda x: x.replace("_", " ").title())
                uploaded_file = st.file_uploader("Select PDF or Certified Scan (Max 15MB)", type=["pdf", "png", "jpg", "jpeg"])
                upload_btn = st.form_submit_button("Upload and Audit Document", use_container_width=True, type="primary")

                if upload_btn:
                    if not uploaded_file:
                        st.error("Please select a file to upload.")
                    else:
                        file_bytes = uploaded_file.read()
                        try:
                            with st.status("Verifying document...", expanded=True) as s_box:
                                s_box.write("📖 Reading uploaded file bytes & verifying magic header...")
                                time.sleep(0.2)
                                s_box.write("📋 Checking statutory document requirements...")
                                time.sleep(0.2)
                                s_box.write("🔍 Running deterministic structural & extraction checks...")
                                time.sleep(0.2)
                                s_box.write("📊 Preparing 7-field explainable findings...")
                                res = ApplicationService.upload_document(app_id, user, doc_type, uploaded_file.name, file_bytes)
                                s_box.update(label="Document processed successfully", state="complete", expanded=False)
                            st.success(f"Document '{uploaded_file.name}' uploaded and verified successfully!")
                            st.rerun()
                        except ValueError as ve:
                            st.error(str(ve))

    # Uploaded Documents Workspace
    st.markdown("### Uploaded Dossier Documents")
    if docs:
        for d in docs:
            run_d = d.get("validation_run") or {}
            c_status = run_d.get("assessment_overall_state", "PASS")
            file_size_kb = max(1, d.get("file_size", 0) // 1024)
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([2.6, 1, 1, 1.4])
                with col1:
                    st.markdown(f"📄 **{d['document_type'].replace('_', ' ')}** (`{d['filename']}`)")
                    st.caption(f"Size: {file_size_kb} KB · Hash: `{d.get('sha256_hash', '')[:12]}...` · Uploaded: {d['uploaded_at'][:10]}")
                with col2:
                    if c_status in ["ISSUE_FOUND", "INCOMPLETE"]:
                        st.markdown('<span class="badge badge-issue">Action Needed</span>', unsafe_allow_html=True)
                    elif c_status == "REVIEW_REQUIRED":
                        st.markdown('<span class="badge badge-review">Under Scrutiny</span>', unsafe_allow_html=True)
                    else:
                        st.markdown('<span class="badge badge-clear">In Order</span>', unsafe_allow_html=True)
                with col3:
                    if st.button("🔄 Re-run Check", key=f"rerun_{d['id']}", use_container_width=True):
                        try:
                            ApplicationService.rerun_validation(d["id"], user)
                            st.success("Re-check complete!")
                            st.rerun()
                        except Exception as ex:
                            st.error(str(ex))
                with col4:
                    file_path = d.get("stored_path")
                    if file_path and os.path.exists(file_path):
                        with open(file_path, "rb") as f:
                            st.download_button(
                                label="⬇️ Download",
                                data=f.read(),
                                file_name=d["filename"],
                                mime=d["mime_type"],
                                key=f"dl_{d['id']}",
                                use_container_width=True
                            )
                    if app["status"] in ["DRAFT", "CLARIFICATION_REQUESTED"]:
                        if st.button("🗑️ Remove", key=f"del_doc_{d['id']}", use_container_width=True):
                            try:
                                ApplicationService.delete_document(d["id"], user)
                                st.success(f"Document '{d['filename']}' removed.")
                                st.rerun()
                            except Exception as e:
                                st.error(str(e))
                # Render the 7-field structured finding feedback
                render_applicant_feedback_panel(d)

                with st.expander(f"🔬 Inspect PDF Anatomy & Metadata: {d['filename']}", expanded=False):
                    render_pdf_inspector_ui(d)
    else:
        render_empty_state(
            icon="📄",
            title="No Documents Uploaded",
            description="Use the upload tool above to attach mandatory statutory certificates (Land Title, Building Approval, AICTE Affidavit, Fire Safety)."
        )

    # Final Submission Button (if DRAFT)
    if app["status"] == "DRAFT":
        st.markdown("---")
        can_submit = packet["completeness_pct"] >= 100
        if st.button("🚀 Final Submission for Regulatory Scrutiny", use_container_width=True, type="primary", disabled=not can_submit):
            try:
                ApplicationService.submit_application(app_id, user)
                st.success("Application successfully submitted to AICTE Scrutiny Queue!")
                st.rerun()
            except ValueError as ve:
                st.error(str(ve))

    # Superseded Document Versions & Change History
    doc_versions = packet.get("document_versions", [])
    if doc_versions:
        st.markdown("<div style='margin-top: 18px;'></div>", unsafe_allow_html=True)
        with st.expander("📑 Superseded Document Versions & Audit Differential", expanded=False):
            st.caption("Historical revisions of statutory certificates replaced or updated during authoring or clarification:")
            for v in doc_versions:
                cur_doc = next((d for d in docs if d["document_type"] == v["document_type"]), None)
                if cur_doc:
                    render_version_differential_card(v, cur_doc)
                else:
                    with st.container(border=True):
                        st.markdown(f"**{v['document_type']}** · v{v['version_number']} (Archived {v['archived_at'][:19]})")
                        st.write(f"Archived Filename: `{v['filename']}` · File Size: {v['file_size']/1024:.1f} KB")

    # Audit Trail Timeline Expander
    st.markdown("<div style='margin-top: 18px;'></div>", unsafe_allow_html=True)
    with st.expander("📜 Application Activity & Audit Timeline", expanded=False):
        timeline = packet.get("audit_trail", [])
        if timeline:
            for ev in timeline:
                ev_type = ev.get("event_type", "EVENT")
                ev_time = ev.get("created_at", "")[:19].replace("T", " ")
                details = {}
                if ev.get("details_json"):
                    try:
                        details = json.loads(ev["details_json"])
                    except Exception:
                        details = {}
                with st.container(border=True):
                    st.markdown(f"**{ev_type.replace('_', ' ')}** · 🕒 `{ev_time}`")
                    if details.get("outcome"):
                        st.write(f"Scrutiny Determination: **{details['outcome']}**")
                    if details.get("notes"):
                        st.caption(f"Remarks: {details['notes']}")
                    if details.get("question"):
                        st.info(f"Clarification Inquiry: {details['question']}")
                    if details.get("response"):
                        st.success(f"Submitted Response: {details['response']}")
                    if details.get("filename"):
                        st.caption(f"Document File: {details['filename']}")
        else:
            st.caption("No audit activity logged yet.")


def college_page():
    """Main College Portal Entrypoint implementing Wireframe 3."""
    user = st.session_state.get("user")
    if not user:
        st.error("Session terminated. Please return to the public login portal.")
        return

    # Top Header matching Wireframe 3
    render_header(
        portal_title="College Representative Portal",
        badge_label="Institutional Workspace",
        subtitle=f"{user.get('institution_name', 'Institutional Portal')} ({user.get('institution_code', '')})",
        user=user
    )

    apps = ApplicationService.get_applications_for_user(user)
    notifications = ApplicationService.get_notifications_for_user(user)

    # Synchronize view and active_app_id with st.query_params
    qp_view = st.query_params.get("view")
    if qp_view and "college_view" not in st.session_state:
        st.session_state["college_view"] = qp_view
    elif "college_view" in st.session_state:
        st.query_params["view"] = st.session_state["college_view"]

    qp_app_id = st.query_params.get("app_id")
    if qp_app_id and "active_app_id" not in st.session_state:
        st.session_state["active_app_id"] = qp_app_id
    elif "active_app_id" in st.session_state:
        st.query_params["app_id"] = st.session_state["active_app_id"]

    view = st.session_state.get("college_view", "dashboard")

    # Routing
    if view == "apply":
        render_apply_view(user, apps)
    elif view == "status":
        render_status_view(user, apps)
    elif view == "notifications":
        render_notifications_view(user, notifications)
    elif view == "dossier_detail":
        render_dossier_detail(user)
    else:
        render_college_dashboard(user, apps, notifications)

    render_footer()

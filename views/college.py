"""
Aegis Foundation - Screen B: College Representative Portal
Directly implements Wireframe 3:
- Top Header: College Representative Portal with profile circle in upper-right corner
- Three prominent navigation cards:
  1. APPLY (application authoring, draft creation & continuation)
  2. APPLICATION STATUS (view existing applications, completeness, details)
  3. NOTIFICATIONS (clarification requests, officer inquiries & responses)
"""

import os
import time
import streamlit as st
from core.auth import ApplicationService, MANDATORY_DOCUMENTS
from views.theme import render_header, render_footer, apply_custom_css
from views.validation_view import render_applicant_feedback_panel


def render_college_dashboard(user, apps, notifications):
    """Main dashboard displaying the 3 prominent navigation cards from Wireframe 3."""
    open_inquiries = [n for n in notifications if n.get("status") == "OPEN"]
    active_drafts = [a for a in apps if a.get("status") == "DRAFT"]

    banner_html = (
        '<div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 18px 24px; margin-bottom: 24px;">'
        '<div style="display: flex; justify-content: space-between; align-items: center;">'
        '<div>'
        f'<h2 style="font-size: 1.35rem; color: #0F172A; margin: 0 0 4px 0; font-weight: 700;">{user.get("institution_name", "Institutional Workspace")}</h2>'
        f'<div style="font-size: 0.85rem; color: #64748B;">Permanent ID: <code style="color: #1E3A8A; font-weight: 600;">{user.get("institution_code", user.get("institution_id"))}</code> · Authorized Representative: <strong>{user.get("name")}</strong> ({user.get("email")})</div>'
        '</div>'
        '<div style="text-align: right;"><span style="font-size: 0.75rem; text-transform: uppercase; font-weight: 700; color: #1E40AF; background: #DBEAFE; padding: 4px 10px; border-radius: 4px;">Approval Cycle 2026-27</span></div>'
        '</div></div>'
    )
    st.markdown(banner_html, unsafe_allow_html=True)

    # Wireframe 3: 3 Prominent Cards (APPLY, APPLICATION STATUS, NOTIFICATIONS)
    c_apply, c_status, c_notify = st.columns(3)

    # 1. APPLY Card
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
            st.rerun()

    # 2. APPLICATION STATUS Card
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
            st.rerun()

    # 3. NOTIFICATIONS Card
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
            st.rerun()

    # Recent overview section
    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
    st.markdown("### 📋 Institutional Dossier Overview")

    if not apps:
        st.info("No applications submitted yet. Click the **APPLY** card above to create your institution's initial approval draft.")
    else:
        for a in apps[:3]:
            with st.container(border=True):
                ca, cb, cc, cd = st.columns([2.5, 1.2, 1.2, 1.2])
                with ca:
                    st.markdown(f"**{a['application_number']}** — *{a['category'].replace('_', ' ')}*")
                    st.caption(f"Academic Year: {a['academic_year']} · Documents: {a['doc_count']}")
                with cb:
                    st.markdown(f"Status: **{a['status']}**")
                with cc:
                    if a.get("open_clarifications", 0) > 0:
                        st.warning(f"⚠️ {a['open_clarifications']} Pending Action")
                    else:
                        st.caption("No pending inquiries")
                with cd:
                    if st.button("Open Dossier →", key=f"dash_open_{a['id']}", use_container_width=True):
                        st.session_state["active_app_id"] = a["id"]
                        st.session_state["college_view"] = "dossier_detail"
                        st.rerun()


def render_apply_view(user, apps):
    """View for Card 1 (APPLY) - Create new or continue active draft."""
    c_back, c_title = st.columns([1, 4])
    with c_back:
        if st.button("← Back to Dashboard", key="btn_apply_back", use_container_width=True):
            st.session_state["college_view"] = "dashboard"
            st.rerun()
    with c_title:
        st.markdown("## 📝 Statutory Approval Application (Apply)")

    # Check if active draft exists
    active_drafts = [a for a in apps if a.get("status") == "DRAFT"]

    if active_drafts:
        st.success(f"You have an active draft application: **{active_drafts[0]['application_number']}** ({active_drafts[0]['category']})")
        col_c1, col_c2 = st.columns([1, 1])
        with col_c1:
            if st.button("Continue Active Draft →", key="btn_cont_draft", use_container_width=True, type="primary"):
                st.session_state["active_app_id"] = active_drafts[0]["id"]
                st.session_state["college_view"] = "dossier_detail"
                st.rerun()
        with col_c2:
            st.caption("You can upload statutory documents or finalize submission on the active draft.")
        st.markdown("---")

    st.markdown("### Initialize New Regulatory Dossier")
    with st.form("create_new_application_form"):
        category = st.selectbox(
            "Application Category",
            ["NEW_TECHNICAL_INSTITUTION", "EXTENSION_OF_APPROVAL"],
            format_func=lambda x: "New Technical Institution (Initial Regulatory Approval)" if x == "NEW_TECHNICAL_INSTITUTION" else "Extension of Approval (EoA - Existing Approved Institution)"
        )
        academic_year = st.selectbox("Academic Year", ["2026-2027", "2027-2028"])
        notes = st.text_area("Institutional Remarks & Purpose (Optional)", placeholder="Describe context, campus location, proposed academic streams, or statutory expansion...")

        submit = st.form_submit_button("Create Application Draft", use_container_width=True, type="primary")

        if submit:
            res = ApplicationService.create_application(user["institution_id"], category, academic_year, user["email"], notes)
            st.session_state["active_app_id"] = res["id"]
            st.session_state["college_view"] = "dossier_detail"
            st.success(f"Application Draft {res['application_number']} created successfully! Proceeding to document checklist...")
            st.rerun()


def render_status_view(user, apps):
    """View for Card 2 (APPLICATION STATUS) - List of applications & details."""
    c_back, c_title = st.columns([1, 4])
    with c_back:
        if st.button("← Back to Dashboard", key="btn_status_back", use_container_width=True):
            st.session_state["college_view"] = "dashboard"
            st.rerun()
    with c_title:
        st.markdown("## 📊 Institutional Application Status")

    if not apps:
        st.info("No applications recorded for this institution. Use the **Apply** section to submit an application.")
        return

    for a in apps:
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([2.5, 1.2, 1.2, 1.2])
            with col1:
                st.markdown(f"**Application No:** `{a['application_number']}`")
                st.caption(f"Category: **{a['category'].replace('_', ' ')}** · Session: **{a['academic_year']}**")
                if a.get("notes"):
                    st.caption(f"Remarks: {a['notes'][:100]}...")
            with col2:
                status = a["status"]
                badge_class = f"badge badge-{status.lower()}"
                st.markdown(f"<span class='{badge_class}'>{status}</span>", unsafe_allow_html=True)
                st.caption(f"Documents: {a['doc_count']}")
            with col3:
                st.caption(f"Created: {a['created_at'][:10]}")
                if a.get("open_clarifications", 0) > 0:
                    st.warning(f"⚠️ {a['open_clarifications']} Action Items")
                else:
                    st.caption("Scrutiny Active")
            with col4:
                if st.button("Open Dossier →", key=f"status_open_{a['id']}", use_container_width=True):
                    st.session_state["active_app_id"] = a["id"]
                    st.session_state["college_view"] = "dossier_detail"
                    st.rerun()


def render_notifications_view(user, notifications):
    """View for Card 3 (NOTIFICATIONS) - Clarification requests and official notices."""
    c_back, c_title = st.columns([1, 4])
    with c_back:
        if st.button("← Back to Dashboard", key="btn_notif_back", use_container_width=True):
            st.session_state["college_view"] = "dashboard"
            st.rerun()
    with c_title:
        st.markdown("## 🔔 Regulatory Inquiries & Clarification Notices")

    if not notifications:
        st.success("✅ No statutory clarification requests or pending inquiries on record. All submissions are in order.")
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
        st.markdown("### 📜 Clarification History (Resolved)")
        for cl in resolved_inquiries:
            with st.container(border=True):
                st.markdown(f"**Inquiry ID:** `{cl['id']}` · Application: `{cl.get('application_number')}` · Status: **{cl['status']}**")
                st.caption(f"Question: {cl['question_text']}")
                st.success(f"**Institution Response:** {cl.get('response_text')}")
                if cl.get("response_documents"):
                    st.caption(f"Attached Proof: {cl['response_documents']}")


def render_dossier_detail(user):
    """Full application dossier view (document upload, completeness, and final submission)."""
    app_id = st.session_state.get("active_app_id")

    c_back, c_title = st.columns([1, 4])
    with c_back:
        if st.button("← Back to Applications", key="btn_dossier_back", use_container_width=True):
            st.session_state["college_view"] = "status"
            st.rerun()

    if not app_id:
        st.info("No active dossier selected.")
        return

    try:
        packet = ApplicationService.get_application_details(app_id, user)
    except (PermissionError, KeyError) as e:
        st.error(f"Access error: {str(e)}. Returning to dashboard.")
        st.session_state.pop("active_app_id", None)
        st.session_state["college_view"] = "dashboard"
        st.rerun()
        return

    app = packet["application"]
    docs = packet["documents"]
    clarifs = packet["clarifications"]

    with c_title:
        st.markdown(f"## Dossier: {app['application_number']}")

    st.markdown(f"""
    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px 20px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <strong>Status:</strong> <span style="font-weight: 700; color: #1E40AF;">{app['status']}</span> · 
                <strong>Category:</strong> {app['category'].replace('_', ' ')} · 
                <strong>Academic Year:</strong> {app['academic_year']}
            </div>
            <div>
                <strong>Institution:</strong> {app['institution_name']} ({app['institution_code']})
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Document Completeness & Submission Readiness
    st.markdown("### Statutory Document Checklist")
    pct = packet["completeness_pct"]
    st.progress(pct / 100.0, text=f"Completeness: {pct}% ({len(docs)} uploaded)")

    if packet["missing_documents"]:
        st.error(f"📋 **Submission Incomplete:** Missing mandatory documents: {', '.join(packet['missing_documents'])}. Please upload the missing items below before final submission.")
    else:
        st.success("✅ **Ready for Submission:** All mandatory statutory documents uploaded and verified. You may proceed with final submission below.")

    # Document Upload (if DRAFT or CLARIFICATION_REQUESTED)
    if app["status"] in ["DRAFT", "CLARIFICATION_REQUESTED"]:
        with st.expander("📤 Upload Statutory Document", expanded=True):
            with st.form("upload_doc_form", clear_on_submit=True):
                doc_type = st.selectbox("Document Type", packet["mandatory_checklist"])
                uploaded_file = st.file_uploader("Select PDF or Scanned Document (Max 15MB)", type=["pdf", "png", "jpg", "jpeg"])
                upload_btn = st.form_submit_button("Upload and Audit Document", use_container_width=True)

                if upload_btn:
                    if not uploaded_file:
                        st.error("Please select a file to upload.")
                    else:
                        file_bytes = uploaded_file.read()
                        try:
                            with st.status("Verifying document...", expanded=True) as s_box:
                                s_box.write("📖 Reading uploaded documents...")
                                time.sleep(0.3)
                                s_box.write("📋 Checking document requirements...")
                                time.sleep(0.3)
                                s_box.write("🔍 Comparing uploaded files with expected categories...")
                                time.sleep(0.3)
                                s_box.write("📊 Preparing the result...")
                                res = ApplicationService.upload_document(app_id, user, doc_type, uploaded_file.name, file_bytes)
                                s_box.update(label="Document processed successfully", state="complete", expanded=False)
                            st.success(f"Document '{uploaded_file.name}' uploaded successfully!")
                            st.rerun()
                        except ValueError as ve:
                            st.error(str(ve))

    # Uploaded Documents List
    st.markdown("### Uploaded Dossier Documents")
    if docs:
        for d in docs:
            run_d = d.get("validation_run") or {}
            c_status = run_d.get("assessment_overall_state", "PASS")
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([2.5, 1, 1, 1.2])
                with col1:
                    st.markdown(f"📄 **{d['document_type'].replace('_', ' ')}** (`{d['filename']}`)")
                    st.caption(f"Uploaded: {d['uploaded_at'][:10]} · Statutory Document")
                with col2:
                    if c_status in ["ISSUE_FOUND", "INCOMPLETE"]:
                        st.markdown('<span class="badge badge-issue">Action Needed</span>', unsafe_allow_html=True)
                    elif c_status == "REVIEW_REQUIRED":
                        st.markdown('<span class="badge badge-review">Under Scrutiny</span>', unsafe_allow_html=True)
                    else:
                        st.markdown('<span class="badge badge-clear">In Order</span>', unsafe_allow_html=True)
                with col3:
                    st.caption(f"Status: Recorded")
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
                render_applicant_feedback_panel(d)
    else:
        st.info("No documents uploaded yet.")

    # Final Submission Button (if DRAFT)
    if app["status"] == "DRAFT":
        st.markdown("---")
        if st.button("🚀 Final Submission for Regulatory Scrutiny", use_container_width=True, type="primary"):
            try:
                ApplicationService.submit_application(app_id, user)
                st.success("Application successfully submitted to AICTE Scrutiny Queue!")
                st.rerun()
            except ValueError as ve:
                st.error(str(ve))


def college_page():
    """Main College Portal Entrypoint implementing Wireframe 3."""
    user = st.session_state.get("user")
    if not user:
        st.error("Session terminated.")
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

    view = st.session_state.get("college_view", "dashboard")

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

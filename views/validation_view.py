"""
Aegis Foundation - Decision-Oriented Validation Interface UI Components
Implements the simplified, decision-oriented review experience for scrutiny officers:
- One prominent application verdict at the top
- Compact processing summary distinguishing OCR, compliance, cross-document, and unverified authenticity
- Shows only exceptions: If all checks pass, shows one clear summary without exposing technical checklists
- When there is a problem, displays only: File, Problem, Evidence, Action
- Compact document list with issues/reviews brought to the top
- All technical diagnostics (24 checks, raw JSON, hashes, run history) collapsed under 'Technical details'
- Simplified applicant feedback for college representatives
"""

import json
import os
import streamlit as st
from typing import Any, Dict, List, Optional
from core.auth import ApplicationService
from core.validation.schema import AssessmentState, AssessmentType, CheckStatus


def render_application_verdict(val_summary: Dict[str, Any], mandatory_count: Optional[int] = None):
    """
    Renders the compact, understandable, and visually credible Document Verification summary:
    **Document Verification**
    - Application documents: X/Y uploaded
    - Document matching: M/Y matched
    - Result: N document(s) need attention / No document mismatches detected
    With immediate plain-language Issue Found box if any mismatch occurs.
    """
    failed = val_summary.get("failed_checks", 0)
    total = val_summary.get("total_checks", 0)

    app_assessments = val_summary.get("app_assessments") or {}
    verdict = app_assessments.get("verdict") or {}
    verdict_key = verdict.get("key", "CHECK_INCOMPLETE")
    actionable_findings = app_assessments.get("actionable_findings", [])
    doc_verif = app_assessments.get("doc_verification") or {}

    uploaded_count = doc_verif.get("uploaded_count", val_summary.get("document_count", 0))
    total_req = mandatory_count or max(uploaded_count, 4)
    matched_count = doc_verif.get("matched_count", uploaded_count)
    result_text = doc_verif.get("result_text", "No document mismatches detected")

    is_clean = (failed == 0 and not actionable_findings and verdict_key in ["CLEAR", "PASSED"])

    if total == 0 or uploaded_count == 0:
        status_badge = '<span class="badge badge-incomplete">INCOMPLETE</span>'
        bg_col = "#F8FAFC"
        border_col = "#CBD5E1"
        res_display = "No documents submitted"
    elif is_clean:
        status_badge = '<span class="badge badge-clear">CLEAR</span>'
        bg_col = "#F0FDF4"
        border_col = "#86EFAC"
        res_display = '<span style="color: #166534; font-weight: 600;">No document mismatches detected</span>'
    elif actionable_findings:
        status_badge = '<span class="badge badge-issue">ISSUE FOUND</span>'
        bg_col = "#FEF2F2"
        border_col = "#FCA5A5"
        res_display = f'<span style="color: #991B1B; font-weight: 600;">{result_text}</span>'
    else:
        status_badge = '<span class="badge badge-review">REVIEW</span>'
        bg_col = "#FFFBEB"
        border_col = "#FCD34D"
        res_display = result_text

    # Build concise issue found section if issues exist
    issue_html = ""
    if actionable_findings and not is_clean:
        top_issue = actionable_findings[0]
        exp_name = top_issue.get("expected_document") or top_issue.get("document_type", "Statutory Document").replace('_', ' ').title()
        up_name = top_issue.get("uploaded_filename") or top_issue.get("file", "document.pdf")
        prob_text = top_issue.get("problem", "The uploaded filename/category does not match the expected document.")
        act_text = top_issue.get("action", "Review document")

        issue_html = (
            f'<div style="margin-top: 12px; padding: 12px 14px; background: #FFFFFF; border: 1px solid #FECACA; border-left: 4px solid #DC2626; border-radius: 6px;">'
            f'<div style="font-weight: 700; color: #991B1B; font-size: 0.88rem; margin-bottom: 6px;">⚠️ Issue found</div>'
            f'<div style="font-size: 0.85rem; color: #1E293B; line-height: 1.6;">'
            f'<div>• <strong>Expected:</strong> {exp_name}</div>'
            f'<div>• <strong>Uploaded:</strong> <code>{up_name}</code></div>'
            f'<div>• <strong>Finding:</strong> {prob_text}</div>'
            f'<div>• <strong>Action:</strong> <span style="color: #1E40AF; font-weight: 600;">{act_text}</span></div>'
            f'</div>'
            f'</div>'
        )

    card_html = (
        f'<div style="background: {bg_col}; border: 1.5px solid {border_col}; border-radius: 8px; padding: 14px 18px; margin-bottom: 14px;">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">'
        f'<div style="font-weight: 700; font-size: 1.05rem; color: #0F172A;">📋 Document Verification</div>'
        f'{status_badge}'
        f'</div>'
        f'<div style="font-size: 0.90rem; color: #334155; line-height: 1.6;">'
        f'<div>• <strong>Application documents:</strong> {uploaded_count}/{total_req} uploaded</div>'
        f'<div>• <strong>Document matching:</strong> {matched_count}/{total_req} matched</div>'
        f'<div>• <strong>Result:</strong> {res_display}</div>'
        f'</div>'
        f'{issue_html}'
        f'</div>'
    )
    st.markdown(card_html, unsafe_allow_html=True)


def render_validation_summary_badge(val_summary: Dict[str, Any]):
    """Compatibility alias for render_application_verdict."""
    render_application_verdict(val_summary)


def render_decision_oriented_results(packet: Dict[str, Any], user: Dict[str, Any]):
    """
    Renders the decision-oriented document validation results on Screen E.
    - If all required checks pass, shows one clear summary and a compact document list.
    - If problems/reviews are detected, shows exactly: Expected, Uploaded, Finding, Action.
    - All technical diagnostics (24 checks, raw JSON, hashes, dispositions) are collapsed under 'Technical Details'.
    """
    import time
    app = packet.get("application", {})
    docs = packet.get("documents", [])
    val_summary = packet.get("validation_summary", {})
    app_assessments = val_summary.get("app_assessments") or {}
    verdict = app_assessments.get("verdict") or {}
    verdict_key = verdict.get("key", "CHECK_INCOMPLETE")
    actionable_findings = app_assessments.get("actionable_findings", [])
    compact_docs = app_assessments.get("compact_documents", [])

    if not docs:
        st.warning("Applicant has not uploaded any documents for this application.")
        return

    # -------------------------------------------------------------------------
    # CASE 1: CLEAN APPLICATION (CLEAR)
    # -------------------------------------------------------------------------
    if verdict_key == "CLEAR" or (not actionable_findings and verdict_key not in ["ACTION_REQUIRED", "MANUAL_REVIEW_REQUIRED", "CHECK_INCOMPLETE"]):
        st.success(
            "All required automated checks passed. No document mismatches detected. "
            "Automated checks do not independently establish document authenticity."
        )

        st.markdown("##### 📄 Submitted Documents")
        for d in docs:
            c_doc1, c_doc2, c_doc3, c_doc4 = st.columns([3, 2, 1.2, 1.2])
            with c_doc1:
                st.markdown(f"**{d['filename']}**")
            with c_doc2:
                st.caption(d['document_type'].replace('_', ' '))
            with c_doc3:
                st.markdown('<span class="badge badge-clear">Clear</span>', unsafe_allow_html=True)
            with c_doc4:
                file_path = d.get("stored_path")
                if file_path and os.path.exists(file_path):
                    with open(file_path, "rb") as f:
                        st.download_button(
                            label="⬇️ Download",
                            data=f.read(),
                            file_name=d["filename"],
                            mime=d["mime_type"],
                            key=f"dl_clean_{d['id']}",
                            use_container_width=True
                        )

    # -------------------------------------------------------------------------
    # CASE 2: PROBLEMS / REVIEWS / EXCEPTIONS DETECTED
    # -------------------------------------------------------------------------
    else:
        st.markdown("### ⚠️ Actionable Findings")
        st.caption("The following items require officer examination or applicant clarification before clearance:")

        for f in actionable_findings:
            f_state = f.get("state", "REVIEW_REQUIRED")
            is_issue = (f_state == AssessmentState.ISSUE_FOUND.value or f.get("severity") in ["CRITICAL", "HIGH"])
            border_left_col = "#DC2626" if is_issue else "#D97706"
            badge_cls = "badge-issue" if is_issue else "badge-review"
            badge_label = "ISSUE" if is_issue else "REVIEW REQUIRED"

            doc_name = f.get("document") or f.get("uploaded_filename") or f.get("file", "document.pdf")
            exp_name = f.get("expected") or f.get("expected_document") or f.get("document_type", "Statutory Document").replace('_', ' ').title()
            prob_text = f.get("finding") or f.get("problem", "The uploaded filename/category does not match the expected document.")
            ev_text = f.get("evidence", "")
            why_text = f.get("why_it_matters", "")
            conf_text = f.get("confidence_or_limitation", "")
            act_text = f.get("recommended_action") or f.get("action", "Review document")

            # Format evidence snippet nicely
            ev_snippet = f"<div style='margin-top: 4px; font-family: monospace; font-size: 0.82rem; background: #F1F5F9; padding: 4px 8px; border-radius: 4px; color: #0F172A;'>{ev_text}</div>" if ev_text else ""
            why_snippet = f"<div style='margin-top: 4px; color: #475569;'>{why_text}</div>" if why_text else ""
            conf_badge = f"<span style='font-size: 0.78rem; color: #64748B; font-style: italic;'>({conf_text})</span>" if conf_text else ""

            st.markdown(f"""
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-left: 5px solid {border_left_col}; padding: 16px 18px; border-radius: 8px; margin-bottom: 14px; box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <div style="font-size: 0.96rem; font-weight: 700; color: #0F172A;">
                        📄 <code>{doc_name}</code>
                    </div>
                    <div>
                        <span class="badge {badge_cls}">{badge_label}</span>
                        {conf_badge}
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: 130px 1fr; row-gap: 8px; font-size: 0.88rem; color: #334155;">
                    <div><strong>Expected:</strong></div>
                    <div>{exp_name}</div>
                    <div><strong>Finding:</strong></div>
                    <div><span style="font-weight: 600; color: #0F172A;">{prob_text}</span></div>
                    <div><strong>Evidence:</strong></div>
                    <div>{ev_snippet}</div>
                    <div><strong>Why it matters:</strong></div>
                    <div>{why_snippet}</div>
                </div>
                <div style="margin-top: 12px; font-size: 0.86rem; color: #1E40AF; background: #EFF6FF; padding: 8px 12px; border-radius: 6px; border: 1px solid #BFDBFE;">
                    💡 <strong>Recommended Action:</strong> {act_text}
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 18px;'></div>", unsafe_allow_html=True)
        st.markdown("##### 📄 Submitted Documents (Exceptions at Top)")

        # Map document objects by id or filename for downloads
        doc_map = {d.get("id"): d for d in docs}
        doc_name_map = {d.get("filename"): d for d in docs}

        for cd in compact_docs:
            d_obj = doc_map.get(cd.get("id")) or doc_name_map.get(cd.get("filename"))
            s_status = cd.get("simple_status", "Clear")

            if s_status == "Issue":
                s_badge = '<span class="badge badge-issue">Issue</span>'
            elif s_status == "Review":
                s_badge = '<span class="badge badge-review">Review</span>'
            elif s_status == "Incomplete":
                s_badge = '<span class="badge badge-incomplete">Incomplete</span>'
            else:
                s_badge = '<span class="badge badge-clear">Clear</span>'

            c_doc1, c_doc2, c_doc3, c_doc4 = st.columns([3, 2, 1.2, 1.2])
            with c_doc1:
                st.markdown(f"**{cd['filename']}**")
            with c_doc2:
                st.caption(cd['document_type'].replace('_', ' '))
            with c_doc3:
                st.markdown(s_badge, unsafe_allow_html=True)
            with c_doc4:
                if d_obj:
                    file_path = d_obj.get("stored_path")
                    if file_path and os.path.exists(file_path):
                        with open(file_path, "rb") as f:
                            st.download_button(
                                label="⬇️ Download",
                                data=f.read(),
                                file_name=d_obj["filename"],
                                mime=d_obj["mime_type"],
                                key=f"dl_list_{cd['id']}",
                                use_container_width=True
                            )

    # -------------------------------------------------------------------------
    # 3. SINGLE COLLAPSED SECTION: TECHNICAL DETAILS
    # -------------------------------------------------------------------------
    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
    with st.expander("🔬 Technical Details", expanded=False):
        st.markdown("#### Detailed Diagnostic Evidence & Technical Execution Records")
        st.caption("This section contains internal check records, raw JSON observations, hashes, rule versions, and officer finding dispositions.")

        doc_tabs = st.tabs([f"📄 {d['filename']}" for d in docs])
        for idx, d in enumerate(docs):
            with doc_tabs[idx]:
                run = d.get("validation_run")
                if not run:
                    st.info(f"No validation record available for {d['filename']}.")
                    continue

                c_meta1, c_meta2 = st.columns(2)
                with c_meta1:
                    st.write(f"**Document Type:** `{d['document_type']}`")
                    st.write(f"**File Size:** `{d['file_size']} bytes`")
                    st.write(f"**SHA-256 Digest:** `{d['sha256_hash']}`")
                with c_meta2:
                    st.write(f"**Validation Run ID:** `{run['id']}`")
                    st.write(f"**Engine Version:** `{run['engine_version']}`")
                    st.write(f"**Completed At:** `{run.get('completed_at', '')[:19]}`")

                # Filters and Re-run
                c_f1, c_f2, c_btn = st.columns([1.5, 1.5, 1.2])
                with c_f1:
                    status_filter = st.selectbox(
                        "Filter by Check Status",
                        ["ALL", "FAIL", "WARNING", "REVIEW_REQUIRED", "PASS", "NOT_RUN", "ERROR"],
                        key=f"tech_sf_{d['id']}"
                    )
                with c_f2:
                    cat_filter = st.selectbox(
                        "Filter by Assessment Category",
                        ["ALL", "file_integrity", "document_structure", "metadata", "content", "consistency", "forensic"],
                        key=f"tech_cf_{d['id']}"
                    )
                with c_btn:
                    st.write("")
                    st.write("")
                    if st.button("🔄 Re-run Validation", key=f"btn_tech_rerun_{d['id']}", use_container_width=True):
                        try:
                            with st.status("Verifying document...", expanded=True) as s_box:
                                s_box.write("📖 Reading uploaded documents...")
                                time.sleep(0.3)
                                s_box.write("📋 Checking document requirements...")
                                time.sleep(0.3)
                                s_box.write("🔍 Comparing uploaded files with expected categories...")
                                time.sleep(0.3)
                                s_box.write("📊 Preparing the result...")
                                ApplicationService.rerun_validation(d["id"], user)
                                s_box.update(label="Verification completed", state="complete", expanded=False)
                            st.success("Validation re-executed successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Re-run failed: {e}")

                checks = run.get("checks", [])
                filtered_checks = checks
                if status_filter != "ALL":
                    filtered_checks = [c for c in filtered_checks if c["status"] == status_filter]
                if cat_filter != "ALL":
                    filtered_checks = [c for c in filtered_checks if c["category"] == cat_filter]

                st.caption(f"Showing {len(filtered_checks)} of {len(checks)} technical checks:")

                dispositions = run.get("dispositions", [])

                for c in filtered_checks:
                    s = c["status"]
                    badge_class = f"badge badge-{s.lower()}"
                    sev_color = "#991B1B" if c["severity"] in ["CRITICAL", "HIGH"] else "#92400E" if c["severity"] == "MEDIUM" else "#1E40AF"

                    with st.container(border=True):
                        col_hdr1, col_hdr2 = st.columns([3, 1])
                        with col_hdr1:
                            st.markdown(
                                f"<span class='{badge_class}'>{s}</span> "
                                f"<span style='font-size: 0.72rem; font-weight: 700; color: {sev_color}; text-transform: uppercase;'>[{c['severity']}]</span> "
                                f"<strong>{c['check_name']}</strong> (`{c['check_id']}`)",
                                unsafe_allow_html=True
                            )
                            st.markdown(f"<div style='font-size: 0.85rem; color: #334155; margin-top: 4px;'>{c['summary']}</div>", unsafe_allow_html=True)
                        with col_hdr2:
                            st.caption(f"Cat: `{c['category']}` · {c.get('duration_ms', 0):.1f} ms")

                        with st.expander("Inspect Technical Evidence"):
                            c_d1, c_d2 = st.columns(2)
                            with c_d1:
                                st.markdown("**Expected Value:**")
                                st.code(c.get("expected_value") or "Standard regulatory compliance", language="text")
                            with c_d2:
                                st.markdown("**Observed Value:**")
                                st.code(c.get("observed_value") or "N/A", language="text")

                            if c.get("details"):
                                st.markdown("**Technical Findings:**")
                                st.write(c["details"])

                            if c.get("evidence"):
                                st.markdown("**Raw Structured Evidence (JSON):**")
                                st.json(c["evidence"])

                            # Human Officer Finding Disposition Form
                            if user.get("role") == "AICTE_SCRUTINY_OFFICER" and s in ["FAIL", "WARNING", "REVIEW_REQUIRED"]:
                                st.markdown("---")
                                st.markdown("##### ✍️ Record Officer Finding Disposition")

                                existing_disps = [disp for disp in dispositions if disp.get("check_record_id") == c.get("id")]
                                if existing_disps:
                                    for ed in existing_disps:
                                        st.success(f"**Recorded:** {ed['disposition']} by `{ed['officer_email']}` on {ed['created_at'][:19]}")
                                        st.caption(f"Notes: {ed['officer_notes']}")

                                with st.form(f"disp_form_tech_{c.get('id', c['check_id'])}"):
                                    disp_choice = st.radio("Finding Disposition", ["ACCEPTED", "DISMISSED", "NOTED"], horizontal=True)
                                    disp_notes = st.text_input("Officer Justification", placeholder="Explain why finding is accepted or dismissed...")
                                    submit_disp = st.form_submit_button("Record Finding Disposition")

                                    if submit_disp:
                                        if not disp_notes.strip():
                                            st.error("Please provide written justification.")
                                        else:
                                            try:
                                                ApplicationService.record_finding_disposition(
                                                    c["id"], d["id"], app["id"], user, disp_choice, disp_notes
                                                )
                                                st.success("Disposition recorded in audit log!")
                                                st.rerun()
                                            except Exception as de:
                                                st.error(f"Error recording disposition: {de}")

        # Dedicated Cross-Document Comparison Table in Technical Details
        st.markdown("---")
        st.markdown("##### 🔄 Dossier Cross-Document Consistency Matrix")
        cross_rows = []
        for d in docs:
            run_d = d.get("validation_run") or {}
            cross_rows.append({
                "Document Type": d["document_type"],
                "Filename": d["filename"],
                "SHA-256 Hash": f"{d['sha256_hash'][:16]}...",
                "Size (Bytes)": d["file_size"],
                "Validation Status": run_d.get("status", "NOT_EVALUATED")
            })
        if cross_rows:
            st.dataframe(cross_rows, use_container_width=True)


def render_document_primary_assessments(doc: Dict[str, Any], user: Dict[str, Any], app_id: str):
    """Compatibility function."""
    pass


def render_application_cross_document_section(packet: Dict[str, Any], user: Dict[str, Any]):
    """Compatibility function."""
    pass


def render_applicant_feedback_panel(doc: Dict[str, Any]):
    """
    Renders simplified, plain-language institutional guidance for College Portal.
    No raw forensic JSON, internal hashes, stack traces, or implementation jargon.
    """
    run = doc.get("validation_run")
    if not run:
        return

    checks = run.get("checks", [])
    actionable_notes = []

    for c in checks:
        if c["status"] in ["FAIL", "WARNING", "REVIEW_REQUIRED"]:
            if c["check_id"] == "DOC_CATEGORY_FILENAME_MATCH" and c["status"] in ["FAIL", "WARNING"]:
                from core.validation.checks.content_rules import DOC_HUMAN_NAMES
                exp_doc = DOC_HUMAN_NAMES.get(doc['document_type'], doc['document_type'].replace('_', ' ').title())
                actionable_notes.append(
                    f"⚠️ **Document Mismatch:** The uploaded file `{doc['filename']}` does not match the expected statutory category `{exp_doc}`. Please replace with the correct document."
                )
            elif c["check_id"] == "TEXT_READABILITY_SCANNED_CHECK":
                actionable_notes.append("📄 **Scanned Document:** Please ensure institutional seals, signatures, and revenue marks are clearly legible for the Scrutiny Committee.")
            elif c["check_id"] in ["FILE_DUPLICATE_CHECK", "CROSS_DOC_DUPLICATE_FILES"]:
                actionable_notes.append("⚠️ **Duplicate Upload:** This file is identical to another uploaded certificate. Each mandatory requirement requires its own distinct statutory certificate.")
            elif c["check_id"] in ["PDF_ENCRYPTION_CHECK", "PDF_ENCRYPTION_PASSWORD"]:
                actionable_notes.append("🔒 **Password Protected:** Document is locked with a password. Please upload an unencrypted PDF copy.")
            elif c["check_id"] == "DOC_TYPE_CONTENT_MATCH" and c["status"] in ["FAIL", "WARNING"]:
                actionable_notes.append(f"📋 **Missing Information:** Ensure the uploaded document explicitly contains the required statutory terms for `{doc['document_type'].replace('_', ' ')}`.")
            elif c["check_id"] == "FILE_SIZE_LIMIT":
                actionable_notes.append("📦 **File Size Notice:** Document exceeds or approaches the permitted size limit (15 MB).")

    if actionable_notes:
        with st.container(border=True):
            st.markdown(f"**ℹ️ Submission Guidance for `{doc['filename']}`:**")
            for note in actionable_notes[:3]:
                st.markdown(note)
    else:
        st.caption("✅ Document uploaded successfully and in order.")

"""
Aegis Foundation - Acceptance Tests for Demo Scenarios A & B
Validates:
- Scenario A: Incorrect filename/category mismatch detected, concise finding displayed (Expected, Uploaded, Finding, Action), officer rejection/clarification with recorded reason.
- Scenario B: Correct documents uploaded under expected categories, clean verification (X/X uploaded, X/X matched, No document mismatches detected), officer download and approval with recorded justification.
- Preserves backend, authentication, multi-tenant security, SQLite DB, and audit logging.
"""

import os
import pytest
from core.db import seed_foundation, get_db
from core.auth import ApplicationService, AuthService
from core.validation.engine import ValidationEngine
from core.validation.schema import AssessmentState, CheckStatus
from core.audit import get_audit_events

TEST_DB = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_demo_scenarios.db"))
TEST_UPLOADS = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_demo_uploads"))


@pytest.fixture(autouse=True)
def setup_teardown():
    os.makedirs(TEST_UPLOADS, exist_ok=True)
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except PermissionError:
            pass
    seed_foundation(TEST_DB, force_reset=True)
    yield
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except PermissionError:
            pass


def _create_regulatory_pdf(title: str, text: str) -> bytes:
    import fitz
    doc = fitz.open()
    doc.set_metadata({
        "creator": "Government Directorate of Technical Education",
        "producer": "Aegis Statutory PDF Writer"
    })
    page = doc.new_page()
    full_text = f"""Apex Institute of Technology
Institution Code: APEX-MH-1001
Date of Issuance: 15/04/2026
Document: {title}

{text}
This is a verified statutory document issued to Apex Institute of Technology under AICTE norms.
"""
    page.insert_text((50, 72), full_text, fontsize=11)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_scenario_a_mismatched_documents_and_officer_rejection():
    """
    Scenario A:
    1. Log in as college representative.
    2. Create an application and upload documents with incorrect filenames or under the wrong document category.
    3. Submit the application.
    4. Log in to the scrutiny officer portal.
    5. Show that Aegis has identified the mismatch and flagged the specific document.
    6. The officer can see the filename, the expected document type, and a short explanation of the problem.
    7. The officer reviews the findings and rejects the application or requests clarification, with a recorded reason.
    """
    college_user = AuthService.authenticate("principal@apextech.edu", "ApexPrincipal@2026#Secure", expected_role="COLLEGE_REPRESENTATIVE", db_path=TEST_DB)
    assert college_user is not None

    officer_user = AuthService.authenticate("admin@aicte.gov.in", "AegisAdmin@2026#Secure", expected_role="AICTE_SCRUTINY_OFFICER", db_path=TEST_DB)
    assert officer_user is not None

    # Step 1: Create application
    app = ApplicationService.create_application(
        institution_id=college_user["institution_id"],
        category="NEW_TECHNICAL_INSTITUTION",
        academic_year="2026-2027",
        actor=college_user["email"],
        db_path=TEST_DB
    )
    app_id = app["id"]

    # Step 2: Upload mismatched file: 'Affiliation_Letter.pdf' under 'LAND_TITLE_CERTIFICATE'
    mismatched_pdf = _create_regulatory_pdf("University Affiliation Letter", "University Affiliation Letter for academic session 2026-2027 affiliated college courses")
    up_res = ApplicationService.upload_document(
        app_id=app_id,
        user=college_user,
        doc_type="LAND_TITLE_CERTIFICATE",
        filename="Affiliation_Letter.pdf",
        file_bytes=mismatched_pdf,
        uploads_dir=TEST_UPLOADS,
        db_path=TEST_DB
    )
    assert up_res["id"] is not None

    # Upload remaining 3 statutory documents to reach 100% completion
    companion_docs = [
        ("BUILDING_PLAN_APPROVAL", "building_plan_approval.pdf", "Municipal Corporation Sanctioned Building Plan Blueprint Architect Approved Layout built-up area approved floor plans"),
        ("AICTE_AFFIDAVIT_1", "aicte_affidavit_1.pdf", "AICTE Statutory Affidavit Deponent Notary Public Sworn Undertaking non-judicial stamp executed before executive magistrate"),
        ("FIRE_SAFETY_CERTIFICATE", "fire_safety_noc.pdf", "Fire Safety Certificate NOC Chief Fire Officer Emergency Station Prevention Inspection operational fire fighting measures")
    ]
    for dtype, fname, text in companion_docs:
        b = _create_regulatory_pdf(dtype, text)
        ApplicationService.upload_document(
            app_id=app_id,
            user=college_user,
            doc_type=dtype,
            filename=fname,
            file_bytes=b,
            uploads_dir=TEST_UPLOADS,
            db_path=TEST_DB
        )

    # Step 3: College submits application
    ApplicationService.submit_application(app_id, college_user, db_path=TEST_DB)

    # Step 4: Officer opens application in scrutiny portal
    packet = ApplicationService.get_application_details(app_id, officer_user, db_path=TEST_DB)
    assert packet["application"]["status"] == "SUBMITTED"
    val_summary = packet["validation_summary"]
    app_assessments = val_summary["app_assessments"]
    doc_verif = app_assessments["doc_verification"]
    actionable_findings = app_assessments["actionable_findings"]

    # Step 5: Verify mismatch is detected and formatted concisely
    assert doc_verif["uploaded_count"] == 4
    assert doc_verif["matched_count"] == 3
    assert doc_verif["mismatches_detected"] == 1
    assert "1 document needs attention" in doc_verif["result_text"]

    # Check the specific actionable finding format: Expected, Uploaded, Finding, Action
    assert len(actionable_findings) == 1
    mismatch_finding = actionable_findings[0]
    assert mismatch_finding["expected_document"] == "Land Title Certificate"
    assert "Affiliation_Letter.pdf" in mismatch_finding["uploaded_filename"]
    assert mismatch_finding["problem"] == "The uploaded filename/category does not match the expected document."
    assert mismatch_finding["action"] == "Review document"

    # Step 6: Officer reviews finding and records rejection with specific reason
    rejection_reason = "Application rejected due to statutory document mismatch: Affiliation Letter uploaded under Land Title requirement."
    ApplicationService.record_decision(app_id, officer_user, "REJECTED", notes=rejection_reason, db_path=TEST_DB)

    # Step 7: Verify application status and audit log
    updated_packet = ApplicationService.get_application_details(app_id, officer_user, db_path=TEST_DB)
    assert updated_packet["application"]["status"] == "REJECTED"
    assert updated_packet["application"]["notes"] == rejection_reason

    events = get_audit_events(db_path=TEST_DB)
    rej_event = next((e for e in events if e["event_type"] == "APPLICATION_REJECTED"), None)
    assert rej_event is not None
    assert rej_event["actor"] == officer_user["email"]
    assert rejection_reason in rej_event["details_json"]


def test_scenario_b_correct_documents_and_officer_approval():
    """
    Scenario B:
    1. Log in as college representative.
    2. Upload correct documents under their expected categories.
    3. Submit application.
    4. Officer sees concise result: X/X uploaded, X/X matched, No document mismatches detected.
    5. Officer downloads and inspects documents.
    6. Officer approves application and records decision in audit trail.
    """
    college_user = AuthService.authenticate("principal@apextech.edu", "ApexPrincipal@2026#Secure", expected_role="COLLEGE_REPRESENTATIVE", db_path=TEST_DB)
    officer_user = AuthService.authenticate("admin@aicte.gov.in", "AegisAdmin@2026#Secure", expected_role="AICTE_SCRUTINY_OFFICER", db_path=TEST_DB)

    # Step 1: Create application
    app = ApplicationService.create_application(
        institution_id=college_user["institution_id"],
        category="NEW_TECHNICAL_INSTITUTION",
        academic_year="2026-2027",
        actor=college_user["email"],
        db_path=TEST_DB
    )
    app_id = app["id"]

    # Step 2: Upload all 4 correct statutory documents
    doc_specs = [
        ("LAND_TITLE_CERTIFICATE", "land_title_deed.pdf", "Land Title Deed Survey Number 42 Patta Revenue Plot 15 Acres Registered conveyance deed ownership in possession"),
        ("BUILDING_PLAN_APPROVAL", "building_plan_approval.pdf", "Municipal Corporation Sanctioned Building Plan Blueprint Architect Approved Layout built-up area approved floor plans"),
        ("AICTE_AFFIDAVIT_1", "aicte_affidavit_1.pdf", "AICTE Statutory Affidavit Deponent Notary Public Sworn Undertaking non-judicial stamp executed before executive magistrate"),
        ("FIRE_SAFETY_CERTIFICATE", "fire_safety_noc.pdf", "Fire Safety Certificate NOC Chief Fire Officer Emergency Station Prevention Inspection operational fire fighting measures")
    ]

    for dtype, fname, text in doc_specs:
        pdf_bytes = _create_regulatory_pdf(dtype, text)
        ApplicationService.upload_document(
            app_id=app_id,
            user=college_user,
            doc_type=dtype,
            filename=fname,
            file_bytes=pdf_bytes,
            uploads_dir=TEST_UPLOADS,
            db_path=TEST_DB
        )

    # Step 3: College submits application
    ApplicationService.submit_application(app_id, college_user, db_path=TEST_DB)

    # Step 4: Officer opens application in scrutiny portal
    packet = ApplicationService.get_application_details(app_id, officer_user, db_path=TEST_DB)
    assert packet["application"]["status"] == "SUBMITTED"
    assert packet["completeness_pct"] == 100
    assert len(packet["missing_documents"]) == 0

    val_summary = packet["validation_summary"]
    app_assessments = val_summary["app_assessments"]
    doc_verif = app_assessments["doc_verification"]
    actionable_findings = app_assessments["actionable_findings"]

    # Step 5: Verify concise clean result
    assert doc_verif["uploaded_count"] == 4
    assert doc_verif["matched_count"] == 4
    assert doc_verif["mismatches_detected"] == 0
    assert doc_verif["result_text"] == "No document mismatches detected"
    assert len(actionable_findings) == 0

    # Step 6: Verify document downloadability
    for doc in packet["documents"]:
        assert os.path.exists(doc["stored_path"])
        with open(doc["stored_path"], "rb") as f:
            data = f.read()
            assert len(data) > 0

    # Step 7: Officer approves application with recorded remarks
    approval_remarks = "All statutory land, building, affidavit, and fire certificates verified and cleared."
    ApplicationService.record_decision(app_id, officer_user, "APPROVED", notes=approval_remarks, db_path=TEST_DB)

    # Step 8: Verify approval in application and audit trail
    final_packet = ApplicationService.get_application_details(app_id, officer_user, db_path=TEST_DB)
    assert final_packet["application"]["status"] == "APPROVED"
    assert final_packet["application"]["notes"] == approval_remarks

    events = get_audit_events(db_path=TEST_DB)
    appr_event = next((e for e in events if e["event_type"] == "APPLICATION_APPROVED"), None)
    assert appr_event is not None
    assert appr_event["actor"] == officer_user["email"]
    assert approval_remarks in appr_event["details_json"]

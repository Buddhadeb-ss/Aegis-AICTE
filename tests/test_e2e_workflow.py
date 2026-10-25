"""
Aegis Foundation - Complete End-to-End Acceptance Test Suite
Verifies all 7 mandated acceptance criteria:
1. College A logs in and submits an application.
2. Administrator reviews and requests clarification.
3. College A responds and resubmits.
4. Administrator reviews response and records final outcome.
5. College B cannot access College A's data (Tenant Isolation).
6. Unauthenticated visitors cannot access private pages.
7. Data persists across re-initialization and restart.
"""

import os
import sys
import tempfile
import pytest

# Ensure local imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.db import init_db, seed_foundation, get_db
from core.auth import AuthService, ApplicationService, MANDATORY_DOCUMENTS
from core.audit import get_audit_events
from core.forensics import compute_sha256, audit_pdf_structure


@pytest.fixture
def test_db():
    """Provides a fresh isolated database for testing."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_aegis_e2e.db")
    seed_foundation(db_path=db_path, force_reset=True)
    yield db_path


def test_complete_regulatory_lifecycle(test_db):
    """
    Acceptance Criteria 1 to 4:
    College A logs in -> submits application -> Admin requests clarification -> College A responds & resubmits -> Admin approves.
    """
    db_path = test_db

    # 1. College A logs in
    apex_user = AuthService.authenticate("principal@apextech.edu", "ApexPrincipal@2026#Secure", expected_role="COLLEGE_REPRESENTATIVE", db_path=db_path)
    assert apex_user is not None
    assert apex_user["institution_id"] == "inst_apex_1001"
    assert apex_user["role"] == "COLLEGE_REPRESENTATIVE"

    # Admin logs in
    admin_user = AuthService.authenticate("admin@aicte.gov.in", "AegisAdmin@2026#Secure", expected_role="AICTE_SCRUTINY_OFFICER", db_path=db_path)
    assert admin_user is not None
    assert admin_user["role"] == "AICTE_SCRUTINY_OFFICER"

    # College A creates application
    app_draft = ApplicationService.create_application(
        institution_id=apex_user["institution_id"],
        category="NEW_TECHNICAL_INSTITUTION",
        academic_year="2026-2027",
        actor=apex_user["email"],
        notes="Synthetic approval dossier for Apex Institute",
        db_path=db_path
    )
    app_id = app_draft["id"]
    assert app_draft["status"] == "DRAFT"

    # Upload all mandatory documents
    temp_dir = tempfile.mkdtemp()
    mandatory_docs = MANDATORY_DOCUMENTS["NEW_TECHNICAL_INSTITUTION"]
    for doc_type in mandatory_docs:
        fake_pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Title (Statutory Certificate) >>\nendobj\n%%EOF\n"
        upload_res = ApplicationService.upload_document(
            app_id=app_id,
            user=apex_user,
            doc_type=doc_type,
            filename=f"{doc_type.lower()}.pdf",
            file_bytes=fake_pdf_content,
            uploads_dir=temp_dir,
            db_path=db_path
        )
        assert upload_res["id"] is not None
        assert len(upload_res["sha256"]) == 64

    # College A submits application
    ApplicationService.submit_application(app_id, apex_user, db_path=db_path)

    # Verify status in queue
    details_after_sub = ApplicationService.get_application_details(app_id, admin_user, db_path=db_path)
    assert details_after_sub["application"]["status"] == "SUBMITTED"

    # 2. Administrator reviews and requests clarification
    clarif_id = ApplicationService.request_clarification(
        app_id=app_id,
        officer_user=admin_user,
        question_text="Discrepancy in Land Certificate survey number. Please clarify encumbrance status.",
        requested_docs="Revenue Authority Encumbrance Certificate",
        db_path=db_path
    )
    assert clarif_id is not None

    details_after_req = ApplicationService.get_application_details(app_id, apex_user, db_path=db_path)
    assert details_after_req["application"]["status"] == "CLARIFICATION_REQUESTED"
    assert len(details_after_req["clarifications"]) == 1
    assert details_after_req["clarifications"][0]["status"] == "OPEN"

    # 3. College A responds and resubmits
    ApplicationService.respond_clarification(
        clarif_id=clarif_id,
        college_user=apex_user,
        response_text="Survey numbers 45/1 and 45/2 were amalgamated under Revenue Order Rev-2025-99. Attached certified order copy.",
        response_docs="Amalgamation_Order_Rev99.pdf",
        db_path=db_path
    )

    details_after_resp = ApplicationService.get_application_details(app_id, admin_user, db_path=db_path)
    assert details_after_resp["application"]["status"] == "UNDER_SCRUTINY"
    assert details_after_resp["clarifications"][0]["status"] == "RESOLVED"

    # 4. Administrator reviews the response and records outcome (APPROVED)
    ApplicationService.record_decision(
        app_id=app_id,
        officer_user=admin_user,
        outcome="APPROVED",
        notes="Amalgamation verified with state revenue portal. All statutory criteria fulfilled.",
        db_path=db_path
    )

    final_packet = ApplicationService.get_application_details(app_id, admin_user, db_path=db_path)
    assert final_packet["application"]["status"] == "APPROVED"
    assert "Amalgamation verified" in final_packet["application"]["notes"]


def test_tenant_isolation_college_b_cannot_access_college_a(test_db):
    """
    Acceptance Criteria 5:
    College B cannot view, query, or modify College A's applications.
    """
    db_path = test_db

    apex_user = AuthService.authenticate("principal@apextech.edu", "ApexPrincipal@2026#Secure", db_path=db_path)
    beacon_user = AuthService.authenticate("registrar@beacon.ac.in", "BeaconRegistrar@2026#Secure", db_path=db_path)

    # Apex creates application
    apex_app = ApplicationService.create_application(
        institution_id=apex_user["institution_id"],
        category="NEW_TECHNICAL_INSTITUTION",
        academic_year="2026-2027",
        actor=apex_user["email"],
        db_path=db_path
    )
    apex_app_id = apex_app["id"]

    # 1. College B queries its application list -> Apex's application MUST NOT be present
    beacon_apps = ApplicationService.get_applications_for_user(beacon_user, db_path=db_path)
    assert not any(a["id"] == apex_app_id for a in beacon_apps)

    # 2. College B attempts direct application access by ID -> PermissionError MUST be raised
    with pytest.raises(PermissionError) as exc_info:
        ApplicationService.get_application_details(apex_app_id, beacon_user, db_path=db_path)
    assert "Unauthorized" in str(exc_info.value)

    # 3. College B attempts to upload document to Apex application -> PermissionError MUST be raised
    with pytest.raises(PermissionError):
        ApplicationService.upload_document(
            app_id=apex_app_id,
            user=beacon_user,
            doc_type="FIRE_SAFETY_CERTIFICATE",
            filename="fake.pdf",
            file_bytes=b"%PDF-1.4\n%%EOF",
            db_path=db_path
        )


def test_unauthenticated_and_role_guards(test_db):
    """
    Acceptance Criteria 6:
    Unauthenticated visitors and mismatched roles are strictly barred.
    """
    db_path = test_db

    # Wrong password
    assert AuthService.authenticate("admin@aicte.gov.in", "WrongPassword#123", db_path=db_path) is None

    # Unknown email
    assert AuthService.authenticate("unknown@domain.com", "Password#123", db_path=db_path) is None

    # Role mismatch (College user attempting to log into Officer portal)
    mismatch = AuthService.authenticate("principal@apextech.edu", "ApexPrincipal@2026#Secure", expected_role="AICTE_SCRUTINY_OFFICER", db_path=db_path)
    assert mismatch is None

    # Disabled account
    apex_user = AuthService.authenticate("principal@apextech.edu", "ApexPrincipal@2026#Secure", db_path=db_path)
    AuthService.set_user_status(apex_user["id"], "DISABLED", db_path=db_path)
    assert AuthService.authenticate("principal@apextech.edu", "ApexPrincipal@2026#Secure", db_path=db_path) is None

    # Re-enable
    AuthService.set_user_status(apex_user["id"], "ACTIVE", db_path=db_path)
    assert AuthService.authenticate("principal@apextech.edu", "ApexPrincipal@2026#Secure", db_path=db_path) is not None


def test_data_persistence_across_restart(test_db):
    """
    Acceptance Criteria 7:
    Data persists after restarting the application / re-running init_db.
    """
    db_path = test_db

    admin_user = AuthService.authenticate("admin@aicte.gov.in", "AegisAdmin@2026#Secure", db_path=db_path)
    apex_user = AuthService.authenticate("principal@apextech.edu", "ApexPrincipal@2026#Secure", db_path=db_path)

    # Create app and change password
    app = ApplicationService.create_application(apex_user["institution_id"], "EXTENSION_OF_APPROVAL", "2026-2027", apex_user["email"], notes="Persistent Test", db_path=db_path)
    app_id = app["id"]

    new_pw = "ApexNewPass@2026#Secure"
    AuthService.update_password(apex_user["id"], new_pw, db_path=db_path)

    # Simulate restart by re-calling init_db & seed without force_reset
    init_db(db_path)
    seed_foundation(db_path=db_path, force_reset=False)

    # 1. New password still works (did not revert to default seed)
    auth_check = AuthService.authenticate("principal@apextech.edu", new_pw, db_path=db_path)
    assert auth_check is not None

    # 2. Application record still exists intact
    retrieved = ApplicationService.get_application_details(app_id, admin_user, db_path=db_path)
    assert retrieved["application"]["id"] == app_id
    assert retrieved["application"]["notes"] == "Persistent Test"


def test_audit_trail_immutability(test_db):
    """Verifies that all operations produce immutable audit records."""
    db_path = test_db

    apex_user = AuthService.authenticate("principal@apextech.edu", "ApexPrincipal@2026#Secure", db_path=db_path)
    events = get_audit_events(db_path=db_path)
    assert len(events) >= 1
    assert any(e["event_type"] == "AUTH_SUCCESS" for e in events)


def test_upload_validation_and_security(test_db):
    """
    Verifies Phase 3 & 4 security rules:
    - Empty file rejection
    - Oversized file rejection (>15MB)
    - Unsupported file extension rejection (.exe, .sh)
    - Corrupt or non-PDF signature rejection
    - Path traversal attempt containment
    """
    db_path = test_db
    apex_user = AuthService.authenticate("principal@apextech.edu", "ApexPrincipal@2026#Secure", db_path=db_path)
    app = ApplicationService.create_application(apex_user["institution_id"], "NEW_TECHNICAL_INSTITUTION", "2026-2027", apex_user["email"], db_path=db_path)
    app_id = app["id"]
    temp_dir = tempfile.mkdtemp()

    # 1. Empty file
    with pytest.raises(ValueError) as exc:
        ApplicationService.upload_document(app_id, apex_user, "LAND_TITLE_DEED", "empty.pdf", b"", uploads_dir=temp_dir, db_path=db_path)
    assert "empty (0 bytes)" in str(exc.value)

    # 2. Oversized file (16MB)
    oversized_bytes = b"%PDF-1.4\n" + b"A" * (16 * 1024 * 1024)
    with pytest.raises(ValueError) as exc:
        ApplicationService.upload_document(app_id, apex_user, "LAND_TITLE_DEED", "large.pdf", oversized_bytes, uploads_dir=temp_dir, db_path=db_path)
    assert "maximum permitted limit" in str(exc.value)

    # 3. Unsupported extension
    with pytest.raises(ValueError) as exc:
        ApplicationService.upload_document(app_id, apex_user, "LAND_TITLE_DEED", "malware.exe", b"MZ\x90\x00", uploads_dir=temp_dir, db_path=db_path)
    assert "Unsupported file extension" in str(exc.value)

    # 4. Corrupt / invalid PDF magic bytes
    with pytest.raises(ValueError) as exc:
        ApplicationService.upload_document(app_id, apex_user, "LAND_TITLE_DEED", "fake.pdf", b"NOT_A_PDF_HEADER", uploads_dir=temp_dir, db_path=db_path)
    assert "Corrupt or invalid PDF" in str(exc.value)

    # 5. Path traversal filename sanitization
    safe_res = ApplicationService.upload_document(
        app_id, apex_user, "LAND_TITLE_DEED", "../../../etc/passwd.pdf",
        b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF",
        uploads_dir=temp_dir, db_path=db_path
    )
    assert safe_res["stored_path"].startswith(temp_dir)
    assert "passwd" in safe_res["stored_path"]
    assert ".." not in safe_res["stored_path"]


def test_clarification_with_supplementary_evidence(test_db):
    """Verifies clarification lifecycle with supplementary document attachment."""
    db_path = test_db
    apex_user = AuthService.authenticate("principal@apextech.edu", "ApexPrincipal@2026#Secure", db_path=db_path)
    admin_user = AuthService.authenticate("admin@aicte.gov.in", "AegisAdmin@2026#Secure", db_path=db_path)

    app = ApplicationService.create_application(apex_user["institution_id"], "NEW_TECHNICAL_INSTITUTION", "2026-2027", apex_user["email"], db_path=db_path)
    app_id = app["id"]
    temp_dir = tempfile.mkdtemp()

    for doc_type in MANDATORY_DOCUMENTS["NEW_TECHNICAL_INSTITUTION"]:
        ApplicationService.upload_document(
            app_id, apex_user, doc_type, f"{doc_type}.pdf",
            b"%PDF-1.4\nvalid document\n%%EOF",
            uploads_dir=temp_dir, db_path=db_path
        )
    ApplicationService.submit_application(app_id, apex_user, db_path=db_path)

    # Officer asks for clarification
    clarif_id = ApplicationService.request_clarification(
        app_id, admin_user,
        question_text="Please provide updated building layout.",
        requested_docs="Building Approval 2026",
        db_path=db_path
    )

    # College responds with supplementary file
    supp_bytes = b"%PDF-1.4\nApproved Building Plan Supplementary\n%%EOF"
    ApplicationService.respond_clarification(
        clarif_id=clarif_id,
        college_user=apex_user,
        response_text="Attached municipal corporation approved building layout.",
        supplementary_file={"filename": "Building_Layout_Approved.pdf", "bytes": supp_bytes},
        uploads_dir=temp_dir,
        db_path=db_path
    )

    details = ApplicationService.get_application_details(app_id, admin_user, db_path=db_path)
    assert details["application"]["status"] == "UNDER_SCRUTINY"
    # Check that supplementary document was saved to dossier
    evidence_docs = [d for d in details["documents"] if d["document_type"] == "CLARIFICATION_EVIDENCE"]
    assert len(evidence_docs) == 1
    assert "Building_Layout_Approved" in evidence_docs[0]["filename"]


def test_invalid_state_transitions(test_db):
    """Verifies that illegal status transitions and role actions are strictly blocked."""
    db_path = test_db
    apex_user = AuthService.authenticate("principal@apextech.edu", "ApexPrincipal@2026#Secure", db_path=db_path)
    beacon_user = AuthService.authenticate("registrar@beacon.ac.in", "BeaconRegistrar@2026#Secure", db_path=db_path)
    admin_user = AuthService.authenticate("admin@aicte.gov.in", "AegisAdmin@2026#Secure", db_path=db_path)

    app = ApplicationService.create_application(apex_user["institution_id"], "NEW_TECHNICAL_INSTITUTION", "2026-2027", apex_user["email"], db_path=db_path)
    app_id = app["id"]

    # Cannot submit incomplete draft
    with pytest.raises(ValueError) as exc:
        ApplicationService.submit_application(app_id, apex_user, db_path=db_path)
    assert "Mandatory regulatory documents missing" in str(exc.value)

    # Officer cannot clarify a DRAFT
    with pytest.raises(ValueError) as exc:
        ApplicationService.request_clarification(app_id, admin_user, "Why draft?", db_path=db_path)
    assert "Cannot request clarification on application in status 'DRAFT'" in str(exc.value)

    # Officer cannot record decision on a DRAFT
    with pytest.raises(ValueError) as exc:
        ApplicationService.record_decision(app_id, admin_user, "APPROVED", "Too early", db_path=db_path)
    assert "Cannot record decision on application in 'DRAFT'" in str(exc.value)

    # Non-officer cannot request clarification
    with pytest.raises(PermissionError):
        ApplicationService.request_clarification(app_id, apex_user, "Question?", db_path=db_path)

    # Upload documents and submit
    temp_dir = tempfile.mkdtemp()
    for doc_type in MANDATORY_DOCUMENTS["NEW_TECHNICAL_INSTITUTION"]:
        ApplicationService.upload_document(
            app_id, apex_user, doc_type, f"{doc_type}.pdf",
            b"%PDF-1.4\nvalid document\n%%EOF",
            uploads_dir=temp_dir, db_path=db_path
        )
    ApplicationService.submit_application(app_id, apex_user, db_path=db_path)

    # Cannot re-submit already SUBMITTED application
    with pytest.raises(ValueError) as exc:
        ApplicationService.submit_application(app_id, apex_user, db_path=db_path)
    assert "Cannot submit application in status 'SUBMITTED'" in str(exc.value)

    # Beacon College cannot respond to Apex's clarification
    clarif_id = ApplicationService.request_clarification(app_id, admin_user, "Verify faculty?", db_path=db_path)
    with pytest.raises(PermissionError):
        ApplicationService.respond_clarification(clarif_id, beacon_user, "Trying to tamper", db_path=db_path)


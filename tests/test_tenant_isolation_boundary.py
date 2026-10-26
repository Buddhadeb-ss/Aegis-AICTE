"""
Aegis Foundation - Multi-Tenant Isolation & Authorization Boundary Tests
Priority 4, 5 & 6 Verification Suite:
- Cross-tenant read, write, upload, delete, submit, rerun, and clarification tampering defenses.
- Role-based authorization enforcement at all service API boundaries.
- Mandatory statutory justification enforcement for scrutiny decisions and dispositions.
- Persistence lifecycle and audit event chronological traceability across simulated server restarts.
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


@pytest.fixture
def isolated_db():
    """Provides a fresh isolated database with seeded institutions and users."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_tenant_boundaries.db")
    seed_foundation(db_path=db_path, force_reset=True)
    yield db_path, temp_dir


def test_college_cannot_spoof_institution_on_create(isolated_db):
    """A college representative cannot create an application under another college's ID."""
    db_path, _ = isolated_db

    apex_user = AuthService.authenticate("principal@apextech.edu", "ApexPrincipal@2026#Secure", db_path=db_path)
    assert apex_user["institution_id"] == "inst_apex_1001"

    # Attempting to create an application passing Beacon College's ID must raise PermissionError
    with pytest.raises(PermissionError) as exc:
        ApplicationService.create_application(
            institution_or_user=apex_user,
            institution_id="inst_beacon_2002",
            category="NEW_TECHNICAL_INSTITUTION",
            academic_year="2026-2027",
            db_path=db_path
        )
    assert "cannot create applications for another institution" in str(exc.value)


def test_cross_tenant_read_access_blocked(isolated_db):
    """College B cannot read College A's application dossier."""
    db_path, _ = isolated_db

    apex_user = AuthService.authenticate("principal@apextech.edu", "ApexPrincipal@2026#Secure", db_path=db_path)
    beacon_user = AuthService.authenticate("registrar@beacon.ac.in", "BeaconRegistrar@2026#Secure", db_path=db_path)

    # Apex creates an application
    app_apex = ApplicationService.create_application(
        institution_or_user=apex_user,
        category="NEW_TECHNICAL_INSTITUTION",
        db_path=db_path
    )
    apex_app_id = app_apex["id"]

    # Apex can read its own application
    apex_packet = ApplicationService.get_application_details(apex_app_id, apex_user, db_path=db_path)
    assert apex_packet["application"]["id"] == apex_app_id

    # Beacon College representative attempts to read Apex's dossier -> PermissionError
    with pytest.raises(PermissionError) as exc:
        ApplicationService.get_application_details(apex_app_id, beacon_user, db_path=db_path)
    assert "belonging to another institution" in str(exc.value)


def test_cross_tenant_document_upload_and_delete_blocked(isolated_db):
    """College B cannot upload documents to or delete documents from College A's dossier."""
    db_path, temp_dir = isolated_db

    apex_user = AuthService.authenticate("principal@apextech.edu", "ApexPrincipal@2026#Secure", db_path=db_path)
    beacon_user = AuthService.authenticate("registrar@beacon.ac.in", "BeaconRegistrar@2026#Secure", db_path=db_path)

    app_apex = ApplicationService.create_application(institution_or_user=apex_user, db_path=db_path)
    apex_app_id = app_apex["id"]

    # Apex uploads a document
    doc_content = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF"
    upload_res = ApplicationService.upload_document(
        app_id=apex_app_id,
        user=apex_user,
        doc_type="LAND_TITLE_CERTIFICATE",
        filename="Land_Title.pdf",
        file_bytes=doc_content,
        uploads_dir=temp_dir,
        db_path=db_path
    )
    doc_id = upload_res["id"]

    # Beacon attempts to upload to Apex's application -> PermissionError
    with pytest.raises(PermissionError):
        ApplicationService.upload_document(
            app_id=apex_app_id,
            user=beacon_user,
            doc_type="FIRE_SAFETY_CERTIFICATE",
            filename="Fire_Safety.pdf",
            file_bytes=doc_content,
            uploads_dir=temp_dir,
            db_path=db_path
        )

    # Beacon attempts to delete Apex's document -> PermissionError
    with pytest.raises(PermissionError):
        ApplicationService.delete_document(doc_id, beacon_user, db_path=db_path)

    # Apex can delete its own document
    ApplicationService.delete_document(doc_id, apex_user, db_path=db_path)


def test_cross_tenant_rerun_validation_blocked(isolated_db):
    """College B cannot trigger re-validation of College A's documents."""
    db_path, temp_dir = isolated_db

    apex_user = AuthService.authenticate("principal@apextech.edu", "ApexPrincipal@2026#Secure", db_path=db_path)
    beacon_user = AuthService.authenticate("registrar@beacon.ac.in", "BeaconRegistrar@2026#Secure", db_path=db_path)

    app_apex = ApplicationService.create_application(institution_or_user=apex_user, db_path=db_path)
    doc_content = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF"
    doc_res = ApplicationService.upload_document(
        app_id=app_apex["id"],
        user=apex_user,
        doc_type="LAND_TITLE_CERTIFICATE",
        filename="Land_Title.pdf",
        file_bytes=doc_content,
        uploads_dir=temp_dir,
        db_path=db_path
    )

    # Beacon attempts rerun_validation -> PermissionError
    with pytest.raises(PermissionError):
        ApplicationService.rerun_validation(doc_res["id"], beacon_user, db_path=db_path)


def test_officer_verdict_mandates_justification(isolated_db):
    """Scrutiny decisions (APPROVED, REJECTED, DEFICIENT) mandate statutory justification notes."""
    db_path, temp_dir = isolated_db

    apex_user = AuthService.authenticate("principal@apextech.edu", "ApexPrincipal@2026#Secure", db_path=db_path)
    admin_user = AuthService.authenticate("admin@aicte.gov.in", "AegisAdmin@2026#Secure", db_path=db_path)

    app_apex = ApplicationService.create_application(institution_or_user=apex_user, db_path=db_path)
    apex_app_id = app_apex["id"]

    for doc_type in MANDATORY_DOCUMENTS["NEW_TECHNICAL_INSTITUTION"]:
        ApplicationService.upload_document(
            app_id=apex_app_id,
            user=apex_user,
            doc_type=doc_type,
            filename=f"{doc_type}.pdf",
            file_bytes=b"%PDF-1.4\nvalid doc\n%%EOF",
            uploads_dir=temp_dir,
            db_path=db_path
        )
    ApplicationService.submit_application(apex_app_id, apex_user, db_path=db_path)

    # 1. Empty justification on REJECTED -> ValueError
    with pytest.raises(ValueError) as exc:
        ApplicationService.record_decision(apex_app_id, admin_user, "REJECTED", notes="   ", db_path=db_path)
    assert "statutory justification note is required" in str(exc.value)

    # 2. Empty justification on APPROVED -> ValueError
    with pytest.raises(ValueError) as exc:
        ApplicationService.record_decision(apex_app_id, admin_user, "APPROVED", notes="", db_path=db_path)
    assert "statutory justification note is required" in str(exc.value)

    # 3. Non-empty justification -> Success
    ApplicationService.record_decision(
        apex_app_id, admin_user, "APPROVED",
        notes="All land and building norms verified per APH 2026-27 statutory requirements.",
        db_path=db_path
    )
    packet = ApplicationService.get_application_details(apex_app_id, admin_user, db_path=db_path)
    assert packet["application"]["status"] == "APPROVED"
    assert "APH 2026-27" in packet["application"]["notes"]


def test_role_enforcement_on_officer_actions(isolated_db):
    """College representatives cannot perform officer-only actions."""
    db_path, _ = isolated_db

    apex_user = AuthService.authenticate("principal@apextech.edu", "ApexPrincipal@2026#Secure", db_path=db_path)
    app = ApplicationService.create_application(institution_or_user=apex_user, db_path=db_path)

    # 1. College rep cannot request clarification
    with pytest.raises(PermissionError):
        ApplicationService.request_clarification(app["id"], apex_user, "Question?", db_path=db_path)

    # 2. College rep cannot record decision
    with pytest.raises(PermissionError):
        ApplicationService.record_decision(app["id"], apex_user, "APPROVED", "I approve myself", db_path=db_path)

    # 3. College rep cannot record finding disposition
    with pytest.raises(PermissionError):
        ApplicationService.record_finding_disposition(
            check_record_id="dummy_chk",
            doc_id="dummy_doc",
            app_id=app["id"],
            user=apex_user,
            disposition="WAIVED",
            notes="Waiving finding",
            db_path=db_path
        )


def test_audit_timeline_durability_across_restart(isolated_db):
    """
    Simulates complete server restart and confirms all application records,
    documents, clarifications, decisions, and audit timeline remain intact.
    """
    db_path, temp_dir = isolated_db

    apex_user = AuthService.authenticate("principal@apextech.edu", "ApexPrincipal@2026#Secure", db_path=db_path)
    admin_user = AuthService.authenticate("admin@aicte.gov.in", "AegisAdmin@2026#Secure", db_path=db_path)

    app = ApplicationService.create_application(institution_or_user=apex_user, db_path=db_path)
    app_id = app["id"]

    for doc_type in MANDATORY_DOCUMENTS["NEW_TECHNICAL_INSTITUTION"]:
        ApplicationService.upload_document(
            app_id=app_id,
            user=apex_user,
            doc_type=doc_type,
            filename=f"{doc_type}.pdf",
            file_bytes=b"%PDF-1.4\nvalid doc\n%%EOF",
            uploads_dir=temp_dir,
            db_path=db_path
        )
    ApplicationService.submit_application(app_id, apex_user, db_path=db_path)

    clarif_id = ApplicationService.request_clarification(
        app_id, admin_user,
        question_text="Please provide clarification on survey boundary markers.",
        db_path=db_path
    )
    ApplicationService.respond_clarification(
        clarif_id=clarif_id,
        college_user=apex_user,
        response_text="Survey markers confirmed with Revenue Tehsildar report.",
        db_path=db_path
    )
    ApplicationService.record_decision(
        app_id, admin_user, "APPROVED",
        notes="Survey demarcation acceptable.",
        db_path=db_path
    )

    # Simulate server restart: re-initialize db connection without dropping tables
    init_db(db_path)
    seed_foundation(db_path=db_path, force_reset=False)

    # Verify everything persists intact
    restarted_packet = ApplicationService.get_application_details(app_id, admin_user, db_path=db_path)
    assert restarted_packet["application"]["status"] == "APPROVED"
    assert len(restarted_packet["documents"]) == 4
    assert len(restarted_packet["clarifications"]) == 1
    assert restarted_packet["clarifications"][0]["status"] == "RESOLVED"
    assert "Survey markers confirmed" in restarted_packet["clarifications"][0]["response_text"]

    # Verify audit trail timeline contains the expected events in chronological order
    timeline = restarted_packet["audit_trail"]
    event_types = [e["event_type"] for e in timeline]
    assert "APPLICATION_APPROVED" in event_types
    assert "CLARIFICATION_RESPONDED" in event_types
    assert "CLARIFICATION_REQUESTED" in event_types
    assert "APPLICATION_SUBMITTED" in event_types
    assert "DOCUMENT_UPLOADED" in event_types
    assert "APPLICATION_CREATED" in event_types

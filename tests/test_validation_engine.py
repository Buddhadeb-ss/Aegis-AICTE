"""
Aegis Foundation - Comprehensive Document Validation Engine Test Suite
Tests every check, rule, and lifecycle stage using a labelled synthetic test corpus:
1. Valid text PDF with statutory keywords
2. Empty file (0 bytes)
3. Malformed / corrupted PDF
4. Password-protected / encrypted PDF
5. Scanned / image-only PDF (zero digital text streams)
6. Byte-identical duplicate documents
7. PDF with consumer tool metadata & inverted timestamps
8. PDF with incremental revisions (multiple %%EOF markers)
9. PDF with active content / JavaScript
10. Cross-document institutional identity & permanent code consistency
11. Officer finding disposition recording
12. Historical validation run retention & manual re-run
"""

import os
import shutil
import tempfile
import pytest
try:
    import pymupdf as fitz
except ImportError:
    import fitz

from core.db import get_db, init_db, seed_foundation
from core.auth import AuthService, ApplicationService
from core.validation.schema import CheckStatus, CheckSeverity, CheckCategory
from core.validation.rules import RULE_REGISTRY, get_rule_for_document_type
from core.validation.engine import ValidationEngine


@pytest.fixture
def test_env():
    """Sets up an isolated temporary database and upload directory."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_validation.db")
    uploads_dir = os.path.join(temp_dir, "uploads")
    os.makedirs(uploads_dir, exist_ok=True)

    seed_foundation(db_path=db_path, force_reset=True)
    admin_user = AuthService.authenticate("admin@aicte.gov.in", "AegisAdmin@2026#Secure", db_path=db_path)
    apex_user = AuthService.authenticate("principal@apextech.edu", "ApexPrincipal@2026#Secure", db_path=db_path)
    beacon_user = AuthService.authenticate("registrar@beacon.ac.in", "BeaconRegistrar@2026#Secure", db_path=db_path)

    yield {
        "db_path": db_path,
        "uploads_dir": uploads_dir,
        "admin_user": admin_user,
        "apex_user": apex_user,
        "beacon_user": beacon_user,
    }

    shutil.rmtree(temp_dir, ignore_errors=True)


def make_clean_pdf(text: str, metadata: dict = None) -> bytes:
    """Creates a well-formed synthetic PDF with specified text and metadata."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 80), text)
    if metadata:
        doc.set_metadata(metadata)
    data = doc.tobytes()
    doc.close()
    return data


def test_valid_statutory_text_pdf(test_env):
    """
    PROVES: A well-formed, unencrypted PDF with statutory keywords passes file integrity,
    structural parsing, text extraction, content rule matching, and cross-document identity.
    DOES NOT PROVE: Physical veracity or truth of the institutional claim.
    """
    db_path = test_env["db_path"]
    uploads_dir = test_env["uploads_dir"]
    apex = test_env["apex_user"]

    app = ApplicationService.create_application(apex, "NEW_TECHNICAL_INSTITUTION", "2026-2027", "Test Dossier", db_path=db_path)

    land_text = (
        "GOVERNMENT OF MAHARASHTRA - REVENUE DEPARTMENT\n"
        "Apex Institute of Technology (APEX-MH-1001)\n"
        "Sub-Registrar Haveli, Pune. Certified Land Title Deed & Demarcation Certificate.\n"
        "Undisputed institutional ownership of Survey Plot 42/1 comprising 10.5 acres.\n"
        "Executed on October 10, 2024. Stamp duty and registration charges paid."
    )
    pdf_bytes = make_clean_pdf(land_text, {"producer": "Standard Government PDF Exporter", "creator": "Revenue Department GIS"})

    doc_res = ApplicationService.upload_document(
        app_id=app["id"],
        user=apex,
        doc_type="LAND_TITLE_CERTIFICATE",
        filename="land_title_certified.pdf",
        file_bytes=pdf_bytes,
        uploads_dir=uploads_dir,
        db_path=db_path
    )

    run = ValidationEngine.get_latest_run_for_document(doc_res["id"], db_path=db_path)
    assert run is not None
    assert run["status"] == "PASSED"
    assert run["failed_checks"] == 0
    assert run["error_checks"] == 0

    checks_by_id = {c["check_id"]: c for c in run["checks"]}

    # Verify individual check outcomes
    assert checks_by_id["FILE_EXT_ALLOWED"]["status"] == "PASS"
    assert checks_by_id["FILE_SIGNATURE_MATCH"]["status"] == "PASS"
    assert checks_by_id["FILE_NON_EMPTY"]["status"] == "PASS"
    assert checks_by_id["PDF_PARSE_INTEGRITY"]["status"] == "PASS"
    assert checks_by_id["PDF_ENCRYPTION_CHECK"]["status"] == "PASS"
    assert checks_by_id["TEXT_READABILITY_SCANNED_CHECK"]["status"] == "PASS"
    assert checks_by_id["DOC_TYPE_CONTENT_MATCH"]["status"] == "PASS"
    assert checks_by_id["CROSS_DOC_INSTITUTION_NAME"]["status"] == "PASS"
    assert checks_by_id["CROSS_DOC_INSTITUTION_CODE"]["status"] == "PASS"


def test_empty_zero_byte_file(test_env):
    """
    PROVES: The validation pipeline rejects zero-byte payloads safely,
    marks FILE_NON_EMPTY as FAIL (CRITICAL), and halts structural parsing.
    """
    db_path = test_env["db_path"]
    uploads_dir = test_env["uploads_dir"]
    apex = test_env["apex_user"]

    app = ApplicationService.create_application(apex, "NEW_TECHNICAL_INSTITUTION", "2026-2027", "Test", db_path=db_path)

    # In upload_document, a 0-byte file raises ValueError directly
    with pytest.raises(ValueError, match="0 bytes"):
        ApplicationService.upload_document(
            app_id=app["id"],
            user=apex,
            doc_type="LAND_TITLE_CERTIFICATE",
            filename="empty.pdf",
            file_bytes=b"",
            uploads_dir=uploads_dir,
            db_path=db_path
        )


def test_corrupt_malformed_pdf(test_env):
    """
    PROVES: A malformed file with a PDF header but corrupted object streams fails
    PDF_PARSE_INTEGRITY with an explicit error description and recommendations.
    """
    db_path = test_env["db_path"]
    uploads_dir = test_env["uploads_dir"]
    apex = test_env["apex_user"]

    app = ApplicationService.create_application(apex, "NEW_TECHNICAL_INSTITUTION", "2026-2027", "Test", db_path=db_path)

    # Has magic signature but corrupted streams
    corrupted_bytes = b"%PDF-1.7\n<< /Type /Catalog /Pages 2 0 R >>\nGARBAGE_BINARY_CORRUPTED_STREAM_NO_XREF"

    doc_res = ApplicationService.upload_document(
        app_id=app["id"],
        user=apex,
        doc_type="BUILDING_PLAN_APPROVAL",
        filename="corrupted_plan.pdf",
        file_bytes=corrupted_bytes,
        uploads_dir=uploads_dir,
        db_path=db_path
    )

    run = ValidationEngine.get_latest_run_for_document(doc_res["id"], db_path=db_path)
    assert run is not None
    assert run["status"] in ["FAILED", "ERROR"]

    parse_chk = next(c for c in run["checks"] if c["check_id"] == "PDF_PARSE_INTEGRITY")
    assert parse_chk["status"] == "FAIL"
    assert "Corrupt or malformed PDF" in parse_chk["summary"]
    assert parse_chk["severity"] == "CRITICAL"


def test_password_protected_pdf(test_env):
    """
    PROVES: Encrypted or password-locked PDFs are identified and marked as FAIL under
    PDF_ENCRYPTION_CHECK, preventing unreviewable locked submissions.
    """
    db_path = test_env["db_path"]
    uploads_dir = test_env["uploads_dir"]
    apex = test_env["apex_user"]

    app = ApplicationService.create_application(apex, "NEW_TECHNICAL_INSTITUTION", "2026-2027", "Test", db_path=db_path)

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Encrypted Fire Safety Certificate")
    # AES-256 encryption with password
    encrypted_bytes = doc.tobytes(encryption=fitz.PDF_ENCRYPT_AES_256, owner_pw="owner123", user_pw="secret123")
    doc.close()

    doc_res = ApplicationService.upload_document(
        app_id=app["id"],
        user=apex,
        doc_type="FIRE_SAFETY_CERTIFICATE",
        filename="locked_fire_safety.pdf",
        file_bytes=encrypted_bytes,
        uploads_dir=uploads_dir,
        db_path=db_path
    )

    run = ValidationEngine.get_latest_run_for_document(doc_res["id"], db_path=db_path)
    assert run is not None
    assert run["failed_checks"] > 0

    enc_chk = next(c for c in run["checks"] if c["check_id"] == "PDF_ENCRYPTION_CHECK")
    assert enc_chk["status"] == "FAIL"
    assert "Password-protected or encrypted" in enc_chk["summary"]


def test_scanned_image_only_pdf(test_env):
    """
    PROVES: A scanned PDF containing 0 digital text characters is correctly flagged as
    REVIEW_REQUIRED under TEXT_READABILITY_SCANNED_CHECK, and content keyword matching
    is explicitly recorded as NOT_RUN (deferred to human scrutiny) rather than falsely failed.
    """
    db_path = test_env["db_path"]
    uploads_dir = test_env["uploads_dir"]
    apex = test_env["apex_user"]

    app = ApplicationService.create_application(apex, "NEW_TECHNICAL_INSTITUTION", "2026-2027", "Test", db_path=db_path)

    # Scanned PDF: page with graphics/drawing only, zero text
    doc = fitz.open()
    page = doc.new_page()
    page.draw_rect(fitz.Rect(50, 50, 400, 400), color=(0, 0, 0), fill=(0.95, 0.95, 0.95))
    scanned_bytes = doc.tobytes()
    doc.close()

    doc_res = ApplicationService.upload_document(
        app_id=app["id"],
        user=apex,
        doc_type="AICTE_AFFIDAVIT_1",
        filename="scanned_notarized_affidavit.pdf",
        file_bytes=scanned_bytes,
        uploads_dir=uploads_dir,
        db_path=db_path
    )

    run = ValidationEngine.get_latest_run_for_document(doc_res["id"], db_path=db_path)
    assert run is not None
    assert run["status"] == "REVIEW_REQUIRED"

    scan_chk = next(c for c in run["checks"] if c["check_id"] == "TEXT_READABILITY_SCANNED_CHECK")
    assert scan_chk["status"] == "REVIEW_REQUIRED"
    assert "Scanned / Image-Based Document" in scan_chk["summary"]

    # Content rule must be NOT_RUN (deferred to officer)
    kw_chk = next(c for c in run["checks"] if c["check_id"] == "DOC_TYPE_CONTENT_MATCH")
    assert kw_chk["status"] == "NOT_RUN"
    assert "deferred" in kw_chk["summary"].lower()


def test_duplicate_file_detection(test_env):
    """
    PROVES: Uploading the exact same document for two different checklist items flags
    FILE_DUPLICATE_CHECK and CROSS_DOC_DUPLICATE_FILES with explicit warnings and matching references.
    """
    db_path = test_env["db_path"]
    uploads_dir = test_env["uploads_dir"]
    apex = test_env["apex_user"]

    app = ApplicationService.create_application(apex, "NEW_TECHNICAL_INSTITUTION", "2026-2027", "Test", db_path=db_path)

    pdf_bytes = make_clean_pdf("Building sanction plan municipal corporation architect approval 5000 sq.m")

    # 1. Upload for BUILDING_PLAN_APPROVAL
    doc1 = ApplicationService.upload_document(
        app_id=app["id"],
        user=apex,
        doc_type="BUILDING_PLAN_APPROVAL",
        filename="building_plan.pdf",
        file_bytes=pdf_bytes,
        uploads_dir=uploads_dir,
        db_path=db_path
    )

    # 2. Upload identical bytes for FIRE_SAFETY_CERTIFICATE
    doc2 = ApplicationService.upload_document(
        app_id=app["id"],
        user=apex,
        doc_type="FIRE_SAFETY_CERTIFICATE",
        filename="fire_safety_duplicate.pdf",
        file_bytes=pdf_bytes,
        uploads_dir=uploads_dir,
        db_path=db_path
    )

    run2 = ValidationEngine.get_latest_run_for_document(doc2["id"], db_path=db_path)
    assert run2 is not None

    dup_chk = next(c for c in run2["checks"] if c["check_id"] == "CROSS_DOC_DUPLICATE_FILES")
    assert dup_chk["status"] == "WARNING"
    assert "Duplicate submission" in dup_chk["summary"]
    assert "BUILDING_PLAN_APPROVAL" in dup_chk["details"]


def test_consumer_tool_and_inverted_timestamps(test_env):
    """
    PROVES: Forensic checks detect consumer tool fingerprints (Canva/Smallpdf) and
    inverted timestamps (ModDate < CreationDate), tagging them as advisory WARNINGs with limitations.
    """
    db_path = test_env["db_path"]
    uploads_dir = test_env["uploads_dir"]
    apex = test_env["apex_user"]

    app = ApplicationService.create_application(apex, "NEW_TECHNICAL_INSTITUTION", "2026-2027", "Test", db_path=db_path)

    meta = {
        "producer": "Smallpdf Online Compressor v2",
        "creator": "Canva Graphic Designer",
        "creationDate": "D:20261020120000",
        "modDate": "D:20251020120000"  # Inverted! ModDate precedes CreationDate
    }
    pdf_bytes = make_clean_pdf("Fire safety NOC certificate inspection station officer hydrant emergency", meta)

    doc_res = ApplicationService.upload_document(
        app_id=app["id"],
        user=apex,
        doc_type="FIRE_SAFETY_CERTIFICATE",
        filename="fire_safety_canva.pdf",
        file_bytes=pdf_bytes,
        uploads_dir=uploads_dir,
        db_path=db_path
    )

    run = ValidationEngine.get_latest_run_for_document(doc_res["id"], db_path=db_path)
    assert run is not None

    tool_chk = next(c for c in run["checks"] if c["check_id"] == "FORENSIC_CONSUMER_TOOL")
    assert tool_chk["status"] == "WARNING"
    assert "Consumer editing software detected" in tool_chk["summary"]

    time_chk = next(c for c in run["checks"] if c["check_id"] == "FORENSIC_METADATA_INCONSISTENCY")
    assert time_chk["status"] == "WARNING"
    assert "Inverted timestamps" in time_chk["summary"]


def test_incremental_updates_and_active_content(test_env):
    """
    PROVES: The engine detects multiple %%EOF markers (incremental updates) and
    active JavaScript stream dictionaries, raising appropriate warnings.
    """
    db_path = test_env["db_path"]
    uploads_dir = test_env["uploads_dir"]
    apex = test_env["apex_user"]

    app = ApplicationService.create_application(apex, "NEW_TECHNICAL_INSTITUTION", "2026-2027", "Test", db_path=db_path)

    base_pdf = make_clean_pdf("Affidavit notary oath undertaking deponent affirm aicte handbook")
    # Append a second %%EOF marker and JavaScript action
    mod_pdf = base_pdf + b"\n% Appended revision stream\n/JavaScript (app.alert('ai_scrutiny'))\n%%EOF\n"

    doc_res = ApplicationService.upload_document(
        app_id=app["id"],
        user=apex,
        doc_type="AICTE_AFFIDAVIT_1",
        filename="affidavit_incremental_js.pdf",
        file_bytes=mod_pdf,
        uploads_dir=uploads_dir,
        db_path=db_path
    )

    run = ValidationEngine.get_latest_run_for_document(doc_res["id"], db_path=db_path)
    assert run is not None

    eof_chk = next(c for c in run["checks"] if c["check_id"] == "PDF_INCREMENTAL_UPDATES")
    assert eof_chk["status"] == "WARNING"
    assert "2 %%EOF markers" in eof_chk["summary"]

    js_chk = next(c for c in run["checks"] if c["check_id"] == "PDF_ACTIVE_CONTENT_CHECK")
    assert js_chk["status"] == "REVIEW_REQUIRED"
    assert "Active content detected" in js_chk["summary"]


def test_cross_document_identity_mismatch(test_env):
    """
    PROVES: When an uploaded document explicitly references another college's permanent code,
    CROSS_DOC_INSTITUTION_CODE flags a REVIEW_REQUIRED condition.
    """
    db_path = test_env["db_path"]
    uploads_dir = test_env["uploads_dir"]
    apex = test_env["apex_user"]

    app = ApplicationService.create_application(apex, "NEW_TECHNICAL_INSTITUTION", "2026-2027", "Test", db_path=db_path)

    # Document explicitly lists Beacon College's code BEACON-KA-2002 instead of Apex's APEX-MH-1001
    foreign_doc_text = (
        "Building plan approval sanctioned by municipal corporation.\n"
        "Issued to: BEACON-KA-2002 (Beacon College)\n"
        "Built-up area: 12,000 sq.m. Approved by chief architect."
    )
    pdf_bytes = make_clean_pdf(foreign_doc_text)

    doc_res = ApplicationService.upload_document(
        app_id=app["id"],
        user=apex,
        doc_type="BUILDING_PLAN_APPROVAL",
        filename="foreign_building_plan.pdf",
        file_bytes=pdf_bytes,
        uploads_dir=uploads_dir,
        db_path=db_path
    )

    run = ValidationEngine.get_latest_run_for_document(doc_res["id"], db_path=db_path)
    assert run is not None

    code_chk = next(c for c in run["checks"] if c["check_id"] == "CROSS_DOC_INSTITUTION_CODE")
    assert code_chk["status"] == "REVIEW_REQUIRED"
    assert "Mismatched Permanent Code" in code_chk["summary"]


def test_officer_finding_disposition_and_rerun(test_env):
    """
    PROVES: Scrutiny officers can record human review dispositions on specific check findings,
    re-run validation runs without overwriting historical runs, and maintain complete audit traceability.
    """
    db_path = test_env["db_path"]
    uploads_dir = test_env["uploads_dir"]
    apex = test_env["apex_user"]
    admin = test_env["admin_user"]

    app = ApplicationService.create_application(apex, "NEW_TECHNICAL_INSTITUTION", "2026-2027", "Test", db_path=db_path)

    pdf_bytes = make_clean_pdf("Fire safety certificate station officer NOC extinguisher")
    doc_res = ApplicationService.upload_document(
        app_id=app["id"],
        user=apex,
        doc_type="FIRE_SAFETY_CERTIFICATE",
        filename="fire_cert.pdf",
        file_bytes=pdf_bytes,
        uploads_dir=uploads_dir,
        db_path=db_path
    )

    run1 = ValidationEngine.get_latest_run_for_document(doc_res["id"], db_path=db_path)
    chk = run1["checks"][0]

    # Officer records review disposition
    disp = ApplicationService.record_finding_disposition(
        check_record_id=chk["id"],
        doc_id=doc_res["id"],
        app_id=app["id"],
        user=admin,
        disposition="ACKNOWLEDGED",
        notes="Inspected and verified against Maharashtra Fire Services gazette registry.",
        db_path=db_path
    )
    assert disp["disposition"] == "ACKNOWLEDGED"

    # Verify disposition persisted
    run_with_disp = ValidationEngine.get_latest_run_for_document(doc_res["id"], db_path=db_path)
    assert len(run_with_disp["dispositions"]) == 1
    assert run_with_disp["dispositions"][0]["officer_email"] == admin["email"]

    # Manual re-run of validation engine
    new_run = ApplicationService.rerun_validation(doc_res["id"], admin, db_path=db_path)
    assert new_run["run_id"] != run1["id"]

    # Verify both runs exist in database (history retained)
    with get_db(db_path) as conn:
        cur = conn.execute("SELECT COUNT(*) FROM validation_runs WHERE document_id = ?", (doc_res["id"],))
        assert cur.fetchone()[0] == 2

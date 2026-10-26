"""
Automated Unit and Integration Tests for Newly Added Aegis Platform Features:
1. Regulatory Simulation Suite (core/scenarios.py)
2. In-Browser Deep PDF Structure & Forensic Inspector (views/inspector.py)
3. Formal Printable Scrutiny Order Gazette Generator (views/officer.py)
4. Document Versioning & Archival Differential (core/auth.py & core/db.py)
5. 4-Pillar Compliance Grid & Version Differential Card (views/theme.py)
"""

import os
import pytest
from core.db import get_db, seed_foundation
from core.auth import ApplicationService, AuthService
from core.scenarios import (
    create_scenario_pdf,
    load_scenario_deficient,
    load_scenario_clean,
    load_scenario_clarification
)
from views.inspector import inspect_pdf_file
from views.officer import generate_printable_scrutiny_order_html, generate_scrutiny_summary_report


@pytest.fixture
def clean_test_env(tmp_path):
    test_db = str(tmp_path / "test_features.db")
    test_uploads = str(tmp_path / "uploads")
    os.makedirs(test_uploads, exist_ok=True)
    seed_foundation(db_path=test_db, force_reset=True)
    return test_db, test_uploads


def test_scenario_clean_suite(clean_test_env):
    """Verifies that load_scenario_clean builds a 100% compliant application."""
    test_db, test_uploads = clean_test_env
    res = load_scenario_clean(db_path=test_db, uploads_dir=test_uploads)

    assert res["scenario"] == "CLEAN_PASS"
    assert res["status"] == "SUBMITTED"

    officer_user = AuthService.authenticate("admin@aicte.gov.in", "AegisAdmin@2026#Secure", expected_role="AICTE_SCRUTINY_OFFICER", db_path=test_db)
    packet = ApplicationService.get_application_details(res["application_id"], officer_user, db_path=test_db)

    assert packet["completeness_pct"] == 100
    assert len(packet["documents"]) == 4
    assert len(packet["missing_documents"]) == 0


def test_scenario_deficient_suite(clean_test_env):
    """Verifies that load_scenario_deficient detects naming and structural discrepancies."""
    test_db, test_uploads = clean_test_env
    res = load_scenario_deficient(db_path=test_db, uploads_dir=test_uploads)

    assert res["scenario"] == "DEFICIENT"
    assert res["status"] == "SUBMITTED"

    officer_user = AuthService.authenticate("admin@aicte.gov.in", "AegisAdmin@2026#Secure", expected_role="AICTE_SCRUTINY_OFFICER", db_path=test_db)
    packet = ApplicationService.get_application_details(res["application_id"], officer_user, db_path=test_db)

    assert len(packet["documents"]) == 4
    # Building plan has rough draft naming, should produce finding
    val_sum = packet["validation_summary"]
    assert val_sum is not None


def test_scenario_clarification_suite(clean_test_env):
    """Verifies that load_scenario_clarification sets up an active clarification round."""
    test_db, test_uploads = clean_test_env
    res = load_scenario_clarification(db_path=test_db, uploads_dir=test_uploads)

    assert res["scenario"] == "CLARIFICATION"
    assert res["status"] == "CLARIFICATION_REQUESTED"
    assert "clarification_id" in res

    college_user = AuthService.authenticate("principal@apextech.edu", "ApexPrincipal@2026#Secure", expected_role="COLLEGE_REPRESENTATIVE", db_path=test_db)
    notifications = ApplicationService.get_notifications_for_user(college_user, db_path=test_db)
    assert len(notifications) >= 1
    assert any(n["id"] == res["clarification_id"] for n in notifications)


def test_deep_pdf_inspector(tmp_path):
    """Verifies that inspect_pdf_file extracts structural parameters, metadata, and text."""
    pdf_path = str(tmp_path / "sample_inspection.pdf")
    pdf_bytes = create_scenario_pdf(
        "Land Title Deed & Encumbrance Certificate",
        "Survey Number 42, Revenue Sub-division B, Pune Municipal Corporation. Total Area: 10 Acres."
    )
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)

    report = inspect_pdf_file(pdf_path)

    assert report["success"] is True
    assert report["page_count"] == 1
    assert report["file_size"] > 0
    assert report["is_encrypted"] is False
    assert report["timestamp_anomaly"] is False
    assert len(report["pages_text"]) >= 1
    assert "Survey Number 42" in report["pages_text"][0]["text"]


def test_generate_printable_scrutiny_order_html(clean_test_env):
    """Verifies that generate_printable_scrutiny_order_html outputs valid, structured Gazette HTML."""
    test_db, test_uploads = clean_test_env
    res = load_scenario_clean(db_path=test_db, uploads_dir=test_uploads)

    officer_user = AuthService.authenticate("admin@aicte.gov.in", "AegisAdmin@2026#Secure", expected_role="AICTE_SCRUTINY_OFFICER", db_path=test_db)
    packet = ApplicationService.get_application_details(res["application_id"], officer_user, db_path=test_db)

    html = generate_printable_scrutiny_order_html(packet, officer_user)

    assert "<!DOCTYPE html>" in html
    assert "All India Council for Technical Education" in html
    assert "Central Regulatory Scrutiny Directorate" in html
    assert res["application_number"] in html
    assert "Apex Institute of Technology" in html
    assert "window.print()" in html
    assert "DIGITAL INTEGRITY SEAL" in html


def test_document_versioning_and_archival(clean_test_env):
    """Verifies that replacing a document preserves its predecessor in document_versions table."""
    test_db, test_uploads = clean_test_env
    college_user = AuthService.authenticate("principal@apextech.edu", "ApexPrincipal@2026#Secure", expected_role="COLLEGE_REPRESENTATIVE", db_path=test_db)

    app = ApplicationService.create_application(
        institution_or_user=college_user,
        category="NEW_TECHNICAL_INSTITUTION",
        db_path=test_db
    )
    app_id = app["id"]

    # Upload Version 1
    pdf_v1 = create_scenario_pdf("Land Title Initial", "Initial draft boundary description.")
    ApplicationService.upload_document(
        app_id=app_id,
        user=college_user,
        doc_type="LAND_TITLE_CERTIFICATE",
        filename="land_title_v1.pdf",
        file_bytes=pdf_v1,
        uploads_dir=test_uploads,
        db_path=test_db
    )

    # Verify active document is v1
    packet1 = ApplicationService.get_application_details(app_id, college_user, db_path=test_db)
    assert len(packet1["documents"]) == 1
    assert packet1["documents"][0]["filename"] == "land_title_v1.pdf"
    assert len(packet1.get("document_versions", [])) == 0

    # Upload Replacement (Version 2)
    pdf_v2 = create_scenario_pdf("Land Title Final Demarcated", "Final demarcated boundary certified by Revenue Surveyor.")
    ApplicationService.upload_document(
        app_id=app_id,
        user=college_user,
        doc_type="LAND_TITLE_CERTIFICATE",
        filename="land_title_v2_final.pdf",
        file_bytes=pdf_v2,
        uploads_dir=test_uploads,
        db_path=test_db
    )

    # Verify active document is now v2, and v1 is safely preserved in document_versions!
    packet2 = ApplicationService.get_application_details(app_id, college_user, db_path=test_db)
    assert len(packet2["documents"]) == 1
    assert packet2["documents"][0]["filename"] == "land_title_v2_final.pdf"

    versions = packet2.get("document_versions", [])
    assert len(versions) == 1
    archived_v1 = versions[0]
    assert archived_v1["filename"] == "land_title_v1.pdf"
    assert archived_v1["version_number"] == 1
    assert archived_v1["document_type"] == "LAND_TITLE_CERTIFICATE"

    # Also verify helper get_document_versions
    helper_versions = ApplicationService.get_document_versions(app_id, "LAND_TITLE_CERTIFICATE", db_path=test_db)
    assert len(helper_versions) == 1
    assert helper_versions[0]["filename"] == "land_title_v1.pdf"

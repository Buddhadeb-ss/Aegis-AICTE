"""
Aegis Foundation — Regulatory Demonstration Scenario Simulator
Provides one-click synthetic demonstration scenarios for evaluation, testing, and SIH presentations:
- Scenario 1 (Deficient): Discrepancies detected (naming mismatch, survey boundary issues), clear 7-field findings.
- Scenario 2 (Clean): 100% compliant statutory dossier, all checks clear.
- Scenario 3 (Clarification): Active round-trip clarification request with supplementary evidence.
"""

import os
import uuid
from typing import Any, Dict, Optional

try:
    import pymupdf as fitz
except ImportError:
    import fitz

from core.db import get_db, seed_foundation
from core.auth import ApplicationService, AuthService
from core.audit import log_event


def create_scenario_pdf(title: str, text: str, institution_name: str = "Apex Institute of Technology", institution_code: str = "APEX-MH-1001") -> bytes:
    """Generates a clean synthetic statutory PDF with appropriate metadata and structure."""
    doc = fitz.open()
    doc.set_metadata({
        "creator": "Government Directorate of Technical Education",
        "producer": "Aegis Statutory PDF Writer",
        "title": title
    })
    page = doc.new_page()
    full_text = f"""{institution_name}
Institution Code: {institution_code}
Approval Process Handbook Cycle: 2026-2027
Date of Issuance: 15/04/2026
Document: {title}

{text}

This is an official statutory record prepared for submission to the All India Council for Technical Education (AICTE).
"""
    page.insert_text((50, 72), full_text, fontsize=11)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def load_scenario_deficient(db_path: Optional[str] = None, uploads_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Scenario 1: Deficient Application.
    Apex Institute submits an application where:
    - Land Title Certificate is valid.
    - Building Plan has a naming anomaly.
    - Fire safety certificate has an outdated date or requires review.
    """
    college_user = AuthService.authenticate("principal@apextech.edu", "ApexPrincipal@2026#Secure", expected_role="COLLEGE_REPRESENTATIVE", db_path=db_path)
    if not college_user:
        seed_foundation(db_path=db_path)
        college_user = AuthService.authenticate("principal@apextech.edu", "ApexPrincipal@2026#Secure", expected_role="COLLEGE_REPRESENTATIVE", db_path=db_path)

    app = ApplicationService.create_application(
        institution_or_user=college_user,
        category="NEW_TECHNICAL_INSTITUTION",
        academic_year="2026-2027",
        notes="Apex Campus Expansion Dossier — Pending Building Sanction Rectification",
        db_path=db_path
    )
    app_id = app["id"]

    # Doc 1: Valid Land Title
    pdf1 = create_scenario_pdf(
        "Land Title Deed & Encumbrance Certificate",
        "Registered Survey No. 45/1A, Katraj-Dehu Bypass Road, Pune. Area: 12.5 Acres contiguous."
    )
    ApplicationService.upload_document(
        app_id=app_id,
        user=college_user,
        doc_type="LAND_TITLE_CERTIFICATE",
        filename="LAND_TITLE_CERTIFICATE.pdf",
        file_bytes=pdf1,
        uploads_dir=uploads_dir,
        db_path=db_path
    )

    # Doc 2: Building Plan with naming anomaly / wrong category pattern
    pdf2 = create_scenario_pdf(
        "Building Floor Layout Rough Draft",
        "Preliminary architectural line sketch for Block B Academic Wing. Detailed sanction pending municipal review."
    )
    ApplicationService.upload_document(
        app_id=app_id,
        user=college_user,
        doc_type="BUILDING_PLAN_APPROVAL",
        filename="rough_draft_academic_wing_b.pdf",
        file_bytes=pdf2,
        uploads_dir=uploads_dir,
        db_path=db_path
    )

    # Doc 3: AICTE Affidavit
    pdf3 = create_scenario_pdf("Registered Statutory Affidavit", "AICTE Stamp Paper Affidavit per Schedule 1.")
    ApplicationService.upload_document(
        app_id=app_id,
        user=college_user,
        doc_type="AICTE_AFFIDAVIT_1",
        filename="AICTE_AFFIDAVIT_1.pdf",
        file_bytes=pdf3,
        uploads_dir=uploads_dir,
        db_path=db_path
    )

    # Doc 4: Fire Safety Certificate
    pdf4 = create_scenario_pdf("State Fire Safety Certificate", "Disaster prevention and emergency evacuation clearance.")
    ApplicationService.upload_document(
        app_id=app_id,
        user=college_user,
        doc_type="FIRE_SAFETY_CERTIFICATE",
        filename="FIRE_SAFETY_CERTIFICATE.pdf",
        file_bytes=pdf4,
        uploads_dir=uploads_dir,
        db_path=db_path
    )

    # Submit application (now 100% complete, but contains naming deficiency finding)
    ApplicationService.submit_application(app_id, college_user, db_path=db_path)

    log_event("SCENARIO_LOADED", "application", app_id, actor="DEMO_RUNNER", details={"scenario": "DEFICIENT_DOSSIER"}, db_path=db_path)

    return {
        "scenario": "DEFICIENT",
        "application_id": app_id,
        "application_number": app["application_number"],
        "status": "SUBMITTED",
        "description": "Application with building plan naming discrepancy and pending statutory clearances."
    }


def load_scenario_clean(db_path: Optional[str] = None, uploads_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Scenario 2: Pristine Compliance Dossier.
    Apex Institute submits an application with all 4 mandatory documents fully conforming to AICTE APH norms.
    """
    college_user = AuthService.authenticate("principal@apextech.edu", "ApexPrincipal@2026#Secure", expected_role="COLLEGE_REPRESENTATIVE", db_path=db_path)
    if not college_user:
        seed_foundation(db_path=db_path)
        college_user = AuthService.authenticate("principal@apextech.edu", "ApexPrincipal@2026#Secure", expected_role="COLLEGE_REPRESENTATIVE", db_path=db_path)

    app = ApplicationService.create_application(
        institution_or_user=college_user,
        category="NEW_TECHNICAL_INSTITUTION",
        academic_year="2026-2027",
        notes="Apex Institute Comprehensive Statutory Dossier 2026-27 (Fully Compliant)",
        db_path=db_path
    )
    app_id = app["id"]

    mandatory_specs = [
        ("LAND_TITLE_CERTIFICATE", "LAND_TITLE_CERTIFICATE.pdf", "Survey #45, Katraj-Dehu Bypass Road, Pune. Total Land Area: 10.2 Acres, fully encumbrance-free."),
        ("BUILDING_PLAN_APPROVAL", "BUILDING_PLAN_APPROVAL.pdf", "Town Planning Authority Sanction #MC/TP/2026/882. Approved Total Built-Up Area: 22,400 sq.m."),
        ("AICTE_AFFIDAVIT_1", "AICTE_AFFIDAVIT_1.pdf", "Registered Statutory Affidavit on Non-Judicial Stamp Paper Rs 500 per AICTE APH 2026-27 Schedule."),
        ("FIRE_SAFETY_CERTIFICATE", "FIRE_SAFETY_CERTIFICATE.pdf", "Disaster Management & Fire Prevention Clearance Certificate #FSC/PN/2026/104. Valid through 2027.")
    ]

    for doc_type, filename, desc in mandatory_specs:
        pdf_bytes = create_scenario_pdf(doc_type.replace("_", " "), desc)
        ApplicationService.upload_document(
            app_id=app_id,
            user=college_user,
            doc_type=doc_type,
            filename=filename,
            file_bytes=pdf_bytes,
            uploads_dir=uploads_dir,
            db_path=db_path
        )

    # Submit application
    ApplicationService.submit_application(app_id, college_user, db_path=db_path)

    log_event("SCENARIO_LOADED", "application", app_id, actor="DEMO_RUNNER", details={"scenario": "CLEAN_PASS"}, db_path=db_path)

    return {
        "scenario": "CLEAN_PASS",
        "application_id": app_id,
        "application_number": app["application_number"],
        "status": "SUBMITTED",
        "description": "100% compliant application with all 4 statutory documents verified."
    }


def load_scenario_clarification(db_path: Optional[str] = None, uploads_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Scenario 3: Active Clarification Round.
    Creates an application, submits it, and has the officer issue a formal clarification inquiry.
    """
    # First create clean or partial
    result = load_scenario_clean(db_path=db_path, uploads_dir=uploads_dir)
    app_id = result["application_id"]

    officer_user = AuthService.authenticate("admin@aicte.gov.in", "AegisAdmin@2026#Secure", expected_role="AICTE_SCRUTINY_OFFICER", db_path=db_path)
    if not officer_user:
        seed_foundation(db_path=db_path)
        officer_user = AuthService.authenticate("admin@aicte.gov.in", "AegisAdmin@2026#Secure", expected_role="AICTE_SCRUTINY_OFFICER", db_path=db_path)

    clarif = ApplicationService.request_clarification(
        app_id=app_id,
        officer_user=officer_user,
        question_text="Plot boundary survey demarcation demarcation requires municipal surveyor certificate for Plot 45/1A.",
        requested_docs="Municipal City Surveyor Demarcation Map (PDF)",
        db_path=db_path
    )

    clarif_id = clarif if isinstance(clarif, str) else clarif.get("id", str(clarif))

    log_event("SCENARIO_LOADED", "application", app_id, actor="DEMO_RUNNER", details={"scenario": "ACTIVE_CLARIFICATION", "clarif_id": clarif_id}, db_path=db_path)

    return {
        "scenario": "CLARIFICATION",
        "application_id": app_id,
        "application_number": result["application_number"],
        "clarification_id": clarif_id,
        "status": "CLARIFICATION_REQUESTED",
        "description": "Application undergoing active statutory clarification round."
    }

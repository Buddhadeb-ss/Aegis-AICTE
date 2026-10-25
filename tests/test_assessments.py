"""
Aegis Foundation - Unit and Integration Tests for Four Primary Assessments
Tests:
- AssessmentAggregator mapping of 24 checks into 4 primary assessments
- Correct status assignment (PASS, ISSUE_FOUND, REVIEW_REQUIRED, INCOMPLETE, NOT_APPLICABLE)
- Conservative application-level clearance aggregation (no false passes)
- Actionable findings prioritization (issues first, review required second)
- Scanned document honest handling (REVIEW_REQUIRED with seal inspection instructions)
- Active scripts detection (ISSUE_FOUND under Authenticity & Anomalies)
- Cross-document discrepancy linking
- Underlying checks and historical run preservation
"""

import os
import shutil
import tempfile
import pytest
from core.db import init_db, seed_foundation
from core.auth import AuthService, ApplicationService
from core.validation.schema import (
    CheckResult,
    CheckStatus,
    CheckSeverity,
    CheckCategory,
    AssessmentType,
    AssessmentState,
    ValidationRunResult
)
from core.validation.assessment import AssessmentAggregator
from core.validation.engine import ValidationEngine


@pytest.fixture
def test_db():
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_aegis_assessments.db")
    init_db(db_path)
    seed_foundation(db_path=db_path)
    yield db_path
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_clean_pass_produces_all_pass_assessments():
    """Valid text document with all passing checks produces PASS across applicable assessments."""
    checks = [
        CheckResult("FILE_EXT_ALLOWED", "File Ext", "file_integrity", "PASS", "CRITICAL", "Ext allowed"),
        CheckResult("FILE_NON_EMPTY", "Non-empty", "file_integrity", "PASS", "CRITICAL", "Non empty"),
        CheckResult("FILE_SIGNATURE_MATCH", "Signature", "file_integrity", "PASS", "CRITICAL", "Sig matched"),
        CheckResult("PDF_PARSE_INTEGRITY", "PDF parse", "document_structure", "PASS", "CRITICAL", "Parsed"),
        CheckResult("PDF_PAGE_COUNT", "Page count", "document_structure", "PASS", "HIGH", "Pages ok"),
        CheckResult("PDF_ENCRYPTION_CHECK", "Encryption", "document_structure", "PASS", "HIGH", "Not encrypted"),
        CheckResult("TEXT_EXTRACT_PER_PAGE", "Text extract", "content", "PASS", "INFO", "Text extracted"),
        CheckResult("TEXT_READABILITY_SCANNED_CHECK", "Scanned check", "content", "PASS", "MEDIUM", "Digital text ok"),
        CheckResult("DOC_TYPE_CONTENT_MATCH", "Content match", "content", "PASS", "HIGH", "Keywords matched"),
        CheckResult("DOC_DATE_VALIDITY", "Date validity", "content", "PASS", "LOW", "Dates valid"),
        CheckResult("CROSS_DOC_DUPLICATE_FILES", "Duplicate check", "consistency", "PASS", "MEDIUM", "Unique file"),
        CheckResult("CROSS_DOC_INSTITUTION_CODE", "Inst code", "consistency", "PASS", "MEDIUM", "Code matches"),
        CheckResult("PDF_METADATA_AUDIT", "Metadata audit", "metadata", "PASS", "LOW", "Metadata present"),
        CheckResult("PDF_ACTIVE_CONTENT_CHECK", "Active content", "document_structure", "PASS", "HIGH", "No scripts"),
        CheckResult("FORENSIC_CONSUMER_TOOL", "Consumer tool", "authenticity", "PASS", "LOW", "No consumer tool"),
    ]
    run_dict = {"checks": [c.to_dict() for c in checks]}
    res = AssessmentAggregator.aggregate_document_run(run_dict, doc_type="LAND_TITLE_CERTIFICATE")

    assessments = res["assessments"]
    assert assessments[AssessmentType.VALIDITY_AND_READABILITY.value]["state"] == AssessmentState.PASS.value
    assert assessments[AssessmentType.REQUIRED_INFO_COMPLIANCE.value]["state"] == AssessmentState.PASS.value
    assert assessments[AssessmentType.CROSS_DOCUMENT_CONSISTENCY.value]["state"] == AssessmentState.PASS.value
    assert assessments[AssessmentType.AUTHENTICITY_AND_ANOMALIES.value]["state"] == AssessmentState.PASS.value
    assert res["overall_state"] == AssessmentState.PASS.value
    assert len(res["actionable_findings"]) == 0


def test_failed_mandatory_rule_produces_issue_found():
    """Failed content rule produces ISSUE_FOUND and prioritizes actionable finding."""
    checks = [
        CheckResult("FILE_EXT_ALLOWED", "File Ext", "file_integrity", "PASS", "CRITICAL", "Ext allowed"),
        CheckResult("FILE_NON_EMPTY", "Non-empty", "file_integrity", "PASS", "CRITICAL", "Non empty"),
        CheckResult("PDF_PARSE_INTEGRITY", "PDF parse", "document_structure", "PASS", "CRITICAL", "Parsed"),
        CheckResult("DOC_TYPE_CONTENT_MATCH", "Content match", "content", "FAIL", "HIGH", "Mandatory land clauses missing",
                    details="Document missing required ownership clauses", expected_value="Keywords present", observed_value="0 keywords matched",
                    recommendation="Submit registered sale deed."),
    ]
    run_dict = {"checks": [c.to_dict() for c in checks]}
    res = AssessmentAggregator.aggregate_document_run(run_dict, doc_type="LAND_TITLE_CERTIFICATE")

    a2 = res["assessments"][AssessmentType.REQUIRED_INFO_COMPLIANCE.value]
    assert a2["state"] == AssessmentState.ISSUE_FOUND.value
    assert res["overall_state"] == AssessmentState.ISSUE_FOUND.value
    assert len(res["actionable_findings"]) > 0
    top_finding = res["actionable_findings"][0]
    assert top_finding["state"] == AssessmentState.ISSUE_FOUND.value
    assert "Mandatory statutory clauses" in top_finding["summary"]


def test_scanned_image_produces_review_required_not_failure():
    """Scanned image document produces REVIEW_REQUIRED with seal inspection instructions, NOT false pass or false fail."""
    checks = [
        CheckResult("FILE_EXT_ALLOWED", "File Ext", "file_integrity", "PASS", "CRITICAL", "Ext allowed"),
        CheckResult("FILE_NON_EMPTY", "Non-empty", "file_integrity", "PASS", "CRITICAL", "Non empty"),
        CheckResult("PDF_PARSE_INTEGRITY", "PDF parse", "document_structure", "PASS", "CRITICAL", "Parsed"),
        CheckResult("TEXT_READABILITY_SCANNED_CHECK", "Scanned check", "content", "REVIEW_REQUIRED", "MEDIUM",
                    "Scanned image detected", details="0 characters found", evidence={"total_chars": 0, "is_scanned": True}),
        CheckResult("DOC_TYPE_CONTENT_MATCH", "Content match", "content", "NOT_RUN", "MEDIUM",
                    "Check not run because document is scanned image", evidence={"reason": "Scanned document"}),
        CheckResult("FILE_SHA256_DIGEST", "Digest", "file_integrity", "PASS", "INFO", "Hash computed"),
    ]
    run_dict = {"checks": [c.to_dict() for c in checks]}
    res = AssessmentAggregator.aggregate_document_run(run_dict, doc_type="LAND_TITLE_CERTIFICATE")

    a1 = res["assessments"][AssessmentType.VALIDITY_AND_READABILITY.value]
    a2 = res["assessments"][AssessmentType.REQUIRED_INFO_COMPLIANCE.value]
    assert a1["state"] == AssessmentState.REVIEW_REQUIRED.value
    assert a2["state"] == AssessmentState.REVIEW_REQUIRED.value
    assert res["overall_state"] == AssessmentState.REVIEW_REQUIRED.value
    assert "visual" in a1["recommendation"].lower() or "viewer" in a1["recommendation"].lower()


def test_active_content_and_script_detection():
    """Active JavaScript in PDF produces ISSUE_FOUND under Authenticity & Anomalies."""
    checks = [
        CheckResult("FILE_EXT_ALLOWED", "File Ext", "file_integrity", "PASS", "CRITICAL", "Ext allowed"),
        CheckResult("PDF_ACTIVE_CONTENT_CHECK", "Active content", "document_structure", "FAIL", "HIGH",
                    "JavaScript actions detected in PDF", evidence={"found_scripts": ["/JavaScript"]}),
    ]
    run_dict = {"checks": [c.to_dict() for c in checks]}
    res = AssessmentAggregator.aggregate_document_run(run_dict, doc_type="FIRE_SAFETY_CERTIFICATE")

    a4 = res["assessments"][AssessmentType.AUTHENTICITY_AND_ANOMALIES.value]
    assert a4["state"] == AssessmentState.ISSUE_FOUND.value
    assert res["overall_state"] == AssessmentState.ISSUE_FOUND.value
    assert "script" in a4["summary"].lower()


def test_duplicate_payload_produces_cross_document_issue():
    """Duplicate file across application checklist produces ISSUE_FOUND in Cross-Document Consistency."""
    checks = [
        CheckResult("CROSS_DOC_DUPLICATE_FILES", "Cross duplicate", "consistency", "WARNING", "MEDIUM",
                    "File bytes identical to BUILDING_PLAN_APPROVAL",
                    evidence={"matching_document_type": "BUILDING_PLAN_APPROVAL", "matching_filename": "plan.pdf"}),
    ]
    run_dict = {"checks": [c.to_dict() for c in checks]}
    res = AssessmentAggregator.aggregate_document_run(run_dict, doc_type="FIRE_SAFETY_CERTIFICATE")

    a3 = res["assessments"][AssessmentType.CROSS_DOCUMENT_CONSISTENCY.value]
    assert a3["state"] == AssessmentState.ISSUE_FOUND.value
    assert "BUILDING_PLAN_APPROVAL" in a3["summary"] or "BUILDING_PLAN_APPROVAL" in a3["problem_explanation"]


def test_incomplete_and_errored_checks():
    """Checks encountering an execution error produce INCOMPLETE, never false pass."""
    checks = [
        CheckResult("STAGE_INTEGRITY_ERROR", "Pipeline crash", "file_integrity", "ERROR", "CRITICAL",
                    "Memory parsing exception", details="ZeroDivisionError in custom parser"),
    ]
    run_dict = {"checks": [c.to_dict() for c in checks]}
    res = AssessmentAggregator.aggregate_document_run(run_dict, doc_type="AICTE_AFFIDAVIT_1")

    a1 = res["assessments"][AssessmentType.VALIDITY_AND_READABILITY.value]
    assert a1["state"] == AssessmentState.INCOMPLETE.value
    assert res["overall_state"] == AssessmentState.INCOMPLETE.value


def test_conservative_application_aggregation():
    """Dossier with one ISSUE_FOUND and one REVIEW_REQUIRED aggregates conservatively to DEFICIENT."""
    doc_assessments = [
        {"document_id": "doc1", "overall_state": AssessmentState.PASS.value, "actionable_findings": []},
        {"document_id": "doc2", "overall_state": AssessmentState.REVIEW_REQUIRED.value, "actionable_findings": [{"title": "Scanned"}]},
        {"document_id": "doc3", "overall_state": AssessmentState.ISSUE_FOUND.value, "actionable_findings": [{"title": "Missing clause"}]},
    ]
    summary = AssessmentAggregator.aggregate_application_assessments(doc_assessments)
    assert summary["application_status"] == "DEFICIENT"
    assert summary["state_counts"][AssessmentState.ISSUE_FOUND.value] == 1
    assert summary["state_counts"][AssessmentState.REVIEW_REQUIRED.value] == 1
    assert summary["state_counts"][AssessmentState.PASS.value] == 1
    assert len(summary["actionable_findings"]) == 2


def test_end_to_end_assessment_integration_with_database(test_db):
    """Verifies that ApplicationService and ValidationEngine populate assessments from real DB data."""
    db_path = test_db
    apex = AuthService.authenticate("principal@apextech.edu", "ApexPrincipal@2026#Secure", db_path=db_path)
    app = ApplicationService.create_application(apex, "NEW_TECHNICAL_INSTITUTION", "2026-2027", db_path=db_path)

    # Minimal PDF
    pdf_bytes = (
        b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n"
        b"4 0 obj\n<< /Length 50 >>\nstream\nBT /F1 12 Tf 72 712 Td (Apex Institute Title Deed) Tj ET\nendstream\nendobj\n"
        b"xref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000206 00000 n \n"
        b"trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n305\n%%EOF\n"
    )

    doc_info = ApplicationService.upload_document(
        app_id=app["id"],
        user=apex,
        doc_type="LAND_TITLE_CERTIFICATE",
        filename="apex_land_title.pdf",
        file_bytes=pdf_bytes,
        db_path=db_path
    )

    # Retrieve application packet
    packet = ApplicationService.get_application_details(app["id"], apex, db_path=db_path)
    val_run = packet["documents"][0]["validation_run"]

    # Verify primary assessments are attached non-destructively
    assert "assessments" in val_run
    assert "assessment_overall_state" in val_run
    assert AssessmentType.VALIDITY_AND_READABILITY.value in val_run["assessments"]
    assert AssessmentType.REQUIRED_INFO_COMPLIANCE.value in val_run["assessments"]
    assert AssessmentType.CROSS_DOCUMENT_CONSISTENCY.value in val_run["assessments"]
    assert AssessmentType.AUTHENTICITY_AND_ANOMALIES.value in val_run["assessments"]

    # Verify underlying 24 check records are still completely intact
    assert len(val_run["checks"]) > 0

    # Verify application validation summary has app_assessments
    val_summary = packet["validation_summary"]
    assert "app_assessments" in val_summary
    assert val_summary["app_assessments"]["total_documents"] == 1

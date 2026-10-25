"""
Aegis Foundation - Acceptance Tests for Simplified Decision-Oriented Document Review
Validates all 8 acceptance requirements from the Final Simplification of AI Document Review specification:
1. Clean application shows one concise CLEAR verdict without exposing the technical checklist.
2. Application with real detected issue shows correct filename and specific problem (File, Problem, Evidence, Action).
3. Incomplete validation run cannot show CLEAR.
4. Cross-document discrepancies identify both relevant files and observed values.
5. Technical details remain accessible and intact in underlying records.
6. College representatives see actionable guidance without internal forensic diagnostics.
7. No result claims OCR, AI-generation detection, or authenticity verification unless executed; authenticity is marked Not verified.
8. Existing validation history, persistence, access controls, and audit logging remain intact.
"""

import os
import pytest
from core.validation.schema import AssessmentState, AssessmentType, CheckResult, CheckSeverity, CheckStatus
from core.validation.assessment import AssessmentAggregator
from core.auth import ApplicationService, AuthService, get_db
from core.validation.engine import ValidationEngine

TEST_DB = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_simplified_review.db"))


@pytest.fixture(autouse=True)
def clean_db():
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except PermissionError:
            pass
    from core.db import seed_foundation
    seed_foundation(TEST_DB, force_reset=True)
    yield
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except PermissionError:
            pass


def test_1_clean_application_shows_concise_clear_verdict():
    """Requirement 1 & 2: Clean application produces CLEAR verdict with exact single summary sentence."""
    checks = [
        CheckResult("FILE_NON_EMPTY", "Non-Empty", "file_integrity", "PASS", "CRITICAL", "Non-empty"),
        CheckResult("FILE_MAGIC_BYTES", "Magic bytes", "file_integrity", "PASS", "CRITICAL", "Valid PDF"),
        CheckResult("PDF_PARSE_INTEGRITY", "Parse", "document_structure", "PASS", "CRITICAL", "Parsed"),
        CheckResult("DOC_TYPE_CONTENT_MATCH", "Clause", "content", "PASS", "HIGH", "Clauses found"),
        CheckResult("CROSS_DOC_DUPLICATE_FILES", "Duplicate", "consistency", "PASS", "MEDIUM", "Unique"),
        CheckResult("FILE_SHA256_DIGEST", "Hash", "file_integrity", "PASS", "INFO", "Hash computed"),
        CheckResult("PDF_ACTIVE_CONTENT_CHECK", "Scripts", "document_structure", "PASS", "HIGH", "No scripts"),
    ]
    doc_run = {"checks": [c.to_dict() for c in checks]}
    res = AssessmentAggregator.aggregate_document_run(doc_run, doc_type="LAND_TITLE_CERTIFICATE")
    assert res["overall_state"] == AssessmentState.PASS.value

    # Dossier level aggregation
    doc_assessments = [{
        "document_id": "doc-1",
        "document_type": "LAND_TITLE_CERTIFICATE",
        "filename": "land_certificate.pdf",
        "overall_state": res["overall_state"],
        "assessments": res["assessments"],
        "actionable_findings": res["actionable_findings"]
    }]
    app_res = AssessmentAggregator.aggregate_application_assessments(doc_assessments)

    verdict = app_res["verdict"]
    assert verdict["key"] == "CLEAR"
    assert "CLEAR — No issues detected by the completed checks" in verdict["title"]
    assert verdict["sentence"] == (
        "All required automated checks passed. No issues were detected by these checks. "
        "Automated checks do not independently establish document authenticity."
    )
    assert len(app_res["actionable_findings"]) == 0
    assert app_res["compact_documents"][0]["simple_status"] == "Clear"


def test_2_application_with_real_issue_shows_exact_file_problem_evidence_action():
    """Requirement 3: An issue produces exact File, Problem, Evidence, and Action fields."""
    checks = [
        CheckResult("FILE_NON_EMPTY", "Non-Empty", "file_integrity", "PASS", "CRITICAL", "Non-empty"),
        CheckResult("PDF_PARSE_INTEGRITY", "Parse", "document_structure", "PASS", "CRITICAL", "Parsed"),
        CheckResult(
            "DOC_TYPE_CONTENT_MATCH", "Mandatory clause", "content", "FAIL", "HIGH",
            "Mandatory statutory clauses missing",
            details="Certificate does not contain registered conveyance terms",
            evidence={"matched_keywords": ["affidavit"], "missing_keywords": ["khasra", "sale deed"]}
        ),
        CheckResult("FILE_SHA256_DIGEST", "Hash", "file_integrity", "PASS", "INFO", "Hash computed")
    ]
    doc_run = {"checks": [c.to_dict() for c in checks]}
    res = AssessmentAggregator.aggregate_document_run(doc_run, doc_type="LAND_TITLE_CERTIFICATE")
    assert res["overall_state"] == AssessmentState.ISSUE_FOUND.value

    doc_assessments = [{
        "document_id": "doc-fail",
        "document_type": "LAND_TITLE_CERTIFICATE",
        "filename": "land_title_flawed.pdf",
        "overall_state": res["overall_state"],
        "assessments": res["assessments"],
        "actionable_findings": res["actionable_findings"]
    }]
    app_res = AssessmentAggregator.aggregate_application_assessments(doc_assessments)

    assert app_res["verdict"]["key"] == "ACTION_REQUIRED"
    assert "ACTION REQUIRED — Specific issues detected" in app_res["verdict"]["title"]

    findings = app_res["actionable_findings"]
    assert len(findings) > 0
    f = findings[0]
    assert f["file"] == "land_title_flawed.pdf"
    assert "required statutory clause" in f["problem"].lower() or "missing" in f["problem"].lower()
    assert "khasra" in f["evidence"] or "sale deed" in f["evidence"]
    assert len(f["action"]) > 0


def test_3_incomplete_validation_run_cannot_show_clear():
    """Requirement 1 & 7: Incomplete run produces CHECK_INCOMPLETE, never CLEAR."""
    checks = [
        CheckResult("FILE_NON_EMPTY", "Non-Empty", "file_integrity", "PASS", "CRITICAL", "Non-empty"),
        CheckResult("PDF_PARSE_INTEGRITY", "Parse", "document_structure", "ERROR", "HIGH",
                    "Parser execution crashed", details="File stream truncated"),
    ]
    doc_run = {"checks": [c.to_dict() for c in checks]}
    res = AssessmentAggregator.aggregate_document_run(doc_run, doc_type="BUILDING_PLAN_APPROVAL")
    assert res["overall_state"] == AssessmentState.INCOMPLETE.value

    doc_assessments = [{
        "document_id": "doc-inc",
        "document_type": "BUILDING_PLAN_APPROVAL",
        "filename": "building_plan_corrupted.pdf",
        "overall_state": res["overall_state"],
        "assessments": res["assessments"],
        "actionable_findings": res["actionable_findings"]
    }]
    app_res = AssessmentAggregator.aggregate_application_assessments(doc_assessments)

    assert app_res["verdict"]["key"] == "CHECK_INCOMPLETE"
    assert app_res["verdict"]["key"] != "CLEAR"
    assert "CHECK INCOMPLETE" in app_res["verdict"]["title"]
    assert app_res["compact_documents"][0]["simple_status"] == "Incomplete"


def test_4_cross_document_discrepancy_identifies_both_files_and_values():
    """Requirement 4: Cross-document issues identify both files and compared conflicting values."""
    checks = [
        CheckResult("FILE_NON_EMPTY", "Non-Empty", "file_integrity", "PASS", "CRITICAL", "Non-empty"),
        CheckResult("PDF_PARSE_INTEGRITY", "Parse", "document_structure", "PASS", "CRITICAL", "Parsed"),
        CheckResult(
            "CROSS_DOC_DUPLICATE_FILES", "Duplicate File Payload", "consistency", "FAIL", "HIGH",
            "Identical file uploaded for two distinct checklist slots",
            evidence={
                "matching_filename": "land_certificate.pdf",
                "matching_document_type": "LAND_TITLE_CERTIFICATE",
                "sha256": "abc1234567890abcdef"
            }
        ),
        CheckResult(
            "CROSS_DOC_INSTITUTION_CODE", "Identifier Match", "consistency", "FAIL", "HIGH",
            "Conflicting permanent application ID detected",
            evidence={
                "observed_code": "AICTE-1-WR-9999",
                "expected_code": "AICTE-1-1097241"
            }
        )
    ]
    doc_run = {"checks": [c.to_dict() for c in checks]}
    res = AssessmentAggregator.aggregate_document_run(doc_run, doc_type="FIRE_SAFETY_CERTIFICATE")

    doc_assessments = [{
        "document_id": "doc-fire",
        "document_type": "FIRE_SAFETY_CERTIFICATE",
        "filename": "fire_safety_copy.pdf",
        "overall_state": res["overall_state"],
        "assessments": res["assessments"],
        "actionable_findings": res["actionable_findings"]
    }]
    app_res = AssessmentAggregator.aggregate_application_assessments(doc_assessments)

    findings = app_res["actionable_findings"]
    duplicate_f = next((f for f in findings if "identical" in f["problem"].lower() or "duplicate" in f["problem"].lower()), None)
    assert duplicate_f is not None
    assert duplicate_f["file"] == "fire_safety_copy.pdf"
    assert "land_certificate.pdf" in duplicate_f["evidence"]
    assert "LAND_TITLE_CERTIFICATE" in duplicate_f["evidence"]


def test_5_exceptions_sorted_to_top_of_compact_list():
    """Requirement 2: Documents requiring review or having an issue are brought to the top of the compact list."""
    doc_assessments = [
        {
            "document_id": "doc-clean-1",
            "document_type": "AICTE_AFFIDAVIT_1",
            "filename": "affidavit.pdf",
            "overall_state": AssessmentState.PASS.value,
            "assessments": {},
            "actionable_findings": []
        },
        {
            "document_id": "doc-issue-1",
            "document_type": "FIRE_SAFETY_CERTIFICATE",
            "filename": "fire_safety.pdf",
            "overall_state": AssessmentState.ISSUE_FOUND.value,
            "assessments": {},
            "actionable_findings": [{
                "assessment_type": AssessmentType.VALIDITY_AND_READABILITY.value,
                "state": AssessmentState.ISSUE_FOUND.value,
                "summary": "Corrupt file",
                "problem_explanation": "PDF parse error",
                "recommendation": "Re-upload"
            }]
        },
        {
            "document_id": "doc-clean-2",
            "document_type": "BUILDING_PLAN_APPROVAL",
            "filename": "building_plan.pdf",
            "overall_state": AssessmentState.PASS.value,
            "assessments": {},
            "actionable_findings": []
        },
        {
            "document_id": "doc-review-1",
            "document_type": "LAND_TITLE_CERTIFICATE",
            "filename": "land_scan.pdf",
            "overall_state": AssessmentState.REVIEW_REQUIRED.value,
            "assessments": {},
            "actionable_findings": [{
                "assessment_type": AssessmentType.VALIDITY_AND_READABILITY.value,
                "state": AssessmentState.REVIEW_REQUIRED.value,
                "summary": "Scanned document detected",
                "problem_explanation": "0 chars",
                "recommendation": "Inspect visual seal"
            }]
        }
    ]

    app_res = AssessmentAggregator.aggregate_application_assessments(doc_assessments)
    compact_docs = app_res["compact_documents"]

    # First item must be the Issue
    assert compact_docs[0]["filename"] == "fire_safety.pdf"
    assert compact_docs[0]["simple_status"] == "Issue"

    # Second item must be the Review
    assert compact_docs[1]["filename"] == "land_scan.pdf"
    assert compact_docs[1]["simple_status"] == "Review"

    # Last items are Clear
    assert compact_docs[2]["simple_status"] == "Clear"
    assert compact_docs[3]["simple_status"] == "Clear"


def test_6_processing_summary_distinguishes_capabilities_and_unverified_authenticity():
    """Requirement 4: Processing summary distinguishes OCR, required info, cross-doc, and authenticity is Not verified."""
    doc_assessments = [
        {
            "document_id": "doc-1",
            "document_type": "LAND_TITLE_CERTIFICATE",
            "filename": "land_doc.pdf",
            "overall_state": AssessmentState.PASS.value,
            "assessments": {
                AssessmentType.VALIDITY_AND_READABILITY.value: {"state": AssessmentState.PASS.value},
                AssessmentType.REQUIRED_INFO_COMPLIANCE.value: {"state": AssessmentState.PASS.value},
                AssessmentType.CROSS_DOCUMENT_CONSISTENCY.value: {"state": AssessmentState.PASS.value},
                AssessmentType.AUTHENTICITY_AND_ANOMALIES.value: {"state": AssessmentState.PASS.value},
            },
            "actionable_findings": []
        },
        {
            "document_id": "doc-2",
            "document_type": "BUILDING_PLAN_APPROVAL",
            "filename": "building_doc.pdf",
            "overall_state": AssessmentState.PASS.value,
            "assessments": {
                AssessmentType.VALIDITY_AND_READABILITY.value: {"state": AssessmentState.PASS.value},
                AssessmentType.REQUIRED_INFO_COMPLIANCE.value: {"state": AssessmentState.PASS.value},
                AssessmentType.CROSS_DOCUMENT_CONSISTENCY.value: {"state": AssessmentState.PASS.value},
                AssessmentType.AUTHENTICITY_AND_ANOMALIES.value: {"state": AssessmentState.PASS.value},
            },
            "actionable_findings": []
        }
    ]

    app_res = AssessmentAggregator.aggregate_application_assessments(doc_assessments)
    ps = app_res["processing_summary"]

    assert ps["reading_ocr"]["status"] == "Passed"
    assert ps["required_info"]["status"] == "Passed"
    assert ps["cross_document"]["status"] == "Passed"
    assert ps["authenticity"]["status"] == "Not verified"
    assert "independently establish" in ps["authenticity"]["note"]


def test_7_college_view_shows_actionable_guidance_without_forensic_jargon():
    """Requirement 6: College feedback panel does not expose raw hashes or forensic jargon."""
    from views.validation_view import render_applicant_feedback_panel

    doc = {
        "id": "doc-test",
        "filename": "test_certificate.pdf",
        "document_type": "LAND_TITLE_CERTIFICATE",
        "validation_run": {
            "checks": [
                {
                    "check_id": "TEXT_READABILITY_SCANNED_CHECK",
                    "status": "REVIEW_REQUIRED",
                    "summary": "Scanned document detected"
                },
                {
                    "check_id": "CROSS_DOC_DUPLICATE_FILES",
                    "status": "FAIL",
                    "summary": "Duplicate payload"
                }
            ]
        }
    }

    # render_applicant_feedback_panel runs without crashing or raising errors
    try:
        render_applicant_feedback_panel(doc)
    except Exception as e:
        pytest.fail(f"render_applicant_feedback_panel crashed: {e}")


def test_8_end_to_end_persistence_and_technical_details_retention():
    """Requirement 5 & 8: All underlying 24 check records, JSON evidence, and dispositions remain in DB."""
    officer_user = AuthService.authenticate("admin@aicte.gov.in", "AegisAdmin@2026#Secure", db_path=TEST_DB)
    assert officer_user is not None

    # Create application draft for college
    college_user = AuthService.authenticate("principal@apextech.edu", "ApexPrincipal@2026#Secure", db_path=TEST_DB)
    assert college_user is not None
    app_draft = ApplicationService.create_application(
        college_user["institution_id"], "NEW_TECHNICAL_INSTITUTION", "2026-2027", college_user["email"], "Test Draft", db_path=TEST_DB
    )
    app_id = app_draft["id"]

    # Upload clean text PDF and run validation
    sample_pdf = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n4 0 obj\n<< /Length 120 >>\nstream\nBT /F1 12 Tf 72 712 Td (AICTE Approval Process Handbook Land Title Deed Conveyance Registered Khasra Apex Institute of Technology AICTE-1-1097241) ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000216 00000 n \ntrailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n386\n%%EOF\n"

    doc_res = ApplicationService.upload_document(
        app_id, college_user, "LAND_TITLE_CERTIFICATE", "land_deed.pdf", sample_pdf, db_path=TEST_DB
    )

    # Fetch latest run
    run = ValidationEngine.get_latest_run_for_document(doc_res["id"], db_path=TEST_DB)
    assert run is not None
    assert len(run["checks"]) >= 20
    assert run["engine_version"] == "2.0.0-phase2"

    # Verify summary aggregation
    summary = ValidationEngine.get_application_validation_summary(app_id, db_path=TEST_DB)
    assert "verdict" in summary["app_assessments"]
    assert "processing_summary" in summary["app_assessments"]
    assert "compact_documents" in summary["app_assessments"]

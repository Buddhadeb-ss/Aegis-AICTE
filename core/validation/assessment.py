"""
Aegis Foundation - Four Primary Validation Assessments Aggregator
Consolidates 24 granular technical checks into four high-level, actionable assessments
for regulatory scrutiny officers, reducing cognitive load without sacrificing rigor or traceability.

The Four Primary Assessments:
1. Document Validity & Readability (format, parseability, completeness, scanned/text streams)
2. Required Information & Compliance (statutory category clauses, required fields, date plausibility)
3. Cross-Document Consistency (payload uniqueness, permanent ID, institutional title across dossier)
4. Authenticity Indicators & Anomaly Evaluation (active content, structural revisions, metadata forensics)
"""

from typing import Any, Dict, List, Optional
from core.validation.schema import (
    AssessmentType,
    AssessmentState,
    PrimaryAssessment,
    CheckStatus,
    CheckSeverity,
)

# Mapping of individual check IDs to the four primary assessments
CHECK_ASSESSMENT_MAP = {
    # 1. Document validity and readability
    "FILE_EXT_ALLOWED": AssessmentType.VALIDITY_AND_READABILITY,
    "FILE_NON_EMPTY": AssessmentType.VALIDITY_AND_READABILITY,
    "FILE_SIGNATURE_MATCH": AssessmentType.VALIDITY_AND_READABILITY,
    "FILE_SIZE_LIMIT": AssessmentType.VALIDITY_AND_READABILITY,
    "FILE_PATH_TRAVERSAL_SAFE": AssessmentType.VALIDITY_AND_READABILITY,
    "FILE_STORAGE_ACCESS": AssessmentType.VALIDITY_AND_READABILITY,
    "STAGE_INTEGRITY_ERROR": AssessmentType.VALIDITY_AND_READABILITY,
    "PDF_PARSE_INTEGRITY": AssessmentType.VALIDITY_AND_READABILITY,
    "PDF_PAGE_COUNT": AssessmentType.VALIDITY_AND_READABILITY,
    "PDF_ENCRYPTION_CHECK": AssessmentType.VALIDITY_AND_READABILITY,
    "STAGE_PDF_STRUCTURAL_ERROR": AssessmentType.VALIDITY_AND_READABILITY,
    "TEXT_EXTRACT_PER_PAGE": AssessmentType.VALIDITY_AND_READABILITY,
    "TEXT_READABILITY_SCANNED_CHECK": AssessmentType.VALIDITY_AND_READABILITY,
    "STAGE_TEXT_EXTRACTION_ERROR": AssessmentType.VALIDITY_AND_READABILITY,

    # 2. Required information and compliance
    "DOC_CATEGORY_FILENAME_MATCH": AssessmentType.REQUIRED_INFO_COMPLIANCE,
    "DOC_TYPE_CONTENT_MATCH": AssessmentType.REQUIRED_INFO_COMPLIANCE,
    "DOC_DATE_VALIDITY": AssessmentType.REQUIRED_INFO_COMPLIANCE,
    "STAGE_CONTENT_RULES_ERROR": AssessmentType.REQUIRED_INFO_COMPLIANCE,

    # 3. Cross-document consistency
    "CROSS_DOC_DUPLICATE_FILES": AssessmentType.CROSS_DOCUMENT_CONSISTENCY,
    "CROSS_DOC_INSTITUTION_CODE": AssessmentType.CROSS_DOCUMENT_CONSISTENCY,
    "CROSS_DOC_INSTITUTION_NAME": AssessmentType.CROSS_DOCUMENT_CONSISTENCY,
    "STAGE_CROSS_DOC_ERROR": AssessmentType.CROSS_DOCUMENT_CONSISTENCY,

    # 4. Authenticity indicators and suspicious anomalies
    "PDF_METADATA_AUDIT": AssessmentType.AUTHENTICITY_AND_ANOMALIES,
    "PDF_ATTACHMENT_CHECK": AssessmentType.AUTHENTICITY_AND_ANOMALIES,
    "PDF_INCREMENTAL_UPDATES": AssessmentType.AUTHENTICITY_AND_ANOMALIES,
    "PDF_ACTIVE_CONTENT_CHECK": AssessmentType.AUTHENTICITY_AND_ANOMALIES,
    "FORENSIC_CONSUMER_TOOL": AssessmentType.AUTHENTICITY_AND_ANOMALIES,
    "FORENSIC_METADATA_INCONSISTENCY": AssessmentType.AUTHENTICITY_AND_ANOMALIES,
    "FORENSIC_FONT_AUDIT": AssessmentType.AUTHENTICITY_AND_ANOMALIES,
    "FILE_SHA256_DIGEST": AssessmentType.AUTHENTICITY_AND_ANOMALIES,
    "STAGE_FORENSICS_ERROR": AssessmentType.AUTHENTICITY_AND_ANOMALIES,
}


class AssessmentAggregator:
    """Aggregates low-level check executions into four primary assessment outcomes."""

    @classmethod
    def aggregate_document_run(cls, run_data: Dict[str, Any], doc_type: str = "STATUTORY_DOCUMENT") -> Dict[str, Any]:
        """
        Takes a validation run dictionary (with raw checks) and returns:
        - assessments: Dict[str, Dict] for the 4 primary assessments
        - actionable_findings: List[Dict] prioritized by importance (issues first, reviews second)
        - overall_state: Overall document assessment state
        """
        raw_checks = run_data.get("checks", [])
        grouped_checks: Dict[str, List[Dict[str, Any]]] = {
            AssessmentType.VALIDITY_AND_READABILITY.value: [],
            AssessmentType.REQUIRED_INFO_COMPLIANCE.value: [],
            AssessmentType.CROSS_DOCUMENT_CONSISTENCY.value: [],
            AssessmentType.AUTHENTICITY_AND_ANOMALIES.value: [],
        }

        for c in raw_checks:
            cid = c.get("check_id")
            atype = CHECK_ASSESSMENT_MAP.get(cid)
            if atype:
                grouped_checks[atype.value].append(c)
            else:
                # Default bucket based on check category
                cat = c.get("category")
                if cat in ["file_integrity", "document_structure"]:
                    grouped_checks[AssessmentType.VALIDITY_AND_READABILITY.value].append(c)
                elif cat == "content":
                    grouped_checks[AssessmentType.REQUIRED_INFO_COMPLIANCE.value].append(c)
                elif cat == "consistency":
                    grouped_checks[AssessmentType.CROSS_DOCUMENT_CONSISTENCY.value].append(c)
                else:
                    grouped_checks[AssessmentType.AUTHENTICITY_AND_ANOMALIES.value].append(c)

        # Build the four primary assessments
        a1 = cls._evaluate_validity_and_readability(grouped_checks[AssessmentType.VALIDITY_AND_READABILITY.value], doc_type)
        a2 = cls._evaluate_required_info(grouped_checks[AssessmentType.REQUIRED_INFO_COMPLIANCE.value], doc_type)
        a3 = cls._evaluate_cross_document(grouped_checks[AssessmentType.CROSS_DOCUMENT_CONSISTENCY.value], doc_type)
        a4 = cls._evaluate_authenticity_and_anomalies(grouped_checks[AssessmentType.AUTHENTICITY_AND_ANOMALIES.value], doc_type)

        assessments_dict = {
            AssessmentType.VALIDITY_AND_READABILITY.value: a1.to_dict(),
            AssessmentType.REQUIRED_INFO_COMPLIANCE.value: a2.to_dict(),
            AssessmentType.CROSS_DOCUMENT_CONSISTENCY.value: a3.to_dict(),
            AssessmentType.AUTHENTICITY_AND_ANOMALIES.value: a4.to_dict(),
        }

        # Determine overall document assessment state
        states = [a1.state, a2.state, a3.state, a4.state]
        if AssessmentState.ISSUE_FOUND.value in states:
            overall_state = AssessmentState.ISSUE_FOUND.value
        elif AssessmentState.INCOMPLETE.value in states:
            overall_state = AssessmentState.INCOMPLETE.value
        elif AssessmentState.REVIEW_REQUIRED.value in states:
            overall_state = AssessmentState.REVIEW_REQUIRED.value
        elif all(s == AssessmentState.PASS.value for s in states if s != AssessmentState.NOT_APPLICABLE.value):
            overall_state = AssessmentState.PASS.value
        else:
            overall_state = AssessmentState.REVIEW_REQUIRED.value

        # Extract prioritized actionable findings (Issues first, then Reviews required)
        actionable_findings = []
        for a in [a1, a2, a3, a4]:
            if a.state in [AssessmentState.ISSUE_FOUND.value, AssessmentState.REVIEW_REQUIRED.value, AssessmentState.INCOMPLETE.value]:
                actionable_findings.append({
                    "assessment_type": a.assessment_type,
                    "title": a.title,
                    "state": a.state,
                    "severity": a.severity,
                    "summary": a.summary,
                    "problem_explanation": a.problem_explanation,
                    "recommendation": a.recommendation,
                    "evidence": a.evidence,
                    "underlying_check_ids": a.underlying_check_ids
                })

        # Sort actionable findings: ISSUE_FOUND (highest priority) -> INCOMPLETE -> REVIEW_REQUIRED
        severity_order = {
            AssessmentState.ISSUE_FOUND.value: 1,
            AssessmentState.INCOMPLETE.value: 2,
            AssessmentState.REVIEW_REQUIRED.value: 3
        }
        actionable_findings.sort(key=lambda x: severity_order.get(x["state"], 99))

        return {
            "assessments": assessments_dict,
            "overall_state": overall_state,
            "actionable_findings": actionable_findings,
            "underlying_checks": raw_checks
        }

    # -------------------------------------------------------------------------
    # Assessment A: Document Validity & Readability
    # -------------------------------------------------------------------------
    @classmethod
    def _evaluate_validity_and_readability(cls, checks: List[Dict[str, Any]], doc_type: str) -> PrimaryAssessment:
        title = "Document Validity & Readability"
        check_ids = [c["check_id"] for c in checks]
        ev: Dict[str, Any] = {}

        if not checks:
            return PrimaryAssessment(
                assessment_type=AssessmentType.VALIDITY_AND_READABILITY.value,
                title=title,
                state=AssessmentState.INCOMPLETE.value,
                severity=CheckSeverity.MEDIUM.value,
                summary="Validity checks were not executed for this document.",
                recommendation="Trigger a fresh validation run to verify document integrity.",
                underlying_check_ids=check_ids,
                underlying_checks=checks
            )

        # 1. Critical Binary / Storage / Format Failures
        failed_checks = [c for c in checks if c["status"] == CheckStatus.FAIL.value]
        error_checks = [c for c in checks if c["status"] == CheckStatus.ERROR.value]

        if error_checks:
            err = error_checks[0]
            return PrimaryAssessment(
                assessment_type=AssessmentType.VALIDITY_AND_READABILITY.value,
                title=title,
                state=AssessmentState.INCOMPLETE.value,
                severity=CheckSeverity.HIGH.value,
                summary=f"Parsing error: {err['summary']}",
                problem_explanation=f"The validation engine encountered an error while attempting to read the file structure: {err.get('details', err['summary'])}",
                evidence=err.get("evidence", {}),
                recommendation="Check filesystem permissions or re-upload the file.",
                underlying_check_ids=check_ids,
                underlying_checks=checks
            )

        # Check for structural integrity failures (zero-byte, bad magic bytes, unparseable, password protected)
        for f in failed_checks:
            cid = f["check_id"]
            if cid in ["FILE_NON_EMPTY", "FILE_SIGNATURE_MATCH", "FILE_EXT_ALLOWED", "PDF_PARSE_INTEGRITY"]:
                return PrimaryAssessment(
                    assessment_type=AssessmentType.VALIDITY_AND_READABILITY.value,
                    title=title,
                    state=AssessmentState.ISSUE_FOUND.value,
                    severity=CheckSeverity.CRITICAL.value,
                    summary=f"Corrupt or invalid document payload ({f['check_name']})",
                    problem_explanation=f.get("details", f["summary"]),
                    evidence=f.get("evidence", {}),
                    recommendation=f.get("recommendation", "Applicant must submit a valid, uncorrupted PDF document."),
                    underlying_check_ids=check_ids,
                    underlying_checks=checks
                )
            elif cid == "PDF_ENCRYPTION_CHECK":
                return PrimaryAssessment(
                    assessment_type=AssessmentType.VALIDITY_AND_READABILITY.value,
                    title=title,
                    state=AssessmentState.ISSUE_FOUND.value,
                    severity=CheckSeverity.HIGH.value,
                    summary="Document is password protected and cannot be evaluated.",
                    problem_explanation="The PDF requires a password to open. AICTE scrutiny officers cannot inspect password-protected files.",
                    evidence=f.get("evidence", {}),
                    recommendation="Request the applicant to re-upload an unencrypted PDF copy.",
                    underlying_check_ids=check_ids,
                    underlying_checks=checks
                )
            elif cid == "FILE_SIZE_LIMIT":
                return PrimaryAssessment(
                    assessment_type=AssessmentType.VALIDITY_AND_READABILITY.value,
                    title=title,
                    state=AssessmentState.ISSUE_FOUND.value,
                    severity=CheckSeverity.HIGH.value,
                    summary="Document exceeds the statutory upload limit of 15 MB.",
                    problem_explanation=f.get("details", f["summary"]),
                    evidence=f.get("evidence", {}),
                    recommendation="Re-upload compressed PDF document within size limits.",
                    underlying_check_ids=check_ids,
                    underlying_checks=checks
                )

        # 2. Scanned / Rasterized Document (Review Required)
        scanned_check = next((c for c in checks if c["check_id"] == "TEXT_READABILITY_SCANNED_CHECK"), None)
        if scanned_check and scanned_check.get("status") == CheckStatus.REVIEW_REQUIRED.value:
            ev = scanned_check.get("evidence", {})
            return PrimaryAssessment(
                assessment_type=AssessmentType.VALIDITY_AND_READABILITY.value,
                title=title,
                state=AssessmentState.REVIEW_REQUIRED.value,
                severity=CheckSeverity.MEDIUM.value,
                summary="Scanned / image-based document detected (manual visual scrutiny required).",
                problem_explanation=(
                    "The PDF stream contains minimal or zero digital text. This is common for notarized paper deeds, "
                    "physical land records, or municipal sanctions that were scanned. Missing digital text does NOT indicate fraud."
                ),
                evidence=ev,
                recommendation="Visually inspect the document in the viewer to verify institutional seals, revenue stamps, and signatures.",
                underlying_check_ids=check_ids,
                underlying_checks=checks
            )

        # 3. Clean Pass
        text_check = next((c for c in checks if c["check_id"] == "TEXT_EXTRACT_PER_PAGE"), None)
        if text_check and text_check.get("evidence"):
            ev = text_check["evidence"]

        return PrimaryAssessment(
            assessment_type=AssessmentType.VALIDITY_AND_READABILITY.value,
            title=title,
            state=AssessmentState.PASS.value,
            severity=CheckSeverity.INFO.value,
            summary="Document structure, format signature, and searchable text streams are fully intact and readable.",
            evidence=ev,
            recommendation="No validity issues. Document is eligible for compliance evaluation.",
            underlying_check_ids=check_ids,
            underlying_checks=checks
        )

    # -------------------------------------------------------------------------
    # Assessment B: Required Information & Compliance
    # -------------------------------------------------------------------------
    @classmethod
    def _evaluate_required_info(cls, checks: List[Dict[str, Any]], doc_type: str) -> PrimaryAssessment:
        title = "Required Information & Compliance"
        check_ids = [c["check_id"] for c in checks]

        if not checks:
            return PrimaryAssessment(
                assessment_type=AssessmentType.REQUIRED_INFO_COMPLIANCE.value,
                title=title,
                state=AssessmentState.INCOMPLETE.value,
                severity=CheckSeverity.MEDIUM.value,
                summary=f"No compliance rules executed for declared document type '{doc_type}'.",
                recommendation="Verify document category mapping in the Rule Registry.",
                underlying_check_ids=check_ids,
                underlying_checks=checks
            )

        concordance_check = next((c for c in checks if c["check_id"] == "DOC_CATEGORY_FILENAME_MATCH"), None)
        content_check = next((c for c in checks if c["check_id"] == "DOC_TYPE_CONTENT_MATCH"), None)
        date_check = next((c for c in checks if c["check_id"] == "DOC_DATE_VALIDITY"), None)

        # If an error occurred
        for c in checks:
            if c["status"] == CheckStatus.ERROR.value:
                return PrimaryAssessment(
                    assessment_type=AssessmentType.REQUIRED_INFO_COMPLIANCE.value,
                    title=title,
                    state=AssessmentState.INCOMPLETE.value,
                    severity=CheckSeverity.MEDIUM.value,
                    summary=f"Compliance check failed to execute: {c['summary']}",
                    problem_explanation=c.get("details", ""),
                    recommendation="Re-run compliance evaluation.",
                    underlying_check_ids=check_ids,
                    underlying_checks=checks
                )

        # If category / filename concordance explicitly failed (mismatch detected)
        if concordance_check and concordance_check.get("status") == CheckStatus.FAIL.value:
            ev = concordance_check.get("evidence", {})
            exp_doc = ev.get("expected_document") or doc_type.replace('_', ' ').title()
            up_fn = ev.get("uploaded_filename") or "uploaded document"
            return PrimaryAssessment(
                assessment_type=AssessmentType.REQUIRED_INFO_COMPLIANCE.value,
                title=title,
                state=AssessmentState.ISSUE_FOUND.value,
                severity=CheckSeverity.HIGH.value,
                summary="The uploaded filename/category does not match the expected document.",
                problem_explanation=(
                    concordance_check.get("details") or
                    f"The uploaded file '{up_fn}' does not match the expected statutory document '{exp_doc}'."
                ),
                evidence=ev,
                recommendation=f"Review document and upload the correct {exp_doc}.",
                underlying_check_ids=check_ids,
                underlying_checks=checks
            )

        # If content check explicitly failed
        if content_check and content_check.get("status") == CheckStatus.FAIL.value:
            return PrimaryAssessment(
                assessment_type=AssessmentType.REQUIRED_INFO_COMPLIANCE.value,
                title=title,
                state=AssessmentState.ISSUE_FOUND.value,
                severity=CheckSeverity.HIGH.value,
                summary=f"Mandatory statutory clauses for '{doc_type.replace('_', ' ')}' were not found.",
                problem_explanation=(
                    f"The document text did not contain the minimum required statutory clauses or terms "
                    f"defined for {doc_type}. Observed keywords matched: {content_check.get('evidence', {}).get('matched_keywords', [])}."
                ),
                evidence=content_check.get("evidence", {}),
                recommendation="Request clarification or submission of the official statutory certificate complying with AICTE norms.",
                underlying_check_ids=check_ids,
                underlying_checks=checks
            )

        # If content check was NOT_RUN because the document is a scanned image
        if content_check and content_check.get("status") == CheckStatus.NOT_RUN.value:
            return PrimaryAssessment(
                assessment_type=AssessmentType.REQUIRED_INFO_COMPLIANCE.value,
                title=title,
                state=AssessmentState.REVIEW_REQUIRED.value,
                severity=CheckSeverity.MEDIUM.value,
                summary="Automated clause extraction not applicable to scanned image; manual verification required.",
                problem_explanation=(
                    "Because this document is image-based without digital text streams, automated keyword matching "
                    "was intentionally not run to avoid false failures. Statutory completeness cannot be verified by machine."
                ),
                evidence=content_check.get("evidence", {}),
                recommendation="Officer must manually verify required statutory clauses and institutional details in the document image.",
                underlying_check_ids=check_ids,
                underlying_checks=checks
            )

        # If content check gave a warning (e.g., partial keywords)
        if content_check and content_check.get("status") == CheckStatus.WARNING.value:
            return PrimaryAssessment(
                assessment_type=AssessmentType.REQUIRED_INFO_COMPLIANCE.value,
                title=title,
                state=AssessmentState.REVIEW_REQUIRED.value,
                severity=CheckSeverity.MEDIUM.value,
                summary=f"Partial statutory terms detected for '{doc_type.replace('_', ' ')}'.",
                problem_explanation=content_check.get("details", content_check["summary"]),
                evidence=content_check.get("evidence", {}),
                recommendation="Verify whether the certificate contains required statutory declarations under local state terminology.",
                underlying_check_ids=check_ids,
                underlying_checks=checks
            )

        # Check date validity warnings
        if date_check and date_check.get("status") in [CheckStatus.WARNING.value, CheckStatus.REVIEW_REQUIRED.value]:
            return PrimaryAssessment(
                assessment_type=AssessmentType.REQUIRED_INFO_COMPLIANCE.value,
                title=title,
                state=AssessmentState.REVIEW_REQUIRED.value,
                severity=CheckSeverity.LOW.value,
                summary="Date references in document require manual review.",
                problem_explanation=date_check.get("details", date_check["summary"]),
                evidence=date_check.get("evidence", {}),
                recommendation="Verify document issuance and validity dates against regulatory handbook deadlines.",
                underlying_check_ids=check_ids,
                underlying_checks=checks
            )

        # Clean Pass
        ev = {}
        if content_check and content_check.get("evidence"):
            ev.update(content_check["evidence"])
        if date_check and date_check.get("evidence"):
            ev["dates_found"] = date_check["evidence"].get("extracted_dates", [])

        return PrimaryAssessment(
            assessment_type=AssessmentType.REQUIRED_INFO_COMPLIANCE.value,
            title=title,
            state=AssessmentState.PASS.value,
            severity=CheckSeverity.INFO.value,
            summary=f"Mandatory identifying clauses and statutory dates for '{doc_type.replace('_', ' ')}' are satisfied.",
            evidence=ev,
            recommendation="Compliant with versioned rule specifications.",
            underlying_check_ids=check_ids,
            underlying_checks=checks
        )

    # -------------------------------------------------------------------------
    # Assessment C: Cross-Document Consistency
    # -------------------------------------------------------------------------
    @classmethod
    def _evaluate_cross_document(cls, checks: List[Dict[str, Any]], doc_type: str) -> PrimaryAssessment:
        title = "Cross-Document Consistency"
        check_ids = [c["check_id"] for c in checks]

        if not checks:
            return PrimaryAssessment(
                assessment_type=AssessmentType.CROSS_DOCUMENT_CONSISTENCY.value,
                title=title,
                state=AssessmentState.NOT_APPLICABLE.value,
                severity=CheckSeverity.INFO.value,
                summary="No cross-document checks were executed for this standalone file.",
                recommendation="No action needed.",
                underlying_check_ids=check_ids,
                underlying_checks=checks
            )

        duplicate_check = next((c for c in checks if c["check_id"] == "CROSS_DOC_DUPLICATE_FILES"), None)
        code_check = next((c for c in checks if c["check_id"] == "CROSS_DOC_INSTITUTION_CODE"), None)
        name_check = next((c for c in checks if c["check_id"] == "CROSS_DOC_INSTITUTION_NAME"), None)

        # Duplicate file detection across application checklist
        if duplicate_check and duplicate_check.get("status") in [CheckStatus.WARNING.value, CheckStatus.FAIL.value]:
            ev = duplicate_check.get("evidence", {})
            matching_doc = ev.get("matching_document_type", "another document")
            matching_file = ev.get("matching_filename", "")
            return PrimaryAssessment(
                assessment_type=AssessmentType.CROSS_DOCUMENT_CONSISTENCY.value,
                title=title,
                state=AssessmentState.ISSUE_FOUND.value,
                severity=CheckSeverity.MEDIUM.value,
                summary=f"Duplicate file payload detected (matches '{matching_doc}').",
                problem_explanation=(
                    f"This document is byte-identical to another uploaded file ('{matching_file}' as {matching_doc}). "
                    "Each mandatory checklist requirement requires distinct statutory evidence."
                ),
                evidence=ev,
                recommendation="Request the applicant to submit the specific, distinct statutory certificate for this requirement.",
                underlying_check_ids=check_ids,
                underlying_checks=checks
            )

        # Permanent Code Mismatch
        if code_check and code_check.get("status") in [CheckStatus.WARNING.value, CheckStatus.FAIL.value]:
            ev = code_check.get("evidence", {})
            return PrimaryAssessment(
                assessment_type=AssessmentType.CROSS_DOCUMENT_CONSISTENCY.value,
                title=title,
                state=AssessmentState.ISSUE_FOUND.value,
                severity=CheckSeverity.HIGH.value,
                summary="Permanent Institution Code mismatch across application.",
                problem_explanation=code_check.get("details", code_check["summary"]),
                evidence=ev,
                recommendation="Verify institutional code in state records; issue clarification if conflicting codes appear.",
                underlying_check_ids=check_ids,
                underlying_checks=checks
            )

        # Institution Name Discrepancy
        if name_check and name_check.get("status") in [CheckStatus.WARNING.value, CheckStatus.REVIEW_REQUIRED.value]:
            ev = name_check.get("evidence", {})
            return PrimaryAssessment(
                assessment_type=AssessmentType.CROSS_DOCUMENT_CONSISTENCY.value,
                title=title,
                state=AssessmentState.REVIEW_REQUIRED.value,
                severity=CheckSeverity.LOW.value,
                summary="Minor variation in institutional title compared to companion documents.",
                problem_explanation=name_check.get("details", name_check["summary"]),
                evidence=ev,
                recommendation="Check if variation is an accepted abbreviation or sponsoring society designation.",
                underlying_check_ids=check_ids,
                underlying_checks=checks
            )

        # Clean Pass
        ev = {}
        if duplicate_check and duplicate_check.get("evidence"):
            ev["unique_hash"] = duplicate_check["evidence"].get("sha256", "")

        return PrimaryAssessment(
            assessment_type=AssessmentType.CROSS_DOCUMENT_CONSISTENCY.value,
            title=title,
            state=AssessmentState.PASS.value,
            severity=CheckSeverity.INFO.value,
            summary="Unique file payload; institutional identity matches companion dossier documents.",
            evidence=ev,
            recommendation="No cross-document discrepancies found.",
            underlying_check_ids=check_ids,
            underlying_checks=checks
        )

    # -------------------------------------------------------------------------
    # Assessment D: Authenticity Indicators & Suspicious Anomalies
    # -------------------------------------------------------------------------
    @classmethod
    def _evaluate_authenticity_and_anomalies(cls, checks: List[Dict[str, Any]], doc_type: str) -> PrimaryAssessment:
        title = "Authenticity Indicators & Anomaly Evaluation"
        check_ids = [c["check_id"] for c in checks]

        if not checks:
            return PrimaryAssessment(
                assessment_type=AssessmentType.AUTHENTICITY_AND_ANOMALIES.value,
                title=title,
                state=AssessmentState.INCOMPLETE.value,
                severity=CheckSeverity.LOW.value,
                summary="Forensic anomaly checks were not executed.",
                recommendation="Re-run validation.",
                underlying_check_ids=check_ids,
                underlying_checks=checks
            )

        active_content = next((c for c in checks if c["check_id"] == "PDF_ACTIVE_CONTENT_CHECK"), None)
        timestamp_check = next((c for c in checks if c["check_id"] == "FORENSIC_METADATA_INCONSISTENCY"), None)
        incremental_check = next((c for c in checks if c["check_id"] == "PDF_INCREMENTAL_UPDATES"), None)
        consumer_tool = next((c for c in checks if c["check_id"] == "FORENSIC_CONSUMER_TOOL"), None)
        metadata_check = next((c for c in checks if c["check_id"] == "PDF_METADATA_AUDIT"), None)

        # 1. Active Content (Security concern)
        if active_content and active_content.get("status") in [CheckStatus.FAIL.value, CheckStatus.WARNING.value]:
            return PrimaryAssessment(
                assessment_type=AssessmentType.AUTHENTICITY_AND_ANOMALIES.value,
                title=title,
                state=AssessmentState.ISSUE_FOUND.value,
                severity=CheckSeverity.HIGH.value,
                summary="Active scripts or interactive actions detected in PDF.",
                problem_explanation=(
                    "The PDF contains embedded script streams (/JavaScript or /Launch actions). "
                    "Regulatory submissions must be static documents to prevent malicious or non-standard execution."
                ),
                evidence=active_content.get("evidence", {}),
                recommendation="Instruct applicant to print to static PDF without interactive scripts.",
                underlying_check_ids=check_ids,
                underlying_checks=checks
            )

        # 2. Forensic Timestamp Inconsistencies (Inverted dates)
        if timestamp_check and timestamp_check.get("status") in [CheckStatus.WARNING.value, CheckStatus.REVIEW_REQUIRED.value]:
            return PrimaryAssessment(
                assessment_type=AssessmentType.AUTHENTICITY_AND_ANOMALIES.value,
                title=title,
                state=AssessmentState.REVIEW_REQUIRED.value,
                severity=CheckSeverity.MEDIUM.value,
                summary="Metadata timestamp anomaly (modification date predates creation).",
                problem_explanation=(
                    "PDF internal timestamps are inconsistent (e.g., Modification date is earlier than Creation date). "
                    "NOTE: Clock desynchronization on scanning workstations can cause this; it does not prove document forgery."
                ),
                evidence=timestamp_check.get("evidence", {}),
                recommendation="Examine document for visual evidence of re-stamping or content manipulation.",
                underlying_check_ids=check_ids,
                underlying_checks=checks
            )

        # 3. Incremental Revisions
        if incremental_check and incremental_check.get("status") in [CheckStatus.WARNING.value, CheckStatus.REVIEW_REQUIRED.value]:
            return PrimaryAssessment(
                assessment_type=AssessmentType.AUTHENTICITY_AND_ANOMALIES.value,
                title=title,
                state=AssessmentState.REVIEW_REQUIRED.value,
                severity=CheckSeverity.LOW.value,
                summary="Multiple revision sections detected in PDF stream.",
                problem_explanation=(
                    "The file has multiple revision sections (incremental saves). This is standard for PDF forms or "
                    "documents saved in Acrobat, but officers should verify that underlying clauses were not altered post-issuance."
                ),
                evidence=incremental_check.get("evidence", {}),
                recommendation="Advisory indicator only. Review file visually if other anomalies are present.",
                underlying_check_ids=check_ids,
                underlying_checks=checks
            )

        # 4. Consumer PDF Editor Fingerprint
        if consumer_tool and consumer_tool.get("status") in [CheckStatus.WARNING.value, CheckStatus.REVIEW_REQUIRED.value]:
            ev = consumer_tool.get("evidence", {})
            detected = ev.get("detected_consumer_tools", ["online PDF editor"])
            return PrimaryAssessment(
                assessment_type=AssessmentType.AUTHENTICITY_AND_ANOMALIES.value,
                title=title,
                state=AssessmentState.REVIEW_REQUIRED.value,
                severity=CheckSeverity.LOW.value,
                summary=f"Consumer PDF editing signature detected ({', '.join(detected)}).",
                problem_explanation=(
                    f"Document metadata indicates the file was processed using a consumer online editor ({', '.join(detected)}). "
                    "This often reflects applicant convenience (merging or compressing), NOT fraud or forgery."
                ),
                evidence=ev,
                recommendation="Advisory signal only. No rejection warranted on this basis alone; inspect official seal and registration numbers.",
                underlying_check_ids=check_ids,
                underlying_checks=checks
            )

        # 5. Missing Authoring Metadata
        if metadata_check and metadata_check.get("status") in [CheckStatus.WARNING.value, CheckStatus.REVIEW_REQUIRED.value]:
            return PrimaryAssessment(
                assessment_type=AssessmentType.AUTHENTICITY_AND_ANOMALIES.value,
                title=title,
                state=AssessmentState.REVIEW_REQUIRED.value,
                severity=CheckSeverity.LOW.value,
                summary="PDF contains no creator or producer metadata.",
                problem_explanation="The PDF dictionary contains no authoring device metadata. Standard flatbed scanners frequently omit these fields.",
                evidence=metadata_check.get("evidence", {}),
                recommendation="Advisory signal only. Standard scanned document review applies.",
                underlying_check_ids=check_ids,
                underlying_checks=checks
            )

        # Clean Pass
        digest_check = next((c for c in checks if c["check_id"] == "FILE_SHA256_DIGEST"), None)
        ev = digest_check.get("evidence", {}) if digest_check else {}

        return PrimaryAssessment(
            assessment_type=AssessmentType.AUTHENTICITY_AND_ANOMALIES.value,
            title=title,
            state=AssessmentState.PASS.value,
            severity=CheckSeverity.INFO.value,
            summary="No structural anomalies, active scripts, hidden attachments, or suspicious metadata detected.",
            evidence=ev,
            recommendation="Authenticity indicators meet standard criteria.",
            underlying_check_ids=check_ids,
            underlying_checks=checks
        )

    # -------------------------------------------------------------------------
    # Application-Level Dossier Aggregation & Decision-Oriented Verdict
    # -------------------------------------------------------------------------
    @classmethod
    def _format_actionable_finding(cls, finding: Dict[str, Any], doc_type: str, filename: str) -> Dict[str, Any]:
        """
        Formats an actionable finding into exactly four concise fields:
        File, Problem, Evidence, and Action.
        """
        f_type = finding.get("assessment_type", "")
        f_state = finding.get("state", AssessmentState.REVIEW_REQUIRED.value)
        raw_ev = finding.get("evidence") or {}
        summary = finding.get("summary", "")
        problem_exp = finding.get("problem_explanation", "")
        rec = finding.get("recommendation", "")

        # Default values
        problem = summary
        evidence_str = problem_exp
        action = rec or "Inspect document details."

        if f_type == AssessmentType.VALIDITY_AND_READABILITY.value:
            if "password" in summary.lower():
                problem = "The document is password-protected and cannot be evaluated."
                evidence_str = "PDF requires password to unlock content."
                action = "Request an unencrypted replacement copy."
            elif "size" in summary.lower():
                problem = "The document exceeds the statutory file size limit."
                evidence_str = f"File size exceeds allowable boundary (15 MB)."
                action = "Request compressed PDF copy within size limits."
            elif "scanned" in summary.lower() or raw_ev.get("is_scanned"):
                problem = "The document contains scanned images without digital text streams."
                chars = raw_ev.get("total_chars", 0)
                pages = raw_ev.get("page_count", "all")
                evidence_str = f"{chars} digital text characters extracted across {pages} page(s); raster image scan detected."
                action = "Visually inspect physical seals, stamps, and signatures in the document viewer."
            elif "parsing error" in summary.lower() or "corrupt" in summary.lower() or f_state == AssessmentState.INCOMPLETE.value:
                problem = "The document could not be read."
                evidence_str = f"PDF parsing failed: {problem_exp or 'Unparseable or damaged PDF structure.'}"
                action = "Request a readable replacement."

        elif f_type == AssessmentType.REQUIRED_INFO_COMPLIANCE.value:
            if "does not match the expected document" in summary.lower() or raw_ev.get("mismatch") or "concordance" in summary.lower():
                from core.validation.checks.content_rules import DOC_HUMAN_NAMES
                exp_name = raw_ev.get("expected_document") or DOC_HUMAN_NAMES.get(doc_type, doc_type.replace('_', ' ').title())
                up_name = raw_ev.get("uploaded_filename") or filename
                problem = "The uploaded filename/category does not match the expected document."
                evidence_str = f"Expected: {exp_name} | Uploaded: {up_name}"
                action = "Review document"
            elif "mandatory" in summary.lower() or "clauses" in summary.lower() or f_state == AssessmentState.ISSUE_FOUND.value:
                problem = f"A required statutory clause could not be located in {doc_type.replace('_', ' ')}."
                matched = raw_ev.get("matched_keywords", [])
                missing = raw_ev.get("missing_keywords", [])
                if missing:
                    evidence_str = f"Missing mandatory statutory clauses: {missing}; Matched clauses: {matched}."
                else:
                    evidence_str = problem_exp or "Required statutory terms not located in text stream."
                action = "Inspect the document or request a corrected copy."
            elif "scanned image" in summary.lower():
                problem = "Automated clause verification not available for scanned image."
                evidence_str = "Text stream empty; OCR capability not configured."
                action = "Manually verify required statutory clauses in document viewer."
            elif "date" in summary.lower():
                problem = "Document dates require scrutiny against the 2026-27 academic session."
                evidence_str = f"Extracted dates: {raw_ev.get('extracted_dates', [])}."
                action = "Inspect document issuance and validity dates."

        elif f_type == AssessmentType.CROSS_DOCUMENT_CONSISTENCY.value:
            if "duplicate" in summary.lower() or raw_ev.get("matching_filename"):
                problem = "This file is identical to another submitted document."
                m_file = raw_ev.get("matching_filename", "companion file")
                m_type = raw_ev.get("matching_document_type", "another document")
                evidence_str = f"Identical file content matches '{m_file}' (submitted as {m_type})."
                action = "Review the discrepancy or request clarification."
            elif "code" in summary.lower() or raw_ev.get("observed_code"):
                problem = "The institution identifier differs from another submitted document."
                obs = raw_ev.get("observed_code", "N/A")
                exp = raw_ev.get("expected_code", "N/A")
                evidence_str = f"This file contains '{obs}'; the other document contains '{exp}'."
                action = "Review the discrepancy or request clarification."
            elif "name" in summary.lower() or raw_ev.get("observed_name"):
                problem = "The institution title differs from another submitted document."
                obs = raw_ev.get("observed_name", "N/A")
                exp = raw_ev.get("expected_name", "N/A")
                evidence_str = f"This file contains '{obs}'; companion document contains '{exp}'."
                action = "Verify whether this is an accepted abbreviation or sponsoring society designation."

        elif f_type == AssessmentType.AUTHENTICITY_AND_ANOMALIES.value:
            if "script" in summary.lower() or raw_ev.get("found_scripts"):
                problem = "The document contains active embedded scripts or executable actions."
                scripts = raw_ev.get("found_scripts", ["/JavaScript"])
                evidence_str = f"Embedded script action(s) detected: {scripts}."
                action = "Request a clean, static PDF replacement without interactive scripts."
            elif "consumer" in summary.lower() or raw_ev.get("detected_consumer_tools"):
                problem = "Document metadata indicates processing with consumer online software."
                tools = raw_ev.get("detected_consumer_tools", ["online editor"])
                evidence_str = f"Consumer editing signature detected: {', '.join(tools)}."
                action = "Advisory indicator only (often file compression). No rejection warranted on this basis alone; inspect official seal."
            elif "timestamp" in summary.lower():
                problem = "Metadata timestamp anomaly (modification date predates creation)."
                evidence_str = "Modification timestamp is earlier than creation timestamp (often caused by scanner workstation clock drift)."
                action = "Advisory indicator only. Review document visual seals."

        from core.validation.checks.content_rules import DOC_HUMAN_NAMES
        exp_doc_name = raw_ev.get("expected_document") or DOC_HUMAN_NAMES.get(doc_type, doc_type.replace('_', ' ').title())
        up_file_name = raw_ev.get("uploaded_filename") or filename

        return {
            "file": filename,
            "document_id": finding.get("document_id"),
            "document_type": doc_type,
            "expected_document": exp_doc_name,
            "uploaded_filename": up_file_name,
            "problem": problem,
            "evidence": evidence_str,
            "action": action,
            "state": f_state,
            "severity": finding.get("severity", "MEDIUM"),
            "title": finding.get("title", ""),
            "summary": summary,
            "raw_evidence": raw_ev
        }

    @classmethod
    def aggregate_application_assessments(cls, doc_assessments_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Conservatively aggregates validation results across all documents in an application dossier.
        Produces the single prominent application verdict, honest processing summary,
        compact document list, and concise actionable findings.
        """
        total_docs = len(doc_assessments_list)
        state_counts = {
            AssessmentState.PASS.value: 0,
            AssessmentState.ISSUE_FOUND.value: 0,
            AssessmentState.REVIEW_REQUIRED.value: 0,
            AssessmentState.INCOMPLETE.value: 0,
            AssessmentState.NOT_APPLICABLE.value: 0
        }

        all_actionable_findings = []
        compact_docs = []

        # Flags for processing summary
        reading_failed = False
        reading_scanned = False
        compliance_issues = False
        compliance_incomplete = False
        cross_doc_discrepancy = False

        for d in doc_assessments_list:
            ostate = d.get("overall_state", AssessmentState.INCOMPLETE.value)
            state_counts[ostate] = state_counts.get(ostate, 0) + 1

            fname = d.get("filename", "document.pdf")
            dtype = d.get("document_type", "STATUTORY_DOCUMENT")
            doc_id = d.get("document_id")

            # Determine compact document simple status: Clear, Review, Issue, or Incomplete
            if ostate == AssessmentState.ISSUE_FOUND.value:
                simple_status = "Issue"
            elif ostate == AssessmentState.REVIEW_REQUIRED.value:
                simple_status = "Review"
            elif ostate == AssessmentState.INCOMPLETE.value:
                simple_status = "Incomplete"
            elif ostate == AssessmentState.PASS.value:
                simple_status = "Clear"
            else:
                simple_status = "Incomplete"

            compact_docs.append({
                "id": doc_id,
                "filename": fname,
                "document_type": dtype,
                "simple_status": simple_status,
                "overall_state": ostate
            })

            # Check primary assessment statuses for processing summary
            ass_dict = d.get("assessments") or {}
            a_val = ass_dict.get(AssessmentType.VALIDITY_AND_READABILITY.value, {})
            a_comp = ass_dict.get(AssessmentType.REQUIRED_INFO_COMPLIANCE.value, {})
            a_cross = ass_dict.get(AssessmentType.CROSS_DOCUMENT_CONSISTENCY.value, {})

            if a_val.get("state") in [AssessmentState.ISSUE_FOUND.value, AssessmentState.INCOMPLETE.value]:
                reading_failed = True
            elif a_val.get("state") == AssessmentState.REVIEW_REQUIRED.value:
                reading_scanned = True

            if a_comp.get("state") == AssessmentState.ISSUE_FOUND.value:
                compliance_issues = True
            elif a_comp.get("state") == AssessmentState.INCOMPLETE.value:
                compliance_incomplete = True

            if a_cross.get("state") == AssessmentState.ISSUE_FOUND.value:
                cross_doc_discrepancy = True

            # Format actionable findings
            for f in d.get("actionable_findings", []):
                item = dict(f)
                item["document_id"] = doc_id
                item["document_type"] = dtype
                item["filename"] = fname
                formatted_finding = cls._format_actionable_finding(item, dtype, fname)
                all_actionable_findings.append(formatted_finding)

        # Sort compact documents: Issue (1) -> Review (2) -> Incomplete (3) -> Clear (4)
        status_priority = {"Issue": 1, "Review": 2, "Incomplete": 3, "Clear": 4}
        compact_docs.sort(key=lambda x: status_priority.get(x["simple_status"], 99))

        # Sort actionable findings: Issue first, then Review, then Incomplete
        finding_priority = {
            AssessmentState.ISSUE_FOUND.value: 1,
            AssessmentState.INCOMPLETE.value: 2,
            AssessmentState.REVIEW_REQUIRED.value: 3
        }
        all_actionable_findings.sort(key=lambda x: finding_priority.get(x.get("state"), 99))

        # ---------------------------------------------------------------------
        # 1. Prominent Application Verdict
        # ---------------------------------------------------------------------
        if total_docs == 0:
            verdict_key = "CHECK_INCOMPLETE"
            verdict_title = "CHECK INCOMPLETE — Required checks could not be completed"
            verdict_sentence = "No documents submitted for automated evaluation."
            app_status = "PENDING"
            app_desc = "No documents submitted for evaluation."
        elif state_counts[AssessmentState.ISSUE_FOUND.value] > 0:
            verdict_key = "ACTION_REQUIRED"
            verdict_title = "ACTION REQUIRED — Specific issues detected"
            verdict_sentence = "One or more documents require attention before this application can proceed."
            app_status = "DEFICIENT"
            app_desc = f"{state_counts[AssessmentState.ISSUE_FOUND.value]} document(s) have statutory or structural deficiencies."
        elif state_counts[AssessmentState.INCOMPLETE.value] > 0:
            verdict_key = "CHECK_INCOMPLETE"
            verdict_title = "CHECK INCOMPLETE — Required checks could not be completed"
            verdict_sentence = "Automated checks could not be completed for one or more submitted documents."
            app_status = "INCOMPLETE"
            app_desc = f"{state_counts[AssessmentState.INCOMPLETE.value]} document(s) have incomplete or failed assessments."
        elif state_counts[AssessmentState.REVIEW_REQUIRED.value] > 0:
            verdict_key = "MANUAL_REVIEW_REQUIRED"
            verdict_title = "MANUAL REVIEW REQUIRED — The evidence cannot be reliably assessed automatically"
            verdict_sentence = "Document evidence cannot be fully assessed by automated checks and requires manual examination by the scrutiny officer."
            app_status = "REVIEW_REQUIRED"
            app_desc = f"{state_counts[AssessmentState.REVIEW_REQUIRED.value]} document(s) require officer scrutiny (e.g. scanned deeds, advisory notices)."
        else:
            verdict_key = "CLEAR"
            verdict_title = "CLEAR — No issues detected by the completed checks"
            verdict_sentence = "All required automated checks passed. No issues were detected by these checks. Automated checks do not independently establish document authenticity."
            app_status = "CLEARED"
            app_desc = "All mandatory documents satisfied the four primary validation assessments."

        # ---------------------------------------------------------------------
        # 2. Honest Processing Summary
        # ---------------------------------------------------------------------
        # Document reading / OCR
        if reading_failed:
            ps_reading = "Failed"
        elif reading_scanned:
            ps_reading = "Not available"  # Scanned image without OCR engine
        else:
            ps_reading = "Passed"

        # Required info checks
        if compliance_issues:
            ps_compliance = "Issues found"
        elif compliance_incomplete:
            ps_compliance = "Incomplete"
        else:
            ps_compliance = "Passed"

        # Cross-document comparison
        if total_docs < 2:
            ps_cross = "Not applicable"
        elif cross_doc_discrepancy:
            ps_cross = "Discrepancy found"
        else:
            ps_cross = "Passed"

        # Authenticity verification: Verified only when actual reliable source used; otherwise Not verified
        ps_authenticity = "Not verified"

        processing_summary = {
            "reading_ocr": {
                "label": "Document reading/OCR",
                "status": ps_reading
            },
            "required_info": {
                "label": "Required information checks",
                "status": ps_compliance
            },
            "cross_document": {
                "label": "Cross-document comparison",
                "status": ps_cross
            },
            "authenticity": {
                "label": "Authenticity verification",
                "status": ps_authenticity,
                "note": "Automated checks do not independently establish document authenticity."
            }
        }

        # ---------------------------------------------------------------------
        # 3. Compact Document Verification Metrics
        # ---------------------------------------------------------------------
        mismatched_docs = set()
        attention_docs = set()
        for f in all_actionable_findings:
            doc_file = f.get("file") or f.get("uploaded_filename") or f.get("document_id")
            if "does not match the expected document" in f.get("problem", "").lower() or "mismatch" in f.get("problem", "").lower():
                mismatched_docs.add(doc_file)
            if f.get("state") in [AssessmentState.ISSUE_FOUND.value, AssessmentState.INCOMPLETE.value]:
                attention_docs.add(doc_file)

        for cd in compact_docs:
            if cd.get("simple_status") in ["Issue", "Incomplete"]:
                attention_docs.add(cd.get("filename") or cd.get("id"))

        total_uploaded = total_docs
        matched_count = max(0, total_uploaded - len(mismatched_docs))
        attention_count = len(attention_docs)

        if attention_count == 0 and len(mismatched_docs) == 0:
            result_text = "No document mismatches detected"
        elif attention_count == 1:
            result_text = "1 document needs attention"
        else:
            result_text = f"{attention_count} documents need attention"

        doc_verification = {
            "uploaded_count": total_uploaded,
            "matched_count": matched_count,
            "attention_count": attention_count,
            "mismatches_detected": len(mismatched_docs),
            "result_text": result_text
        }

        return {
            "application_status": app_status,
            "description": app_desc,
            "total_documents": total_docs,
            "state_counts": state_counts,
            "actionable_findings": all_actionable_findings,
            "verdict": {
                "key": verdict_key,
                "title": verdict_title,
                "sentence": verdict_sentence
            },
            "processing_summary": processing_summary,
            "compact_documents": compact_docs,
            "doc_verification": doc_verification
        }

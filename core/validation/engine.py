"""
Aegis Foundation - Modular Document Validation Engine
Orchestrates file integrity, PDF structure, text extraction, forensic heuristics,
content rules, and cross-document consistency checks into transparent, persisted runs.
"""

import json
import os
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.db import get_db
from core.audit import log_event
from core.validation.schema import (
    CheckResult,
    CheckStatus,
    CheckSeverity,
    CheckCategory,
    ValidationRunResult,
    ENGINE_VERSION
)
from core.validation.checks.file_integrity import run_file_integrity_checks
from core.validation.checks.pdf_structure import run_pdf_structural_checks
from core.validation.checks.text_extraction import run_text_extraction_checks
from core.validation.checks.forensics import run_forensic_heuristic_checks
from core.validation.checks.content_rules import run_content_rule_checks
from core.validation.checks.cross_document import run_cross_document_checks


class ValidationEngine:
    """Core validation pipeline orchestrator."""

    @classmethod
    def validate_document(
        cls,
        doc_id: str,
        app_id: str,
        filepath: str,
        filename: str,
        doc_type: str,
        file_bytes: Optional[bytes] = None,
        triggered_by: str = "AUTO_UPLOAD",
        db_path: Optional[str] = None
    ) -> ValidationRunResult:
        """Executes full validation suite on a document and persists results."""
        run_id = f"vrun_{uuid.uuid4().hex[:12]}"
        started_at = datetime.now().isoformat()
        checks: List[CheckResult] = []

        # Read file bytes if not supplied
        if file_bytes is None:
            try:
                with open(filepath, "rb") as f:
                    file_bytes = f.read()
            except Exception as e:
                checks.append(
                    CheckResult(
                        check_id="FILE_STORAGE_ACCESS",
                        check_name="File Storage Access",
                        category=CheckCategory.FILE_INTEGRITY.value,
                        status=CheckStatus.ERROR.value,
                        severity=CheckSeverity.CRITICAL.value,
                        summary=f"Failed to read file from storage: {e}",
                        details=str(e),
                        recommendation="Check filesystem permissions and storage directory."
                    )
                )
                completed_at = datetime.now().isoformat()
                run_res = ValidationRunResult.from_checks(
                    run_id=run_id,
                    document_id=doc_id,
                    application_id=app_id,
                    checks=checks,
                    started_at=started_at,
                    completed_at=completed_at,
                    triggered_by=triggered_by
                )
                cls._persist_run(run_res, db_path=db_path)
                return run_res

        # Fetch companion documents & application metadata for cross-document validation
        companion_docs = []
        app_meta = {}
        with get_db(db_path) as conn:
            cur_app = conn.execute(
                """
                SELECT a.*, i.name as institution_name, i.code as institution_code, i.state, i.city
                FROM applications a
                JOIN institutions i ON a.institution_id = i.id
                WHERE a.id = ?
                """,
                (app_id,)
            )
            row_app = cur_app.fetchone()
            if row_app:
                app_meta = dict(row_app)

            cur_docs = conn.execute(
                "SELECT id, document_type, filename, sha256_hash, file_size FROM documents WHERE application_id = ?",
                (app_id,)
            )
            companion_docs = [dict(r) for r in cur_docs.fetchall()]

        # Stage 1: File Integrity Checks
        try:
            integrity_checks = run_file_integrity_checks(
                filepath=filepath,
                filename=filename,
                file_bytes=file_bytes,
                existing_hashes=companion_docs,
                current_doc_id=doc_id
            )
            checks.extend(integrity_checks)
        except Exception as e:
            checks.append(
                CheckResult(
                    check_id="STAGE_INTEGRITY_ERROR",
                    check_name="Integrity Pipeline Execution",
                    category=CheckCategory.FILE_INTEGRITY.value,
                    status=CheckStatus.ERROR.value,
                    severity=CheckSeverity.HIGH.value,
                    summary=f"Integrity check crashed: {e}",
                    details=str(e)
                )
            )

        # If zero-byte or corrupt non-PDF, halt further PDF-specific checks
        is_zero_byte = len(file_bytes) == 0
        ext = os.path.splitext(filename)[1].lower()
        sha256 = next((c.observed_value for c in checks if c.check_id == "FILE_SHA256_DIGEST"), "")

        if not is_zero_byte and ext == ".pdf":
            # Stage 2: PDF Structural Checks
            try:
                struct_checks = run_pdf_structural_checks(filepath=filepath, file_bytes=file_bytes)
                checks.extend(struct_checks)
            except Exception as e:
                checks.append(
                    CheckResult(
                        check_id="STAGE_STRUCTURAL_ERROR",
                        check_name="Structural Pipeline Execution",
                        category=CheckCategory.DOCUMENT_STRUCTURE.value,
                        status=CheckStatus.ERROR.value,
                        severity=CheckSeverity.HIGH.value,
                        summary=f"Structural check crashed: {e}",
                        details=str(e)
                    )
                )

            # Stage 3: Text Extraction & Readability
            extracted_text = ""
            is_scanned = False
            try:
                text_res = run_text_extraction_checks(filepath=filepath, file_bytes=file_bytes)
                checks.extend(text_res["checks"])
                extracted_text = text_res["extracted_text"]
                is_scanned = text_res["is_scanned"]
            except Exception as e:
                checks.append(
                    CheckResult(
                        check_id="STAGE_TEXT_ERROR",
                        check_name="Text Extraction Execution",
                        category=CheckCategory.CONTENT.value,
                        status=CheckStatus.ERROR.value,
                        severity=CheckSeverity.HIGH.value,
                        summary=f"Text extraction crashed: {e}",
                        details=str(e)
                    )
                )

            # Stage 4: Forensic Heuristics
            try:
                forensic_checks = run_forensic_heuristic_checks(filepath=filepath, file_bytes=file_bytes)
                checks.extend(forensic_checks)
            except Exception as e:
                checks.append(
                    CheckResult(
                        check_id="STAGE_FORENSIC_ERROR",
                        check_name="Forensic Pipeline Execution",
                        category=CheckCategory.AUTHENTICITY.value,
                        status=CheckStatus.ERROR.value,
                        severity=CheckSeverity.HIGH.value,
                        summary=f"Forensic heuristic check crashed: {e}",
                        details=str(e)
                    )
                )

            # Stage 5: Content & Rule Registry Matching
            try:
                content_checks = run_content_rule_checks(
                    doc_type=doc_type,
                    extracted_text=extracted_text,
                    is_scanned=is_scanned,
                    filename=filename
                )
                checks.extend(content_checks)
            except Exception as e:
                checks.append(
                    CheckResult(
                        check_id="STAGE_CONTENT_ERROR",
                        check_name="Content Rules Execution",
                        category=CheckCategory.CONTENT.value,
                        status=CheckStatus.ERROR.value,
                        severity=CheckSeverity.HIGH.value,
                        summary=f"Content rule check crashed: {e}",
                        details=str(e)
                    )
                )

            # Stage 6: Cross-Document Consistency
            try:
                cross_checks = run_cross_document_checks(
                    current_doc_id=doc_id,
                    current_doc_type=doc_type,
                    current_sha256=sha256,
                    extracted_text=extracted_text,
                    application=app_meta,
                    companion_docs=companion_docs
                )
                checks.extend(cross_checks)
            except Exception as e:
                checks.append(
                    CheckResult(
                        check_id="STAGE_CROSS_DOC_ERROR",
                        check_name="Cross-Document Pipeline Execution",
                        category=CheckCategory.CONSISTENCY.value,
                        status=CheckStatus.ERROR.value,
                        severity=CheckSeverity.HIGH.value,
                        summary=f"Cross-document consistency check crashed: {e}",
                        details=str(e)
                    )
                )

        completed_at = datetime.now().isoformat()
        run_res = ValidationRunResult.from_checks(
            run_id=run_id,
            document_id=doc_id,
            application_id=app_id,
            checks=checks,
            started_at=started_at,
            completed_at=completed_at,
            triggered_by=triggered_by
        )

        cls._persist_run(run_res, db_path=db_path)

        # Backward compatibility with existing forensic_results table
        cls._sync_legacy_forensics(doc_id, app_id, run_res, db_path=db_path)

        log_event(
            "DOCUMENT_VALIDATED",
            "validation_run",
            run_id,
            actor=triggered_by,
            details={
                "document_id": doc_id,
                "application_id": app_id,
                "status": run_res.status,
                "total_checks": run_res.total_checks,
                "passed": run_res.passed_checks,
                "failed": run_res.failed_checks,
                "warnings": run_res.warning_checks,
                "review_required": run_res.review_required_checks
            },
            db_path=db_path
        )

        return run_res

    @classmethod
    def _persist_run(cls, run_res: ValidationRunResult, db_path: Optional[str] = None):
        """Persists the validation run and all check results into SQLite."""
        with get_db(db_path) as conn:
            # 1. Insert validation run record
            conn.execute(
                """
                INSERT INTO validation_runs (
                    id, document_id, application_id, engine_version, status,
                    total_checks, passed_checks, failed_checks, warning_checks,
                    review_required_checks, not_run_checks, error_checks,
                    summary_text, started_at, completed_at, triggered_by
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_res.run_id,
                    run_res.document_id,
                    run_res.application_id,
                    run_res.engine_version,
                    run_res.status,
                    run_res.total_checks,
                    run_res.passed_checks,
                    run_res.failed_checks,
                    run_res.warning_checks,
                    run_res.review_required_checks,
                    run_res.not_run_checks,
                    run_res.error_checks,
                    run_res.summary_text,
                    run_res.started_at,
                    run_res.completed_at,
                    run_res.triggered_by
                )
            )

            # 2. Insert each individual check record
            for c in run_res.checks:
                chk_id = f"vchk_{uuid.uuid4().hex[:12]}"
                conn.execute(
                    """
                    INSERT INTO validation_checks (
                        id, run_id, document_id, application_id, check_id, check_name,
                        category, status, severity, summary, details, evidence_json,
                        expected_value, observed_value, recommendation, duration_ms,
                        engine_version, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        chk_id,
                        run_res.run_id,
                        run_res.document_id,
                        run_res.application_id,
                        c.check_id,
                        c.check_name,
                        c.category,
                        c.status,
                        c.severity,
                        c.summary,
                        c.details,
                        json.dumps(c.evidence, default=str),
                        c.expected_value,
                        c.observed_value,
                        c.recommendation,
                        c.duration_ms,
                        c.engine_version,
                        c.created_at
                    )
                )

    @classmethod
    def _sync_legacy_forensics(cls, doc_id: str, app_id: str, run_res: ValidationRunResult, db_path: Optional[str] = None):
        """Maintains backward compatibility with legacy forensic_results table."""
        # Calculate equivalent risk band from real executed checks
        if run_res.failed_checks > 0 or run_res.error_checks > 0:
            risk_band = "HIGH"
            risk_score = 0.85
        elif run_res.review_required_checks > 0 or run_res.warning_checks > 0:
            risk_band = "MEDIUM"
            risk_score = 0.45
        else:
            risk_band = "LOW"
            risk_score = 0.05

        flag_summaries = [f"{c.check_id}: {c.summary}" for c in run_res.checks if c.status in ["FAIL", "WARNING", "REVIEW_REQUIRED"]]

        with get_db(db_path) as conn:
            conn.execute(
                """
                INSERT INTO forensic_results (id, document_id, application_id, risk_score, risk_band, pdf_audit_json, findings_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(document_id) DO UPDATE SET
                    risk_score=excluded.risk_score,
                    risk_band=excluded.risk_band,
                    pdf_audit_json=excluded.pdf_audit_json,
                    findings_json=excluded.findings_json,
                    analysed_at=CURRENT_TIMESTAMP
                """,
                (
                    f"frn_{run_res.run_id[:10]}",
                    doc_id,
                    app_id,
                    risk_score,
                    risk_band,
                    json.dumps(run_res.to_dict(), default=str),
                    json.dumps(flag_summaries)
                )
            )

    @classmethod
    def get_latest_run_for_document(cls, doc_id: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieves the most recent validation run and all check results for a document."""
        with get_db(db_path) as conn:
            run_cur = conn.execute(
                """
                SELECT * FROM validation_runs
                WHERE document_id = ?
                ORDER BY started_at DESC
                LIMIT 1
                """,
                (doc_id,)
            )
            run_row = run_cur.fetchone()
            if not run_row:
                return None

            run_dict = dict(run_row)

            # Fetch checks
            chk_cur = conn.execute(
                """
                SELECT * FROM validation_checks
                WHERE run_id = ?
                ORDER BY 
                    CASE status
                        WHEN 'FAIL' THEN 1
                        WHEN 'REVIEW_REQUIRED' THEN 2
                        WHEN 'WARNING' THEN 3
                        WHEN 'ERROR' THEN 4
                        WHEN 'PASS' THEN 5
                        WHEN 'NOT_RUN' THEN 6
                    END,
                    category ASC
                """,
                (run_dict["id"],)
            )
            checks = []
            for r in chk_cur.fetchall():
                c_dict = dict(r)
                if c_dict.get("evidence_json"):
                    try:
                        c_dict["evidence"] = json.loads(c_dict["evidence_json"])
                    except Exception:
                        c_dict["evidence"] = {}
                else:
                    c_dict["evidence"] = {}
                checks.append(c_dict)

            run_dict["checks"] = checks

            # Fetch finding dispositions
            disp_cur = conn.execute(
                "SELECT * FROM finding_dispositions WHERE document_id = ? ORDER BY created_at DESC",
                (doc_id,)
            )
            run_dict["dispositions"] = [dict(d) for d in disp_cur.fetchall()]

            # Fetch document type for rule context
            doc_type_cur = conn.execute("SELECT document_type, filename FROM documents WHERE id = ?", (doc_id,))
            doc_info = doc_type_cur.fetchone()
            dtype = doc_info["document_type"] if doc_info else "STATUTORY_DOCUMENT"

            # Compute Four Primary Assessments
            from core.validation.assessment import AssessmentAggregator
            assessment_data = AssessmentAggregator.aggregate_document_run(run_dict, doc_type=dtype)
            run_dict["assessments"] = assessment_data["assessments"]
            run_dict["assessment_overall_state"] = assessment_data["overall_state"]
            run_dict["actionable_findings"] = assessment_data["actionable_findings"]

            return run_dict

    @classmethod
    def get_application_validation_summary(cls, app_id: str, db_path: Optional[str] = None) -> Dict[str, Any]:
        """Calculates aggregated validation metrics across all documents in an application."""
        with get_db(db_path) as conn:
            docs_cur = conn.execute("SELECT id, document_type, filename FROM documents WHERE application_id = ?", (app_id,))
            docs = [dict(r) for r in docs_cur.fetchall()]

            doc_summaries = []
            total_checks = 0
            total_passed = 0
            total_failed = 0
            total_warnings = 0
            total_review = 0
            total_not_run = 0
            total_errors = 0

            doc_assessments_for_app = []

            for d in docs:
                run = cls.get_latest_run_for_document(d["id"], db_path=db_path)
                if run:
                    total_checks += run["total_checks"]
                    total_passed += run["passed_checks"]
                    total_failed += run["failed_checks"]
                    total_warnings += run["warning_checks"]
                    total_review += run["review_required_checks"]
                    total_not_run += run["not_run_checks"]
                    total_errors += run["error_checks"]
                    doc_summaries.append({
                        "document": d,
                        "run": run
                    })
                    doc_assessments_for_app.append({
                        "document_id": d["id"],
                        "document_type": d["document_type"],
                        "filename": d["filename"],
                        "overall_state": run.get("assessment_overall_state"),
                        "assessments": run.get("assessments"),
                        "actionable_findings": run.get("actionable_findings", [])
                    })
                else:
                    doc_summaries.append({
                        "document": d,
                        "run": None
                    })

            from core.validation.assessment import AssessmentAggregator
            app_assessments = AssessmentAggregator.aggregate_application_assessments(doc_assessments_for_app)

            overall_status = "PASSED"
            if total_errors > 0:
                overall_status = "ERROR"
            elif total_failed > 0:
                overall_status = "FAILED"
            elif total_review > 0:
                overall_status = "REVIEW_REQUIRED"
            elif total_warnings > 0:
                overall_status = "WARNING"
            elif total_checks == 0:
                overall_status = "PENDING"

            return {
                "application_id": app_id,
                "document_count": len(docs),
                "total_checks": total_checks,
                "passed_checks": total_passed,
                "failed_checks": total_failed,
                "warning_checks": total_warnings,
                "review_required_checks": total_review,
                "not_run_checks": total_not_run,
                "error_checks": total_errors,
                "overall_status": overall_status,
                "documents": doc_summaries,
                "app_assessments": app_assessments
            }

    @classmethod
    def record_finding_disposition(
        cls,
        check_record_id: str,
        doc_id: str,
        app_id: str,
        officer_email: str,
        disposition: str,
        officer_notes: str,
        db_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Records a human officer review disposition for a specific automated finding."""
        disp_id = f"disp_{uuid.uuid4().hex[:12]}"
        created_at = datetime.now().isoformat()
        with get_db(db_path) as conn:
            conn.execute(
                """
                INSERT INTO finding_dispositions (
                    id, check_record_id, document_id, application_id, officer_email,
                    disposition, officer_notes, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (disp_id, check_record_id, doc_id, app_id, officer_email, disposition, officer_notes, created_at)
            )

        log_event(
            "FINDING_DISPOSITION_RECORDED",
            "finding_disposition",
            disp_id,
            actor=officer_email,
            details={"check_record_id": check_record_id, "disposition": disposition, "notes": officer_notes},
            db_path=db_path
        )
        return {"id": disp_id, "disposition": disposition, "officer_notes": officer_notes, "created_at": created_at}

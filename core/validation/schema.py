"""
Aegis Foundation - Document Validation Schema & Data Models
Defines typed schemas and enumerations for all validation pipeline checks.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import json

ENGINE_VERSION = "2.0.0-phase2"


class CheckStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    NOT_RUN = "NOT_RUN"
    ERROR = "ERROR"


class CheckSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class CheckCategory(str, Enum):
    FILE_INTEGRITY = "file_integrity"
    DOCUMENT_STRUCTURE = "document_structure"
    METADATA = "metadata"
    CONTENT = "content"
    CONSISTENCY = "consistency"
    AUTHENTICITY = "authenticity"


class AssessmentType(str, Enum):
    VALIDITY_AND_READABILITY = "validity_and_readability"
    REQUIRED_INFO_COMPLIANCE = "required_info_compliance"
    CROSS_DOCUMENT_CONSISTENCY = "cross_document_consistency"
    AUTHENTICITY_AND_ANOMALIES = "authenticity_and_anomalies"


class AssessmentState(str, Enum):
    PASS = "PASS"
    ISSUE_FOUND = "ISSUE_FOUND"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    INCOMPLETE = "INCOMPLETE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass
class PrimaryAssessment:
    assessment_type: str
    title: str
    state: str  # AssessmentState
    severity: str  # CheckSeverity
    summary: str
    problem_explanation: Optional[str] = None
    evidence: Dict[str, Any] = field(default_factory=dict)
    recommendation: Optional[str] = None
    underlying_check_ids: List[str] = field(default_factory=list)
    underlying_checks: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CheckResult:
    check_id: str
    check_name: str
    category: str
    status: str
    severity: str
    summary: str
    details: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)
    expected_value: Optional[str] = None
    observed_value: Optional[str] = None
    recommendation: Optional[str] = None
    duration_ms: float = 0.0
    engine_version: str = ENGINE_VERSION
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


@dataclass
class ValidationRunResult:
    run_id: str
    document_id: str
    application_id: str
    engine_version: str
    status: str
    total_checks: int
    passed_checks: int
    failed_checks: int
    warning_checks: int
    review_required_checks: int
    not_run_checks: int
    error_checks: int
    summary_text: str
    started_at: str
    completed_at: str
    triggered_by: str
    checks: List[CheckResult] = field(default_factory=list)

    @classmethod
    def from_checks(
        cls,
        run_id: str,
        document_id: str,
        application_id: str,
        checks: List[CheckResult],
        started_at: str,
        completed_at: str,
        triggered_by: str = "AUTO_UPLOAD",
        engine_version: str = ENGINE_VERSION
    ) -> "ValidationRunResult":
        total = len(checks)
        passed = sum(1 for c in checks if c.status == CheckStatus.PASS.value)
        failed = sum(1 for c in checks if c.status == CheckStatus.FAIL.value)
        warnings = sum(1 for c in checks if c.status == CheckStatus.WARNING.value)
        review_req = sum(1 for c in checks if c.status == CheckStatus.REVIEW_REQUIRED.value)
        not_run = sum(1 for c in checks if c.status == CheckStatus.NOT_RUN.value)
        errors = sum(1 for c in checks if c.status == CheckStatus.ERROR.value)

        # Compute overall status
        if errors > 0:
            overall = "ERROR"
        elif failed > 0:
            overall = "FAILED"
        elif review_req > 0:
            overall = "REVIEW_REQUIRED"
        elif warnings > 0:
            overall = "WARNING"
        else:
            overall = "PASSED"

        summary = f"{passed}/{total} checks passed, {failed} failed, {warnings} warnings, {review_req} review required."

        return cls(
            run_id=run_id,
            document_id=document_id,
            application_id=application_id,
            engine_version=engine_version,
            status=overall,
            total_checks=total,
            passed_checks=passed,
            failed_checks=failed,
            warning_checks=warnings,
            review_required_checks=review_req,
            not_run_checks=not_run,
            error_checks=errors,
            summary_text=summary,
            started_at=started_at,
            completed_at=completed_at,
            triggered_by=triggered_by,
            checks=checks
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

"""
Aegis Foundation - Document Validation Engine Package
"""

from core.validation.schema import (
    CheckResult,
    CheckStatus,
    CheckSeverity,
    CheckCategory,
    ValidationRunResult,
    AssessmentType,
    AssessmentState,
    PrimaryAssessment,
    ENGINE_VERSION
)
from core.validation.rules import (
    RULE_REGISTRY,
    RULE_REGISTRY_VERSION,
    DocumentTypeRule,
    get_rule_for_document_type
)
from core.validation.assessment import AssessmentAggregator
from core.validation.engine import ValidationEngine

__all__ = [
    "CheckResult",
    "CheckStatus",
    "CheckSeverity",
    "CheckCategory",
    "ValidationRunResult",
    "AssessmentType",
    "AssessmentState",
    "PrimaryAssessment",
    "AssessmentAggregator",
    "ENGINE_VERSION",
    "RULE_REGISTRY",
    "RULE_REGISTRY_VERSION",
    "DocumentTypeRule",
    "get_rule_for_document_type",
    "ValidationEngine"
]

"""
Aegis Foundation - Cross-Document Consistency Checks
Compares extracted institutional entities, permanent codes, and cryptographic digests
across all documents within the same institutional application dossier.
"""

import os
import re
import time
from typing import Any, Dict, List, Optional
from core.validation.schema import CheckResult, CheckStatus, CheckSeverity, CheckCategory, ENGINE_VERSION


def run_cross_document_checks(
    current_doc_id: str,
    current_doc_type: str,
    current_sha256: str,
    extracted_text: str,
    application: Dict[str, Any],
    companion_docs: List[Dict[str, Any]]
) -> List[CheckResult]:
    """Runs cross-document consistency checks comparing current document with companion dossier files."""
    results = []
    inst_name = application.get("institution_name", "").strip()
    inst_code = application.get("institution_code", "").strip()

    # 1. CROSS_DOC_DUPLICATE_FILES
    t0 = time.perf_counter()
    duplicates = [
        d for d in companion_docs
        if d.get("id") != current_doc_id and d.get("sha256_hash") == current_sha256
    ]
    dur = (time.perf_counter() - t0) * 1000

    if duplicates:
        dup_names = [f"'{d.get('filename')}' (Category: {d.get('document_type')})" for d in duplicates]
        results.append(
            CheckResult(
                check_id="CROSS_DOC_DUPLICATE_FILES",
                check_name="Cross-Document Duplicate Payload Check",
                category=CheckCategory.CONSISTENCY.value,
                status=CheckStatus.WARNING.value,
                severity=CheckSeverity.MEDIUM.value,
                summary=f"Duplicate submission: Exact same file used for {len(duplicates)} other checklist item(s).",
                details=(
                    f"This document shares the exact byte-level SHA-256 hash ({current_sha256[:16]}...) with: {'; '.join(dup_names)}. "
                    "In statutory scrutiny, each mandatory checklist requirement (e.g. Land Title vs Fire Safety) "
                    "must be fulfilled by its distinct statutory certificate, not duplicate re-uploads."
                ),
                expected_value="Distinct statutory proof for each checklist requirement",
                observed_value=f"Identical bytes to {len(duplicates)} file(s): {', '.join(dup_names)}",
                evidence={"duplicate_documents": duplicates, "sha256": current_sha256},
                recommendation="Replace duplicate upload with the specific statutory certificate required for this heading.",
                duration_ms=dur
            )
        )
    else:
        results.append(
            CheckResult(
                check_id="CROSS_DOC_DUPLICATE_FILES",
                check_name="Cross-Document Duplicate Payload Check",
                category=CheckCategory.CONSISTENCY.value,
                status=CheckStatus.PASS.value,
                severity=CheckSeverity.INFO.value,
                summary="Dossier distinction verified: File bytes are unique within this application.",
                details="No other checklist item in this application shares the same cryptographic hash.",
                duration_ms=dur
            )
        )

    # 2. CROSS_DOC_INSTITUTION_CODE
    t0 = time.perf_counter()
    dur = (time.perf_counter() - t0) * 1000
    if inst_code and extracted_text:
        # Check if declared code appears, or if another institution code pattern appears
        # Typical pattern: 3-6 letters, hyphen, 2 letters, hyphen, numbers (e.g. APEX-MH-1001)
        found_codes = re.findall(r'\b[A-Z]{3,8}-[A-Z]{2}-\d{3,6}\b', extracted_text)
        if found_codes:
            unique_found = set(found_codes)
            if inst_code in unique_found and len(unique_found) == 1:
                results.append(
                    CheckResult(
                        check_id="CROSS_DOC_INSTITUTION_CODE",
                        check_name="Permanent Institution ID Alignment",
                        category=CheckCategory.CONSISTENCY.value,
                        status=CheckStatus.PASS.value,
                        severity=CheckSeverity.INFO.value,
                        summary=f"Institution Code alignment confirmed: Document references '{inst_code}'.",
                        details=f"Permanent AICTE code in text directly matches applicant profile code '{inst_code}'.",
                        expected_value=inst_code,
                        observed_value=inst_code,
                        duration_ms=dur
                    )
                )
            elif inst_code not in unique_found:
                results.append(
                    CheckResult(
                        check_id="CROSS_DOC_INSTITUTION_CODE",
                        check_name="Permanent Institution ID Alignment",
                        category=CheckCategory.CONSISTENCY.value,
                        status=CheckStatus.REVIEW_REQUIRED.value,
                        severity=CheckSeverity.HIGH.value,
                        summary=f"Mismatched Permanent Code detected in text: Found {list(unique_found)}.",
                        details=(
                            f"Applicant declared code '{inst_code}', but document text explicitly references "
                            f"{list(unique_found)}. This may indicate a misfiled document belonging to another college."
                        ),
                        expected_value=inst_code,
                        observed_value=", ".join(unique_found),
                        evidence={"declared_code": inst_code, "observed_codes": list(unique_found)},
                        recommendation="Scrutiny officer must verify whether this certificate was erroneously issued to another college.",
                        duration_ms=dur
                    )
                )
            else:
                results.append(
                    CheckResult(
                        check_id="CROSS_DOC_INSTITUTION_CODE",
                        check_name="Permanent Institution ID Alignment",
                        category=CheckCategory.CONSISTENCY.value,
                        status=CheckStatus.PASS.value,
                        severity=CheckSeverity.INFO.value,
                        summary=f"Institution Code verified: Document references '{inst_code}'.",
                        observed_value=inst_code,
                        duration_ms=dur
                    )
                )
        else:
            results.append(
                CheckResult(
                    check_id="CROSS_DOC_INSTITUTION_CODE",
                    check_name="Permanent Institution ID Alignment",
                    category=CheckCategory.CONSISTENCY.value,
                    status=CheckStatus.NOT_RUN.value,
                    severity=CheckSeverity.INFO.value,
                    summary="Institution Code check not run: No standard permanent code patterns found in text.",
                    details="Permanent code format [XXX-XX-0000] not found in extracted text streams.",
                    duration_ms=dur
                )
            )
    else:
        results.append(
            CheckResult(
                check_id="CROSS_DOC_INSTITUTION_CODE",
                check_name="Permanent Institution ID Alignment",
                category=CheckCategory.CONSISTENCY.value,
                status=CheckStatus.NOT_RUN.value,
                severity=CheckSeverity.INFO.value,
                summary="Institution Code check not run: Text absent or scanned document.",
                duration_ms=dur
            )
        )

    # 3. CROSS_DOC_INSTITUTION_NAME
    t0 = time.perf_counter()
    dur = (time.perf_counter() - t0) * 1000
    if inst_name and extracted_text and len(extracted_text) > 50:
        # Token overlap check (ignoring stopwords like of, and, the, institute, college)
        stopwords = {"of", "and", "the", "institute", "technology", "college", "engineering", "sciences", "for"}
        inst_tokens = set(re.findall(r'[a-zA-Z]{3,}', inst_name.lower())) - stopwords
        text_tokens = set(re.findall(r'[a-zA-Z]{3,}', extracted_text.lower()))

        overlap = inst_tokens.intersection(text_tokens)
        if inst_tokens and len(overlap) >= min(len(inst_tokens), 1):
            results.append(
                CheckResult(
                    check_id="CROSS_DOC_INSTITUTION_NAME",
                    check_name="Institutional Name Consistency",
                    category=CheckCategory.CONSISTENCY.value,
                    status=CheckStatus.PASS.value,
                    severity=CheckSeverity.INFO.value,
                    summary=f"Institutional identity aligned: Distinctive tokens {list(overlap)} matched in document.",
                    details=f"Document text contains institutional tokens matching declared name '{inst_name}'.",
                    expected_value=inst_name,
                    observed_value=f"Tokens matched: {', '.join(overlap)}",
                    evidence={"institution_name": inst_name, "matched_tokens": list(overlap)},
                    duration_ms=dur
                )
            )
        else:
            results.append(
                CheckResult(
                    check_id="CROSS_DOC_INSTITUTION_NAME",
                    check_name="Institutional Name Consistency",
                    category=CheckCategory.CONSISTENCY.value,
                    status=CheckStatus.REVIEW_REQUIRED.value,
                    severity=CheckSeverity.LOW.value,
                    summary=f"Unconfirmed institution name in text: Distinctive tokens for '{inst_name}' not observed.",
                    details=(
                        f"Expected institutional name tokens: {list(inst_tokens)}. Document text does not contain "
                        "distinctive name matches. Note: Title deeds frequently list Society/Trust names rather than "
                        "the college name itself; officer scrutiny of Trust registration is required."
                    ),
                    expected_value=inst_name,
                    observed_value="Name tokens not found in text stream",
                    evidence={"institution_name": inst_name, "expected_tokens": list(inst_tokens)},
                    recommendation="Verify whether deed was executed under the parent Trust/Society name rather than the institution name.",
                    duration_ms=dur
                )
            )
    else:
        results.append(
            CheckResult(
                check_id="CROSS_DOC_INSTITUTION_NAME",
                check_name="Institutional Name Consistency",
                category=CheckCategory.CONSISTENCY.value,
                status=CheckStatus.NOT_RUN.value,
                severity=CheckSeverity.INFO.value,
                summary="Institutional name check deferred: Document is scanned or text stream absent.",
                details="Name verification requires physical visual inspection of scanned deed header.",
                duration_ms=dur
            )
        )

    return results

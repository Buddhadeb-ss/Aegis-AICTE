"""
Aegis Foundation - Document Content & Rule-Based Validation Checks
Evaluates extracted text against versioned statutory rules from the Rule Registry.
"""

import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from core.validation.schema import CheckResult, CheckStatus, CheckSeverity, CheckCategory, ENGINE_VERSION
import os
from core.validation.rules import get_rule_for_document_type, RULE_REGISTRY_VERSION

CATEGORY_CONCORDANCE_RULES = {
    "LAND_TITLE_CERTIFICATE": {
        "expected_name": "Land Title Certificate",
        "concordant_tokens": ["land", "title", "deed", "ownership", "patta", "khasra", "revenue", "property", "registry", "encumbrance", "plot", "survey", "conveyance", "mutation", "satbara"],
        "discordant_tokens": ["affiliation", "syllabus", "curriculum", "fee", "receipt", "salary", "marksheet", "admit", "building_plan", "blueprint", "fire_safety", "fire_noc", "affidavit", "faculty", "cadre", "occupancy"]
    },
    "BUILDING_PLAN_APPROVAL": {
        "expected_name": "Building Plan Approval",
        "concordant_tokens": ["building", "plan", "sanction", "approval", "blueprint", "architect", "municipal", "layout", "fsi", "floor", "built_up", "map"],
        "discordant_tokens": ["affiliation", "land_deed", "land_title", "patta", "khasra", "syllabus", "fee", "salary", "fire_safety", "fire_noc", "affidavit", "faculty"]
    },
    "AICTE_AFFIDAVIT_1": {
        "expected_name": "Statutory Affidavit (AICTE Affidavit 1)",
        "concordant_tokens": ["affidavit", "stamp", "undertaking", "notary", "oath", "sworn", "non_judicial", "annexure", "declaration"],
        "discordant_tokens": ["affiliation", "syllabus", "building_plan", "blueprint", "fire_safety", "fire_noc", "land_title", "land_deed", "salary"]
    },
    "FIRE_SAFETY_CERTIFICATE": {
        "expected_name": "Fire Safety Certificate (NOC)",
        "concordant_tokens": ["fire", "safety", "noc", "emergency", "extinguisher", "cfo", "fire_officer", "prevention"],
        "discordant_tokens": ["affiliation", "land_title", "land_deed", "patta", "building_plan", "blueprint", "affidavit", "syllabus", "salary", "faculty"]
    },
    "FACULTY_CADRE_CERTIFICATE": {
        "expected_name": "Faculty Cadre Certificate",
        "concordant_tokens": ["faculty", "cadre", "teaching", "staff", "professor", "roster", "salary", "pay_scale"],
        "discordant_tokens": ["affiliation", "land_title", "building_plan", "fire_safety"]
    },
    "OCCUPANCY_CERTIFICATE": {
        "expected_name": "Occupancy Certificate",
        "concordant_tokens": ["occupancy", "completion", "possession", "fit_out", "completion_certificate"],
        "discordant_tokens": ["affiliation", "land_title", "fire_safety", "affidavit"]
    },
    "CLARIFICATION_EVIDENCE": {
        "expected_name": "Clarification Supporting Evidence",
        "concordant_tokens": ["clarification", "evidence", "proof", "supplementary", "response", "rectification", "report"],
        "discordant_tokens": []
    }
}

DOC_HUMAN_NAMES = {k: v["expected_name"] for k, v in CATEGORY_CONCORDANCE_RULES.items()}


def run_category_filename_concordance_check(
    doc_type: str,
    filename: str,
    extracted_text: str = "",
    is_scanned: bool = False
) -> CheckResult:
    """
    Evaluates concordance between the expected document category and the uploaded filename/header.
    Distinguishes naming/category mismatches without claiming filename matches prove authenticity.
    """
    t0 = time.perf_counter()
    rule = CATEGORY_CONCORDANCE_RULES.get(doc_type)
    expected_name = rule["expected_name"] if rule else doc_type.replace('_', ' ').title()

    if not filename:
        dur = (time.perf_counter() - t0) * 1000
        return CheckResult(
            check_id="DOC_CATEGORY_FILENAME_MATCH",
            check_name="Document Category & Filename Concordance",
            category=CheckCategory.CONTENT.value,
            status=CheckStatus.NOT_RUN.value,
            severity=CheckSeverity.INFO.value,
            summary="Filename not supplied for category concordance check.",
            details="No filename provided to evaluate concordance.",
            expected_value=expected_name,
            observed_value="Empty filename",
            evidence={"expected_document": expected_name, "uploaded_filename": ""},
            recommendation="Ensure document is uploaded with its original filename.",
            duration_ms=dur
        )

    base = os.path.splitext(os.path.basename(filename))[0].lower()
    fn_clean = re.sub(r'[^a-zA-Z0-9]', ' ', base)
    fn_tokens = set(fn_clean.split())

    concordant_tokens = rule["concordant_tokens"] if rule else []
    discordant_tokens = rule["discordant_tokens"] if rule else []

    # 1. Explicit discordant token in filename (e.g. affiliation letter under land title)
    found_discordant = [t for t in discordant_tokens if t in fn_tokens or (t in fn_clean and len(t) > 3)]
    dur = (time.perf_counter() - t0) * 1000

    if found_discordant:
        return CheckResult(
            check_id="DOC_CATEGORY_FILENAME_MATCH",
            check_name="Document Category & Filename Concordance",
            category=CheckCategory.CONTENT.value,
            status=CheckStatus.FAIL.value,
            severity=CheckSeverity.HIGH.value,
            summary="The uploaded filename/category does not match the expected document.",
            details=(
                f"The uploaded file '{filename}' was submitted under category '{expected_name}', "
                f"but the filename contains keywords indicating a different category: {found_discordant}."
            ),
            expected_value=expected_name,
            observed_value=filename,
            evidence={
                "expected_document": expected_name,
                "uploaded_filename": filename,
                "category": doc_type,
                "mismatch": True,
                "discordant_keywords": found_discordant,
                "authenticity_verified": False
            },
            recommendation=f"Review document. Upload the correct {expected_name}.",
            duration_ms=dur
        )

    # 2. Concordant token in filename (e.g. "land_title.pdf", "plot_survey.pdf")
    found_concordant = [t for t in concordant_tokens if t in fn_tokens or (t in fn_clean and len(t) > 3)]
    if found_concordant:
        return CheckResult(
            check_id="DOC_CATEGORY_FILENAME_MATCH",
            check_name="Document Category & Filename Concordance",
            category=CheckCategory.CONTENT.value,
            status=CheckStatus.PASS.value,
            severity=CheckSeverity.INFO.value,
            summary=f"Filename and category match expected document type: {expected_name}.",
            details=(
                f"Uploaded filename '{filename}' contains concordant keyword(s): {found_concordant}. "
                "Concordance check passed. Note: Filename concordance does not independently establish physical authenticity."
            ),
            expected_value=expected_name,
            observed_value=filename,
            evidence={
                "expected_document": expected_name,
                "uploaded_filename": filename,
                "category": doc_type,
                "mismatch": False,
                "matched_keywords": found_concordant,
                "authenticity_verified": False,
                "note": "Automated checks do not independently establish physical document authenticity."
            },
            recommendation="Compliant with document category naming rules.",
            duration_ms=dur
        )

    # 3. Check extracted text if filename is generic (e.g. "scan01.pdf", "doc.pdf")
    generic_words = {"doc", "document", "scan", "scanned", "file", "upload", "page", "image", "pdf", "img", "copy", "new"}
    is_generic = bool(fn_tokens.issubset(generic_words))

    if extracted_text and len(extracted_text.strip()) > 30:
        lower_text = extracted_text.lower()
        matched_text_tokens = [t for t in concordant_tokens if re.search(r'\b' + re.escape(t) + r'\b', lower_text)]
        discordant_text_tokens = [t for t in discordant_tokens if re.search(r'\b' + re.escape(t) + r'\b', lower_text)]

        if len(discordant_text_tokens) >= 2 and len(matched_text_tokens) == 0:
            return CheckResult(
                check_id="DOC_CATEGORY_FILENAME_MATCH",
                check_name="Document Category & Filename Concordance",
                category=CheckCategory.CONTENT.value,
                status=CheckStatus.FAIL.value,
                severity=CheckSeverity.HIGH.value,
                summary="The uploaded filename/category does not match the expected document.",
                details=(
                    f"The document text contains content indicating a different category: {discordant_text_tokens}. "
                    f"Expected a valid {expected_name}."
                ),
                expected_value=expected_name,
                observed_value=filename,
                evidence={
                    "expected_document": expected_name,
                    "uploaded_filename": filename,
                    "category": doc_type,
                    "mismatch": True,
                    "discordant_text": discordant_text_tokens,
                    "authenticity_verified": False
                },
                recommendation=f"Review document. Upload the correct {expected_name}.",
                duration_ms=dur
            )

        if len(matched_text_tokens) >= 1:
            return CheckResult(
                check_id="DOC_CATEGORY_FILENAME_MATCH",
                check_name="Document Category & Filename Concordance",
                category=CheckCategory.CONTENT.value,
                status=CheckStatus.PASS.value,
                severity=CheckSeverity.INFO.value,
                summary=f"Document content matches expected statutory category ({expected_name}).",
                details=f"Document text contains terms concordant with {expected_name}: {matched_text_tokens[:4]}.",
                expected_value=expected_name,
                observed_value=filename,
                evidence={
                    "expected_document": expected_name,
                    "uploaded_filename": filename,
                    "category": doc_type,
                    "mismatch": False,
                    "matched_text": matched_text_tokens,
                    "authenticity_verified": False
                },
                recommendation="Compliant with statutory category requirements.",
                duration_ms=dur
            )

    # 4. Generic filename with scanned image (0 text streams)
    if is_scanned or is_generic:
        return CheckResult(
            check_id="DOC_CATEGORY_FILENAME_MATCH",
            check_name="Document Category & Filename Concordance",
            category=CheckCategory.CONTENT.value,
            status=CheckStatus.REVIEW_REQUIRED.value,
            severity=CheckSeverity.MEDIUM.value,
            summary=f"Generic filename for {expected_name}; visual inspection required.",
            details=f"The file is named '{filename}'. Because it lacks descriptive naming or digital text streams, manual visual review is required to verify the document heading.",
            expected_value=expected_name,
            observed_value=filename,
            evidence={
                "expected_document": expected_name,
                "uploaded_filename": filename,
                "category": doc_type,
                "mismatch": False,
                "is_scanned": is_scanned,
                "authenticity_verified": False
            },
            recommendation=f"Officer must visually inspect document heading to verify it is {expected_name}.",
            duration_ms=dur
        )

    # 5. Default fallback
    return CheckResult(
        check_id="DOC_CATEGORY_FILENAME_MATCH",
        check_name="Document Category & Filename Concordance",
        category=CheckCategory.CONTENT.value,
        status=CheckStatus.WARNING.value,
        severity=CheckSeverity.MEDIUM.value,
        summary=f"Filename '{filename}' does not contain standard keywords for {expected_name}.",
        details=f"Expected keywords related to: {', '.join(concordant_tokens[:4])}.",
        expected_value=expected_name,
        observed_value=filename,
        evidence={
            "expected_document": expected_name,
            "uploaded_filename": filename,
            "category": doc_type,
            "mismatch": True,
            "authenticity_verified": False
        },
        recommendation=f"Confirm that '{filename}' genuinely corresponds to {expected_name}.",
        duration_ms=dur
    )


def run_content_rule_checks(
    doc_type: str,
    extracted_text: str,
    is_scanned: bool = False,
    filename: str = ""
) -> List[CheckResult]:
    """Evaluates document content and category concordance against registered statutory rules."""
    results = []

    # 0. DOC_CATEGORY_FILENAME_MATCH
    concordance_res = run_category_filename_concordance_check(
        doc_type=doc_type,
        filename=filename,
        extracted_text=extracted_text,
        is_scanned=is_scanned
    )
    results.append(concordance_res)

    rule = get_rule_for_document_type(doc_type)

    if not rule:
        # Unregistered document category
        results.append(
            CheckResult(
                check_id="DOC_TYPE_CONTENT_MATCH",
                check_name="Document Type Statutory Keyword Match",
                category=CheckCategory.CONTENT.value,
                status=CheckStatus.NOT_RUN.value,
                severity=CheckSeverity.INFO.value,
                summary=f"No automated content rule registered for category '{doc_type}'.",
                details=f"Document type '{doc_type}' is treated as a general submission. Manual review required.",
                recommendation="Scrutinize document manually according to institutional submission notes."
            )
        )
        return results

    # 1. DOC_TYPE_CONTENT_MATCH
    t0 = time.perf_counter()
    if is_scanned or not extracted_text or len(extracted_text.strip()) < 30:
        dur = (time.perf_counter() - t0) * 1000
        results.append(
            CheckResult(
                check_id="DOC_TYPE_CONTENT_MATCH",
                check_name=f"Statutory Keyword Match ({rule.rule_id})",
                category=CheckCategory.CONTENT.value,
                status=CheckStatus.NOT_RUN.value,
                severity=CheckSeverity.INFO.value,
                summary="Content keyword matching deferred: Document is a scanned image.",
                details=(
                    f"Rule '{rule.rule_id}' (v{rule.rule_version}) defines expected keywords: {', '.join(rule.required_keywords[:6])}. "
                    "Because this document is image-based without digital text streams, automated keyword matching cannot execute. "
                    "This is an expected condition for physical stamped/notarized certificates and is NOT a failure."
                ),
                expected_value=f"At least {rule.min_keyword_matches} keywords matching {rule.document_type}",
                observed_value="Scanned image (0 digital text streams)",
                evidence={"governing_framework": rule.governing_framework, "is_scanned": True},
                recommendation="Officer must physically inspect document image to confirm it is a genuine " + rule.document_type.replace("_", " "),
                duration_ms=dur
            )
        )
    else:
        lower_text = extracted_text.lower()
        matched_required = [kw for kw in rule.required_keywords if re.search(r'\b' + re.escape(kw) + r'\b', lower_text)]
        matched_supporting = [kw for kw in rule.supporting_keywords if re.search(r'\b' + re.escape(kw) + r'\b', lower_text)]
        all_matched = matched_required + matched_supporting
        dur = (time.perf_counter() - t0) * 1000

        if len(all_matched) >= rule.min_keyword_matches:
            results.append(
                CheckResult(
                    check_id="DOC_TYPE_CONTENT_MATCH",
                    check_name=f"Statutory Keyword Match ({rule.rule_id})",
                    category=CheckCategory.CONTENT.value,
                    status=CheckStatus.PASS.value,
                    severity=CheckSeverity.INFO.value,
                    summary=f"Statutory keywords verified: Found {len(all_matched)} domain terms ({', '.join(all_matched[:5])}).",
                    details=(
                        f"Evaluated against Rule {rule.rule_id} (v{rule.rule_version}). "
                        f"Found required terms: {', '.join(matched_required) or 'None'}. "
                        f"Found supporting terms: {', '.join(matched_supporting) or 'None'}. "
                        f"Governing requirement: {rule.governing_framework}."
                    ),
                    expected_value=f">={rule.min_keyword_matches} domain terms for {rule.document_type}",
                    observed_value=f"{len(all_matched)} matched terms: {', '.join(all_matched[:6])}",
                    evidence={"matched_terms": all_matched, "rule_id": rule.rule_id, "framework": rule.governing_framework},
                    duration_ms=dur
                )
            )
        else:
            results.append(
                CheckResult(
                    check_id="DOC_TYPE_CONTENT_MATCH",
                    check_name=f"Statutory Keyword Match ({rule.rule_id})",
                    category=CheckCategory.CONTENT.value,
                    status=CheckStatus.WARNING.value,
                    severity=CheckSeverity.MEDIUM.value,
                    summary=f"Low keyword relevance: Found only {len(all_matched)} matching terms for '{rule.document_type}'.",
                    details=(
                        f"Evaluated against Rule {rule.rule_id}. Expected terms relating to: {', '.join(rule.required_keywords[:6])}. "
                        f"Observed matches: {', '.join(all_matched) or 'None'}. Document may be misfiled or an unrelated file."
                    ),
                    expected_value=f">={rule.min_keyword_matches} domain terms for {rule.document_type}",
                    observed_value=f"{len(all_matched)} matched: {', '.join(all_matched) or 'None'}",
                    evidence={"all_matched": all_matched, "rule_id": rule.rule_id},
                    recommendation=f"Confirm that the uploaded document genuinely corresponds to statutory category '{rule.document_type}'.",
                    duration_ms=dur
                )
            )

    # 2. DOC_DATE_VALIDITY
    t0 = time.perf_counter()
    date_patterns = [
        r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b',  # DD/MM/YYYY or MM/DD/YYYY
        r'\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b',  # YYYY-MM-DD
        r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+(\d{4})\b'
    ]
    extracted_years = []
    if extracted_text:
        for p in date_patterns:
            matches = re.finditer(p, extracted_text, re.IGNORECASE)
            for m in matches:
                # Find the 4-digit group
                for g in m.groups():
                    if g and len(g) == 4 and g.isdigit():
                        extracted_years.append(int(g))

    dur = (time.perf_counter() - t0) * 1000
    current_year = datetime.now().year

    if extracted_years:
        future_years = [y for y in extracted_years if y > current_year + 1]
        ancient_years = [y for y in extracted_years if y < 1970]

        if future_years:
            results.append(
                CheckResult(
                    check_id="DOC_DATE_VALIDITY",
                    check_name="Document Text Date Range Plausibility",
                    category=CheckCategory.CONTENT.value,
                    status=CheckStatus.WARNING.value,
                    severity=CheckSeverity.LOW.value,
                    summary=f"Future date reference detected in text: {future_years}.",
                    details=f"Text contains references to years {future_years}, which are in the future relative to {current_year}.",
                    expected_value=f"Historical years <= {current_year + 1}",
                    observed_value=f"Detected years: {sorted(set(extracted_years))}",
                    evidence={"detected_years": extracted_years, "future_years": future_years},
                    recommendation="Verify whether date represents an anticipated completion milestone or a typographical discrepancy.",
                    duration_ms=dur
                )
            )
        else:
            results.append(
                CheckResult(
                    check_id="DOC_DATE_VALIDITY",
                    check_name="Document Text Date Range Plausibility",
                    category=CheckCategory.CONTENT.value,
                    status=CheckStatus.PASS.value,
                    severity=CheckSeverity.INFO.value,
                    summary=f"Extracted date references are chronologically plausible ({min(extracted_years)}–{max(extracted_years)}).",
                    details=f"Document references historical dates consistent with modern technical institution approvals.",
                    observed_value=f"Years: {min(extracted_years)}–{max(extracted_years)}",
                    duration_ms=dur
                )
            )
    else:
        results.append(
            CheckResult(
                check_id="DOC_DATE_VALIDITY",
                check_name="Document Text Date Range Plausibility",
                category=CheckCategory.CONTENT.value,
                status=CheckStatus.NOT_RUN.value,
                severity=CheckSeverity.INFO.value,
                summary="Date plausibility check not run: No explicit 4-digit date patterns found in text.",
                details="Scanned or formatted date fields could not be matched by standard regex date parsers.",
                duration_ms=dur
            )
        )

    return results

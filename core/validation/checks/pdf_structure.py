"""
Aegis Foundation - PDF Structural Integrity Checks
Performs PyMuPDF stream parsing, encryption, metadata, incremental revision,
attachment, and active content checks with explicit advisory limitations.
"""

import os
import re
import time
from typing import Any, Dict, List, Optional
import fitz  # PyMuPDF
from core.validation.schema import CheckResult, CheckStatus, CheckSeverity, CheckCategory, ENGINE_VERSION


def run_pdf_structural_checks(
    filepath: str,
    file_bytes: Optional[bytes] = None
) -> List[CheckResult]:
    """Runs PDF-specific structural checks on a PDF document."""
    results = []

    if file_bytes is None:
        try:
            with open(filepath, "rb") as f:
                file_bytes = f.read()
        except Exception as e:
            results.append(
                CheckResult(
                    check_id="PDF_READ_ERROR",
                    check_name="PDF File Access",
                    category=CheckCategory.DOCUMENT_STRUCTURE.value,
                    status=CheckStatus.ERROR.value,
                    severity=CheckSeverity.CRITICAL.value,
                    summary=f"Unable to read PDF file: {e}",
                    details=str(e),
                    recommendation="Verify storage volume and permissions."
                )
            )
            return results

    # 1. PDF_PARSE_INTEGRITY
    t0 = time.perf_counter()
    doc = None
    parse_error = None
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        parse_error = str(e)
    dur = (time.perf_counter() - t0) * 1000

    if parse_error or doc is None:
        results.append(
            CheckResult(
                check_id="PDF_PARSE_INTEGRITY",
                check_name="PDF Object & Stream Parsing",
                category=CheckCategory.DOCUMENT_STRUCTURE.value,
                status=CheckStatus.FAIL.value,
                severity=CheckSeverity.CRITICAL.value,
                summary=f"Corrupt or malformed PDF structure: {parse_error}",
                details=f"PyMuPDF engine failed to parse internal cross-reference table or object streams: {parse_error}",
                expected_value="Well-formed PDF structure",
                observed_value=f"Parse Error: {parse_error}",
                recommendation="Document is corrupt. Request applicant re-export clean PDF from authoring software.",
                duration_ms=dur
            )
        )
        return results  # Cannot proceed with structural checks on unparseable PDF

    results.append(
        CheckResult(
            check_id="PDF_PARSE_INTEGRITY",
            check_name="PDF Object & Stream Parsing",
            category=CheckCategory.DOCUMENT_STRUCTURE.value,
            status=CheckStatus.PASS.value,
            severity=CheckSeverity.INFO.value,
            summary="PDF parsed successfully: Internal cross-reference table and object streams are intact.",
            details="Document cross-reference table (XREF), page trees, and stream dictionaries are well-formed. LIMITATION: Successful parsing indicates structural readability, not statutory authenticity.",
            expected_value="Well-formed PDF structure",
            observed_value="Parse Success (PyMuPDF)",
            duration_ms=dur
        )
    )

    # 2. PDF_PAGE_COUNT
    t0 = time.perf_counter()
    page_count = len(doc)
    dur = (time.perf_counter() - t0) * 1000
    if page_count > 0:
        results.append(
            CheckResult(
                check_id="PDF_PAGE_COUNT",
                check_name="Document Page Count Verification",
                category=CheckCategory.DOCUMENT_STRUCTURE.value,
                status=CheckStatus.PASS.value,
                severity=CheckSeverity.INFO.value,
                summary=f"Document contains {page_count} page(s).",
                expected_value=">= 1 page",
                observed_value=f"{page_count} page(s)",
                evidence={"page_count": page_count},
                duration_ms=dur
            )
        )
    else:
        results.append(
            CheckResult(
                check_id="PDF_PAGE_COUNT",
                check_name="Document Page Count Verification",
                category=CheckCategory.DOCUMENT_STRUCTURE.value,
                status=CheckStatus.FAIL.value,
                severity=CheckSeverity.HIGH.value,
                summary="PDF contains 0 pages (empty page tree).",
                expected_value=">= 1 page",
                observed_value="0 pages",
                recommendation="Document has no pages. Re-upload complete document.",
                duration_ms=dur
            )
        )

    # 3. PDF_ENCRYPTION_CHECK
    t0 = time.perf_counter()
    is_encrypted = doc.is_encrypted or doc.needs_pass
    dur = (time.perf_counter() - t0) * 1000
    if is_encrypted:
        results.append(
            CheckResult(
                check_id="PDF_ENCRYPTION_CHECK",
                check_name="PDF Password & Access Permissions",
                category=CheckCategory.DOCUMENT_STRUCTURE.value,
                status=CheckStatus.FAIL.value,
                severity=CheckSeverity.HIGH.value,
                summary="Password-protected or encrypted PDF detected.",
                details="Document is encrypted or requires password authentication, preventing statutory officer review.",
                expected_value="Unencrypted PDF",
                observed_value="Encrypted / Password Required",
                recommendation="Re-upload an unencrypted PDF without password restrictions.",
                duration_ms=dur
            )
        )
    else:
        results.append(
            CheckResult(
                check_id="PDF_ENCRYPTION_CHECK",
                check_name="PDF Password & Access Permissions",
                category=CheckCategory.DOCUMENT_STRUCTURE.value,
                status=CheckStatus.PASS.value,
                severity=CheckSeverity.INFO.value,
                summary="Document is unencrypted and accessible for scrutiny.",
                expected_value="Unencrypted PDF",
                observed_value="Unencrypted",
                duration_ms=dur
            )
        )

    # 4. PDF_METADATA_AUDIT
    t0 = time.perf_counter()
    meta = doc.metadata or {}
    creator = meta.get("creator") or ""
    producer = meta.get("producer") or ""
    creation_date = meta.get("creationDate") or ""
    mod_date = meta.get("modDate") or ""
    title = meta.get("title") or ""
    author = meta.get("author") or ""
    dur = (time.perf_counter() - t0) * 1000

    evidence_meta = {
        "creator": creator,
        "producer": producer,
        "creationDate": creation_date,
        "modDate": mod_date,
        "title": title,
        "author": author
    }

    if not creator and not producer and not creation_date:
        results.append(
            CheckResult(
                check_id="PDF_METADATA_AUDIT",
                check_name="Document Metadata Extraction & Audit",
                category=CheckCategory.METADATA.value,
                status=CheckStatus.WARNING.value,
                severity=CheckSeverity.LOW.value,
                summary="PDF dictionary contains no authoring metadata.",
                details="Document dictionary lacks creator, producer, or creation timestamps. Note: Sanitized or scanned documents frequently omit metadata; this does not prove tampering.",
                evidence=evidence_meta,
                recommendation="Inspect document content to verify issuing authority.",
                duration_ms=dur
            )
        )
    else:
        results.append(
            CheckResult(
                check_id="PDF_METADATA_AUDIT",
                check_name="Document Metadata Extraction & Audit",
                category=CheckCategory.METADATA.value,
                status=CheckStatus.PASS.value,
                severity=CheckSeverity.INFO.value,
                summary=f"Metadata extracted: Producer '{producer[:32]}', Creator '{creator[:32]}'.",
                details=f"Extracted PDF Information Dictionary fields: Producer: {producer or 'None'}, Creator: {creator or 'None'}, Created: {creation_date or 'None'}, Modified: {mod_date or 'None'}.",
                evidence=evidence_meta,
                observed_value=f"Producer: {producer[:30]}, Creator: {creator[:30]}",
                duration_ms=dur
            )
        )

    # 5. PDF_ATTACHMENT_CHECK
    t0 = time.perf_counter()
    emb_count = doc.embfile_count() if hasattr(doc, "embfile_count") else 0
    dur = (time.perf_counter() - t0) * 1000
    if emb_count > 0:
        emb_names = [doc.embfile_info(i)["filename"] for i in range(emb_count)] if hasattr(doc, "embfile_info") else []
        results.append(
            CheckResult(
                check_id="PDF_ATTACHMENT_CHECK",
                check_name="Embedded Attachment Detection",
                category=CheckCategory.DOCUMENT_STRUCTURE.value,
                status=CheckStatus.REVIEW_REQUIRED.value,
                severity=CheckSeverity.LOW.value,
                summary=f"Found {emb_count} embedded attachment file(s) inside PDF.",
                details=f"Document contains embedded files: {', '.join(emb_names)}. Supplementary files require manual verification.",
                expected_value="0 embedded attachments",
                observed_value=f"{emb_count} attachments ({', '.join(emb_names)})",
                evidence={"embedded_count": emb_count, "filenames": emb_names},
                recommendation="Extract and review embedded attachments to confirm they contain valid statutory evidence.",
                duration_ms=dur
            )
        )
    else:
        results.append(
            CheckResult(
                check_id="PDF_ATTACHMENT_CHECK",
                check_name="Embedded Attachment Detection",
                category=CheckCategory.DOCUMENT_STRUCTURE.value,
                status=CheckStatus.PASS.value,
                severity=CheckSeverity.INFO.value,
                summary="No hidden or embedded attachments detected inside PDF.",
                details="Document contains clean visual pages without secondary file payloads.",
                duration_ms=dur
            )
        )

    # 6. PDF_INCREMENTAL_UPDATES
    t0 = time.perf_counter()
    eof_matches = list(re.finditer(b"%%EOF", file_bytes))
    eof_count = len(eof_matches)
    dur = (time.perf_counter() - t0) * 1000

    if eof_count > 1:
        results.append(
            CheckResult(
                check_id="PDF_INCREMENTAL_UPDATES",
                check_name="Incremental Revisions (%%EOF Markers)",
                category=CheckCategory.DOCUMENT_STRUCTURE.value,
                status=CheckStatus.WARNING.value,
                severity=CheckSeverity.LOW.value,
                summary=f"Detected {eof_count} %%EOF markers (incremental revision sections).",
                details=(
                    f"Document contains {eof_count} file termination markers, indicating incremental revision history. "
                    "LIMITATION: Incremental revisions are standard when documents are digitally signed, annotated, "
                    "or appended in Adobe Acrobat. This finding is advisory and does NOT prove fraudulent tampering."
                ),
                expected_value="1 %%EOF marker",
                observed_value=f"{eof_count} %%EOF markers",
                evidence={"eof_count": eof_count, "byte_offsets": [m.start() for m in eof_matches]},
                recommendation="Inspect whether incremental revisions represent legitimate digital signature timestamps or post-issue edits.",
                duration_ms=dur
            )
        )
    elif eof_count == 1:
        results.append(
            CheckResult(
                check_id="PDF_INCREMENTAL_UPDATES",
                check_name="Incremental Revisions (%%EOF Markers)",
                category=CheckCategory.DOCUMENT_STRUCTURE.value,
                status=CheckStatus.PASS.value,
                severity=CheckSeverity.INFO.value,
                summary="Single revision section: Document has 1 standard %%EOF marker.",
                details="Document is a monolithic PDF export without secondary appended revision trailers.",
                expected_value="1 %%EOF marker",
                observed_value="1 %%EOF marker",
                duration_ms=dur
            )
        )
    else:
        results.append(
            CheckResult(
                check_id="PDF_INCREMENTAL_UPDATES",
                check_name="Incremental Revisions (%%EOF Markers)",
                category=CheckCategory.DOCUMENT_STRUCTURE.value,
                status=CheckStatus.FAIL.value,
                severity=CheckSeverity.HIGH.value,
                summary="Truncated PDF: Missing standard %%EOF termination marker.",
                details="File stream ends abruptly without standard PDF trailer. Document may be incomplete or truncated during transmission.",
                expected_value="1 %%EOF marker",
                observed_value="0 %%EOF markers",
                recommendation="Re-upload full document; file appears partially downloaded or truncated.",
                duration_ms=dur
            )
        )

    # 7. PDF_ACTIVE_CONTENT_CHECK
    t0 = time.perf_counter()
    has_js = bool(re.search(b"/JavaScript|/JS\\b", file_bytes))
    has_launch = bool(re.search(b"/Launch\\b", file_bytes))
    dur = (time.perf_counter() - t0) * 1000

    if has_js or has_launch:
        flagged = []
        if has_js:
            flagged.append("JavaScript Actions (/JS)")
        if has_launch:
            flagged.append("External Launch Actions (/Launch)")
        results.append(
            CheckResult(
                check_id="PDF_ACTIVE_CONTENT_CHECK",
                check_name="Active Content & Scripting Scanner",
                category=CheckCategory.DOCUMENT_STRUCTURE.value,
                status=CheckStatus.REVIEW_REQUIRED.value,
                severity=CheckSeverity.HIGH.value,
                summary=f"Active content detected: {', '.join(flagged)}.",
                details="Statutory institutional documents must be inert static records. Active scripts present potential security or integrity risks.",
                expected_value="Zero active scripts",
                observed_value=", ".join(flagged),
                evidence={"has_javascript": has_js, "has_launch": has_launch},
                recommendation="Print document to static PDF before submitting to eliminate active scripts.",
                duration_ms=dur
            )
        )
    else:
        results.append(
            CheckResult(
                check_id="PDF_ACTIVE_CONTENT_CHECK",
                check_name="Active Content & Scripting Scanner",
                category=CheckCategory.DOCUMENT_STRUCTURE.value,
                status=CheckStatus.PASS.value,
                severity=CheckSeverity.INFO.value,
                summary="Static document: Zero JavaScript or launch actions detected.",
                details="Document contains inert text and graphic streams without executable scripts.",
                expected_value="Zero active scripts",
                observed_value="0 scripts detected",
                duration_ms=dur
            )
        )

    doc.close()
    return results

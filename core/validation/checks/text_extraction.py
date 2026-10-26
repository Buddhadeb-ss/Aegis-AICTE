"""
Aegis Foundation - Text Extraction & Readability Checks
Extracts text page-by-page using PyMuPDF, detects zero-character pages,
and differentiates native digital PDFs from scanned image-based records.
"""

import time
from typing import Any, Dict, List, Optional
try:
    import pymupdf as fitz
except ImportError:
    import fitz  # Fallback for older environments
from core.validation.schema import CheckResult, CheckStatus, CheckSeverity, CheckCategory, ENGINE_VERSION


def run_text_extraction_checks(
    filepath: str,
    file_bytes: Optional[bytes] = None
) -> Dict[str, Any]:
    """
    Extracts text page-by-page and returns both CheckResults and extracted text data.
    Returns:
        {
            "checks": List[CheckResult],
            "extracted_text": str,
            "page_texts": List[str],
            "is_scanned": bool,
            "total_chars": int
        }
    """
    results = []
    page_texts = []
    full_text = ""
    is_scanned = False
    total_chars = 0

    try:
        if file_bytes is not None:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
        else:
            doc = fitz.open(filepath)
    except Exception as e:
        results.append(
            CheckResult(
                check_id="TEXT_EXTRACTION_ENGINE",
                check_name="Text Stream Extraction Engine",
                category=CheckCategory.CONTENT.value,
                status=CheckStatus.ERROR.value,
                severity=CheckSeverity.HIGH.value,
                summary=f"Text extraction failed: {e}",
                details=str(e),
                recommendation="Document could not be opened for text stream extraction."
            )
        )
        return {
            "checks": results,
            "extracted_text": "",
            "page_texts": [],
            "is_scanned": True,
            "total_chars": 0
        }

    t0 = time.perf_counter()
    page_metrics = []
    blank_pages = []

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        txt = page.get_text("text").strip()
        page_texts.append(txt)
        char_count = len(txt)
        total_chars += char_count
        page_metrics.append({
            "page_number": page_idx + 1,
            "char_count": char_count,
            "word_count": len(txt.split()) if txt else 0
        })
        if char_count == 0:
            blank_pages.append(page_idx + 1)

    full_text = "\n\n".join(page_texts)
    dur = (time.perf_counter() - t0) * 1000
    doc.close()

    # 1. TEXT_EXTRACT_PER_PAGE Check
    if not blank_pages and total_chars > 0:
        results.append(
            CheckResult(
                check_id="TEXT_EXTRACT_PER_PAGE",
                check_name="Page-by-Page Text Stream Extraction",
                category=CheckCategory.CONTENT.value,
                status=CheckStatus.PASS.value,
                severity=CheckSeverity.INFO.value,
                summary=f"Machine-readable text extracted across all {len(page_texts)} page(s) ({total_chars:,} characters).",
                details=f"All pages contain valid digital text streams. Total words: {len(full_text.split()):,}.",
                expected_value=f"Text on all {len(page_texts)} pages",
                observed_value=f"{total_chars:,} chars across {len(page_texts)} pages",
                evidence={"page_metrics": page_metrics, "total_chars": total_chars},
                duration_ms=dur
            )
        )
    elif blank_pages and total_chars > 50:
        results.append(
            CheckResult(
                check_id="TEXT_EXTRACT_PER_PAGE",
                check_name="Page-by-Page Text Stream Extraction",
                category=CheckCategory.CONTENT.value,
                status=CheckStatus.WARNING.value,
                severity=CheckSeverity.LOW.value,
                summary=f"Partial text extraction: Page(s) {blank_pages} contain no extractable text streams.",
                details=(
                    f"Pages {blank_pages} have 0 digital characters, while other pages contain {total_chars:,} chars. "
                    "This typically indicates inserted photographic scans, blueprints, or rasterized seals."
                ),
                expected_value=f"Text on all {len(page_texts)} pages",
                observed_value=f"Empty pages: {blank_pages}",
                evidence={"blank_pages": blank_pages, "page_metrics": page_metrics},
                recommendation="Inspect highlighted pages manually to ensure scanned attachments or seals are legible.",
                duration_ms=dur
            )
        )

    # 2. TEXT_READABILITY_SCANNED_CHECK
    t0 = time.perf_counter()
    if total_chars < 50:
        is_scanned = True
        dur_scan = (time.perf_counter() - t0) * 1000
        results.append(
            CheckResult(
                check_id="TEXT_READABILITY_SCANNED_CHECK",
                check_name="Document Readability & Scanned Detection",
                category=CheckCategory.CONTENT.value,
                status=CheckStatus.REVIEW_REQUIRED.value,
                severity=CheckSeverity.MEDIUM.value,
                summary="Scanned / Image-Based Document: Direct PDF stream contains zero or minimal digital text.",
                details=(
                    f"Extracted {total_chars} total characters across {len(page_texts)} page(s). "
                    "Document appears to be a scanned paper document, photograph, or flattened image. "
                    "IMPORTANT: Missing digital text streams does NOT prove the document is blank or fraudulent; "
                    "physical land records, municipal sanction maps, and notarized deeds are frequently scanned."
                ),
                expected_value="Searchable digital text streams",
                observed_value="Rasterized / Scanned Image (< 50 chars)",
                evidence={"total_chars": total_chars, "is_scanned": True},
                recommendation="Officer must physically inspect scanned image for institutional seals, signatures, and survey boundaries.",
                duration_ms=dur_scan
            )
        )
    else:
        is_scanned = False
        dur_scan = (time.perf_counter() - t0) * 1000
        results.append(
            CheckResult(
                check_id="TEXT_READABILITY_SCANNED_CHECK",
                check_name="Document Readability & Scanned Detection",
                category=CheckCategory.CONTENT.value,
                status=CheckStatus.PASS.value,
                severity=CheckSeverity.INFO.value,
                summary="Digital searchable document: High-density text streams available for automated scrutiny.",
                details=f"Document contains {total_chars:,} characters of digital text, enabling automated keyword and date validation.",
                expected_value="Searchable digital text streams",
                observed_value=f"{total_chars:,} characters",
                duration_ms=dur_scan
            )
        )

    return {
        "checks": results,
        "extracted_text": full_text,
        "page_texts": page_texts,
        "is_scanned": is_scanned,
        "total_chars": total_chars
    }

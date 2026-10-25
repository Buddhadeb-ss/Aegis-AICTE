"""
Aegis Foundation - File Integrity Validation Checks
Implements physical file, signature, size, hash, and duplicate checks.
"""

import hashlib
import os
import time
from typing import Any, Dict, List, Optional
from core.validation.schema import CheckResult, CheckStatus, CheckSeverity, CheckCategory, ENGINE_VERSION

MAX_FILE_SIZE = 15 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}

MAGIC_SIGNATURES = {
    ".pdf": [b"%PDF-"],
    ".png": [b"\x89PNG\r\n\x1a\n"],
    ".jpg": [b"\xff\xd8\xff"],
    ".jpeg": [b"\xff\xd8\xff"],
}


def run_file_integrity_checks(
    filepath: str,
    filename: str,
    file_bytes: Optional[bytes] = None,
    existing_hashes: Optional[List[Dict[str, Any]]] = None,
    current_doc_id: Optional[str] = None
) -> List[CheckResult]:
    """Runs all 7 file integrity checks on the given document."""
    results = []

    # Read bytes if not provided
    if file_bytes is None:
        try:
            with open(filepath, "rb") as f:
                file_bytes = f.read()
        except Exception as e:
            results.append(
                CheckResult(
                    check_id="FILE_READ_ACCESS",
                    check_name="Filesystem Read Access",
                    category=CheckCategory.FILE_INTEGRITY.value,
                    status=CheckStatus.ERROR.value,
                    severity=CheckSeverity.CRITICAL.value,
                    summary=f"Unable to read file from storage: {e}",
                    details=str(e),
                    recommendation="Verify storage mount and filesystem permissions."
                )
            )
            return results

    # 1. FILE_EXT_ALLOWED
    t0 = time.perf_counter()
    ext = os.path.splitext(filename)[1].lower()
    dur = (time.perf_counter() - t0) * 1000
    if ext in ALLOWED_EXTENSIONS:
        results.append(
            CheckResult(
                check_id="FILE_EXT_ALLOWED",
                check_name="Allowed File Extension",
                category=CheckCategory.FILE_INTEGRITY.value,
                status=CheckStatus.PASS.value,
                severity=CheckSeverity.INFO.value,
                summary=f"File extension '{ext}' is in the statutory permitted list.",
                details=f"Permitted extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}.",
                expected_value="One of " + ", ".join(sorted(ALLOWED_EXTENSIONS)),
                observed_value=ext,
                duration_ms=dur
            )
        )
    else:
        results.append(
            CheckResult(
                check_id="FILE_EXT_ALLOWED",
                check_name="Allowed File Extension",
                category=CheckCategory.FILE_INTEGRITY.value,
                status=CheckStatus.FAIL.value,
                severity=CheckSeverity.HIGH.value,
                summary=f"Disallowed file extension '{ext}'.",
                details=f"Only {', '.join(sorted(ALLOWED_EXTENSIONS))} are supported.",
                expected_value="One of " + ", ".join(sorted(ALLOWED_EXTENSIONS)),
                observed_value=ext,
                recommendation="Convert document to statutory PDF or JPEG format and re-upload.",
                duration_ms=dur
            )
        )

    # 2. FILE_NON_EMPTY
    t0 = time.perf_counter()
    file_size = len(file_bytes)
    dur = (time.perf_counter() - t0) * 1000
    if file_size > 0:
        results.append(
            CheckResult(
                check_id="FILE_NON_EMPTY",
                check_name="Non-Empty Payload Verification",
                category=CheckCategory.FILE_INTEGRITY.value,
                status=CheckStatus.PASS.value,
                severity=CheckSeverity.INFO.value,
                summary=f"File contains valid binary payload ({file_size:,} bytes).",
                expected_value="> 0 bytes",
                observed_value=f"{file_size:,} bytes",
                duration_ms=dur
            )
        )
    else:
        results.append(
            CheckResult(
                check_id="FILE_NON_EMPTY",
                check_name="Non-Empty Payload Verification",
                category=CheckCategory.FILE_INTEGRITY.value,
                status=CheckStatus.FAIL.value,
                severity=CheckSeverity.CRITICAL.value,
                summary="Zero-byte file detected. Document contains no readable data.",
                details="Uploaded payload is completely empty (0 bytes).",
                expected_value="> 0 bytes",
                observed_value="0 bytes",
                recommendation="Re-upload a non-empty document.",
                duration_ms=dur
            )
        )
        return results  # Stop integrity checks if file has 0 bytes

    # 3. FILE_SIGNATURE_MATCH
    t0 = time.perf_counter()
    expected_magics = MAGIC_SIGNATURES.get(ext, [])
    has_match = any(file_bytes.startswith(m) for m in expected_magics)
    dur = (time.perf_counter() - t0) * 1000
    if has_match:
        observed_magic = file_bytes[:8].decode("latin-1", errors="replace")
        results.append(
            CheckResult(
                check_id="FILE_SIGNATURE_MATCH",
                check_name="Binary File Signature (Magic Bytes)",
                category=CheckCategory.FILE_INTEGRITY.value,
                status=CheckStatus.PASS.value,
                severity=CheckSeverity.INFO.value,
                summary=f"Header signature matches expected format for '{ext}'.",
                details="File header bytes match statutory format specifications.",
                expected_value=f"Magic bytes for {ext}",
                observed_value=f"Matched magic prefix: {repr(file_bytes[:6])}",
                duration_ms=dur
            )
        )
    else:
        results.append(
            CheckResult(
                check_id="FILE_SIGNATURE_MATCH",
                check_name="Binary File Signature (Magic Bytes)",
                category=CheckCategory.FILE_INTEGRITY.value,
                status=CheckStatus.FAIL.value,
                severity=CheckSeverity.CRITICAL.value,
                summary=f"File header signature does not match declared extension '{ext}'.",
                details=f"Expected magic prefix for {ext}, observed: {repr(file_bytes[:8])}. Possible renamed or disguised executable/binary file.",
                expected_value=f"Magic bytes for {ext}",
                observed_value=repr(file_bytes[:8]),
                recommendation="Inspect file for corruption or disguised format. Re-export clean PDF.",
                duration_ms=dur
            )
        )

    # 4. FILE_SIZE_LIMIT
    t0 = time.perf_counter()
    dur = (time.perf_counter() - t0) * 1000
    if file_size <= MAX_FILE_SIZE:
        results.append(
            CheckResult(
                check_id="FILE_SIZE_LIMIT",
                check_name="Permitted File Size Boundary",
                category=CheckCategory.FILE_INTEGRITY.value,
                status=CheckStatus.PASS.value,
                severity=CheckSeverity.INFO.value,
                summary=f"File size ({file_size / (1024*1024):.2f} MB) is within the statutory limit of 15 MB.",
                expected_value="<= 15.00 MB",
                observed_value=f"{file_size / (1024*1024):.2f} MB",
                duration_ms=dur
            )
        )
    else:
        results.append(
            CheckResult(
                check_id="FILE_SIZE_LIMIT",
                check_name="Permitted File Size Boundary",
                category=CheckCategory.FILE_INTEGRITY.value,
                status=CheckStatus.FAIL.value,
                severity=CheckSeverity.HIGH.value,
                summary=f"File size ({file_size / (1024*1024):.2f} MB) exceeds maximum limit of 15 MB.",
                expected_value="<= 15.00 MB",
                observed_value=f"{file_size / (1024*1024):.2f} MB",
                recommendation="Compress or downsample document to under 15 MB before re-submitting.",
                duration_ms=dur
            )
        )

    # 5. FILE_SHA256_DIGEST
    t0 = time.perf_counter()
    sha256 = hashlib.sha256(file_bytes).hexdigest()
    dur = (time.perf_counter() - t0) * 1000
    results.append(
        CheckResult(
            check_id="FILE_SHA256_DIGEST",
            check_name="Cryptographic SHA-256 Digest",
            category=CheckCategory.FILE_INTEGRITY.value,
            status=CheckStatus.PASS.value,
            severity=CheckSeverity.INFO.value,
            summary=f"SHA-256 cryptographic digest computed successfully.",
            details="Tamper-evident cryptographic fingerprint recorded for regulatory audit logging.",
            observed_value=sha256,
            evidence={"sha256": sha256, "file_size_bytes": file_size},
            duration_ms=dur
        )
    )

    # 6. FILE_DUPLICATE_CHECK
    t0 = time.perf_counter()
    matches = []
    if existing_hashes:
        for item in existing_hashes:
            if current_doc_id and item.get("id") == current_doc_id:
                continue
            if item.get("sha256_hash") == sha256:
                matches.append(item)
    dur = (time.perf_counter() - t0) * 1000

    if matches:
        match_info = ", ".join([f"'{m.get('filename')}' ({m.get('document_type')})" for m in matches])
        results.append(
            CheckResult(
                check_id="FILE_DUPLICATE_CHECK",
                check_name="Duplicate File Byte Check",
                category=CheckCategory.FILE_INTEGRITY.value,
                status=CheckStatus.WARNING.value,
                severity=CheckSeverity.MEDIUM.value,
                summary=f"Byte-identical document already exists in application: {match_info}.",
                details=(
                    f"Found {len(matches)} matching document(s) with identical SHA-256 digest ({sha256[:16]}...). "
                    "A matching hash proves identical bytes, not necessarily fraud; the applicant may have inadvertently re-uploaded the same document."
                ),
                observed_value=f"Matches {len(matches)} document(s): {match_info}",
                evidence={"matching_documents": matches, "sha256": sha256},
                recommendation="Review if the same certificate was accidentally submitted under multiple statutory headings.",
                duration_ms=dur
            )
        )
    else:
        results.append(
            CheckResult(
                check_id="FILE_DUPLICATE_CHECK",
                check_name="Duplicate File Byte Check",
                category=CheckCategory.FILE_INTEGRITY.value,
                status=CheckStatus.PASS.value,
                severity=CheckSeverity.INFO.value,
                summary="Unique document bytes: No duplicate uploads found with identical hash.",
                details="Cryptographic digest does not match any other dossier file.",
                duration_ms=dur
            )
        )

    # 7. FILE_PATH_TRAVERSAL_SAFE
    t0 = time.perf_counter()
    norm_filename = os.path.basename(filename)
    is_safe = (".." not in filename and "/" not in norm_filename and "\\" not in norm_filename)
    dur = (time.perf_counter() - t0) * 1000
    if is_safe:
        results.append(
            CheckResult(
                check_id="FILE_PATH_TRAVERSAL_SAFE",
                check_name="Path Traversal & Filesystem Safety",
                category=CheckCategory.FILE_INTEGRITY.value,
                status=CheckStatus.PASS.value,
                severity=CheckSeverity.INFO.value,
                summary="Filename and storage path conform to directory containment rules.",
                details="No relative traversal sequences ('..') or unauthorized separators detected.",
                expected_value="Strict directory containment",
                observed_value=norm_filename,
                duration_ms=dur
            )
        )
    else:
        results.append(
            CheckResult(
                check_id="FILE_PATH_TRAVERSAL_SAFE",
                check_name="Path Traversal & Filesystem Safety",
                category=CheckCategory.FILE_INTEGRITY.value,
                status=CheckStatus.FAIL.value,
                severity=CheckSeverity.CRITICAL.value,
                summary="Security violation: Filename contains path traversal sequences.",
                details=f"Unsanitized path detected: {filename}",
                recommendation="Filename must be sanitized before storage.",
                duration_ms=dur
            )
        )

    return results

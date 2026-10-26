"""
Aegis Foundation - Modular Document Forensics Engine
Derived in part from Doc-Sentry (MIT License, Copyright (c) 2026 Spandan Mukherjee).

Provides:
- PDF structural integrity checks (EOF count, creator/producer drift, consumer tool detection).
- SHA-256 digest computation & tamper-evident verification.
- Evidence-linked citation generation for statutory scrutiny.
"""

import hashlib
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
try:
    import pymupdf as fitz
except ImportError:
    import fitz  # Fallback for older environments


def compute_sha256(filepath_or_bytes) -> str:
    """Computes SHA-256 digest."""
    h = hashlib.sha256()
    if isinstance(filepath_or_bytes, (str, os.PathLike)):
        with open(filepath_or_bytes, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
    else:
        h.update(filepath_or_bytes)
    return h.hexdigest()


def is_valid_pdf_magic(file_bytes: bytes) -> bool:
    """Checks whether the first bytes contain the standard PDF magic header."""
    return file_bytes.startswith(b"%PDF-")


def audit_pdf_structure(filepath: str) -> Dict[str, Any]:
    """
    Structural audit for PDF files.
    Detects incremental updates, editor fingerprints, and metadata drift.
    Preserves techniques from Doc-Sentry (Spandan Mukherjee, MIT License).
    All outputs are explicitly ADVISORY.
    """
    flags = []
    eof_count = 0
    file_bytes = b""

    try:
        with open(filepath, "rb") as f:
            file_bytes = f.read()
    except Exception as e:
        return {
            "file": os.path.basename(filepath),
            "sha256": "",
            "error": f"Failed to read file: {e}",
            "flags": ["FILE_READ_ERROR"],
            "risk_score": 1.0,
            "risk_band": "HIGH",
            "advisory_notice": "ADVISORY ONLY: Automated forensic signals require human officer verification."
        }

    # 1. Empty file validation
    if len(file_bytes) == 0:
        return {
            "file": os.path.basename(filepath),
            "sha256": compute_sha256(b""),
            "pages": 0,
            "eof_markers": 0,
            "flags": ["EMPTY_FILE: Document contains zero bytes."],
            "risk_score": 1.0,
            "risk_band": "HIGH",
            "advisory_notice": "ADVISORY ONLY: Automated forensic signals require human officer verification."
        }

    # 2. Magic header check
    if not is_valid_pdf_magic(file_bytes):
        flags.append("INVALID_PDF_HEADER: Missing or corrupt %PDF- magic signature.")

    # 3. Count %%EOF markers
    eof_count = len(re.findall(b"%%EOF", file_bytes))
    if eof_count > 1:
        flags.append(f"INCREMENTAL_UPDATES_DETECTED: Found {eof_count} %%EOF markers (possible post-issue tampering).")
    elif eof_count == 0 and is_valid_pdf_magic(file_bytes):
        flags.append("TRUNCATED_PDF: Missing standard %%EOF termination marker.")

    # 4. PyMuPDF metadata inspection
    metadata = {}
    pages = 0
    try:
        doc = fitz.open(filepath)
        pages = len(doc)
        metadata = doc.metadata or {}
        doc.close()
    except Exception as e:
        flags.append(f"CORRUPT_OR_UNREADABLE_PDF: {e}")

    producer = str(metadata.get("producer", "")).lower()
    creator = str(metadata.get("creator", "")).lower()

    # 5. Consumer tool signature detection (e.g. Smallpdf, Canva, iLovePDF, Sejda)
    consumer_tools = ["smallpdf", "ilovepdf", "canva", "sejda", "pdfescape", "soda pdf", "phantompdf"]
    for tool in consumer_tools:
        if tool in producer or tool in creator:
            flags.append(f"CONSUMER_TOOL_DETECTED: Document edited via '{tool}' (incompatible with statutory government records).")

    # 6. Metadata drift check
    if producer and creator and producer != creator:
        if "pymupdf" in creator and "smallpdf" in producer:
            flags.append("PRODUCER_CREATOR_DRIFT: Asymmetric PDF producer and creator signatures.")

    # Risk scoring
    risk_score = 0.05
    if any("CONSUMER_TOOL" in f for f in flags):
        risk_score += 0.45
    if eof_count > 1:
        risk_score += 0.35
    if any("CORRUPT" in f or "INVALID_PDF" in f for f in flags):
        risk_score = 1.0

    risk_score = min(round(risk_score, 2), 1.0)
    risk_band = "LOW" if risk_score < 0.30 else "MEDIUM" if risk_score < 0.60 else "HIGH"

    return {
        "file": os.path.basename(filepath),
        "sha256": compute_sha256(filepath),
        "pages": pages,
        "eof_markers": eof_count,
        "producer": metadata.get("producer", ""),
        "creator": metadata.get("creator", ""),
        "flags": flags,
        "risk_score": risk_score,
        "risk_band": risk_band,
        "advisory_notice": "ADVISORY ONLY: Automated forensic signals are advisory only. Final regulatory determination rests solely with the designated AICTE Scrutiny Officer.",
        "analysed_at": datetime.now().isoformat()
    }

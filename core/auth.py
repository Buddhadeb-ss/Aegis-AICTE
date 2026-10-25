"""
Aegis Foundation - Authentication & Authorization Service
Persistent bcrypt authentication, session lifecycle, and strict multi-tenant data isolation.
"""

import os
import re
import uuid
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
import bcrypt
from core.db import get_db
from core.audit import log_event
from core.forensics import compute_sha256, audit_pdf_structure, is_valid_pdf_magic
from core.validation.engine import ValidationEngine

# Mandatory regulatory document checklist per application category
MANDATORY_DOCUMENTS = {
    "NEW_TECHNICAL_INSTITUTION": [
        "LAND_TITLE_CERTIFICATE",
        "BUILDING_PLAN_APPROVAL",
        "AICTE_AFFIDAVIT_1",
        "FIRE_SAFETY_CERTIFICATE"
    ],
    "EXTENSION_OF_APPROVAL": [
        "FACULTY_CADRE_CERTIFICATE",
        "OCCUPANCY_CERTIFICATE",
        "AICTE_AFFIDAVIT_1"
    ]
}

MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB statutory upload limit
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}


class AuthService:
    @staticmethod
    def authenticate(email: str, password: str, expected_role: Optional[str] = None, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Validates credentials against persistent SQLite database using bcrypt."""
        if not email or not password:
            return None

        clean_email = email.strip().lower()

        with get_db(db_path) as conn:
            cursor = conn.execute(
                """
                SELECT u.*, i.name as institution_name, i.code as institution_code
                FROM users u
                LEFT JOIN institutions i ON u.institution_id = i.id
                WHERE LOWER(TRIM(u.email)) = ?
                """,
                (clean_email,)
            )
            row = cursor.fetchone()

        if not row:
            log_event("AUTH_FAILED", "user", clean_email, actor=clean_email, details={"reason": "USER_NOT_FOUND"}, db_path=db_path)
            return None

        user = dict(row)

        # Check account status
        if user["status"] != "ACTIVE" or not user["is_active"]:
            log_event("AUTH_FAILED", "user", user["id"], actor=clean_email, details={"reason": "ACCOUNT_DISABLED"}, db_path=db_path)
            return None

        # Check role compatibility
        if expected_role and user["role"] != expected_role:
            log_event("AUTH_FAILED", "user", user["id"], actor=clean_email, details={"reason": "ROLE_MISMATCH", "expected": expected_role, "actual": user["role"]}, db_path=db_path)
            return None

        # Verify password with bcrypt
        stored_hash = user["password_hash"]
        try:
            is_valid = bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
        except Exception:
            is_valid = False

        if not is_valid:
            log_event("AUTH_FAILED", "user", user["id"], actor=clean_email, details={"reason": "INVALID_PASSWORD"}, db_path=db_path)
            return None

        # Update last_login_at
        with get_db(db_path) as conn:
            conn.execute("UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = ?", (user["id"],))

        log_event("AUTH_SUCCESS", "user", user["id"], actor=clean_email, details={"role": user["role"], "institution_id": user["institution_id"]}, db_path=db_path)

        user.pop("password_hash", None)
        return user

    @staticmethod
    def update_password(user_id: str, new_password: str, db_path: Optional[str] = None) -> bool:
        salt = bcrypt.gensalt(rounds=12)
        pw_hash = bcrypt.hashpw(new_password.encode("utf-8"), salt).decode("utf-8")
        with get_db(db_path) as conn:
            conn.execute("UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (pw_hash, user_id))
        log_event("PASSWORD_ROTATED", "user", user_id, actor="SYSTEM", db_path=db_path)
        return True

    @staticmethod
    def set_user_status(user_id: str, status: str, db_path: Optional[str] = None) -> bool:
        is_active = 1 if status.upper() == "ACTIVE" else 0
        with get_db(db_path) as conn:
            conn.execute("UPDATE users SET status = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (status.upper(), is_active, user_id))
        log_event("USER_STATUS_CHANGED", "user", user_id, actor="SYSTEM", details={"new_status": status.upper()}, db_path=db_path)
        return True


class ApplicationService:
    @staticmethod
    def create_application(
        institution_or_user: Any = None,
        category: str = "NEW_TECHNICAL_INSTITUTION",
        academic_year: str = "2026-2027",
        actor: str = "",
        notes: str = "",
        db_path: Optional[str] = None,
        institution_id: Optional[str] = None,
        initial_status: str = "DRAFT"
    ) -> Dict[str, Any]:
        """Creates an application for a college."""
        target_inst = institution_id if institution_id is not None else institution_or_user
        if isinstance(target_inst, dict):
            final_inst_id = target_inst.get("institution_id") or target_inst.get("id")
            if not actor:
                actor = target_inst.get("email", "USER")
        else:
            final_inst_id = str(target_inst)

        app_id = f"app_{uuid.uuid4().hex[:10]}"
        app_no = f"AICTE-{datetime.now().year}-{uuid.uuid4().hex[:6].upper()}"

        with get_db(db_path) as conn:
            conn.execute(
                """
                INSERT INTO applications (id, application_number, institution_id, category, academic_year, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (app_id, app_no, final_inst_id, category, academic_year, initial_status, notes)
            )

        log_event("APPLICATION_CREATED", "application", app_id, actor=actor or "USER", details={"application_number": app_no, "institution_id": final_inst_id, "status": initial_status}, db_path=db_path)
        return {"id": app_id, "application_number": app_no, "status": initial_status}

    @staticmethod
    def get_all_institutions(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns all registered institutions."""
        with get_db(db_path) as conn:
            cursor = conn.execute("SELECT * FROM institutions ORDER BY name ASC")
            return [dict(r) for r in cursor.fetchall()]


    @staticmethod
    def get_applications_for_user(user: Dict[str, Any], db_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns applications strictly filtered by institution for college reps, or all for officers."""
        role = user.get("role")
        inst_id = user.get("institution_id")

        with get_db(db_path) as conn:
            if role == "COLLEGE_REPRESENTATIVE":
                cursor = conn.execute(
                    """
                    SELECT a.*, i.name as institution_name, i.code as institution_code,
                           (SELECT COUNT(*) FROM documents d WHERE d.application_id = a.id) as doc_count,
                           (SELECT COUNT(*) FROM clarifications c WHERE c.application_id = a.id AND c.status = 'OPEN') as open_clarifications
                    FROM applications a
                    JOIN institutions i ON a.institution_id = i.id
                    WHERE a.institution_id = ?
                    ORDER BY a.created_at DESC
                    """,
                    (inst_id,)
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT a.*, i.name as institution_name, i.code as institution_code,
                           (SELECT COUNT(*) FROM documents d WHERE d.application_id = a.id) as doc_count,
                           (SELECT COUNT(*) FROM clarifications c WHERE c.application_id = a.id AND c.status = 'OPEN') as open_clarifications
                    FROM applications a
                    JOIN institutions i ON a.institution_id = i.id
                    ORDER BY a.created_at DESC
                    """
                )
            return [dict(r) for r in cursor.fetchall()]

    @staticmethod
    def get_notifications_for_user(user: Dict[str, Any], db_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns clarification inquiries and regulatory status notifications for an institution."""
        role = user.get("role")
        inst_id = user.get("institution_id")
        if role != "COLLEGE_REPRESENTATIVE" or not inst_id:
            return []

        with get_db(db_path) as conn:
            cursor = conn.execute(
                """
                SELECT c.*, a.application_number, a.status as app_status, a.category
                FROM clarifications c
                JOIN applications a ON c.application_id = a.id
                WHERE c.institution_id = ?
                ORDER BY c.created_at DESC
                """,
                (inst_id,)
            )
            return [dict(r) for r in cursor.fetchall()]

    @staticmethod
    def get_application_details(app_id: str, user: Dict[str, Any], db_path: Optional[str] = None) -> Dict[str, Any]:
        """Fetches application packet with multi-tenant isolation guard."""
        role = user.get("role")
        user_inst_id = user.get("institution_id")

        with get_db(db_path) as conn:
            cursor = conn.execute(
                """
                SELECT a.*, i.name as institution_name, i.code as institution_code, i.state, i.city
                FROM applications a
                JOIN institutions i ON a.institution_id = i.id
                WHERE a.id = ?
                """,
                (app_id,)
            )
            row = cursor.fetchone()

        if not row:
            raise KeyError(f"Application '{app_id}' not found.")

        app = dict(row)

        # Multi-tenant security guard: college reps cannot access other colleges' applications
        if role == "COLLEGE_REPRESENTATIVE" and app["institution_id"] != user_inst_id:
            raise PermissionError(f"Unauthorized: College Representative cannot access application '{app_id}' belonging to another institution.")

        # Load documents
        with get_db(db_path) as conn:
            doc_cur = conn.execute(
                """
                SELECT d.*, f.risk_score, f.risk_band, f.findings_json as forensic_flags
                FROM documents d
                LEFT JOIN forensic_results f ON d.id = f.document_id
                WHERE d.application_id = ?
                ORDER BY d.uploaded_at ASC
                """,
                (app_id,)
            )
            docs = [dict(d) for d in doc_cur.fetchall()]

            # Load clarifications
            clarif_cur = conn.execute(
                """
                SELECT * FROM clarifications
                WHERE application_id = ?
                ORDER BY created_at DESC
                """,
                (app_id,)
            )
            clarifs = [dict(c) for c in clarif_cur.fetchall()]

        # Compute document completeness
        mandatory = MANDATORY_DOCUMENTS.get(app["category"], MANDATORY_DOCUMENTS["NEW_TECHNICAL_INSTITUTION"])
        present_types = {d["document_type"] for d in docs}
        missing_docs = [m for m in mandatory if m not in present_types]
        completeness_pct = int(100 * (len(mandatory) - len(missing_docs)) / max(len(mandatory), 1))

        # Attach latest validation run per document
        for d in docs:
            d["validation_run"] = ValidationEngine.get_latest_run_for_document(d["id"], db_path=db_path)

        val_summary = ValidationEngine.get_application_validation_summary(app_id, db_path=db_path)

        return {
            "application": app,
            "documents": docs,
            "clarifications": clarifs,
            "mandatory_checklist": mandatory,
            "missing_documents": missing_docs,
            "completeness_pct": completeness_pct,
            "validation_summary": val_summary
        }

    @staticmethod
    def upload_document(
        app_id: str,
        user: Dict[str, Any],
        doc_type: str,
        filename: str,
        file_bytes: bytes,
        uploads_dir: Optional[str] = None,
        db_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Uploads and performs automated forensic analysis with safety checks."""
        # 1. Multi-tenant check
        app_packet = ApplicationService.get_application_details(app_id, user, db_path=db_path)
        app = app_packet["application"]

        if app["status"] in ["APPROVED", "REJECTED"]:
            raise PermissionError("Cannot upload documents to concluded applications.")

        # 2. File size & empty check
        if not file_bytes or len(file_bytes) == 0:
            raise ValueError("Uploaded file is empty (0 bytes). Please upload a valid document.")

        if len(file_bytes) > MAX_FILE_SIZE:
            raise ValueError(f"File size exceeds maximum permitted limit of 15 MB (received {len(file_bytes)} bytes).")

        # 3. Filename sanitization & path traversal defense
        clean_basename = os.path.basename(filename)
        clean_basename = re.sub(r'[^a-zA-Z0-9_.-]', '_', clean_basename)
        if not clean_basename:
            clean_basename = "document.pdf"

        ext = os.path.splitext(clean_basename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file extension '{ext}'. Only PDF and image files ({', '.join(ALLOWED_EXTENSIONS)}) are permitted.")

        # 4. PDF header check
        if ext == ".pdf" and not is_valid_pdf_magic(file_bytes):
            raise ValueError("Corrupt or invalid PDF: File lacks the required '%PDF-' file signature.")

        doc_id = f"doc_{uuid.uuid4().hex[:12]}"
        sha256 = compute_sha256(file_bytes)
        safe_name = f"{doc_id}_{clean_basename}"

        target_dir = uploads_dir or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "uploads"))
        os.makedirs(target_dir, exist_ok=True)
        stored_path = os.path.join(target_dir, safe_name)

        # Defend against directory traversal
        if not os.path.abspath(stored_path).startswith(os.path.abspath(target_dir)):
            raise ValueError("Security violation: Filename contains invalid path traversal sequences.")

        with open(stored_path, "wb") as f:
            f.write(file_bytes)

        mime_type = "application/pdf" if ext == ".pdf" else "image/jpeg"

        with get_db(db_path) as conn:
            # If replacing an existing document of the same category in DRAFT or CLARIFICATION_REQUESTED
            if app["status"] in ["DRAFT", "CLARIFICATION_REQUESTED"]:
                old_cur = conn.execute("SELECT id FROM documents WHERE application_id = ? AND document_type = ?", (app_id, doc_type))
                for old_r in old_cur.fetchall():
                    conn.execute("DELETE FROM documents WHERE id = ?", (old_r["id"],))
                    conn.execute("DELETE FROM validation_runs WHERE document_id = ?", (old_r["id"],))

            conn.execute(
                """
                INSERT INTO documents (id, application_id, document_type, filename, stored_path, file_size, sha256_hash, mime_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (doc_id, app_id, doc_type, clean_basename, stored_path, len(file_bytes), sha256, mime_type)
            )

        # 5. Run automated validation suite (Transparent Engine)
        val_run = ValidationEngine.validate_document(
            doc_id=doc_id,
            app_id=app_id,
            filepath=stored_path,
            filename=clean_basename,
            doc_type=doc_type,
            file_bytes=file_bytes,
            triggered_by=user.get("email", "USER"),
            db_path=db_path
        )
        forensic_data = val_run.to_dict()

        log_event("DOCUMENT_UPLOADED", "document", doc_id, actor=user["email"], details={"filename": clean_basename, "sha256": sha256, "validation_status": val_run.status}, db_path=db_path)
        return {"id": doc_id, "sha256": sha256, "forensic": forensic_data, "validation_run": forensic_data, "stored_path": stored_path}

    @staticmethod
    def delete_document(doc_id: str, user: Dict[str, Any], db_path: Optional[str] = None):
        """Removes an uploaded document from a draft or clarification application."""
        with get_db(db_path) as conn:
            cur = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
            row = cur.fetchone()
        if not row:
            raise KeyError(f"Document '{doc_id}' not found.")
        doc = dict(row)

        app_packet = ApplicationService.get_application_details(doc["application_id"], user, db_path=db_path)
        app = app_packet["application"]
        if app["status"] not in ["DRAFT", "CLARIFICATION_REQUESTED"]:
            raise PermissionError("Documents can only be modified in DRAFT or CLARIFICATION_REQUESTED status.")

        with get_db(db_path) as conn:
            conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            conn.execute("DELETE FROM validation_runs WHERE document_id = ?", (doc_id,))

        log_event("DOCUMENT_REMOVED", "document", doc_id, actor=user["email"], details={"filename": doc["filename"], "application_id": doc["application_id"]}, db_path=db_path)

    @staticmethod
    def submit_application(app_id: str, user: Dict[str, Any], db_path: Optional[str] = None):
        """Submits draft application for regulatory scrutiny."""
        app_packet = ApplicationService.get_application_details(app_id, user, db_path=db_path)
        app = app_packet["application"]

        if app["status"] != "DRAFT":
            raise ValueError(f"Cannot submit application in status '{app['status']}'. Only DRAFT applications can be submitted.")

        if app_packet["completeness_pct"] < 100:
            raise ValueError(f"Cannot submit: Mandatory regulatory documents missing: {', '.join(app_packet['missing_documents'])}")

        with get_db(db_path) as conn:
            conn.execute(
                "UPDATE applications SET status = 'SUBMITTED', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (app_id,)
            )

        log_event("APPLICATION_SUBMITTED", "application", app_id, actor=user["email"], db_path=db_path)

    @staticmethod
    def request_clarification(
        app_id: str,
        officer_user: Dict[str, Any],
        question_text: str,
        requested_docs: Optional[str] = None,
        db_path: Optional[str] = None
    ) -> str:
        """AICTE Scrutiny Officer requests clarification from applicant."""
        if officer_user.get("role") != "AICTE_SCRUTINY_OFFICER":
            raise PermissionError("Only AICTE Scrutiny Officers can request statutory clarification.")

        app_packet = ApplicationService.get_application_details(app_id, officer_user, db_path=db_path)
        app = app_packet["application"]

        if app["status"] not in ["SUBMITTED", "UNDER_SCRUTINY"]:
            raise ValueError(f"Cannot request clarification on application in status '{app['status']}'. Application must be SUBMITTED or UNDER_SCRUTINY.")

        clarif_id = f"clr_{uuid.uuid4().hex[:10]}"

        with get_db(db_path) as conn:
            conn.execute(
                """
                INSERT INTO clarifications (id, application_id, institution_id, requested_by, question_text, requested_documents, status)
                VALUES (?, ?, ?, ?, ?, ?, 'OPEN')
                """,
                (clarif_id, app_id, app["institution_id"], officer_user["email"], question_text, requested_docs)
            )
            conn.execute(
                "UPDATE applications SET status = 'CLARIFICATION_REQUESTED', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (app_id,)
            )

        log_event("CLARIFICATION_REQUESTED", "clarification", clarif_id, actor=officer_user["email"], details={"application_id": app_id, "question": question_text}, db_path=db_path)
        return clarif_id

    @staticmethod
    def respond_clarification(
        clarif_id: str,
        college_user: Dict[str, Any],
        response_text: str,
        response_docs: Optional[str] = None,
        supplementary_file: Optional[Dict[str, Any]] = None,
        uploads_dir: Optional[str] = None,
        db_path: Optional[str] = None
    ):
        """College representative responds to clarification, optionally attaching a supplementary file, and resubmits."""
        with get_db(db_path) as conn:
            cursor = conn.execute("SELECT * FROM clarifications WHERE id = ?", (clarif_id,))
            row = cursor.fetchone()

        if not row:
            raise KeyError(f"Clarification '{clarif_id}' not found.")

        clarif = dict(row)
        if college_user.get("role") == "COLLEGE_REPRESENTATIVE" and clarif["institution_id"] != college_user.get("institution_id"):
            raise PermissionError("Unauthorized: Institution representative cannot respond to another college's clarification.")

        if clarif["status"] == "RESOLVED":
            raise ValueError(f"Clarification '{clarif_id}' is already resolved.")

        # If a supplementary file was provided, upload it to the application dossier
        doc_note = response_docs or ""
        if supplementary_file and supplementary_file.get("bytes"):
            s_name = supplementary_file.get("filename", "supplementary_evidence.pdf")
            s_bytes = supplementary_file["bytes"]
            doc_res = ApplicationService.upload_document(
                app_id=clarif["application_id"],
                user=college_user,
                doc_type="CLARIFICATION_EVIDENCE",
                filename=s_name,
                file_bytes=s_bytes,
                uploads_dir=uploads_dir,
                db_path=db_path
            )
            doc_note = f"{s_name} (SHA-256: {doc_res['sha256'][:16]}...) - {doc_note}".strip(" -")

        with get_db(db_path) as conn:
            conn.execute(
                """
                UPDATE clarifications
                SET status = 'RESOLVED', response_text = ?, response_documents = ?, resolved_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (response_text, doc_note, clarif_id)
            )
            conn.execute(
                "UPDATE applications SET status = 'UNDER_SCRUTINY', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (clarif["application_id"],)
            )

        log_event("CLARIFICATION_RESPONDED", "clarification", clarif_id, actor=college_user["email"], details={"application_id": clarif["application_id"], "response": response_text, "attachment": doc_note}, db_path=db_path)

    @staticmethod
    def record_decision(
        app_id: str,
        officer_user: Dict[str, Any],
        outcome: str,
        notes: str = "",
        db_path: Optional[str] = None
    ):
        """AICTE Officer records final statutory outcome (APPROVED or REJECTED)."""
        if officer_user.get("role") != "AICTE_SCRUTINY_OFFICER":
            raise PermissionError("Only AICTE Scrutiny Officers can record final approval/rejection outcomes.")

        valid_outcomes = ["APPROVED", "REJECTED", "UNDER_SCRUTINY"]
        if outcome not in valid_outcomes:
            raise ValueError(f"Outcome must be one of {valid_outcomes}")

        app_packet = ApplicationService.get_application_details(app_id, officer_user, db_path=db_path)
        app = app_packet["application"]
        if app["status"] == "DRAFT":
            raise ValueError("Cannot record decision on application in 'DRAFT' status. Application must be submitted for scrutiny.")

        clean_notes = notes.strip() if notes else f"Application {outcome.lower()} by AICTE Scrutiny Officer."

        with get_db(db_path) as conn:
            conn.execute(
                "UPDATE applications SET status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (outcome, clean_notes, app_id)
            )

        log_event(f"APPLICATION_{outcome}", "application", app_id, actor=officer_user["email"], details={"outcome": outcome, "notes": clean_notes}, db_path=db_path)


    @staticmethod
    def rerun_validation(doc_id: str, user: Dict[str, Any], db_path: Optional[str] = None) -> Dict[str, Any]:
        """Manually re-triggers the document validation engine."""
        with get_db(db_path) as conn:
            cur = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
            doc_row = cur.fetchone()
        if not doc_row:
            raise KeyError(f"Document '{doc_id}' not found.")
        d = dict(doc_row)
        run_res = ValidationEngine.validate_document(
            doc_id=d["id"],
            app_id=d["application_id"],
            filepath=d["stored_path"],
            filename=d["filename"],
            doc_type=d["document_type"],
            triggered_by=user.get("email", "OFFICER"),
            db_path=db_path
        )
        return run_res.to_dict()

    @staticmethod
    def record_finding_disposition(
        check_record_id: str,
        doc_id: str,
        app_id: str,
        user: Dict[str, Any],
        disposition: str,
        notes: str,
        db_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Records an officer's human review determination on a specific check finding."""
        return ValidationEngine.record_finding_disposition(
            check_record_id=check_record_id,
            doc_id=doc_id,
            app_id=app_id,
            officer_email=user["email"],
            disposition=disposition,
            officer_notes=notes,
            db_path=db_path
        )

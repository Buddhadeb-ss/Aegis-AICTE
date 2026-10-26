"""
Aegis Foundation - Database Engine and Persistence
SQLite database schema, connection pooling, and idempotent seeding.
"""

import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional
import bcrypt

DEFAULT_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "aegis.db"))


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    target_path = db_path or DEFAULT_DB_PATH
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    conn = sqlite3.connect(target_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


@contextmanager
def get_db(db_path: Optional[str] = None):
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: Optional[str] = None):
    """Initializes schema idempotently."""
    with get_db(db_path) as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS institutions (
            id VARCHAR(64) PRIMARY KEY,
            name VARCHAR(256) NOT NULL,
            code VARCHAR(64) UNIQUE NOT NULL,
            state VARCHAR(64),
            city VARCHAR(64),
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS users (
            id VARCHAR(64) PRIMARY KEY,
            name VARCHAR(128) NOT NULL,
            email VARCHAR(128) UNIQUE NOT NULL,
            password_hash VARCHAR(256) NOT NULL,
            role VARCHAR(64) NOT NULL,
            institution_id VARCHAR(64),
            status VARCHAR(32) DEFAULT 'ACTIVE' NOT NULL,
            is_active INTEGER DEFAULT 1 NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login_at TIMESTAMP,
            FOREIGN KEY (institution_id) REFERENCES institutions(id)
        );

        CREATE TABLE IF NOT EXISTS applications (
            id VARCHAR(64) PRIMARY KEY,
            application_number VARCHAR(64) UNIQUE NOT NULL,
            institution_id VARCHAR(64) NOT NULL,
            category VARCHAR(64) NOT NULL,
            academic_year VARCHAR(32) NOT NULL,
            status VARCHAR(64) DEFAULT 'DRAFT' NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (institution_id) REFERENCES institutions(id)
        );

        CREATE TABLE IF NOT EXISTS documents (
            id VARCHAR(64) PRIMARY KEY,
            application_id VARCHAR(64) NOT NULL,
            document_type VARCHAR(64) NOT NULL,
            filename VARCHAR(256) NOT NULL,
            stored_path VARCHAR(512) NOT NULL,
            file_size INTEGER NOT NULL,
            sha256_hash VARCHAR(64) NOT NULL,
            mime_type VARCHAR(64) NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS document_versions (
            id VARCHAR(64) PRIMARY KEY,
            document_id VARCHAR(64) NOT NULL,
            application_id VARCHAR(64) NOT NULL,
            document_type VARCHAR(64) NOT NULL,
            filename VARCHAR(256) NOT NULL,
            stored_path VARCHAR(512) NOT NULL,
            file_size INTEGER NOT NULL,
            sha256_hash VARCHAR(64) NOT NULL,
            mime_type VARCHAR(64) NOT NULL,
            version_number INTEGER NOT NULL,
            validation_status VARCHAR(32) DEFAULT 'PENDING',
            findings_summary TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            archived_by VARCHAR(128) NOT NULL,
            FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS clarifications (
            id VARCHAR(64) PRIMARY KEY,
            application_id VARCHAR(64) NOT NULL,
            institution_id VARCHAR(64) NOT NULL,
            requested_by VARCHAR(128) NOT NULL,
            question_text TEXT NOT NULL,
            requested_documents TEXT,
            status VARCHAR(32) DEFAULT 'OPEN' NOT NULL,
            response_text TEXT,
            response_documents TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP,
            FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE,
            FOREIGN KEY (institution_id) REFERENCES institutions(id)
        );

        CREATE TABLE IF NOT EXISTS audit_events (
            id VARCHAR(64) PRIMARY KEY,
            event_type VARCHAR(64) NOT NULL,
            entity_type VARCHAR(64) NOT NULL,
            entity_id VARCHAR(64) NOT NULL,
            actor VARCHAR(128) NOT NULL,
            details_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS forensic_results (
            id VARCHAR(64) PRIMARY KEY,
            document_id VARCHAR(64) UNIQUE NOT NULL,
            application_id VARCHAR(64) NOT NULL,
            risk_score REAL NOT NULL,
            risk_band VARCHAR(32) NOT NULL,
            pdf_audit_json TEXT,
            findings_json TEXT,
            analysed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
            FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS validation_runs (
            id VARCHAR(64) PRIMARY KEY,
            document_id VARCHAR(64) NOT NULL,
            application_id VARCHAR(64) NOT NULL,
            engine_version VARCHAR(32) NOT NULL,
            status VARCHAR(32) NOT NULL,
            total_checks INTEGER DEFAULT 0 NOT NULL,
            passed_checks INTEGER DEFAULT 0 NOT NULL,
            failed_checks INTEGER DEFAULT 0 NOT NULL,
            warning_checks INTEGER DEFAULT 0 NOT NULL,
            review_required_checks INTEGER DEFAULT 0 NOT NULL,
            not_run_checks INTEGER DEFAULT 0 NOT NULL,
            error_checks INTEGER DEFAULT 0 NOT NULL,
            summary_text TEXT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            triggered_by VARCHAR(128) DEFAULT 'AUTO_UPLOAD' NOT NULL,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
            FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS validation_checks (
            id VARCHAR(64) PRIMARY KEY,
            run_id VARCHAR(64) NOT NULL,
            document_id VARCHAR(64) NOT NULL,
            application_id VARCHAR(64) NOT NULL,
            check_id VARCHAR(64) NOT NULL,
            check_name VARCHAR(128) NOT NULL,
            category VARCHAR(64) NOT NULL,
            status VARCHAR(32) NOT NULL,
            severity VARCHAR(32) NOT NULL,
            summary TEXT NOT NULL,
            details TEXT,
            evidence_json TEXT,
            expected_value TEXT,
            observed_value TEXT,
            recommendation TEXT,
            duration_ms REAL DEFAULT 0.0,
            engine_version VARCHAR(32) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (run_id) REFERENCES validation_runs(id) ON DELETE CASCADE,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
            FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS finding_dispositions (
            id VARCHAR(64) PRIMARY KEY,
            check_record_id VARCHAR(64) NOT NULL,
            document_id VARCHAR(64) NOT NULL,
            application_id VARCHAR(64) NOT NULL,
            officer_email VARCHAR(128) NOT NULL,
            disposition VARCHAR(32) NOT NULL,
            officer_notes TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (check_record_id) REFERENCES validation_checks(id) ON DELETE CASCADE,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
            FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_apps_inst ON applications(institution_id);
        CREATE INDEX IF NOT EXISTS idx_docs_app ON documents(application_id);
        CREATE INDEX IF NOT EXISTS idx_clarif_app ON clarifications(application_id);
        CREATE INDEX IF NOT EXISTS idx_doc_versions_app ON document_versions(application_id);
        CREATE INDEX IF NOT EXISTS idx_doc_versions_type ON document_versions(application_id, document_type);
        CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_events(created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_val_runs_doc ON validation_runs(document_id);
        CREATE INDEX IF NOT EXISTS idx_val_runs_app ON validation_runs(application_id);
        CREATE INDEX IF NOT EXISTS idx_val_checks_run ON validation_checks(run_id);
        CREATE INDEX IF NOT EXISTS idx_val_checks_doc ON validation_checks(document_id);
        CREATE INDEX IF NOT EXISTS idx_val_checks_status ON validation_checks(status);
        CREATE INDEX IF NOT EXISTS idx_dispositions_check ON finding_dispositions(check_record_id);
        """)


def seed_foundation(db_path: Optional[str] = None, force_reset: bool = False):
    """Seeds synthetic test institutions and persistent users."""
    init_db(db_path)
    with get_db(db_path) as conn:
        if force_reset:
            conn.execute("DELETE FROM finding_dispositions")
            conn.execute("DELETE FROM validation_checks")
            conn.execute("DELETE FROM validation_runs")
            conn.execute("DELETE FROM clarifications")
            conn.execute("DELETE FROM forensic_results")
            conn.execute("DELETE FROM document_versions")
            conn.execute("DELETE FROM documents")
            conn.execute("DELETE FROM applications")
            conn.execute("DELETE FROM users")
            conn.execute("DELETE FROM institutions")

        # 1. Institutions
        inst_records = [
            ("inst_apex_1001", "Apex Institute of Technology", "APEX-MH-1001", "Maharashtra", "Pune", "Survey 45, Katraj-Dehu Bypass Road, Pune"),
            ("inst_beacon_2002", "Beacon College of Engineering", "BEACON-KA-2002", "Karnataka", "Bengaluru", "Plot 12, Whitefield Industrial Area, Bengaluru")
        ]
        for inst_id, name, code, state, city, addr in inst_records:
            conn.execute(
                """
                INSERT INTO institutions (id, name, code, state, city, address)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET name=excluded.name, code=excluded.code
                """,
                (inst_id, name, code, state, city, addr)
            )

        # 2. Users (bcrypt hash)
        user_specs = [
            ("usr_admin_01", "Aegis Test Administrator", "admin@aicte.gov.in", "AegisAdmin@2026#Secure", "AICTE_SCRUTINY_OFFICER", None),
            ("usr_apex_01", "Apex Institute Representative", "principal@apextech.edu", "ApexPrincipal@2026#Secure", "COLLEGE_REPRESENTATIVE", "inst_apex_1001"),
            ("usr_beacon_01", "Beacon College Representative", "registrar@beacon.ac.in", "BeaconRegistrar@2026#Secure", "COLLEGE_REPRESENTATIVE", "inst_beacon_2002")
        ]
        for uid, name, email, plain_pw, role, inst_id in user_specs:
            cursor = conn.execute("SELECT id FROM users WHERE email = ?", (email.strip().lower(),))
            existing = cursor.fetchone()
            if not existing or force_reset:
                salt = bcrypt.gensalt(rounds=12)
                pw_hash = bcrypt.hashpw(plain_pw.encode("utf-8"), salt).decode("utf-8")
                conn.execute(
                    """
                    INSERT INTO users (id, name, email, password_hash, role, institution_id, status, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, 'ACTIVE', 1)
                    ON CONFLICT(email) DO UPDATE SET password_hash=excluded.password_hash
                    """,
                    (uid, name, email.strip().lower(), pw_hash, role, inst_id)
                )

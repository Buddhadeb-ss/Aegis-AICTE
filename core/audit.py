"""
Aegis Foundation - Regulatory Audit Trail
Append-only structured audit logger for statutory compliance.
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from core.db import get_db


def log_event(
    event_type: str,
    entity_type: str,
    entity_id: str,
    actor: str,
    details: Optional[Dict[str, Any]] = None,
    db_path: Optional[str] = None
) -> str:
    """Records an immutable audit event."""
    event_id = f"aud_{uuid.uuid4().hex[:12]}"
    details_str = json.dumps(details or {}, default=str)

    with get_db(db_path) as conn:
        conn.execute(
            """
            INSERT INTO audit_events (id, event_type, entity_type, entity_id, actor, details_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (event_id, event_type, entity_type, entity_id, actor, details_str, datetime.now().isoformat())
        )
    return event_id


def get_audit_events(
    entity_id: Optional[str] = None,
    limit: int = 100,
    db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Retrieves recent audit events."""
    with get_db(db_path) as conn:
        if entity_id:
            cursor = conn.execute(
                """
                SELECT * FROM audit_events
                WHERE entity_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (entity_id, limit)
            )
        else:
            cursor = conn.execute(
                """
                SELECT * FROM audit_events
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,)
            )
        return [dict(r) for r in cursor.fetchall()]

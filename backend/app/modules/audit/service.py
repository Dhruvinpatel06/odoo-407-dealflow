"""Audit service layer."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.modules.audit.repository import audit_repository


class AuditService:
    """Coordinates cross-cutting audit event generation and querying."""

    def log_event(
        self,
        db: Session,
        entity_type: str,
        entity_id: uuid.UUID,
        action: str,
        user_id: Optional[uuid.UUID] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None,
    ) -> AuditLog:
        """
        Create and record an authoritative backend audit event.
        Persisted within the active transaction to maintain consistency.
        """
        audit_entry = AuditLog(
            user_id=user_id,
            entity_type=entity_type.upper(),
            entity_id=entity_id,
            action=action.upper(),
            old_values=old_values,
            new_values=new_values,
            reason=reason,
        )
        return audit_repository.create_audit_log(db, audit_entry)

    def list_logs(
        self,
        db: Session,
        entity_type: Optional[str] = None,
        entity_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        action: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AuditLog]:
        """Query audit log history with optional filters."""
        return audit_repository.list_audit_logs(
            db=db,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            action=action,
            skip=skip,
            limit=limit,
        )


audit_service = AuditService()

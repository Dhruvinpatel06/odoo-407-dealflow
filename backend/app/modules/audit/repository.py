"""Audit repository layer."""

from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditRepository:
    """Persistence operations for the cross-cutting audit log."""

    def create_audit_log(self, db: Session, audit_log: AuditLog) -> AuditLog:
        """Persist an audit log entry in the database session."""
        db.add(audit_log)
        db.flush()
        return audit_log

    def list_audit_logs(
        self,
        db: Session,
        entity_type: Optional[str] = None,
        entity_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        action: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AuditLog]:
        """Query audit logs with optional entity, user, and action filters."""
        stmt = select(AuditLog).order_by(AuditLog.created_at.desc())
        if entity_type is not None:
            stmt = stmt.where(AuditLog.entity_type == entity_type)
        if entity_id is not None:
            stmt = stmt.where(AuditLog.entity_id == entity_id)
        if user_id is not None:
            stmt = stmt.where(AuditLog.user_id == user_id)
        if action is not None:
            stmt = stmt.where(AuditLog.action == action)

        stmt = stmt.offset(skip).limit(limit)
        return list(db.execute(stmt).scalars().all())

    def get_audit_log_by_id(
        self, db: Session, audit_log_id: uuid.UUID
    ) -> Optional[AuditLog]:
        """Retrieve a specific audit log by its UUID."""
        return db.get(AuditLog, audit_log_id)


audit_repository = AuditRepository()

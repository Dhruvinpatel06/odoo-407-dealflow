"""Approval Policies repository layer."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.approval_policy import ApprovalPolicy


class ApprovalPolicyRepository:
    """Handles persistence operations for ApprovalPolicy entities."""

    def create_policy(
        self, db: Session, policy: ApprovalPolicy
    ) -> ApprovalPolicy:
        """Add and flush a new ApprovalPolicy entity."""
        db.add(policy)
        db.flush()
        return policy

    def get_policy_by_id(
        self, db: Session, policy_id: uuid.UUID
    ) -> Optional[ApprovalPolicy]:
        """Fetch an ApprovalPolicy by primary key UUID."""
        return (
            db.query(ApprovalPolicy)
            .filter(ApprovalPolicy.id == policy_id)
            .first()
        )

    def get_policy_by_name(
        self, db: Session, name: str
    ) -> Optional[ApprovalPolicy]:
        """Fetch an ApprovalPolicy by case-insensitive name."""
        return (
            db.query(ApprovalPolicy)
            .filter(func.lower(ApprovalPolicy.name) == name.strip().lower())
            .first()
        )

    def list_policies(
        self,
        db: Session,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ApprovalPolicy]:
        """
        List approval policies with optional active status filter, ordered by priority descending.
        """
        query = db.query(ApprovalPolicy)
        if is_active is not None:
            query = query.filter(ApprovalPolicy.is_active == is_active)

        return (
            query.order_by(
                ApprovalPolicy.priority.desc(),
                ApprovalPolicy.created_at.asc(),
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def list_active_policies(self, db: Session) -> List[ApprovalPolicy]:
        """Retrieve all active approval policies ordered by priority descending."""
        return (
            db.query(ApprovalPolicy)
            .filter(ApprovalPolicy.is_active.is_(True))
            .order_by(
                ApprovalPolicy.priority.desc(),
                ApprovalPolicy.created_at.asc(),
            )
            .all()
        )

    def update_policy(
        self,
        db: Session,
        policy: ApprovalPolicy,
        updates: Dict[str, Any],
    ) -> ApprovalPolicy:
        """Apply updates dictionary to the policy and flush changes."""
        for key, value in updates.items():
            setattr(policy, key, value)
        db.flush()
        return policy

    def deactivate_policy(
        self, db: Session, policy: ApprovalPolicy
    ) -> ApprovalPolicy:
        """Logically deactivate an approval policy."""
        policy.is_active = False
        db.flush()
        return policy


approval_policy_repository = ApprovalPolicyRepository()

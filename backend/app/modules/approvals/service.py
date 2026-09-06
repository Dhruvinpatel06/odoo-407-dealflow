"""Approval Policy service layer."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.exceptions import (
    BusinessRuleViolationError,
    DealFlowException,
    ResourceNotFoundError,
)
from app.models.approval_policy import ApprovalPolicy
from app.models.user import User
from app.modules.approvals.repository import (
    ApprovalPolicyRepository,
    approval_policy_repository,
)
from app.modules.approvals.schemas import (
    ApprovalPolicyCreateRequest,
    ApprovalPolicyUpdateRequest,
)
from app.modules.audit.service import audit_service


def _policy_to_audit_dict(policy: ApprovalPolicy) -> Dict[str, Any]:
    """Serialize ApprovalPolicy state for authoritative audit logging."""
    return {
        "id": str(policy.id),
        "name": policy.name,
        "min_risk_score": (
            str(policy.min_risk_score)
            if policy.min_risk_score is not None
            else None
        ),
        "max_risk_score": (
            str(policy.max_risk_score)
            if policy.max_risk_score is not None
            else None
        ),
        "requires_manager": policy.requires_manager,
        "requires_finance": policy.requires_finance,
        "priority": policy.priority,
        "is_active": policy.is_active,
    }


class ApprovalPolicyService:
    """Coordinates business logic and workflows for approval policies."""

    def __init__(
        self, repository: ApprovalPolicyRepository = approval_policy_repository
    ) -> None:
        self.repository = repository

    def find_conflicting_policy(
        self,
        db: Session,
        min_risk_score: Decimal,
        max_risk_score: Optional[Decimal],
        priority: int,
        exclude_id: Optional[uuid.UUID] = None,
    ) -> Optional[ApprovalPolicy]:
        """Check if an active policy already covers the exact same risk boundary and priority."""
        active_policies = self.repository.list_active_policies(db)
        for p in active_policies:
            if exclude_id and p.id == exclude_id:
                continue
            p_min = Decimal(str(p.min_risk_score))
            p_max = (
                Decimal(str(p.max_risk_score))
                if p.max_risk_score is not None
                else None
            )
            if (
                p_min == min_risk_score
                and p_max == max_risk_score
                and p.priority == priority
            ):
                return p
        return None

    def create_policy(
        self,
        db: Session,
        request: ApprovalPolicyCreateRequest,
        current_user: Optional[User] = None,
    ) -> ApprovalPolicy:
        """
        Create a new ApprovalPolicy with business constraint validation and audit logging.
        """
        # Validate unique active policy name
        existing = self.repository.get_policy_by_name(db, request.name)
        if existing and existing.is_active:
            raise DealFlowException(
                f"An active approval policy named '{request.name}' already exists",
                status_code=400,
            )

        # Validate score bounds
        if request.min_risk_score < Decimal("0.00"):
            raise BusinessRuleViolationError(
                "min_risk_score must be greater than or equal to 0.00"
            )
        if (
            request.max_risk_score is not None
            and request.max_risk_score < request.min_risk_score
        ):
            raise BusinessRuleViolationError(
                "max_risk_score must be greater than or equal to min_risk_score"
            )

        # Validate approver sequence invariant
        if request.requires_finance and not request.requires_manager:
            raise BusinessRuleViolationError(
                "Finance approval requires Sales Manager approval in the sequence"
            )

        # Detect duplicate/conflicting active policy with identical range and priority
        if request.is_active:
            conflict = self.find_conflicting_policy(
                db=db,
                min_risk_score=request.min_risk_score,
                max_risk_score=request.max_risk_score,
                priority=request.priority,
            )
            if conflict:
                raise DealFlowException(
                    f"An active approval policy '{conflict.name}' already covers the identical risk score range and priority",
                    status_code=400,
                )

        policy = ApprovalPolicy(
            name=request.name,
            min_risk_score=request.min_risk_score,
            max_risk_score=request.max_risk_score,
            requires_manager=request.requires_manager,
            requires_finance=request.requires_finance,
            priority=request.priority,
            is_active=request.is_active,
        )

        created_policy = self.repository.create_policy(db, policy)

        # Record authoritative backend audit log
        audit_service.log_event(
            db=db,
            entity_type="APPROVAL_POLICY",
            entity_id=created_policy.id,
            action="CREATE",
            user_id=current_user.id if current_user else None,
            old_values=None,
            new_values=_policy_to_audit_dict(created_policy),
            reason=f"Created approval policy '{created_policy.name}'",
        )

        db.commit()
        db.refresh(created_policy)
        return created_policy

    def get_policy(
        self, db: Session, policy_id: uuid.UUID
    ) -> ApprovalPolicy:
        """Fetch approval policy by ID or raise ResourceNotFoundError."""
        policy = self.repository.get_policy_by_id(db, policy_id)
        if not policy:
            raise ResourceNotFoundError(
                f"Approval policy '{policy_id}' not found"
            )
        return policy

    def list_policies(
        self,
        db: Session,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ApprovalPolicy]:
        """List approval policies with optional active status filter."""
        return self.repository.list_policies(
            db=db, is_active=is_active, skip=skip, limit=limit
        )

    def update_policy(
        self,
        db: Session,
        policy_id: uuid.UUID,
        request: ApprovalPolicyUpdateRequest,
        current_user: Optional[User] = None,
    ) -> ApprovalPolicy:
        """
        Update an existing approval policy with validation and audit logging.
        """
        policy = self.get_policy(db, policy_id)
        updates = request.model_dump(exclude_unset=True)

        if not updates:
            return policy

        old_values = _policy_to_audit_dict(policy)

        # Determine target values
        target_name = (
            updates["name"] if "name" in updates else policy.name
        )
        target_min = (
            updates["min_risk_score"]
            if "min_risk_score" in updates
            else policy.min_risk_score
        )
        target_max = (
            updates["max_risk_score"]
            if "max_risk_score" in updates
            else policy.max_risk_score
        )
        target_mgr = (
            updates["requires_manager"]
            if "requires_manager" in updates
            else policy.requires_manager
        )
        target_fin = (
            updates["requires_finance"]
            if "requires_finance" in updates
            else policy.requires_finance
        )
        target_is_active = (
            updates["is_active"]
            if "is_active" in updates
            else policy.is_active
        )
        target_priority = (
            updates["priority"]
            if "priority" in updates
            else policy.priority
        )

        # Name uniqueness check if name is modified or activated
        if "name" in updates or (
            target_is_active and not policy.is_active
        ):
            existing = self.repository.get_policy_by_name(db, target_name)
            if existing and existing.id != policy.id and existing.is_active:
                raise DealFlowException(
                    f"An active approval policy named '{target_name}' already exists",
                    status_code=400,
                )

        # Validate score bounds
        if target_min < Decimal("0.00"):
            raise BusinessRuleViolationError(
                "min_risk_score must be greater than or equal to 0.00"
            )
        if target_max is not None and target_max < target_min:
            raise BusinessRuleViolationError(
                "max_risk_score must be greater than or equal to min_risk_score"
            )
        if target_priority < 0:
            raise BusinessRuleViolationError(
                "priority must be greater than or equal to 0"
            )

        # Validate approver sequence invariant
        if target_fin and not target_mgr:
            raise BusinessRuleViolationError(
                "Finance approval requires Sales Manager approval in the sequence"
            )

        # Detect conflicting active policy with identical range and priority
        if target_is_active:
            conflict = self.find_conflicting_policy(
                db=db,
                min_risk_score=target_min,
                max_risk_score=target_max,
                priority=target_priority,
                exclude_id=policy.id,
            )
            if conflict:
                raise DealFlowException(
                    f"An active approval policy '{conflict.name}' already covers the identical risk score range and priority",
                    status_code=400,
                )

        updated_policy = self.repository.update_policy(db, policy, updates)
        new_values = _policy_to_audit_dict(updated_policy)

        # Distinguish activation, deactivation, or general update
        if (
            updates.get("is_active") is True
            and old_values.get("is_active") is False
        ):
            action = "ACTIVATE"
            reason = f"Activated approval policy '{updated_policy.name}'"
        elif (
            updates.get("is_active") is False
            and old_values.get("is_active") is True
        ):
            action = "DEACTIVATE"
            reason = f"Deactivated approval policy '{updated_policy.name}'"
        else:
            action = "UPDATE"
            reason = f"Updated approval policy '{updated_policy.name}' configuration"

        audit_service.log_event(
            db=db,
            entity_type="APPROVAL_POLICY",
            entity_id=updated_policy.id,
            action=action,
            user_id=current_user.id if current_user else None,
            old_values=old_values,
            new_values=new_values,
            reason=reason,
        )

        db.commit()
        db.refresh(updated_policy)
        return updated_policy

    def deactivate_policy(
        self,
        db: Session,
        policy_id: uuid.UUID,
        current_user: Optional[User] = None,
    ) -> ApprovalPolicy:
        """
        Logically deactivate an approval policy following the DELETE contract.
        """
        policy = self.get_policy(db, policy_id)
        if not policy.is_active:
            return policy

        old_values = _policy_to_audit_dict(policy)
        updated_policy = self.repository.deactivate_policy(db, policy)
        new_values = _policy_to_audit_dict(updated_policy)

        audit_service.log_event(
            db=db,
            entity_type="APPROVAL_POLICY",
            entity_id=updated_policy.id,
            action="DEACTIVATE",
            user_id=current_user.id if current_user else None,
            old_values=old_values,
            new_values=new_values,
            reason=f"Deactivated approval policy '{updated_policy.name}' via delete endpoint",
        )

        db.commit()
        db.refresh(updated_policy)
        return updated_policy


approval_policy_service = ApprovalPolicyService()

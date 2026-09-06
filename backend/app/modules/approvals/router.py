"""Approval Policies endpoints router."""

from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.user import User
from app.modules.approvals.schemas import (

    ApprovalDecisionRequest,
    ApprovalInstanceResponse,
    ApprovalPolicyCreateRequest,
    ApprovalPolicyResponse,
    ApprovalPolicyUpdateRequest,
    ApprovalStepResponse,
    PendingApprovalStepResponse,
)
from app.modules.approvals.service import approval_policy_service


policy_router = APIRouter(prefix="/approval-policies", tags=["approval-policies"])


@policy_router.get(
    "",
    response_model=List[ApprovalPolicyResponse],
    status_code=status.HTTP_200_OK,
    summary="List Approval Policies",
)
def list_approval_policies(
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(
        require_roles(
            [
                UserRole.ADMIN,
                UserRole.SALES_MANAGER,
                UserRole.SALES_REP,
                UserRole.FINANCE_OPERATIONS,
            ]
        )
    ),
    db: Session = Depends(get_db),
) -> List[ApprovalPolicyResponse]:
    """List configurable approval policies with optional active status filter."""
    policies = approval_policy_service.list_policies(
        db=db, is_active=is_active, skip=skip, limit=limit
    )
    return [ApprovalPolicyResponse.model_validate(p) for p in policies]


@policy_router.post(
    "",
    response_model=ApprovalPolicyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Approval Policy",
)
def create_approval_policy(
    request: ApprovalPolicyCreateRequest,
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.SALES_MANAGER])
    ),
    db: Session = Depends(get_db),
) -> ApprovalPolicyResponse:
    """Create a new configurable approval policy. Admin and Sales Manager operation."""
    policy = approval_policy_service.create_policy(
        db=db, request=request, current_user=current_user
    )
    return ApprovalPolicyResponse.model_validate(policy)


@policy_router.get(
    "/{id}",
    response_model=ApprovalPolicyResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Approval Policy Details",
)
def get_approval_policy(
    id: uuid.UUID,
    current_user: User = Depends(
        require_roles(
            [
                UserRole.ADMIN,
                UserRole.SALES_MANAGER,
                UserRole.SALES_REP,
                UserRole.FINANCE_OPERATIONS,
            ]
        )
    ),
    db: Session = Depends(get_db),
) -> ApprovalPolicyResponse:
    """Return approval policy details by UUID."""
    policy = approval_policy_service.get_policy(db=db, policy_id=id)
    return ApprovalPolicyResponse.model_validate(policy)


@policy_router.patch(
    "/{id}",
    response_model=ApprovalPolicyResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Approval Policy",
)
def update_approval_policy(
    id: uuid.UUID,
    request: ApprovalPolicyUpdateRequest,
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.SALES_MANAGER])
    ),
    db: Session = Depends(get_db),
) -> ApprovalPolicyResponse:
    """Update approval policy configuration. Admin and Sales Manager operation."""
    policy = approval_policy_service.update_policy(
        db=db, policy_id=id, request=request, current_user=current_user
    )
    return ApprovalPolicyResponse.model_validate(policy)


@policy_router.delete(
    "/{id}",
    response_model=ApprovalPolicyResponse,
    status_code=status.HTTP_200_OK,
    summary="Deactivate Approval Policy",
)
def delete_approval_policy(
    id: uuid.UUID,
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.SALES_MANAGER])
    ),
    db: Session = Depends(get_db),
) -> ApprovalPolicyResponse:
    """Deactivate an approval policy following logical-deactivation convention. Admin and Sales Manager operation."""
    policy = approval_policy_service.deactivate_policy(
        db=db, policy_id=id, current_user=current_user
    )
    return ApprovalPolicyResponse.model_validate(policy)


# Central router for approvals module
execution_router = APIRouter(prefix="/approvals", tags=["Approvals"])


def _to_instance_response(inst) -> ApprovalInstanceResponse:
    """Map ApprovalInstance model to response schema."""
    from app.modules.approvals.schemas import ApprovalStepResponse

    steps_resp = [
        ApprovalStepResponse(
            id=s.id,
            approval_instance_id=s.approval_instance_id,
            step_order=s.step_order,
            approver_role=(
                s.approver_role.value
                if hasattr(s.approver_role, "value")
                else str(s.approver_role)
            ),
            approver_user_id=s.approver_user_id,
            status=(
                s.status.value
                if hasattr(s.status, "value")
                else str(s.status)
            ),
            decision_reason=s.decision_reason,
            decided_at=s.decided_at,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in (inst.steps or [])
    ]
    q = inst.quotation
    return ApprovalInstanceResponse(
        id=inst.id,
        quotation_id=inst.quotation_id,
        quotation_number=q.quotation_number if q else None,
        customer_name=q.customer.name if q and q.customer else None,
        risk_score=inst.risk_score,
        status=(
            inst.status.value
            if hasattr(inst.status, "value")
            else str(inst.status)
        ),
        started_at=inst.started_at,
        completed_at=inst.completed_at,
        created_at=inst.created_at,
        updated_at=inst.updated_at,
        steps=steps_resp,
    )


@execution_router.get(
    "",
    response_model=List[ApprovalInstanceResponse],
    status_code=status.HTTP_200_OK,
    summary="List Approval Workflows",
)
def list_approvals(
    status: Optional[str] = None,
    quotation_id: Optional[uuid.UUID] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(
        require_roles(
            [
                UserRole.ADMIN,
                UserRole.SALES_MANAGER,
                UserRole.FINANCE_OPERATIONS,
                UserRole.SALES_REP,
            ]
        )
    ),
    db: Session = Depends(get_db),
) -> List[ApprovalInstanceResponse]:
    """List approval workflows visible to authorized roles."""
    from app.modules.approvals.service import approval_execution_service

    instances = approval_execution_service.list_instances(
        db=db,
        status=status,
        quotation_id=quotation_id,
        skip=skip,
        limit=limit,
    )
    return [_to_instance_response(inst) for inst in instances]


@execution_router.get(
    "/pending",
    response_model=List[PendingApprovalStepResponse],
    status_code=status.HTTP_200_OK,
    summary="List Pending Approval Work Relevant to Current User",
)
def list_pending_approvals(
    current_user: User = Depends(
        require_roles(
            [
                UserRole.ADMIN,
                UserRole.SALES_MANAGER,
                UserRole.FINANCE_OPERATIONS,
            ]
        )
    ),
    db: Session = Depends(get_db),
) -> List[PendingApprovalStepResponse]:
    """Return pending approval steps the current user is authorized to act on."""
    from app.modules.approvals.service import approval_execution_service

    return approval_execution_service.get_pending_approvals(
        db=db, current_user=current_user
    )


@execution_router.get(
    "/{id}",
    response_model=ApprovalInstanceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Approval Instance Details",
)
def get_approval(
    id: uuid.UUID,
    current_user: User = Depends(
        require_roles(
            [
                UserRole.ADMIN,
                UserRole.SALES_MANAGER,
                UserRole.FINANCE_OPERATIONS,
                UserRole.SALES_REP,
            ]
        )
    ),
    db: Session = Depends(get_db),
) -> ApprovalInstanceResponse:
    """Return approval instance with its sequential reviewer steps."""
    from app.modules.approvals.service import approval_execution_service

    instance = approval_execution_service.get_instance(db=db, instance_id=id)
    return _to_instance_response(instance)


@execution_router.post(
    "/{id}/approve",
    response_model=ApprovalInstanceResponse,
    status_code=status.HTTP_200_OK,
    summary="Approve Current Approval Step",
)
def approve_step(
    id: uuid.UUID,
    request: Optional[ApprovalDecisionRequest] = None,
    current_user: User = Depends(
        require_roles(
            [
                UserRole.ADMIN,
                UserRole.SALES_MANAGER,
                UserRole.FINANCE_OPERATIONS,
            ]
        )
    ),
    db: Session = Depends(get_db),
) -> ApprovalInstanceResponse:
    """Approve the current approval step in sequence."""
    from app.modules.approvals.service import approval_execution_service

    decision_req = request or ApprovalDecisionRequest()
    instance = approval_execution_service.approve_step(
        db=db,
        instance_id=id,
        current_user=current_user,
        request=decision_req,
    )
    return _to_instance_response(instance)


@execution_router.post(
    "/{id}/reject",
    response_model=ApprovalInstanceResponse,
    status_code=status.HTTP_200_OK,
    summary="Reject Approval Workflow",
)
def reject_step(
    id: uuid.UUID,
    request: Optional[ApprovalDecisionRequest] = None,
    current_user: User = Depends(
        require_roles(
            [
                UserRole.ADMIN,
                UserRole.SALES_MANAGER,
                UserRole.FINANCE_OPERATIONS,
            ]
        )
    ),
    db: Session = Depends(get_db),
) -> ApprovalInstanceResponse:
    """Reject the current approval step/workflow."""
    from app.modules.approvals.service import approval_execution_service

    decision_req = request or ApprovalDecisionRequest()
    instance = approval_execution_service.reject_step(
        db=db,
        instance_id=id,
        current_user=current_user,
        request=decision_req,
    )
    return _to_instance_response(instance)


@execution_router.post(
    "/{id}/return-for-revision",
    response_model=ApprovalInstanceResponse,
    status_code=status.HTTP_200_OK,
    summary="Return Quotation for Revision",
)
def return_for_revision(
    id: uuid.UUID,
    request: Optional[ApprovalDecisionRequest] = None,
    current_user: User = Depends(
        require_roles(
            [
                UserRole.ADMIN,
                UserRole.SALES_MANAGER,
                UserRole.FINANCE_OPERATIONS,
            ]
        )
    ),
    db: Session = Depends(get_db),
) -> ApprovalInstanceResponse:
    """Return quotation and approval workflow for revision."""
    from app.modules.approvals.service import approval_execution_service

    decision_req = request or ApprovalDecisionRequest()
    instance = approval_execution_service.return_step_for_revision(
        db=db,
        instance_id=id,
        current_user=current_user,
        request=decision_req,
    )
    return _to_instance_response(instance)


@execution_router.get(
    "/{id}/audit-log",
    response_model=List[dict],
    status_code=status.HTTP_200_OK,
    summary="Get Approval Workflow Audit Log",
)
def get_approval_audit_log(
    id: uuid.UUID,
    current_user: User = Depends(
        require_roles(
            [
                UserRole.ADMIN,
                UserRole.SALES_MANAGER,
                UserRole.FINANCE_OPERATIONS,
                UserRole.SALES_REP,
            ]
        )
    ),
    db: Session = Depends(get_db),
) -> List[dict]:
    """Return audit history related to approval workflow."""
    from app.models.audit_log import AuditLog
    from app.modules.approvals.service import approval_execution_service

    instance = approval_execution_service.get_instance(db=db, instance_id=id)
    step_ids = [s.id for s in instance.steps]
    from sqlalchemy import or_

    logs = (
        db.query(AuditLog)
        .filter(
            or_(
                (AuditLog.entity_type == "APPROVAL_INSTANCE") & (AuditLog.entity_id == id),
                (AuditLog.entity_type == "APPROVAL_STEP") & (AuditLog.entity_id.in_(step_ids)),
            )
        )
        .order_by(AuditLog.created_at.desc())
        .all()
    )
    return [
        {
            "id": log.id,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "action": log.action,
            "user_id": log.user_id,
            "old_values": log.old_values,
            "new_values": log.new_values,
            "reason": log.reason,
            "created_at": log.created_at,
        }
        for log in logs
    ]


# Central router for approvals module
router = APIRouter()
router.include_router(policy_router)
router.include_router(execution_router)


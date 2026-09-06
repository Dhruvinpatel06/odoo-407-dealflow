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
    ApprovalPolicyCreateRequest,
    ApprovalPolicyResponse,
    ApprovalPolicyUpdateRequest,
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
router = APIRouter()
router.include_router(policy_router)

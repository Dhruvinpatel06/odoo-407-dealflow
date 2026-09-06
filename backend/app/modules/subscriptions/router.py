"""Subscription Plans and Subscriptions API routers."""

from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.common.enums import SubscriptionStatus, UserRole
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.user import User
from app.modules.subscriptions.schemas import (
    ProrationApplyRequest,
    ProrationPreviewRequest,
    ProrationPreviewResponse,
    SubscriptionCancelRequest,
    SubscriptionModifyRequest,
    SubscriptionPlanCreateRequest,
    SubscriptionPlanResponse,
    SubscriptionPlanUpdateRequest,
    SubscriptionResponse,
)
from app.modules.subscriptions.service import subscriptions_service

INTERNAL_ROLES = [
    UserRole.ADMIN,
    UserRole.FINANCE_OPERATIONS,
    UserRole.SALES_MANAGER,
    UserRole.SALES_REP,
]

FINANCE_ADMIN_ROLES = [
    UserRole.ADMIN,
    UserRole.FINANCE_OPERATIONS,
]

subscription_plan_router = APIRouter(
    prefix="/subscription-plans", tags=["Subscription Plans"]
)
subscription_router = APIRouter(
    prefix="/subscriptions", tags=["Subscriptions"]
)


# =====================================================================
# Subscription Plans Endpoints
# =====================================================================


@subscription_plan_router.get("", response_model=List[SubscriptionPlanResponse])
def list_subscription_plans(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(INTERNAL_ROLES)),
) -> List[SubscriptionPlanResponse]:
    """List recurring subscription plans."""
    return subscriptions_service.list_plans(
        db, is_active=is_active, skip=skip, limit=limit
    )


@subscription_plan_router.post(
    "", response_model=SubscriptionPlanResponse, status_code=status.HTTP_201_CREATED
)
def create_subscription_plan(
    request: SubscriptionPlanCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(FINANCE_ADMIN_ROLES)),
) -> SubscriptionPlanResponse:
    """Create a recurring subscription plan."""
    return subscriptions_service.create_plan(
        db, request, current_user=current_user
    )


@subscription_plan_router.get("/{id}", response_model=SubscriptionPlanResponse)
def get_subscription_plan(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(INTERNAL_ROLES)),
) -> SubscriptionPlanResponse:
    """Get subscription plan details by UUID."""
    return subscriptions_service.get_plan(db, plan_id=id)


@subscription_plan_router.patch("/{id}", response_model=SubscriptionPlanResponse)
def update_subscription_plan(
    id: uuid.UUID,
    request: SubscriptionPlanUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(FINANCE_ADMIN_ROLES)),
) -> SubscriptionPlanResponse:
    """Update subscription plan configuration."""
    return subscriptions_service.update_plan(
        db, plan_id=id, request=request, current_user=current_user
    )


@subscription_plan_router.delete("/{id}", response_model=SubscriptionPlanResponse)
def deactivate_subscription_plan(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(FINANCE_ADMIN_ROLES)),
) -> SubscriptionPlanResponse:
    """Deactivate subscription plan."""
    return subscriptions_service.deactivate_plan(
        db, plan_id=id, current_user=current_user
    )


# =====================================================================
# Subscriptions Endpoints
# =====================================================================


@subscription_router.get("", response_model=List[SubscriptionResponse])
def list_subscriptions(
    customer_id: Optional[uuid.UUID] = Query(None, description="Filter by customer"),
    status: Optional[SubscriptionStatus] = Query(None, description="Filter by status"),
    order_id: Optional[uuid.UUID] = Query(None, description="Filter by order"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(INTERNAL_ROLES)),
) -> List[SubscriptionResponse]:
    """List customer subscriptions."""
    return subscriptions_service.list_subscriptions(
        db, customer_id=customer_id, status=status, order_id=order_id, skip=skip, limit=limit
    )


@subscription_router.get("/{id}", response_model=SubscriptionResponse)
def get_subscription(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(INTERNAL_ROLES)),
) -> SubscriptionResponse:
    """Get subscription details by UUID."""
    return subscriptions_service.get_subscription(db, subscription_id=id)


@subscription_router.post("/{id}/modify", response_model=SubscriptionResponse)
def modify_subscription(
    id: uuid.UUID,
    request: SubscriptionModifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(FINANCE_ADMIN_ROLES)),
) -> SubscriptionResponse:
    """Modify subscription quantity, plan, or price."""
    return subscriptions_service.modify_subscription(
        db, subscription_id=id, request=request, current_user=current_user
    )


@subscription_router.post("/{id}/cancel", response_model=SubscriptionResponse)
def cancel_subscription(
    id: uuid.UUID,
    request: SubscriptionCancelRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(FINANCE_ADMIN_ROLES)),
) -> SubscriptionResponse:
    """Cancel subscription with optional credit-note generation."""
    return subscriptions_service.cancel_subscription(
        db, subscription_id=id, request=request, current_user=current_user
    )


@subscription_router.post("/{id}/pause", response_model=SubscriptionResponse)
def pause_subscription(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(FINANCE_ADMIN_ROLES)),
) -> SubscriptionResponse:
    """Pause an active subscription."""
    return subscriptions_service.pause_subscription(
        db, subscription_id=id, current_user=current_user
    )


@subscription_router.post(
    "/{id}/proration/preview", response_model=ProrationPreviewResponse
)
def preview_subscription_proration(
    id: uuid.UUID,
    request: ProrationPreviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(INTERNAL_ROLES)),
) -> ProrationPreviewResponse:
    """Calculate non-mutating preview of mid-cycle proration adjustment."""
    return subscriptions_service.preview_proration(
        db, subscription_id=id, request=request
    )


@subscription_router.post(
    "/{id}/proration/apply", response_model=SubscriptionResponse
)
def apply_subscription_proration(
    id: uuid.UUID,
    request: ProrationApplyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(FINANCE_ADMIN_ROLES)),
) -> SubscriptionResponse:
    """Apply evaluated proration adjustment to subscription."""
    return subscriptions_service.apply_proration(
        db, subscription_id=id, request=request, current_user=current_user
    )


@subscription_router.post("/{id}/credit-note", response_model=dict)
def generate_subscription_credit_note(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(FINANCE_ADMIN_ROLES)),
) -> dict:
    """Generate a credit note for subscription balance adjustment."""
    credit_inv = subscriptions_service.create_credit_note_for_subscription(
        db, subscription_id=id, current_user=current_user
    )
    return {
        "invoice_id": credit_inv.id,
        "invoice_number": credit_inv.invoice_number,
        "amount": credit_inv.total_amount,
        "invoice_type": credit_inv.invoice_type.value,
        "status": credit_inv.status.value,
    }

"""Discount Rules endpoints router."""

from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.user import User
from app.modules.discounts.schemas import (
    DiscountRuleCreateRequest,
    DiscountRuleResponse,
    DiscountRuleUpdateRequest,
)
from app.modules.discounts.service import discount_service

router = APIRouter(prefix="/discount-rules", tags=["discount-rules"])


@router.get(
    "",
    response_model=List[DiscountRuleResponse],
    status_code=status.HTTP_200_OK,
    summary="List Discount Rules",
)
def list_discount_rules(
    customer_tier_id: Optional[uuid.UUID] = None,
    category_id: Optional[uuid.UUID] = None,
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
) -> List[DiscountRuleResponse]:
    """List configurable discount rules with optional customer tier, category, and active status filters."""
    rules = discount_service.list_discount_rules(
        db=db,
        customer_tier_id=customer_tier_id,
        category_id=category_id,
        is_active=is_active,
        skip=skip,
        limit=limit,
    )
    return [DiscountRuleResponse.model_validate(r) for r in rules]


@router.post(
    "",
    response_model=DiscountRuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Discount Rule",
)
def create_discount_rule(
    request: DiscountRuleCreateRequest,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db),
) -> DiscountRuleResponse:
    """Create a new configurable discount rule. Admin-only operation."""
    rule = discount_service.create_discount_rule(
        db=db, request=request, current_user=current_user
    )
    return DiscountRuleResponse.model_validate(rule)


@router.get(
    "/{id}",
    response_model=DiscountRuleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Discount Rule Details",
)
def get_discount_rule(
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
) -> DiscountRuleResponse:
    """Return discount rule details by UUID."""
    rule = discount_service.get_discount_rule(db=db, rule_id=id)
    return DiscountRuleResponse.model_validate(rule)


@router.patch(
    "/{id}",
    response_model=DiscountRuleResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Discount Rule",
)
def update_discount_rule(
    id: uuid.UUID,
    request: DiscountRuleUpdateRequest,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db),
) -> DiscountRuleResponse:
    """Update discount rule configuration. Admin-only operation."""
    rule = discount_service.update_discount_rule(
        db=db, rule_id=id, request=request, current_user=current_user
    )
    return DiscountRuleResponse.model_validate(rule)


@router.delete(
    "/{id}",
    response_model=DiscountRuleResponse,
    status_code=status.HTTP_200_OK,
    summary="Deactivate Discount Rule",
)
def delete_discount_rule(
    id: uuid.UUID,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: Session = Depends(get_db),
) -> DiscountRuleResponse:
    """Deactivate a discount rule following logical-deactivation convention. Admin-only operation."""
    rule = discount_service.deactivate_discount_rule(
        db=db, rule_id=id, current_user=current_user
    )
    return DiscountRuleResponse.model_validate(rule)

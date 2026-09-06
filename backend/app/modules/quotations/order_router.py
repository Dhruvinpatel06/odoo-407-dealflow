"""Orders endpoints router."""

from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.audit_log import AuditLog
from app.models.order import Order
from app.models.user import User
from app.modules.quotations.schemas import OrderResponse, OrderUpdateRequest
from app.modules.quotations.service import quotation_service

order_router = APIRouter(prefix="/orders", tags=["Orders"])

INTERNAL_ORDER_ROLES = [
    UserRole.SALES_REP,
    UserRole.SALES_MANAGER,
    UserRole.FINANCE_OPERATIONS,
    UserRole.ADMIN,
]


def _to_order_response(order: Order) -> OrderResponse:
    """Map Order SQLAlchemy model to response schema."""
    customer_name = order.customer.name if order.customer else None
    return OrderResponse(
        id=order.id,
        order_number=order.order_number,
        quotation_id=order.quotation_id,
        customer_id=order.customer_id,
        customer_name=customer_name,
        status=order.status.value if hasattr(order.status, "value") else str(order.status),
        total_amount=order.total_amount,
        confirmed_at=order.confirmed_at,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


@order_router.get("", response_model=List[OrderResponse])
def list_orders(
    customer_id: Optional[uuid.UUID] = Query(None, description="Filter by customer UUID"),
    status: Optional[str] = Query(None, description="Filter by order status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(INTERNAL_ORDER_ROLES)),
) -> List[OrderResponse]:
    """List confirmed sales orders with optional filters."""
    orders = quotation_service.list_orders(
        db=db,
        customer_id=customer_id,
        status=status,
        skip=skip,
        limit=limit,
    )
    return [_to_order_response(o) for o in orders]


@order_router.get("/{id}", response_model=OrderResponse)
def get_order(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(INTERNAL_ORDER_ROLES)),
) -> OrderResponse:
    """Return complete order details by UUID."""
    order = quotation_service.get_order_by_id(db=db, order_id=id)
    return _to_order_response(order)


@order_router.patch("/{id}", response_model=OrderResponse)
def update_order(
    id: uuid.UUID,
    request: OrderUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.FINANCE_OPERATIONS, UserRole.SALES_MANAGER])
    ),
) -> OrderResponse:
    """Update permitted order fields/state."""
    order = quotation_service.update_order(
        db=db,
        order_id=id,
        request=request,
        current_user=current_user,
    )
    return _to_order_response(order)


@order_router.get("/{id}/audit-log", response_model=List[dict])
def get_order_audit_log(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(INTERNAL_ORDER_ROLES)),
) -> List[dict]:
    """Return order audit history."""
    # Ensure order exists
    quotation_service.get_order_by_id(db=db, order_id=id)
    logs = (
        db.query(AuditLog)
        .filter(AuditLog.entity_type == "ORDER", AuditLog.entity_id == id)
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

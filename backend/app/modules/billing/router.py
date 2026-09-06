"""Billing, Billing Schedules, Invoices, and Payments API routers."""

from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.common.enums import (
    BillingScheduleStatus,
    InvoiceStatus,
    InvoiceType,
    PaymentStatus,
    UserRole,
)
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.user import User
from app.modules.billing.schemas import (
    BillingScheduleResponse,
    CreditNoteCreateRequest,
    InvoiceResponse,
    OrderBillingResponse,
    PaymentCreateRequest,
    PaymentResponse,
)
from app.modules.billing.service import billing_service

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

order_billing_router = APIRouter(prefix="/orders", tags=["Billing"])
billing_schedule_router = APIRouter(
    prefix="/billing-schedules", tags=["Billing Schedules"]
)
invoice_router = APIRouter(prefix="/invoices", tags=["Invoices"])
payment_router = APIRouter(prefix="/payments", tags=["Payments"])


# =====================================================================
# Order Billing Endpoints (/orders/{id}/billing*)
# =====================================================================


@order_billing_router.get("/{id}/billing", response_model=OrderBillingResponse)
def get_order_billing(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(INTERNAL_ROLES)),
) -> OrderBillingResponse:
    """Return complete billing state for an order (one-time + recurring)."""
    return billing_service.get_order_billing(db, order_id=id)


@order_billing_router.post(
    "/{id}/billing/generate", response_model=OrderBillingResponse
)
def generate_order_billing(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(FINANCE_ADMIN_ROLES)),
) -> OrderBillingResponse:
    """Generate one-time invoices and recurring subscriptions/schedules for an order."""
    return billing_service.generate_order_billing(
        db, order_id=id, current_user=current_user
    )


@order_billing_router.post(
    "/{id}/credit-notes",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_order_credit_note(
    id: uuid.UUID,
    request: CreditNoteCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(FINANCE_ADMIN_ROLES)),
) -> InvoiceResponse:
    """Issue a credit note against an order."""
    return billing_service.create_credit_note(
        db, order_id=id, request=request, current_user=current_user
    )


# =====================================================================
# Billing Schedules Endpoints (/billing-schedules/*)
# =====================================================================


@billing_schedule_router.get("", response_model=List[BillingScheduleResponse])
def list_billing_schedules(
    subscription_id: Optional[uuid.UUID] = Query(None, description="Filter by subscription"),
    status: Optional[BillingScheduleStatus] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(INTERNAL_ROLES)),
) -> List[BillingScheduleResponse]:
    """List recurring billing schedule entries."""
    return billing_service.list_schedules(
        db, subscription_id=subscription_id, status=status, skip=skip, limit=limit
    )


@billing_schedule_router.get("/{id}", response_model=BillingScheduleResponse)
def get_billing_schedule(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(INTERNAL_ROLES)),
) -> BillingScheduleResponse:
    """Get billing schedule entry by UUID."""
    return billing_service.get_schedule(db, schedule_id=id)


@billing_schedule_router.post(
    "/{id}/generate-invoice", response_model=InvoiceResponse
)
def generate_invoice_from_schedule(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(FINANCE_ADMIN_ROLES)),
) -> InvoiceResponse:
    """Generate recurring invoice from scheduled billing event."""
    return billing_service.generate_invoice_from_schedule(
        db, schedule_id=id, current_user=current_user
    )


@billing_schedule_router.post("/{id}/cancel", response_model=BillingScheduleResponse)
def cancel_billing_schedule(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(FINANCE_ADMIN_ROLES)),
) -> BillingScheduleResponse:
    """Cancel scheduled billing event."""
    return billing_service.cancel_schedule(
        db, schedule_id=id, current_user=current_user
    )


# =====================================================================
# Invoices Endpoints (/invoices/*)
# =====================================================================


@invoice_router.get("", response_model=List[InvoiceResponse])
def list_invoices(
    order_id: Optional[uuid.UUID] = Query(None, description="Filter by order"),
    status: Optional[InvoiceStatus] = Query(None, description="Filter by status"),
    invoice_type: Optional[InvoiceType] = Query(None, description="Filter by type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(INTERNAL_ROLES)),
) -> List[InvoiceResponse]:
    """List invoices."""
    return billing_service.list_invoices(
        db, order_id=order_id, status=status, invoice_type=invoice_type, skip=skip, limit=limit
    )


@invoice_router.get("/{id}", response_model=InvoiceResponse)
def get_invoice(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(INTERNAL_ROLES)),
) -> InvoiceResponse:
    """Get invoice details by UUID."""
    return billing_service.get_invoice(db, invoice_id=id)


@invoice_router.post("/{id}/issue", response_model=InvoiceResponse)
def issue_invoice(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(FINANCE_ADMIN_ROLES)),
) -> InvoiceResponse:
    """Issue draft invoice."""
    return billing_service.issue_invoice(
        db, invoice_id=id, current_user=current_user
    )


@invoice_router.post("/{id}/cancel", response_model=InvoiceResponse)
def cancel_invoice(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(FINANCE_ADMIN_ROLES)),
) -> InvoiceResponse:
    """Cancel invoice."""
    return billing_service.cancel_invoice(
        db, invoice_id=id, current_user=current_user
    )


@invoice_router.get("/{id}/payments", response_model=List[PaymentResponse])
def get_invoice_payments(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(INTERNAL_ROLES)),
) -> List[PaymentResponse]:
    """Return all payments recorded against an invoice."""
    return billing_service.list_payments(db, invoice_id=id)


@invoice_router.get("/{id}/credit-notes", response_model=List[InvoiceResponse])
def get_invoice_credit_notes(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(INTERNAL_ROLES)),
) -> List[InvoiceResponse]:
    """Return credit notes for an invoice/order."""
    inv = billing_service.get_invoice(db, invoice_id=id)
    return billing_service.list_invoices(
        db, order_id=inv.order_id, invoice_type=InvoiceType.CREDIT_NOTE
    )


@invoice_router.post(
    "/{id}/payments",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
def record_invoice_payment(
    id: uuid.UUID,
    request: PaymentCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(FINANCE_ADMIN_ROLES)),
) -> PaymentResponse:
    """Record payment against invoice with overpayment protection."""
    return billing_service.record_payment(
        db, invoice_id=id, request=request, current_user=current_user
    )


# =====================================================================
# Payments Endpoints (/payments/*)
# =====================================================================


@payment_router.get("", response_model=List[PaymentResponse])
def list_payments(
    invoice_id: Optional[uuid.UUID] = Query(None, description="Filter by invoice"),
    status: Optional[PaymentStatus] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(INTERNAL_ROLES)),
) -> List[PaymentResponse]:
    """List recorded payments."""
    return billing_service.list_payments(
        db, invoice_id=invoice_id, status=status, skip=skip, limit=limit
    )


@payment_router.get("/{id}", response_model=PaymentResponse)
def get_payment(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(INTERNAL_ROLES)),
) -> PaymentResponse:
    """Get payment details by UUID."""
    return billing_service.get_payment(db, payment_id=id)


@payment_router.post("/{id}/refund", response_model=PaymentResponse)
def refund_payment(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(FINANCE_ADMIN_ROLES)),
) -> PaymentResponse:
    """Refund a recorded payment and adjust invoice balance and status."""
    return billing_service.refund_payment(
        db, payment_id=id, current_user=current_user
    )

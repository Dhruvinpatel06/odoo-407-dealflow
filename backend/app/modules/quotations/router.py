"""Quotations endpoints router."""

from __future__ import annotations

import datetime
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.common.enums import QuotationStatus, UserRole
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.modules.quotations.schemas import (
    QuotationCreateRequest,
    QuotationDetailResponse,
    QuotationLineCreateRequest,
    QuotationLineResponse,
    QuotationLineUpdateRequest,
    QuotationRecalculateResponse,
    QuotationResponse,
    QuotationRiskResponse,
    QuotationUpdateRequest,
)
from app.modules.quotations.service import quotation_service

router = APIRouter(prefix="/quotations", tags=["Quotations"])

INTERNAL_SALES_ROLES = [
    UserRole.SALES_REP,
    UserRole.SALES_MANAGER,
    UserRole.FINANCE_OPERATIONS,
    UserRole.ADMIN,
]


@router.get("", response_model=List[QuotationResponse])
def list_quotations(
    status: Optional[QuotationStatus] = Query(None, description="Filter by quotation status"),
    customer_id: Optional[uuid.UUID] = Query(None, description="Filter by customer UUID"),
    sales_rep_id: Optional[uuid.UUID] = Query(None, description="Filter by sales rep UUID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(INTERNAL_SALES_ROLES)),
) -> List[QuotationResponse]:
    """List quotations with optional filtering."""
    return quotation_service.list_quotations(
        db=db,
        status=status,
        customer_id=customer_id,
        sales_rep_id=sales_rep_id,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=QuotationDetailResponse, status_code=status.HTTP_201_CREATED)
def create_quotation(
    request: QuotationCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(INTERNAL_SALES_ROLES)),
) -> QuotationDetailResponse:
    """Create a new draft quotation for a customer."""
    quote = quotation_service.create_quotation(
        db=db,
        request=request,
        current_user=current_user,
    )
    return _to_detail_response(quote)


@router.get("/{id}", response_model=QuotationDetailResponse)
def get_quotation(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(INTERNAL_SALES_ROLES)),
) -> QuotationDetailResponse:
    """Retrieve full quotation details including lines and latest calculated financial state."""
    quote = quotation_service.get_quotation_by_id(db=db, quotation_id=id)
    return _to_detail_response(quote)


@router.patch("/{id}", response_model=QuotationDetailResponse)
def update_quotation(
    id: uuid.UUID,
    request: QuotationUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(INTERNAL_SALES_ROLES)),
) -> QuotationDetailResponse:
    """Update allowed quotation metadata."""
    quote = quotation_service.update_quotation(
        db=db, quotation_id=id, request=request
    )
    return _to_detail_response(quote)


# --- Quotation Lines ---


@router.post("/{id}/lines", response_model=QuotationDetailResponse, status_code=status.HTTP_201_CREATED)
def add_quotation_line(
    id: uuid.UUID,
    request: QuotationLineCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(INTERNAL_SALES_ROLES)),
) -> QuotationDetailResponse:
    """Add a product/variant line to a quotation and trigger complete server recalculation."""
    quote = quotation_service.add_line(
        db=db,
        quotation_id=id,
        request=request,
        current_user=current_user,
    )
    return _to_detail_response(quote)


@router.patch("/{id}/lines/{line_id}", response_model=QuotationDetailResponse)
def update_quotation_line(
    id: uuid.UUID,
    line_id: uuid.UUID,
    request: QuotationLineUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(INTERNAL_SALES_ROLES)),
) -> QuotationDetailResponse:
    """Update line-level values (quantity, discount, etc.) and recalculate dependent quotation state."""
    quote = quotation_service.update_line(
        db=db,
        quotation_id=id,
        line_id=line_id,
        request=request,
        current_user=current_user,
    )
    return _to_detail_response(quote)


@router.delete("/{id}/lines/{line_id}", response_model=QuotationDetailResponse)
def delete_quotation_line(
    id: uuid.UUID,
    line_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(INTERNAL_SALES_ROLES)),
) -> QuotationDetailResponse:
    """Remove a quotation line and trigger complete quotation recalculation."""
    quote = quotation_service.delete_line(
        db=db,
        quotation_id=id,
        line_id=line_id,
        current_user=current_user,
    )
    return _to_detail_response(quote)


# --- Recalculation & Risk Endpoints ---


@router.post("/{id}/recalculate", response_model=QuotationRecalculateResponse)
def recalculate_quotation(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(INTERNAL_SALES_ROLES)),
) -> QuotationRecalculateResponse:
    """
    Trigger full authoritative quotation recalculation across line pricing, discount governance,
    totals, margin, blended risk score, and approval requirement.
    """
    quote, risk_resp = quotation_service.recalculate(db=db, quotation_id=id)
    return QuotationRecalculateResponse(
        quotation=_to_detail_response(quote),
        risk=risk_resp,
        recalculated_at=datetime.datetime.now(datetime.timezone.utc),
    )


@router.get("/{id}/risk", response_model=QuotationRiskResponse)
def get_quotation_risk(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(INTERNAL_SALES_ROLES)),
) -> QuotationRiskResponse:
    """
    Return authoritative quotation discount-risk state, blended risk score,
    approval requirement, and line-level discount limits/excess for UI explanation.
    """
    return quotation_service.get_risk(db=db, quotation_id=id)


@router.post("/{id}/submit", response_model=QuotationDetailResponse)
def submit_quotation(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(INTERNAL_SALES_ROLES)),
) -> QuotationDetailResponse:
    """
    Submit quotation into the next workflow state.
    Recalculates server-side first, then automatically determines approval requirement.
    """
    quote = quotation_service.submit(
        db=db, quotation_id=id, current_user=current_user
    )
    return _to_detail_response(quote)


def _to_detail_response(quote) -> QuotationDetailResponse:
    """Helper to map a quotation SQLAlchemy model to QuotationDetailResponse schema."""
    lines_resp = [
        QuotationLineResponse.model_validate(line) for line in (quote.lines or [])
    ]
    customer_name = quote.customer.name if quote.customer else None
    return QuotationDetailResponse(
        id=quote.id,
        quotation_number=quote.quotation_number,
        customer_id=quote.customer_id,
        sales_rep_id=quote.sales_rep_id,
        status=quote.status,
        subtotal=quote.subtotal,
        discount_amount=quote.discount_amount,
        order_discount_percent=quote.order_discount_percent,
        tax_amount=quote.tax_amount,
        total_amount=quote.total_amount,
        total_cost=quote.total_cost,
        margin_amount=quote.margin_amount,
        margin_percent=quote.margin_percent,
        risk_score=quote.risk_score,
        approval_required=quote.approval_required,
        current_approval_level=quote.current_approval_level,
        sent_at=quote.sent_at,
        last_activity_at=quote.last_activity_at,
        valid_until=quote.valid_until,
        created_at=quote.created_at,
        updated_at=quote.updated_at,
        lines=lines_resp,
        customer_name=customer_name,
    )

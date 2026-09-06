"""Quotations service layer."""

from __future__ import annotations

import datetime
import uuid
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.common.enums import ApprovalStatus, ApproverRole, QuotationStatus
from app.core.exceptions import DealFlowException, ResourceNotFoundError
from app.models.approval_instance import ApprovalInstance
from app.models.approval_step import ApprovalStep
from app.models.customer import Customer
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.quotation import Quotation
from app.models.quotation_line import QuotationLine
from app.models.user import User
from app.modules.discounts.engine import discount_engine
from app.modules.pricing.engine import pricing_engine
from app.modules.pricing.repository import pricing_repository
from app.modules.quotations.engine import quotation_engine
from app.modules.quotations.repository import quotation_repository
from app.modules.quotations.schemas import (
    LineRiskDetail,
    QuotationCreateRequest,
    QuotationLineCreateRequest,
    QuotationLineUpdateRequest,
    QuotationRiskResponse,
    QuotationUpdateRequest,
)


class QuotationService:
    """Orchestrates quotation workflows, mutations, recalculation, and governance."""

    def get_quotation_by_id(
        self, db: Session, quotation_id: uuid.UUID
    ) -> Quotation:
        """Retrieve quotation with relationships eagerly loaded, or raise 404."""
        quote = quotation_repository.get_quotation_by_id(db, quotation_id)
        if not quote:
            raise ResourceNotFoundError("Quotation not found")
        return quote

    def list_quotations(
        self,
        db: Session,
        status: Optional[QuotationStatus] = None,
        customer_id: Optional[uuid.UUID] = None,
        sales_rep_id: Optional[uuid.UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Quotation]:
        """List quotations with optional filters."""
        return quotation_repository.list_quotations(
            db=db,
            status=status,
            customer_id=customer_id,
            sales_rep_id=sales_rep_id,
            skip=skip,
            limit=limit,
        )

    def create_quotation(
        self, db: Session, request: QuotationCreateRequest, current_user: User
    ) -> Quotation:
        """Create a new draft quotation for a customer."""
        customer = db.get(Customer, request.customer_id)
        if not customer:
            raise ResourceNotFoundError("Customer not found")
        if not customer.is_active:
            raise DealFlowException("Customer is inactive", status_code=400)

        now = datetime.datetime.now(datetime.timezone.utc)
        unique_suffix = uuid.uuid4().hex[:6].upper()
        quote_number = f"QT-{now.strftime('%Y%m%d')}-{unique_suffix}"

        quotation = Quotation(
            quotation_number=quote_number,
            customer_id=customer.id,
            sales_rep_id=current_user.id,
            status=QuotationStatus.DRAFT,
            valid_until=request.valid_until,
            subtotal=Decimal("0.00"),
            discount_amount=Decimal("0.00"),
            order_discount_percent=Decimal("0.00"),
            tax_amount=Decimal("0.00"),
            total_amount=Decimal("0.00"),
            total_cost=Decimal("0.00"),
            margin_amount=Decimal("0.00"),
            margin_percent=Decimal("0.00"),
            risk_score=Decimal("0.00"),
            approval_required=False,
            current_approval_level=None,
        )

        return quotation_repository.create_quotation(db, quotation)

    def update_quotation(
        self, db: Session, quotation_id: uuid.UUID, request: QuotationUpdateRequest
    ) -> Quotation:
        """Update quotation metadata."""
        quote = self.get_quotation_by_id(db, quotation_id)
        if quote.status not in (
            QuotationStatus.DRAFT,
            QuotationStatus.REVISION_REQUIRED,
        ):
            raise DealFlowException(
                f"Quotation cannot be edited in state {quote.status.value}",
                status_code=400,
            )

        if request.valid_until is not None:
            quote.valid_until = request.valid_until

        db.add(quote)
        db.commit()
        db.refresh(quote)
        return quote

    # --- Line Mutations ---

    def add_line(
        self,
        db: Session,
        quotation_id: uuid.UUID,
        request: QuotationLineCreateRequest,
        current_user: User,
    ) -> Quotation:
        """Add a product line to the quotation and recalculate all dependent state."""
        quote = self.get_quotation_by_id(db, quotation_id)
        if quote.status not in (
            QuotationStatus.DRAFT,
            QuotationStatus.REVISION_REQUIRED,
        ):
            raise DealFlowException(
                f"Cannot add lines to quotation in state {quote.status.value}",
                status_code=400,
            )

        product = db.get(Product, request.product_id)
        if not product:
            raise ResourceNotFoundError("Product not found")
        if not product.is_active:
            raise DealFlowException("Product is inactive", status_code=400)

        variant = None
        variant_extra = Decimal("0.00")
        if request.variant_id is not None:
            variant = db.get(ProductVariant, request.variant_id)
            if not variant:
                raise ResourceNotFoundError("Product variant not found")
            if variant.product_id != product.id:
                raise DealFlowException(
                    "Product variant does not belong to specified product",
                    status_code=400,
                )
            if not variant.is_active:
                raise DealFlowException("Product variant is inactive", status_code=400)
            variant_extra = variant.extra_price or Decimal("0.00")

        # Resolve authoritative selling price if not explicitly given
        if request.unit_price is not None:
            unit_price = Decimal(str(request.unit_price))
        else:
            # Check price list for customer tier
            effective_tier_id = (
                quote.customer.customer_tier_id if quote.customer else None
            )
            price_list = pricing_repository.find_applicable_price_list(
                db=db,
                currency="USD",
                customer_tier_id=effective_tier_id,
            )
            if price_list:
                item = pricing_repository.find_price_list_item(
                    db=db,
                    price_list_id=price_list.id,
                    product_id=product.id,
                    variant_id=request.variant_id,
                )
                if item:
                    is_var_override = item.variant_id is not None
                    unit_price, _ = pricing_engine.calculate_resolved_price(
                        base_unit_price=item.price,
                        variant_extra_price=variant_extra,
                        is_variant_specific_override=is_var_override,
                    )
                else:
                    unit_price, _ = pricing_engine.calculate_resolved_price(
                        base_unit_price=product.base_price,
                        variant_extra_price=variant_extra,
                    )
            else:
                unit_price, _ = pricing_engine.calculate_resolved_price(
                    base_unit_price=product.base_price,
                    variant_extra_price=variant_extra,
                )

        unit_cost = product.cost_price or Decimal("0.00")
        desc = request.description or product.name

        line = QuotationLine(
            quotation=quote,
            product=product,
            quotation_id=quote.id,
            product_id=product.id,
            variant_id=request.variant_id,
            description=desc,
            quantity=Decimal(str(request.quantity)),
            unit_price=unit_price,
            discount_percent=Decimal(str(request.discount_percent)),
            tax_rate=Decimal(str(request.tax_rate)),
            unit_cost=unit_cost,
            discount_amount=Decimal("0.00"),
            line_total=Decimal("0.00"),
            margin_amount=Decimal("0.00"),
            margin_percent=Decimal("0.00"),
            allowed_discount_percent=Decimal("0.00"),
            discount_excess_percent=Decimal("0.00"),
        )
        quotation_repository.add_line(db, line)

        # Recalculate quotation with newly added line
        self._recalculate_quotation_internal(db, quote)
        return quote

    def update_line(
        self,
        db: Session,
        quotation_id: uuid.UUID,
        line_id: uuid.UUID,
        request: QuotationLineUpdateRequest,
        current_user: User,
    ) -> Quotation:
        """Update line values (quantity, discount, etc.) and recalculate dependent state."""
        quote = self.get_quotation_by_id(db, quotation_id)
        if quote.status not in (
            QuotationStatus.DRAFT,
            QuotationStatus.REVISION_REQUIRED,
            QuotationStatus.UNDER_NEGOTIATION,
        ):
            raise DealFlowException(
                f"Cannot update line for quotation in state {quote.status.value}",
                status_code=400,
            )

        line = quotation_repository.get_line_by_id(db, quotation_id, line_id)
        if not line:
            raise ResourceNotFoundError("Quotation line not found")

        if request.quantity is not None:
            line.quantity = Decimal(str(request.quantity))
        if request.unit_price is not None:
            line.unit_price = Decimal(str(request.unit_price))
        if request.discount_percent is not None:
            line.discount_percent = Decimal(str(request.discount_percent))
        if request.tax_rate is not None:
            line.tax_rate = Decimal(str(request.tax_rate))
        if request.description is not None:
            line.description = request.description

        self._recalculate_quotation_internal(db, quote)
        return quote

    def delete_line(
        self,
        db: Session,
        quotation_id: uuid.UUID,
        line_id: uuid.UUID,
        current_user: User,
    ) -> Quotation:
        """Delete a line from quotation and recalculate dependent state."""
        quote = self.get_quotation_by_id(db, quotation_id)
        if quote.status not in (
            QuotationStatus.DRAFT,
            QuotationStatus.REVISION_REQUIRED,
        ):
            raise DealFlowException(
                f"Cannot delete line for quotation in state {quote.status.value}",
                status_code=400,
            )

        line = quotation_repository.get_line_by_id(db, quotation_id, line_id)
        if not line:
            raise ResourceNotFoundError("Quotation line not found")

        quotation_repository.delete_line(db, line)
        self._recalculate_quotation_internal(db, quote)
        return quote

    # --- Core Recalculation & Discount Governance Integration ---

    def recalculate(
        self, db: Session, quotation_id: uuid.UUID
    ) -> Tuple[Quotation, QuotationRiskResponse]:
        """Trigger complete server-authoritative quotation recalculation."""
        quote = self.get_quotation_by_id(db, quotation_id)
        risk_resp = self._recalculate_quotation_internal(db, quote)
        return quote, risk_resp

    def _recalculate_quotation_internal(
        self, db: Session, quote: Quotation
    ) -> QuotationRiskResponse:
        """
        Execute full authoritative recalculation across:
        1. Discount Governance Engine per line
        2. Financial calculations (line totals, tax, margin)
        3. Quotation totals aggregation
        4. Blended discount-risk score
        5. Approval requirement & required approval level
        6. Persist snapshots atomically
        """
        customer = quote.customer
        if not customer and quote.customer_id:
            customer = db.get(Customer, quote.customer_id)
        customer_tier_id = (
            customer.customer_tier_id if customer else None
        )
        active_rules = quotation_repository.get_active_discount_rules(db)
        active_policies = quotation_repository.get_active_approval_policies(db)

        line_financials_list = []
        line_risk_inputs = []
        line_risk_details: List[LineRiskDetail] = []
        violating_count = 0

        # Evaluate EVERY quotation line server-side
        for line in quote.lines:
            product = line.product
            if not product and line.product_id:
                product = db.get(Product, line.product_id)
            category_id = (
                product.category_id if product else None
            )

            # Invoke Discount Governance & Resolution Engine
            gov_result = discount_engine.resolve_line_discount(
                requested_discount_percent=line.discount_percent,
                customer_tier_id=customer_tier_id,
                category_id=category_id,
                discount_rules=active_rules,
            )

            # Update required discount snapshots on quotation_lines
            if gov_result.applicable_discount_limit is not None:
                line.allowed_discount_percent = gov_result.applicable_discount_limit
            else:
                line.allowed_discount_percent = Decimal("100.00")
            line.discount_excess_percent = gov_result.discount_excess_percent

            # Refresh unit cost snapshot from product if available
            if line.product and line.product.cost_price is not None:
                line.unit_cost = line.product.cost_price

            # Calculate line financials
            financials = quotation_engine.calculate_line_financials(
                quantity=line.quantity,
                unit_price=line.unit_price,
                discount_percent=line.discount_percent,
                tax_rate=line.tax_rate,
                unit_cost=line.unit_cost,
            )

            line.discount_amount = financials["discount_amount"]
            line.line_total = financials["line_total"]
            line.margin_amount = financials["margin_amount"]
            line.margin_percent = financials["margin_percent"]

            line_financials_list.append(financials)
            line_risk_inputs.append(
                {
                    "quantity": line.quantity,
                    "unit_price": line.unit_price,
                    "discount_excess_percent": line.discount_excess_percent,
                }
            )

            if gov_result.is_violation:
                violating_count += 1

            line_risk_details.append(
                LineRiskDetail(
                    line_id=line.id,
                    product_id=line.product_id,
                    product_name=line.product.name if line.product else None,
                    quantity=line.quantity,
                    unit_price=line.unit_price,
                    line_gross_value=financials["gross_amount"],
                    requested_discount_percent=line.discount_percent,
                    applicable_discount_limit=gov_result.applicable_discount_limit,
                    allowed_discount_percent=gov_result.allowed_discount_percent,
                    discount_excess_percent=gov_result.discount_excess_percent,
                    is_violation=gov_result.is_violation,
                    has_applicable_rule=gov_result.has_applicable_rule,
                    applied_rule_id=gov_result.applied_rule_id,
                    applied_rule_type=gov_result.applied_rule_type,
                    applied_tier_id=gov_result.applied_tier_id,
                    applied_category_id=gov_result.applied_category_id,
                    resolution_summary=gov_result.resolution_summary,
                )
            )

        # Quotation-level financial aggregation
        aggs = quotation_engine.calculate_quotation_aggregates(line_financials_list)
        quote.subtotal = aggs["subtotal"]
        quote.discount_amount = aggs["discount_amount"]
        quote.order_discount_percent = aggs["order_discount_percent"]
        quote.tax_amount = aggs["tax_amount"]
        quote.total_amount = aggs["total_amount"]
        quote.total_cost = aggs["total_cost"]
        quote.margin_amount = aggs["margin_amount"]
        quote.margin_percent = aggs["margin_percent"]

        # Blended discount-risk score
        blended_risk = quotation_engine.calculate_blended_risk_score(
            line_risk_inputs
        )
        quote.risk_score = blended_risk

        # Approval requirement & required level determination
        has_violations = violating_count > 0
        app_req, req_level = quotation_engine.determine_approval_requirement(
            risk_score=blended_risk,
            has_line_violations=has_violations,
            approval_policies=active_policies,
        )
        quote.approval_required = app_req
        quote.current_approval_level = req_level
        quote.last_activity_at = datetime.datetime.now(datetime.timezone.utc)

        # Commit atomically
        quotation_repository.save_recalculated_state(db, quote)

        return QuotationRiskResponse(
            quotation_id=quote.id,
            quotation_number=quote.quotation_number,
            subtotal=quote.subtotal,
            discount_amount=quote.discount_amount,
            order_discount_percent=quote.order_discount_percent,
            risk_score=quote.risk_score,
            approval_required=quote.approval_required,
            required_approval_level=quote.current_approval_level,
            total_lines_count=len(quote.lines),
            violating_lines_count=violating_count,
            line_risks=line_risk_details,
            formula_explanation=quotation_engine.BLENDED_RISK_FORMULA_EXPLANATION,
        )

    # --- Risk State ---

    def get_risk(self, db: Session, quotation_id: uuid.UUID) -> QuotationRiskResponse:
        """Fetch current authoritative quotation risk state."""
        quote = self.get_quotation_by_id(db, quotation_id)
        # Recalculate to ensure absolute fresh state
        return self._recalculate_quotation_internal(db, quote)

    # --- Quotation Submission ---

    def submit(
        self, db: Session, quotation_id: uuid.UUID, current_user: User
    ) -> Quotation:
        """
        Submit quotation into the next workflow state.
        MUST recalculate first, then automatically evaluate approval requirements.
        """
        quote = self.get_quotation_by_id(db, quotation_id)
        if quote.status not in (
            QuotationStatus.DRAFT,
            QuotationStatus.REVISION_REQUIRED,
            QuotationStatus.UNDER_NEGOTIATION,
        ):
            raise DealFlowException(
                f"Quotation cannot be submitted from status {quote.status.value}",
                status_code=400,
            )

        # Recalculate first: Server is authoritative, never trust stale frontend state
        self._recalculate_quotation_internal(db, quote)

        if quote.approval_required:
            quote.status = QuotationStatus.PENDING_APPROVAL

            # Create an ApprovalInstance
            instance = ApprovalInstance(
                quotation_id=quote.id,
                risk_score=quote.risk_score,
                status=ApprovalStatus.PENDING,
            )
            db.add(instance)
            db.flush()

            # Sequential approval step 1: Sales Manager
            step1 = ApprovalStep(
                approval_instance_id=instance.id,
                step_order=1,
                approver_role=ApproverRole.SALES_MANAGER,
                status=ApprovalStatus.PENDING,
            )
            db.add(step1)

            # If Finance Operations approval is also required
            if (
                quote.current_approval_level
                == ApproverRole.FINANCE_OPERATIONS.value
            ):
                step2 = ApprovalStep(
                    approval_instance_id=instance.id,
                    step_order=2,
                    approver_role=ApproverRole.FINANCE_OPERATIONS,
                    status=ApprovalStatus.PENDING,
                )
                db.add(step2)
        else:
            # Approval not required: eligible to progress
            quote.status = QuotationStatus.APPROVED

        quote.last_activity_at = datetime.datetime.now(datetime.timezone.utc)
        db.add(quote)
        db.commit()
        db.refresh(quote)
        return quote


quotation_service = QuotationService()

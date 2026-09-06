"""Quotations service layer."""

from __future__ import annotations

import datetime
import uuid
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.common.enums import (
    ApprovalStatus,
    ApproverRole,
    OrderStatus,
    QuotationStatus,
    UserRole,
)
from app.core.exceptions import DealFlowException, ResourceNotFoundError
from app.models.approval_instance import ApprovalInstance
from app.models.approval_step import ApprovalStep
from app.models.customer import Customer
from app.models.order import Order
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.quotation import Quotation
from app.models.quotation_line import QuotationLine
from app.models.user import User
from app.modules.audit.service import audit_service
from app.modules.discounts.engine import discount_engine
from app.modules.pricing.engine import pricing_engine
from app.modules.pricing.repository import pricing_repository
from app.modules.quotations.engine import quotation_engine
from app.modules.quotations.repository import quotation_repository
from app.modules.quotations.schemas import (
    LineRiskDetail,
    OrderResponse,
    OrderUpdateRequest,
    PipelineCardResponse,
    PipelineResponse,
    PipelineStageResponse,
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

        created_quote = quotation_repository.create_quotation(db, quotation)

        audit_service.log_event(
            db=db,
            entity_type="QUOTATION",
            entity_id=created_quote.id,
            action="CREATE",
            user_id=current_user.id if current_user else None,
            old_values=None,
            new_values={
                "quotation_number": created_quote.quotation_number,
                "customer_id": str(created_quote.customer_id),
                "status": created_quote.status.value,
            },
            reason=f"Created draft quotation {created_quote.quotation_number}",
        )
        db.commit()
        return created_quote

    def update_quotation(
        self,
        db: Session,
        quotation_id: uuid.UUID,
        request: QuotationUpdateRequest,
        current_user: Optional[User] = None,
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

        old_valid_until = str(quote.valid_until) if quote.valid_until else None
        if request.valid_until is not None:
            quote.valid_until = request.valid_until

        quote.last_activity_at = datetime.datetime.now(datetime.timezone.utc)
        db.add(quote)

        audit_service.log_event(
            db=db,
            entity_type="QUOTATION",
            entity_id=quote.id,
            action="UPDATE",
            user_id=current_user.id if current_user else None,
            old_values={"valid_until": old_valid_until},
            new_values={
                "valid_until": str(quote.valid_until) if quote.valid_until else None
            },
            reason="Updated quotation metadata",
        )

        db.commit()
        db.refresh(quote)
        return quote

    def delete_quotation(
        self,
        db: Session,
        quotation_id: uuid.UUID,
        current_user: Optional[User] = None,
    ) -> None:
        """Delete/deactivate quotation where allowed (DRAFT only)."""
        quote = self.get_quotation_by_id(db, quotation_id)
        if quote.status != QuotationStatus.DRAFT:
            raise DealFlowException(
                f"Cannot delete quotation in state '{quote.status.value}'. Only DRAFT quotations can be deleted.",
                status_code=400,
            )

        audit_service.log_event(
            db=db,
            entity_type="QUOTATION",
            entity_id=quote.id,
            action="DELETE",
            user_id=current_user.id if current_user else None,
            old_values={
                "quotation_number": quote.quotation_number,
                "status": quote.status.value,
            },
            reason=f"Deleted draft quotation {quote.quotation_number}",
        )
        quotation_repository.delete_quotation(db, quote)

    def get_lines(
        self, db: Session, quotation_id: uuid.UUID
    ) -> List[QuotationLine]:
        """Fetch all lines belonging to a quotation."""
        self.get_quotation_by_id(db, quotation_id)  # verifies existence
        return quotation_repository.get_lines(db, quotation_id)


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

        audit_service.log_event(
            db=db,
            entity_type="QUOTATION",
            entity_id=quote.id,
            action="ADD_LINE",
            user_id=current_user.id if current_user else None,
            old_values=None,
            new_values={
                "line_id": str(line.id),
                "product_id": str(line.product_id),
                "quantity": str(line.quantity),
                "discount_percent": str(line.discount_percent),
            },
            reason=f"Added product line {product.sku} to quotation {quote.quotation_number}",
        )
        db.commit()
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

        old_values = {
            "quantity": str(line.quantity),
            "unit_price": str(line.unit_price),
            "discount_percent": str(line.discount_percent),
        }

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

        audit_service.log_event(
            db=db,
            entity_type="QUOTATION",
            entity_id=quote.id,
            action="UPDATE_LINE",
            user_id=current_user.id if current_user else None,
            old_values=old_values,
            new_values={
                "line_id": str(line.id),
                "quantity": str(line.quantity),
                "unit_price": str(line.unit_price),
                "discount_percent": str(line.discount_percent),
            },
            reason=f"Updated line on quotation {quote.quotation_number}",
        )
        db.commit()
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

        old_values = {
            "line_id": str(line.id),
            "product_id": str(line.product_id),
            "quantity": str(line.quantity),
        }

        quotation_repository.delete_line(db, line)
        self._recalculate_quotation_internal(db, quote)

        audit_service.log_event(
            db=db,
            entity_type="QUOTATION",
            entity_id=quote.id,
            action="DELETE_LINE",
            user_id=current_user.id if current_user else None,
            old_values=old_values,
            new_values=None,
            reason=f"Deleted line from quotation {quote.quotation_number}",
        )
        db.commit()
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

        old_status = quote.status.value

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

            audit_service.log_event(
                db=db,
                entity_type="APPROVAL_INSTANCE",
                entity_id=instance.id,
                action="CREATE",
                user_id=current_user.id if current_user else None,
                old_values=None,
                new_values={
                    "quotation_id": str(quote.id),
                    "risk_score": str(quote.risk_score),
                    "required_level": quote.current_approval_level,
                },
                reason=f"Generated approval workflow with risk score {quote.risk_score}",
            )
        else:
            # Approval not required: eligible to progress
            quote.status = QuotationStatus.APPROVED

        quote.last_activity_at = datetime.datetime.now(datetime.timezone.utc)
        db.add(quote)

        audit_service.log_event(
            db=db,
            entity_type="QUOTATION",
            entity_id=quote.id,
            action="SUBMIT",
            user_id=current_user.id if current_user else None,
            old_values={"status": old_status},
            new_values={"status": quote.status.value},
            reason=f"Submitted quotation {quote.quotation_number}",
        )

        db.commit()
        db.refresh(quote)
        return quote

    def send_quotation(
        self, db: Session, quotation_id: uuid.UUID, current_user: User
    ) -> Quotation:
        """Mark quotation as sent to customer."""
        quote = self.get_quotation_by_id(db, quotation_id)
        if quote.status not in (QuotationStatus.APPROVED, QuotationStatus.DRAFT):
            raise DealFlowException(
                f"Quotation cannot be sent from state '{quote.status.value}'",
                status_code=400,
            )
        now = datetime.datetime.now(datetime.timezone.utc)
        old_status = quote.status.value
        quote.status = QuotationStatus.SENT
        quote.sent_at = now
        quote.last_activity_at = now

        audit_service.log_event(
            db=db,
            entity_type="QUOTATION",
            entity_id=quote.id,
            action="SEND",
            user_id=current_user.id if current_user else None,
            old_values={"status": old_status},
            new_values={"status": quote.status.value, "sent_at": now.isoformat()},
            reason=f"Sent quotation {quote.quotation_number} to customer",
        )
        db.add(quote)
        db.commit()
        db.refresh(quote)
        return quote

    def return_for_revision(
        self,
        db: Session,
        quotation_id: uuid.UUID,
        current_user: User,
        reason: Optional[str] = None,
    ) -> Quotation:
        """Return quotation to revision state."""
        quote = self.get_quotation_by_id(db, quotation_id)
        if quote.status in (QuotationStatus.CONFIRMED, QuotationStatus.REVISION_REQUIRED):
            raise DealFlowException(
                f"Quotation in state '{quote.status.value}' cannot be returned for revision",
                status_code=400,
            )
        now = datetime.datetime.now(datetime.timezone.utc)
        old_status = quote.status.value
        quote.status = QuotationStatus.REVISION_REQUIRED
        quote.last_activity_at = now

        audit_service.log_event(
            db=db,
            entity_type="QUOTATION",
            entity_id=quote.id,
            action="RETURN_FOR_REVISION",
            user_id=current_user.id if current_user else None,
            old_values={"status": old_status},
            new_values={"status": quote.status.value},
            reason=reason or "Quotation returned for revision",
        )
        db.add(quote)
        db.commit()
        db.refresh(quote)
        return quote

    def confirm_quotation(
        self, db: Session, quotation_id: uuid.UUID, current_user: User
    ) -> Tuple[Quotation, Order]:
        """
        Confirm quotation and create corresponding Order.
        Must verify:
        - Quotation is in confirmable state (APPROVED or SENT)
        - If approval was required, at least one approval instance is APPROVED
        - Prevents duplicate order creation (at most one order per quotation)
        - Quotation has lines
        - Updates quotation status to CONFIRMED
        - Atomically creates Order
        - Writes audit logs
        """
        quote = self.get_quotation_by_id(db, quotation_id)

        # Check existing order / duplicate confirmation
        existing_order = quotation_repository.get_order_by_quotation_id(db, quotation_id)
        if existing_order or quote.status == QuotationStatus.CONFIRMED:
            raise DealFlowException(
                "Quotation has already been confirmed and an order already exists",
                status_code=400,
            )

        if quote.status not in (QuotationStatus.APPROVED, QuotationStatus.SENT):
            raise DealFlowException(
                f"Quotation cannot be confirmed from status '{quote.status.value}'. Must be APPROVED or SENT.",
                status_code=400,
            )

        if not quote.lines:
            raise DealFlowException(
                "Cannot confirm a quotation with no product lines",
                status_code=400,
            )

        if quote.approval_required:
            # Verify approval instance is approved
            instances = quotation_repository.get_quotation_approval_instances(db, quote.id)
            has_approved_instance = any(i.status == ApprovalStatus.APPROVED for i in instances)
            if not has_approved_instance:
                raise DealFlowException(
                    "Quotation requires approval before confirmation, but no approved workflow was found",
                    status_code=400,
                )

        now = datetime.datetime.now(datetime.timezone.utc)
        unique_suffix = uuid.uuid4().hex[:6].upper()
        order_number = f"SO-{now.strftime('%Y%m%d')}-{unique_suffix}"

        order = Order(
            order_number=order_number,
            quotation_id=quote.id,
            customer_id=quote.customer_id,
            status=OrderStatus.CONFIRMED,
            total_amount=quote.total_amount,
            confirmed_at=now,
        )
        quotation_repository.create_order(db, order)

        old_status = quote.status.value
        quote.status = QuotationStatus.CONFIRMED
        quote.last_activity_at = now
        db.add(quote)

        audit_service.log_event(
            db=db,
            entity_type="QUOTATION",
            entity_id=quote.id,
            action="CONFIRM",
            user_id=current_user.id if current_user else None,
            old_values={"status": old_status},
            new_values={
                "status": QuotationStatus.CONFIRMED.value,
                "order_number": order_number,
            },
            reason=f"Confirmed quotation and generated Order {order_number}",
        )

        audit_service.log_event(
            db=db,
            entity_type="ORDER",
            entity_id=order.id,
            action="CREATE",
            user_id=current_user.id if current_user else None,
            old_values=None,
            new_values={
                "order_number": order.order_number,
                "quotation_id": str(quote.id),
                "customer_id": str(quote.customer_id),
                "status": order.status.value,
                "total_amount": str(order.total_amount),
            },
            reason=f"Created order {order_number} from confirmed quotation {quote.quotation_number}",
        )

        db.commit()
        db.refresh(quote)
        db.refresh(order)
        return quote, order

    def get_order_for_quotation(
        self, db: Session, quotation_id: uuid.UUID
    ) -> Order:
        """Fetch order generated from a quotation or raise 404."""
        self.get_quotation_by_id(db, quotation_id)
        order = quotation_repository.get_order_by_quotation_id(db, quotation_id)
        if not order:
            raise ResourceNotFoundError("No order found for this quotation")
        return order

    def get_quotation_approvals(
        self, db: Session, quotation_id: uuid.UUID
    ):
        """Fetch approval history and workflows for quotation."""
        self.get_quotation_by_id(db, quotation_id)
        return quotation_repository.get_quotation_approval_instances(db, quotation_id)

    def get_pipeline(self, db: Session) -> PipelineResponse:
        """Return Kanban pipeline stage grouping of quotations."""
        quotations = quotation_repository.get_all_quotations_for_pipeline(db)
        all_stages = [
            QuotationStatus.DRAFT.value,
            QuotationStatus.PENDING_APPROVAL.value,
            QuotationStatus.APPROVED.value,
            QuotationStatus.SENT.value,
            QuotationStatus.UNDER_NEGOTIATION.value,
            QuotationStatus.CONFIRMED.value,
            QuotationStatus.REVISION_REQUIRED.value,
            QuotationStatus.REJECTED.value,
        ]

        stage_map = {stage: [] for stage in all_stages}
        total_deals = len(quotations)
        total_pipeline_value = Decimal("0.00")

        for q in quotations:
            total_pipeline_value += q.total_amount
            status_str = q.status.value if hasattr(q.status, "value") else str(q.status)
            if status_str not in stage_map:
                stage_map[status_str] = []
            stage_map[status_str].append(
                PipelineCardResponse(
                    quotation_id=q.id,
                    quotation_number=q.quotation_number,
                    customer_id=q.customer_id,
                    customer_name=q.customer.name if q.customer else None,
                    sales_rep_id=q.sales_rep_id,
                    sales_rep_name=q.sales_rep.name if q.sales_rep else None,
                    status=status_str,
                    total_amount=q.total_amount,
                    margin_percent=q.margin_percent,
                    risk_score=q.risk_score,
                    created_at=q.created_at,
                    last_activity_at=q.last_activity_at,
                )
            )

        stage_responses = []
        for stage in all_stages:
            cards = stage_map[stage]
            stage_val = sum((c.total_amount for c in cards), Decimal("0.00"))
            stage_responses.append(
                PipelineStageResponse(
                    stage=stage,
                    count=len(cards),
                    total_value=stage_val,
                    cards=cards,
                )
            )

        return PipelineResponse(
            stages=stage_responses,
            total_deals=total_deals,
            total_pipeline_value=total_pipeline_value,
        )

    # --- Orders Management ---

    def list_orders(
        self,
        db: Session,
        customer_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Order]:
        """List confirmed sales orders."""
        return quotation_repository.list_orders(
            db=db,
            customer_id=customer_id,
            status=status,
            skip=skip,
            limit=limit,
        )

    def get_order_by_id(self, db: Session, order_id: uuid.UUID) -> Order:
        """Get order by ID or raise 404."""
        order = quotation_repository.get_order_by_id(db, order_id)
        if not order:
            raise ResourceNotFoundError("Order not found")
        return order

    def update_order(
        self,
        db: Session,
        order_id: uuid.UUID,
        request: OrderUpdateRequest,
        current_user: User,
    ) -> Order:
        """Update permitted order fields/state."""
        order = self.get_order_by_id(db, order_id)
        old_status = order.status.value
        if request.status is not None:
            try:
                target_status = OrderStatus(request.status)
            except ValueError:
                raise DealFlowException(f"Invalid order status: {request.status}", status_code=400)
            order.status = target_status

        order.updated_at = datetime.datetime.now(datetime.timezone.utc)
        db.add(order)

        audit_service.log_event(
            db=db,
            entity_type="ORDER",
            entity_id=order.id,
            action="UPDATE",
            user_id=current_user.id,
            old_values={"status": old_status},
            new_values={"status": order.status.value},
            reason=f"Updated order {order.order_number} status",
        )
        db.commit()
        db.refresh(order)
        return order


quotation_service = QuotationService()


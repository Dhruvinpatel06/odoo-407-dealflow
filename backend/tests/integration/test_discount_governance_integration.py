"""Integration tests for Discount Governance & Resolution with persisted domain models."""

from __future__ import annotations

import uuid
from decimal import Decimal
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.security import hash_password
from app.models.customer import Customer
from app.models.customer_tier import CustomerTier
from app.models.discount_rule import DiscountRule
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.quotation import Quotation
from app.models.quotation_line import QuotationLine
from app.models.user import User
from app.modules.discounts.service import discount_service


def test_discount_governance_end_to_end_persisted_flow(db: Session):
    """
    Verify complete persisted flow:
    Customer -> Customer Tier -> Product -> Product Category -> Discount Rule -> Quotation -> Quotation Line
    -> Discount Service / Engine -> Authoritative Governance Result.
    """
    # 1. Persist User (Sales Rep)
    sales_rep = User(
        name="Rep Jane",
        email=f"rep-{uuid.uuid4().hex[:6]}@dealflow360.local",
        password_hash=hash_password("Password123!"),
        role=UserRole.SALES_REP,
        is_active=True,
    )
    db.add(sales_rep)

    # 2. Persist Customer Tier
    tier = CustomerTier(
        name=f"Enterprise Tier-{uuid.uuid4().hex[:6]}",
        default_discount_limit=Decimal("20.00"),
        is_active=True,
    )
    db.add(tier)
    db.flush()

    # 3. Persist Customer linked to Tier
    customer = Customer(
        name="Acme Global Corporation",
        email=f"procure-{uuid.uuid4().hex[:6]}@acme.local",
        customer_tier_id=tier.id,
        is_active=True,
    )
    db.add(customer)

    # 4. Persist Product Category
    category = ProductCategory(
        name=f"Enterprise Hardware-{uuid.uuid4().hex[:6]}",
        is_active=True,
    )
    db.add(category)
    db.flush()

    # 5. Persist Product linked to Category
    product = Product(
        category_id=category.id,
        name="Rackmount Server 2U",
        sku=f"SRV-{uuid.uuid4().hex[:6].upper()}",
        unit="units",
        base_price=Decimal("2500.00"),
        cost_price=Decimal("1600.00"),
        tax_rate=Decimal("18.00"),
        is_active=True,
    )
    db.add(product)

    # 6. Persist Discount Rules
    # Tier rule: 10% ceiling
    tier_rule = DiscountRule(
        customer_tier_id=tier.id,
        category_id=None,
        max_discount_percent=Decimal("10.00"),
        priority=1,
        is_active=True,
    )
    # Category rule: 15% ceiling
    cat_rule = DiscountRule(
        customer_tier_id=None,
        category_id=category.id,
        max_discount_percent=Decimal("15.00"),
        priority=1,
        is_active=True,
    )
    db.add_all([tier_rule, cat_rule])
    db.flush()

    # 7. Persist Quotation linked to Customer and Sales Rep
    quotation = Quotation(
        quotation_number=f"QT-{uuid.uuid4().hex[:8].upper()}",
        customer_id=customer.id,
        sales_rep_id=sales_rep.id,
    )
    db.add(quotation)
    db.flush()

    # 8. Persist QuotationLine with requested discount = 12%
    line = QuotationLine(
        quotation_id=quotation.id,
        product_id=product.id,
        quantity=Decimal("5.00"),
        unit_price=Decimal("2500.00"),
        discount_percent=Decimal("12.00"),
    )
    db.add(line)
    db.commit()

    # Refresh relationships
    db.refresh(line)
    db.refresh(quotation)
    db.refresh(customer)
    db.refresh(product)

    # --- Phase 1: Both Rules Active -> Stricter Tier Limit (10%) wins ---
    result1 = discount_service.evaluate_quotation_line(db=db, quotation_line=line)

    assert result1.has_applicable_rule is True
    assert result1.applicable_discount_limit == Decimal("10.00")
    assert result1.allowed_discount_percent == Decimal("10.00")
    assert result1.discount_excess_percent == Decimal("2.00")
    assert result1.is_violation is True
    assert result1.applied_rule_id == tier_rule.id
    assert result1.applied_rule_type == "TIER"

    # --- Phase 2: Deactivate Tier Rule -> Category Rule (15%) now wins ---
    discount_service.deactivate_discount_rule(db=db, rule_id=tier_rule.id)

    result2 = discount_service.evaluate_quotation_line(db=db, quotation_line=line)

    assert result2.has_applicable_rule is True
    assert result2.applicable_discount_limit == Decimal("15.00")
    # Requested 12% <= Limit 15% -> Allowed is 12%, excess is 0, no violation
    assert result2.allowed_discount_percent == Decimal("12.00")
    assert result2.discount_excess_percent == Decimal("0.00")
    assert result2.is_violation is False
    assert result2.applied_rule_id == cat_rule.id
    assert result2.applied_rule_type == "CATEGORY"

    # --- Phase 3: Deactivate Category Rule -> No active rules apply ---
    discount_service.deactivate_discount_rule(db=db, rule_id=cat_rule.id)

    result3 = discount_service.evaluate_quotation_line(db=db, quotation_line=line)

    assert result3.has_applicable_rule is False
    assert result3.applicable_discount_limit is None
    assert result3.allowed_discount_percent == Decimal("12.00")
    assert result3.discount_excess_percent == Decimal("0.00")
    assert result3.is_violation is False

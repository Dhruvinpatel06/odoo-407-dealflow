"""Persistence-level unit tests for the DiscountRule model and database schema foundation."""

from __future__ import annotations

import uuid
from decimal import Decimal
import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import Base
from app.models.customer_tier import CustomerTier
from app.models.discount_rule import DiscountRule
from app.models.product_category import ProductCategory
from app.models.quotation import Quotation
from app.models.quotation_line import QuotationLine


def test_discount_rule_persistence_minimal(db: Session):
    """Verify DiscountRule can be persisted with minimal required fields and appropriate defaults."""
    rule = DiscountRule(
        max_discount_percent=Decimal("15.00"),
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    assert rule.id is not None
    assert isinstance(rule.id, uuid.UUID)
    assert rule.customer_tier_id is None
    assert rule.category_id is None
    assert rule.max_discount_percent == Decimal("15.00")
    assert rule.priority == 0
    assert rule.is_active is True
    assert rule.created_at is not None
    assert rule.updated_at is not None
    assert rule.customer_tier is None
    assert rule.category is None


def test_discount_rule_with_customer_tier(db: Session):
    """Verify foreign key and bidirectional relationship with CustomerTier."""
    tier = CustomerTier(
        name=f"Gold Tier-{uuid.uuid4().hex[:6]}",
        description="High volume customers",
        default_discount_limit=Decimal("20.00"),
        is_active=True,
    )
    db.add(tier)
    db.commit()
    db.refresh(tier)

    rule = DiscountRule(
        customer_tier_id=tier.id,
        max_discount_percent=Decimal("25.00"),
        priority=1,
        is_active=True,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    assert rule.customer_tier_id == tier.id
    assert rule.customer_tier is not None
    assert rule.customer_tier.id == tier.id
    assert rule.customer_tier.name == tier.name

    # Test inverse relationship on CustomerTier
    db.refresh(tier)
    assert any(r.id == rule.id for r in tier.discount_rules)


def test_discount_rule_with_product_category(db: Session):
    """Verify foreign key and bidirectional relationship with ProductCategory."""
    category = ProductCategory(
        name=f"Hardware-{uuid.uuid4().hex[:6]}",
        description="Physical servers and parts",
        is_active=True,
    )
    db.add(category)
    db.commit()
    db.refresh(category)

    rule = DiscountRule(
        category_id=category.id,
        max_discount_percent=Decimal("12.50"),
        priority=2,
        is_active=True,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    assert rule.category_id == category.id
    assert rule.category is not None
    assert rule.category.id == category.id
    assert rule.category.name == category.name

    # Test inverse relationship on ProductCategory
    db.refresh(category)
    assert any(r.id == rule.id for r in category.discount_rules)


def test_discount_rule_combined_tier_and_category(db: Session):
    """Verify DiscountRule can target both CustomerTier and ProductCategory simultaneously."""
    tier = CustomerTier(
        name=f"Platinum Tier-{uuid.uuid4().hex[:6]}",
        default_discount_limit=Decimal("30.00"),
        is_active=True,
    )
    category = ProductCategory(
        name=f"Cloud Services-{uuid.uuid4().hex[:6]}",
        is_active=True,
    )
    db.add_all([tier, category])
    db.commit()
    db.refresh(tier)
    db.refresh(category)

    rule = DiscountRule(
        customer_tier_id=tier.id,
        category_id=category.id,
        max_discount_percent=Decimal("35.00"),
        priority=10,
        is_active=True,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    assert rule.customer_tier_id == tier.id
    assert rule.category_id == category.id
    assert rule.customer_tier.id == tier.id
    assert rule.category.id == category.id
    assert rule.priority == 10
    assert rule.max_discount_percent == Decimal("35.00")


def test_discount_rule_priority_and_inactive_persistence(db: Session):
    """Verify priority/precedence and active/inactive state persist correctly."""
    rule = DiscountRule(
        max_discount_percent=Decimal("5.00"),
        priority=99,
        is_active=False,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    assert rule.priority == 99
    assert rule.is_active is False
    assert rule.max_discount_percent == Decimal("5.00")


def test_discount_rule_required_fields_enforced(db: Session):
    """Verify required field max_discount_percent cannot be null."""
    rule = DiscountRule(
        max_discount_percent=None,  # type: ignore
    )
    db.add(rule)
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            db.flush()


def test_discount_rule_database_schema_contract():
    """Verify table name, columns, nullability, and foreign key definitions match finalized schema."""
    table = Base.metadata.tables.get("discount_rules")
    assert table is not None, "Table 'discount_rules' must exist in Base.metadata"

    expected_columns = {
        "id": (False, True),  # (nullable, is_pk)
        "customer_tier_id": (True, False),
        "category_id": (True, False),
        "max_discount_percent": (False, False),
        "priority": (False, False),
        "is_active": (False, False),
        "created_at": (False, False),
        "updated_at": (False, False),
    }

    assert set(table.columns.keys()) == set(expected_columns.keys())

    for col_name, (expected_nullable, expected_pk) in expected_columns.items():
        col = table.columns[col_name]
        assert col.nullable is expected_nullable, f"Column {col_name} nullable mismatch"
        assert col.primary_key is expected_pk, f"Column {col_name} PK mismatch"

    # Verify Foreign Keys
    fk_targets = {fk.target_fullname for fk in table.foreign_keys}
    assert "customer_tiers.id" in fk_targets
    assert "product_categories.id" in fk_targets

    # Verify Indexes
    indexed_columns = {
        idx.columns.keys()[0]
        for idx in table.indexes
        if len(idx.columns) == 1
    }
    assert "customer_tier_id" in indexed_columns
    assert "category_id" in indexed_columns


def test_existing_quotation_models_unaffected():
    """Verify existing Quotation and QuotationLine models remain fully functional and unchanged."""
    quotation_cols = set(Base.metadata.tables["quotations"].columns.keys())
    assert "quotation_number" in quotation_cols
    assert "customer_id" in quotation_cols
    assert "sales_rep_id" in quotation_cols
    assert "status" in quotation_cols
    assert "total_amount" in quotation_cols
    assert "margin_amount" in quotation_cols
    assert "margin_percent" in quotation_cols

    line_cols = set(Base.metadata.tables["quotation_lines"].columns.keys())
    assert "quotation_id" in line_cols
    assert "product_id" in line_cols
    assert "quantity" in line_cols
    assert "unit_price" in line_cols
    assert "discount_percent" in line_cols
    assert "allowed_discount_percent" in line_cols
    assert "discount_excess_percent" in line_cols

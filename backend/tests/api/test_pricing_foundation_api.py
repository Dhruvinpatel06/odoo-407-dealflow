"""Tests for Pricing module database models, schemas, and foundation endpoints."""

from __future__ import annotations

import uuid
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.security import create_access_token
from app.models.customer_tier import CustomerTier
from app.models.price_list import PriceList
from app.models.price_list_item import PriceListItem
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.product_variant import ProductVariant
from app.models.user import User
from app.modules.pricing.schemas import (
    PriceListCreateRequest,
    PriceListItemCreateRequest,
    PriceListItemResponse,
    PriceListResponse,
    PricingResolveRequest,
    PricingResolveResponse,
)


def _create_auth_headers(user: User) -> dict:
    """Helper to generate Authorization header for a given user."""
    token = create_access_token(user_id=user.id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_tier(db: Session) -> CustomerTier:
    """Create a default customer tier for testing price list association."""
    tier = CustomerTier(
        name=f"Enterprise Tier-{uuid.uuid4().hex[:6]}",
        default_discount_limit=Decimal("20.00"),
        is_active=True,
    )
    db.add(tier)
    db.commit()
    db.refresh(tier)
    return tier


@pytest.fixture
def test_product(db: Session) -> Product:
    """Create a default product for price list item testing."""
    cat = ProductCategory(name=f"PricingCat-{uuid.uuid4().hex[:6]}", is_active=True)
    db.add(cat)
    db.commit()
    db.refresh(cat)

    prod = Product(
        category_id=cat.id,
        name="Server Blade",
        sku=f"SVR-BLD-{uuid.uuid4().hex[:6].upper()}",
        unit="units",
        base_price=Decimal("1500.00"),
        cost_price=Decimal("950.00"),
        tax_rate=Decimal("18.00"),
        is_active=True,
    )
    db.add(prod)
    db.commit()
    db.refresh(prod)
    return prod


def test_pricing_models_and_relationships(
    db: Session, test_tier: CustomerTier, test_product: Product
):
    """
    Step 1 Database Model Verification:
    Verify PriceList and PriceListItem SQLAlchemy models, attributes, constraints,
    and relationships with CustomerTier, Product, and ProductVariant.
    """
    # 1. Create PriceList
    price_list = PriceList(
        name="Enterprise USD Price List",
        customer_tier_id=test_tier.id,
        currency="USD",
        is_active=True,
    )
    db.add(price_list)
    db.commit()
    db.refresh(price_list)

    assert price_list.id is not None
    assert price_list.name == "Enterprise USD Price List"
    assert price_list.currency == "USD"
    assert price_list.customer_tier_id == test_tier.id
    assert price_list.customer_tier.name == test_tier.name

    # 2. Create Variant
    variant = ProductVariant(
        product_id=test_product.id,
        attribute_name="RAM",
        attribute_value="64GB",
        extra_price=Decimal("300.00"),
    )
    db.add(variant)
    db.commit()
    db.refresh(variant)

    # 3. Create PriceListItem linked to PriceList, Product, and Variant
    item = PriceListItem(
        price_list_id=price_list.id,
        product_id=test_product.id,
        variant_id=variant.id,
        price=Decimal("1750.00"),
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    assert item.id is not None
    assert item.price_list_id == price_list.id
    assert item.product_id == test_product.id
    assert item.variant_id == variant.id
    assert item.price == Decimal("1750.00")
    assert item.price_list.id == price_list.id
    assert item.product.id == test_product.id
    assert item.variant.id == variant.id

    # 4. Inverse relationships
    assert len(price_list.items) == 1
    assert price_list.items[0].id == item.id
    assert len(test_product.price_list_items) >= 1
    assert len(variant.price_list_items) >= 1


def test_pricing_pydantic_schemas():
    """
    Step 3 Pydantic Schema Verification:
    Verify serialization, validation, and defaults of foundational pricing schemas.
    """
    # PriceList Create
    pl_create = PriceListCreateRequest(
        name="VIP Tier List",
        currency="eur",
        is_active=True,
    )
    assert pl_create.name == "VIP Tier List"

    # PriceListItem Create
    prod_id = uuid.uuid4()
    item_create = PriceListItemCreateRequest(
        product_id=prod_id,
        price=Decimal("99.99"),
    )
    assert item_create.product_id == prod_id
    assert item_create.price == Decimal("99.99")
    assert item_create.variant_id is None

    # Pricing Resolve Request & Response
    resolve_req = PricingResolveRequest(
        product_id=prod_id,
        currency="USD",
    )
    assert resolve_req.product_id == prod_id
    assert resolve_req.currency == "USD"

    resolve_resp = PricingResolveResponse(
        product_id=prod_id,
        currency="USD",
        base_price=Decimal("100.00"),
        resolved_unit_price=Decimal("100.00"),
        cost_price=Decimal("60.00"),
        pricing_source="BASE_CATALOG",
    )
    assert resolve_resp.resolved_unit_price == Decimal("100.00")
    assert resolve_resp.pricing_source == "BASE_CATALOG"


def test_pricing_foundation_endpoints(
    client: TestClient, admin_user: User, test_user: User, test_product: Product
):
    """
    Step 4 Router Registration & Basic Flow:
    Verify endpoints under /api/v1/price-lists and /api/v1/pricing/resolve.
    """
    admin_h = _create_auth_headers(admin_user)
    rep_h = _create_auth_headers(test_user)

    # 1. Admin creates price list
    create_resp = client.post(
        "/api/v1/price-lists",
        json={"name": "Global Retail List", "currency": "USD"},
        headers=admin_h,
    )
    assert create_resp.status_code == 201
    pl_data = create_resp.json()
    assert pl_data["name"] == "Global Retail List"
    assert pl_data["currency"] == "USD"
    pl_id = pl_data["id"]

    # 2. Non-admin (SALES_REP) listing price lists -> 200
    list_resp = client.get("/api/v1/price-lists", headers=rep_h)
    assert list_resp.status_code == 200
    assert any(pl["id"] == pl_id for pl in list_resp.json())

    # 3. Non-admin creating price list -> 403
    forbidden_resp = client.post(
        "/api/v1/price-lists",
        json={"name": "Hacker List", "currency": "USD"},
        headers=rep_h,
    )
    assert forbidden_resp.status_code == 403

    # 4. Unauthenticated -> 401
    assert client.get("/api/v1/price-lists").status_code == 401
    assert client.post("/api/v1/price-lists", json={"name": "No Auth"}).status_code == 401

    # 5. Resolve pricing endpoint foundation
    resolve_resp = client.post(
        "/api/v1/pricing/resolve",
        json={"product_id": str(test_product.id), "currency": "USD"},
        headers=rep_h,
    )
    assert resolve_resp.status_code == 200
    res_data = resolve_resp.json()
    assert res_data["product_id"] == str(test_product.id)
    assert Decimal(str(res_data["resolved_unit_price"])) == test_product.base_price
    assert res_data["pricing_source"] == "BASE_CATALOG"

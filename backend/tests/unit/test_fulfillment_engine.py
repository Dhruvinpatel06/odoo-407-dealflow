"""Unit tests for the Fulfillment Allocation & Splitting Engine."""

from __future__ import annotations

import uuid
from decimal import Decimal

from app.modules.fulfillment.engine import (
    FulfillmentEngine,
    WarehouseCandidate,
    calculate_available_stock,
)


def test_calculate_available_stock():
    """Verify available stock calculations and non-negative bounds."""
    assert calculate_available_stock(Decimal("100.00"), Decimal("30.00")) == Decimal("70.00")
    assert calculate_available_stock(Decimal("50.00"), Decimal("50.00")) == Decimal("0.00")
    assert calculate_available_stock(Decimal("20.00"), Decimal("50.00")) == Decimal("0.00")


def test_engine_single_warehouse_lowest_shipping_cost():
    """Verify engine picks the single warehouse with the lowest shipping cost weight."""
    engine = FulfillmentEngine()
    product_id = uuid.uuid4()
    line_id = uuid.uuid4()

    w1_id = uuid.uuid4()
    w2_id = uuid.uuid4()

    c1 = WarehouseCandidate(
        warehouse_id=w1_id,
        name="East Coast",
        code="WH-EAST",
        shipping_cost_weight=Decimal("1.50"),
        is_active=True,
        available_stock=Decimal("100.00"),
    )
    c2 = WarehouseCandidate(
        warehouse_id=w2_id,
        name="Central Hub",
        code="WH-CENTRAL",
        shipping_cost_weight=Decimal("1.00"),
        is_active=True,
        available_stock=Decimal("100.00"),
    )

    result = engine.suggest_split(
        order_lines=[
            {"quotation_line_id": line_id, "product_id": product_id, "quantity": Decimal("20.00")}
        ],
        warehouse_candidates_by_product={product_id: [c1, c2]},
        warehouse_weights={w1_id: Decimal("1.50"), w2_id: Decimal("1.00")},
    )

    assert len(result.allocations) == 1
    assert result.allocations[0].warehouse_id == w2_id
    assert result.allocations[0].quantity_allocated == Decimal("20.00")
    assert len(result.backorders) == 0
    assert result.estimated_shipment_count == 1
    assert result.estimated_shipping_cost == Decimal("15.00")  # 15.00 * 1.00
    assert result.is_split is False


def test_engine_multi_warehouse_split():
    """Verify engine splits across multiple warehouses when no single warehouse has enough stock."""
    engine = FulfillmentEngine()
    product_id = uuid.uuid4()
    line_id = uuid.uuid4()

    w1_id = uuid.uuid4()
    w2_id = uuid.uuid4()

    c1 = WarehouseCandidate(
        warehouse_id=w1_id,
        name="Warehouse A",
        code="WH-A",
        shipping_cost_weight=Decimal("1.00"),
        is_active=True,
        available_stock=Decimal("15.00"),
    )
    c2 = WarehouseCandidate(
        warehouse_id=w2_id,
        name="Warehouse B",
        code="WH-B",
        shipping_cost_weight=Decimal("1.20"),
        is_active=True,
        available_stock=Decimal("20.00"),
    )

    # Request 25 units -> Neither has 25 alone -> Split 15 from WH-A, 10 from WH-B
    result = engine.suggest_split(
        order_lines=[
            {"quotation_line_id": line_id, "product_id": product_id, "quantity": Decimal("25.00")}
        ],
        warehouse_candidates_by_product={product_id: [c1, c2]},
        warehouse_weights={w1_id: Decimal("1.00"), w2_id: Decimal("1.20")},
    )

    assert len(result.allocations) == 2
    assert result.allocations[0].warehouse_id == w1_id
    assert result.allocations[0].quantity_allocated == Decimal("15.00")
    assert result.allocations[1].warehouse_id == w2_id
    assert result.allocations[1].quantity_allocated == Decimal("10.00")
    assert len(result.backorders) == 0
    assert result.estimated_shipment_count == 2
    assert result.is_split is True
    # Shipping: 15*1.00 + 15*1.20 = 15.00 + 18.00 = 33.00
    assert result.estimated_shipping_cost == Decimal("33.00")


def test_engine_shortage_creates_backorder():
    """Verify engine creates backorder for quantities exceeding all available stock."""
    engine = FulfillmentEngine()
    product_id = uuid.uuid4()
    line_id = uuid.uuid4()

    w1_id = uuid.uuid4()
    c1 = WarehouseCandidate(
        warehouse_id=w1_id,
        name="Warehouse Only",
        code="WH-ONLY",
        shipping_cost_weight=Decimal("1.00"),
        is_active=True,
        available_stock=Decimal("8.00"),
    )

    # Request 20 units -> Only 8 available -> 8 allocated, 12 backordered
    result = engine.suggest_split(
        order_lines=[
            {"quotation_line_id": line_id, "product_id": product_id, "quantity": Decimal("20.00")}
        ],
        warehouse_candidates_by_product={product_id: [c1]},
        warehouse_weights={w1_id: Decimal("1.00")},
    )

    assert len(result.allocations) == 1
    assert result.allocations[0].quantity_allocated == Decimal("8.00")
    assert len(result.backorders) == 1
    assert result.backorders[0].quantity_backordered == Decimal("12.00")
    assert result.estimated_shipment_count == 1


def test_engine_ignores_inactive_warehouses():
    """Verify engine does not allocate from inactive warehouses."""
    engine = FulfillmentEngine()
    product_id = uuid.uuid4()
    line_id = uuid.uuid4()

    w_inactive = uuid.uuid4()
    c_inactive = WarehouseCandidate(
        warehouse_id=w_inactive,
        name="Inactive WH",
        code="WH-INACT",
        shipping_cost_weight=Decimal("0.50"),
        is_active=False,
        available_stock=Decimal("500.00"),
    )

    result = engine.suggest_split(
        order_lines=[
            {"quotation_line_id": line_id, "product_id": product_id, "quantity": Decimal("10.00")}
        ],
        warehouse_candidates_by_product={product_id: [c_inactive]},
        warehouse_weights={w_inactive: Decimal("0.50")},
    )

    assert len(result.allocations) == 0
    assert len(result.backorders) == 1
    assert result.backorders[0].quantity_backordered == Decimal("10.00")

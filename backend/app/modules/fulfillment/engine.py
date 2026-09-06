"""Deterministic Warehouse Allocation and Splitting Engine."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List, Optional, Set

BASE_SHIPMENT_RATE = Decimal("15.00")


def calculate_available_stock(
    quantity_on_hand: Decimal, quantity_reserved: Decimal
) -> Decimal:
    """Calculate effective available stock enforcing non-negative lower bound."""
    return max(Decimal("0.00"), quantity_on_hand - quantity_reserved)


@dataclass
class WarehouseCandidate:
    """Inventory and weighting snapshot of a warehouse for allocation."""

    warehouse_id: uuid.UUID
    name: str
    code: str
    shipping_cost_weight: Decimal
    is_active: bool
    available_stock: Decimal


@dataclass
class LineAllocationProposal:
    """Proposed allocation of a quotation line to a specific warehouse."""

    quotation_line_id: uuid.UUID
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    quantity_allocated: Decimal
    estimated_shipping_cost: Decimal = Decimal("0.00")


@dataclass
class LineBackorderProposal:
    """Proposed backorder for unfulfillable quantity."""

    quotation_line_id: uuid.UUID
    product_id: uuid.UUID
    quantity_backordered: Decimal


@dataclass
class SplitSuggestionResult:
    """Aggregated proposal for an order's fulfillment split."""

    allocations: List[LineAllocationProposal] = field(default_factory=list)
    backorders: List[LineBackorderProposal] = field(default_factory=list)
    estimated_shipment_count: int = 0
    estimated_shipping_cost: Decimal = Decimal("0.00")
    is_split: bool = False


class FulfillmentEngine:
    """
    Deterministic fulfillment engine responsible for:
    - Availability checks.
    - Single-warehouse preference optimization (minimizing shipments and shipping cost).
    - Multi-warehouse splitting when stock is distributed.
    - Backorder calculation for inventory shortages.
    - Shipment count and shipping cost estimation.
    """

    def suggest_split(
        self,
        order_lines: List[dict],
        warehouse_candidates_by_product: Dict[uuid.UUID, List[WarehouseCandidate]],
        warehouse_weights: Dict[uuid.UUID, Decimal],
    ) -> SplitSuggestionResult:
        """
        Calculates optimal allocation split across active warehouses.

        :param order_lines: List of dicts containing:
               - quotation_line_id: UUID
               - product_id: UUID
               - quantity: Decimal
        :param warehouse_candidates_by_product: Mapping from product_id to list of active WarehouseCandidate
        :param warehouse_weights: Mapping from warehouse_id to shipping_cost_weight
        :return: SplitSuggestionResult with allocations and backorders.
        """
        allocations: List[LineAllocationProposal] = []
        backorders: List[LineBackorderProposal] = []
        warehouses_used: Set[uuid.UUID] = set()

        # Track remaining temporary available stock across lines to prevent double-allocating during suggestion
        temp_stock: Dict[tuple[uuid.UUID, uuid.UUID], Decimal] = {}

        for product_id, candidates in warehouse_candidates_by_product.items():
            for c in candidates:
                if c.is_active:
                    temp_stock[(c.warehouse_id, product_id)] = c.available_stock

        for line in order_lines:
            line_id = line["quotation_line_id"]
            product_id = line["product_id"]
            needed_qty = Decimal(str(line["quantity"]))

            if needed_qty <= Decimal("0.00"):
                continue

            candidates = [
                c
                for c in warehouse_candidates_by_product.get(product_id, [])
                if c.is_active
            ]

            # 1. Check for single warehouse that can fulfill full needed_qty
            # Sort candidates by:
            # - lowest shipping_cost_weight
            # - highest remaining temporary stock
            single_warehouse_match: Optional[WarehouseCandidate] = None
            eligible_singles = [
                c
                for c in candidates
                if temp_stock.get((c.warehouse_id, product_id), Decimal("0.00")) >= needed_qty
            ]

            if eligible_singles:
                eligible_singles.sort(
                    key=lambda c: (
                        c.shipping_cost_weight,
                        -temp_stock.get((c.warehouse_id, product_id), Decimal("0.00")),
                    )
                )
                single_warehouse_match = eligible_singles[0]

            if single_warehouse_match:
                # Fully satisfied by single warehouse
                wid = single_warehouse_match.warehouse_id
                temp_stock[(wid, product_id)] -= needed_qty
                warehouses_used.add(wid)

                allocations.append(
                    LineAllocationProposal(
                        quotation_line_id=line_id,
                        product_id=product_id,
                        warehouse_id=wid,
                        quantity_allocated=needed_qty,
                    )
                )
            else:
                # 2. Multi-warehouse split
                remaining_to_allocate = needed_qty

                # Sort available candidates by lowest shipping_cost_weight then highest available stock
                split_candidates = [
                    c
                    for c in candidates
                    if temp_stock.get((c.warehouse_id, product_id), Decimal("0.00")) > Decimal("0.00")
                ]
                split_candidates.sort(
                    key=lambda c: (
                        c.shipping_cost_weight,
                        -temp_stock.get((c.warehouse_id, product_id), Decimal("0.00")),
                    )
                )

                for c in split_candidates:
                    avail = temp_stock.get((c.warehouse_id, product_id), Decimal("0.00"))
                    if avail <= Decimal("0.00"):
                        continue

                    alloc_qty = min(remaining_to_allocate, avail)
                    temp_stock[(c.warehouse_id, product_id)] -= alloc_qty
                    remaining_to_allocate -= alloc_qty
                    warehouses_used.add(c.warehouse_id)

                    allocations.append(
                        LineAllocationProposal(
                            quotation_line_id=line_id,
                            product_id=product_id,
                            warehouse_id=c.warehouse_id,
                            quantity_allocated=alloc_qty,
                        )
                    )

                    if remaining_to_allocate <= Decimal("0.00"):
                        break

                # 3. If remaining quantity cannot be satisfied across all warehouses -> Backorder
                if remaining_to_allocate > Decimal("0.00"):
                    backorders.append(
                        LineBackorderProposal(
                            quotation_line_id=line_id,
                            product_id=product_id,
                            quantity_backordered=remaining_to_allocate,
                        )
                    )

        # 4. Calculate shipment count and shipping costs
        shipment_count = len(warehouses_used)
        total_shipping_cost = Decimal("0.00")

        # Each distinct warehouse shipment incurs: BASE_SHIPMENT_RATE * weight
        warehouse_cost_map: Dict[uuid.UUID, Decimal] = {}
        for wid in warehouses_used:
            weight = warehouse_weights.get(wid, Decimal("1.00"))
            w_cost = (BASE_SHIPMENT_RATE * weight).quantize(Decimal("0.01"))
            warehouse_cost_map[wid] = w_cost
            total_shipping_cost += w_cost

        # Distribute shipping cost to allocations (per warehouse)
        for alloc in allocations:
            # If multiple allocations share the warehouse, share cost proportionally or attribute per shipment
            alloc.estimated_shipping_cost = (
                warehouse_cost_map.get(alloc.warehouse_id, Decimal("0.00"))
            )

        # Check if any line was split or multiple warehouses used
        is_split = shipment_count > 1 or any(
            len([a for a in allocations if a.quotation_line_id == line["quotation_line_id"]]) > 1
            for line in order_lines
        )

        return SplitSuggestionResult(
            allocations=allocations,
            backorders=backorders,
            estimated_shipment_count=shipment_count,
            estimated_shipping_cost=total_shipping_cost.quantize(Decimal("0.01")),
            is_split=is_split,
        )


fulfillment_engine = FulfillmentEngine()

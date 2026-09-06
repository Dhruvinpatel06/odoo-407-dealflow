"""Fulfillment service layer managing warehouses, inventory, allocations, and backorders."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.common.enums import (
    BackorderStatus,
    FulfillmentAllocationStatus,
    OrderStatus,
)
from app.core.exceptions import (
    BusinessRuleViolationError,
    InsufficientInventoryError,
    InvalidStateTransitionError,
    ResourceNotFoundError,
)
from app.models.backorder import Backorder
from app.models.fulfillment_allocation import FulfillmentAllocation
from app.models.inventory import Inventory
from app.models.order import Order
from app.models.product import Product
from app.models.quotation_line import QuotationLine
from app.models.user import User
from app.models.warehouse import Warehouse
from app.modules.audit.service import audit_service
from app.modules.fulfillment.engine import (
    WarehouseCandidate,
    calculate_available_stock,
    fulfillment_engine,
)
from app.modules.fulfillment.repository import fulfillment_repository
from app.modules.fulfillment.schemas import (
    AllocationResponse,
    AllocationUpdateRequest,
    BackorderResponse,
    FulfillmentOverrideRequest,
    FulfillmentSummaryResponse,
    InventoryCreateRequest,
    InventoryResponse,
    InventoryUpdateRequest,
    ProductInventoryResponse,
    ProductInventoryWarehouseItem,
    WarehouseCreateRequest,
    WarehouseResponse,
    WarehouseUpdateRequest,
)


class FulfillmentService:
    """Coordinates inventory and fulfillment domain logic."""

    # =====================================================================
    # Warehouses
    # =====================================================================

    def list_warehouses(
        self,
        db: Session,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[WarehouseResponse]:
        """List warehouses with optional active filtering."""
        warehouses = fulfillment_repository.list_warehouses(
            db, is_active=is_active, skip=skip, limit=limit
        )
        return [WarehouseResponse.model_validate(w) for w in warehouses]

    def get_warehouse(self, db: Session, warehouse_id: uuid.UUID) -> WarehouseResponse:
        """Fetch warehouse by UUID or raise 404."""
        warehouse = fulfillment_repository.get_warehouse_by_id(db, warehouse_id)
        if not warehouse:
            raise ResourceNotFoundError("Warehouse not found")
        return WarehouseResponse.model_validate(warehouse)

    def create_warehouse(
        self,
        db: Session,
        request: WarehouseCreateRequest,
        current_user: Optional[User] = None,
    ) -> WarehouseResponse:
        """Create a new fulfillment warehouse."""
        existing = fulfillment_repository.get_warehouse_by_code(db, request.code)
        if existing:
            raise BusinessRuleViolationError(
                f"Warehouse with code '{request.code}' already exists"
            )

        warehouse = Warehouse(
            name=request.name,
            code=request.code,
            address=request.address,
            shipping_cost_weight=request.shipping_cost_weight,
            replenishment_enabled=request.replenishment_enabled,
            is_active=request.is_active,
        )
        created = fulfillment_repository.create_warehouse(db, warehouse)

        audit_service.log_event(
            db=db,
            entity_type="WAREHOUSE",
            entity_id=created.id,
            action="CREATE",
            user_id=current_user.id if current_user else None,
            new_values={
                "name": created.name,
                "code": created.code,
                "shipping_cost_weight": str(created.shipping_cost_weight),
            },
        )
        return WarehouseResponse.model_validate(created)

    def update_warehouse(
        self,
        db: Session,
        warehouse_id: uuid.UUID,
        request: WarehouseUpdateRequest,
        current_user: Optional[User] = None,
    ) -> WarehouseResponse:
        """Update warehouse fields."""
        warehouse = fulfillment_repository.get_warehouse_by_id(db, warehouse_id)
        if not warehouse:
            raise ResourceNotFoundError("Warehouse not found")

        old_values = {
            "name": warehouse.name,
            "code": warehouse.code,
            "shipping_cost_weight": str(warehouse.shipping_cost_weight),
            "is_active": warehouse.is_active,
        }

        if request.code and request.code != warehouse.code:
            existing = fulfillment_repository.get_warehouse_by_code(db, request.code)
            if existing and existing.id != warehouse_id:
                raise BusinessRuleViolationError(
                    f"Warehouse with code '{request.code}' already exists"
                )
            warehouse.code = request.code

        if request.name is not None:
            warehouse.name = request.name
        if request.address is not None:
            warehouse.address = request.address
        if request.shipping_cost_weight is not None:
            warehouse.shipping_cost_weight = request.shipping_cost_weight
        if request.replenishment_enabled is not None:
            warehouse.replenishment_enabled = request.replenishment_enabled
        if request.is_active is not None:
            warehouse.is_active = request.is_active

        updated = fulfillment_repository.update_warehouse(db, warehouse)

        audit_service.log_event(
            db=db,
            entity_type="WAREHOUSE",
            entity_id=updated.id,
            action="UPDATE",
            user_id=current_user.id if current_user else None,
            old_values=old_values,
            new_values={
                "name": updated.name,
                "code": updated.code,
                "shipping_cost_weight": str(updated.shipping_cost_weight),
                "is_active": updated.is_active,
            },
        )
        return WarehouseResponse.model_validate(updated)

    def deactivate_warehouse(
        self,
        db: Session,
        warehouse_id: uuid.UUID,
        current_user: Optional[User] = None,
    ) -> WarehouseResponse:
        """Soft-deactivate warehouse."""
        warehouse = fulfillment_repository.get_warehouse_by_id(db, warehouse_id)
        if not warehouse:
            raise ResourceNotFoundError("Warehouse not found")

        warehouse.is_active = False
        updated = fulfillment_repository.update_warehouse(db, warehouse)

        audit_service.log_event(
            db=db,
            entity_type="WAREHOUSE",
            entity_id=updated.id,
            action="DEACTIVATE",
            user_id=current_user.id if current_user else None,
            new_values={"is_active": False},
        )
        return WarehouseResponse.model_validate(updated)

    # =====================================================================
    # Inventory
    # =====================================================================

    def _to_inventory_response(self, inv: Inventory) -> InventoryResponse:
        """Map inventory model to response schema with relation details."""
        return InventoryResponse(
            id=inv.id,
            warehouse_id=inv.warehouse_id,
            product_id=inv.product_id,
            warehouse_name=inv.warehouse.name if inv.warehouse else None,
            warehouse_code=inv.warehouse.code if inv.warehouse else None,
            product_name=inv.product.name if inv.product else None,
            product_sku=inv.product.sku if inv.product else None,
            quantity_on_hand=inv.quantity_on_hand,
            quantity_reserved=inv.quantity_reserved,
            available_stock=calculate_available_stock(
                inv.quantity_on_hand, inv.quantity_reserved
            ),
            reorder_level=inv.reorder_level,
            reorder_quantity=inv.reorder_quantity,
            updated_at=inv.updated_at,
        )

    def list_inventory(
        self,
        db: Session,
        warehouse_id: Optional[uuid.UUID] = None,
        product_id: Optional[uuid.UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[InventoryResponse]:
        """List inventory records."""
        records = fulfillment_repository.list_inventory(
            db, warehouse_id=warehouse_id, product_id=product_id, skip=skip, limit=limit
        )
        return [self._to_inventory_response(r) for r in records]

    def get_inventory(self, db: Session, inventory_id: uuid.UUID) -> InventoryResponse:
        """Get inventory record by UUID."""
        inv = fulfillment_repository.get_inventory_by_id(db, inventory_id)
        if not inv:
            raise ResourceNotFoundError("Inventory record not found")
        return self._to_inventory_response(inv)

    def get_product_inventory(
        self, db: Session, product_id: uuid.UUID
    ) -> ProductInventoryResponse:
        """Get stock across all active warehouses for a given product."""
        product = db.get(Product, product_id)
        if not product:
            raise ResourceNotFoundError("Product not found")

        records = fulfillment_repository.get_inventory_for_product(
            db, product_id, active_warehouses_only=True
        )

        total_on_hand = Decimal("0.00")
        total_reserved = Decimal("0.00")
        total_available = Decimal("0.00")
        warehouse_items: List[ProductInventoryWarehouseItem] = []

        for r in records:
            avail = calculate_available_stock(r.quantity_on_hand, r.quantity_reserved)
            total_on_hand += r.quantity_on_hand
            total_reserved += r.quantity_reserved
            total_available += avail

            warehouse_items.append(
                ProductInventoryWarehouseItem(
                    warehouse_id=r.warehouse_id,
                    warehouse_name=r.warehouse.name,
                    warehouse_code=r.warehouse.code,
                    quantity_on_hand=r.quantity_on_hand,
                    quantity_reserved=r.quantity_reserved,
                    available_stock=avail,
                    reorder_level=r.reorder_level,
                    reorder_quantity=r.reorder_quantity,
                )
            )

        return ProductInventoryResponse(
            product_id=product.id,
            product_name=product.name,
            product_sku=product.sku,
            total_on_hand=total_on_hand,
            total_reserved=total_reserved,
            total_available=total_available,
            warehouses=warehouse_items,
        )

    def create_or_set_inventory(
        self,
        db: Session,
        warehouse_id: uuid.UUID,
        request: InventoryCreateRequest,
        current_user: Optional[User] = None,
    ) -> InventoryResponse:
        """Configure stock or replenishment levels for a product in a warehouse."""
        warehouse = fulfillment_repository.get_warehouse_by_id(db, warehouse_id)
        if not warehouse:
            raise ResourceNotFoundError("Warehouse not found")

        product = db.get(Product, request.product_id)
        if not product:
            raise ResourceNotFoundError("Product not found")

        inv = fulfillment_repository.get_inventory_by_warehouse_and_product(
            db, warehouse_id, request.product_id, for_update=True
        )

        if inv:
            # Update existing stock config
            inv.quantity_on_hand += request.quantity_on_hand
            inv.reorder_level = request.reorder_level
            inv.reorder_quantity = request.reorder_quantity
            updated = fulfillment_repository.update_inventory(db, inv)
            action = "UPDATE"
        else:
            inv = Inventory(
                warehouse_id=warehouse_id,
                product_id=request.product_id,
                quantity_on_hand=request.quantity_on_hand,
                quantity_reserved=Decimal("0.00"),
                reorder_level=request.reorder_level,
                reorder_quantity=request.reorder_quantity,
            )
            updated = fulfillment_repository.create_inventory(db, inv)
            action = "CREATE"

        audit_service.log_event(
            db=db,
            entity_type="INVENTORY",
            entity_id=updated.id,
            action=action,
            user_id=current_user.id if current_user else None,
            new_values={
                "warehouse_id": str(warehouse_id),
                "product_id": str(request.product_id),
                "quantity_on_hand": str(updated.quantity_on_hand),
            },
        )
        return self._to_inventory_response(updated)

    def update_inventory(
        self,
        db: Session,
        inventory_id: uuid.UUID,
        request: InventoryUpdateRequest,
        current_user: Optional[User] = None,
    ) -> InventoryResponse:
        """Update inventory stock quantities or replenishment parameters."""
        inv = fulfillment_repository.get_inventory_by_id(db, inventory_id)
        if not inv:
            raise ResourceNotFoundError("Inventory record not found")

        new_on_hand = (
            request.quantity_on_hand
            if request.quantity_on_hand is not None
            else inv.quantity_on_hand
        )
        new_reserved = (
            request.quantity_reserved
            if request.quantity_reserved is not None
            else inv.quantity_reserved
        )

        if new_reserved > new_on_hand:
            raise BusinessRuleViolationError(
                f"Reserved quantity ({new_reserved}) cannot exceed on-hand quantity ({new_on_hand})"
            )

        inv.quantity_on_hand = new_on_hand
        inv.quantity_reserved = new_reserved

        if request.reorder_level is not None:
            inv.reorder_level = request.reorder_level
        if request.reorder_quantity is not None:
            inv.reorder_quantity = request.reorder_quantity

        updated = fulfillment_repository.update_inventory(db, inv)

        audit_service.log_event(
            db=db,
            entity_type="INVENTORY",
            entity_id=updated.id,
            action="UPDATE",
            user_id=current_user.id if current_user else None,
            new_values={
                "quantity_on_hand": str(updated.quantity_on_hand),
                "quantity_reserved": str(updated.quantity_reserved),
            },
        )
        return self._to_inventory_response(updated)

    # =====================================================================
    # Fulfillment
    # =====================================================================

    def _to_allocation_response(
        self, alloc: FulfillmentAllocation
    ) -> AllocationResponse:
        """Map allocation model to response schema."""
        product_id = (
            alloc.quotation_line.product_id if alloc.quotation_line else None
        )
        product_name = (
            alloc.quotation_line.product.name
            if alloc.quotation_line and alloc.quotation_line.product
            else None
        )

        return AllocationResponse(
            id=alloc.id,
            order_id=alloc.order_id,
            quotation_line_id=alloc.quotation_line_id,
            warehouse_id=alloc.warehouse_id,
            warehouse_name=alloc.warehouse.name if alloc.warehouse else None,
            warehouse_code=alloc.warehouse.code if alloc.warehouse else None,
            product_id=product_id,
            product_name=product_name,
            quantity_allocated=alloc.quantity_allocated,
            quantity_fulfilled=alloc.quantity_fulfilled,
            estimated_shipping_cost=alloc.estimated_shipping_cost,
            is_suggested=alloc.is_suggested,
            is_manual_override=alloc.is_manual_override,
            status=alloc.status,
            created_at=alloc.created_at,
            updated_at=alloc.updated_at,
        )

    def _to_backorder_response(self, bo: Backorder) -> BackorderResponse:
        """Map backorder model to response schema."""
        product_id = bo.quotation_line.product_id if bo.quotation_line else None
        product_name = (
            bo.quotation_line.product.name
            if bo.quotation_line and bo.quotation_line.product
            else None
        )

        return BackorderResponse(
            id=bo.id,
            order_id=bo.order_id,
            quotation_line_id=bo.quotation_line_id,
            product_id=product_id,
            product_name=product_name,
            quantity_backordered=bo.quantity_backordered,
            quantity_remaining=bo.quantity_remaining,
            status=bo.status,
            consolidation_requested=bo.consolidation_requested,
            created_at=bo.created_at,
            updated_at=bo.updated_at,
        )

    def get_order_fulfillment(
        self, db: Session, order_id: uuid.UUID
    ) -> FulfillmentSummaryResponse:
        """Return comprehensive order fulfillment view."""
        order = db.get(Order, order_id)
        if not order:
            raise ResourceNotFoundError("Order not found")

        allocations = fulfillment_repository.list_allocations_for_order(db, order_id)
        backorders = fulfillment_repository.get_backorders_for_order(db, order_id)

        # Compute totals
        quotation_lines = (
            order.quotation.lines
            if order.quotation and order.quotation.lines
            else []
        )
        total_required = sum(
            (Decimal(str(line.quantity)) for line in quotation_lines),
            Decimal("0.00"),
        )
        total_allocated = sum(
            (a.quantity_allocated for a in allocations if a.status != FulfillmentAllocationStatus.CANCELLED),
            Decimal("0.00"),
        )
        total_fulfilled = sum(
            (a.quantity_fulfilled for a in allocations),
            Decimal("0.00"),
        )
        total_backordered = sum(
            (b.quantity_remaining for b in backorders if b.status in (BackorderStatus.OPEN, BackorderStatus.CONSOLIDATION_AVAILABLE)),
            Decimal("0.00"),
        )

        distinct_warehouses = {
            a.warehouse_id
            for a in allocations
            if a.status != FulfillmentAllocationStatus.CANCELLED and a.quantity_allocated > 0
        }
        shipment_count = len(distinct_warehouses)
        shipping_cost = sum(
            (a.estimated_shipping_cost for a in allocations if a.status != FulfillmentAllocationStatus.CANCELLED),
            Decimal("0.00"),
        )
        is_split = shipment_count > 1

        return FulfillmentSummaryResponse(
            order_id=order.id,
            order_number=order.order_number,
            order_status=order.status,
            allocations=[self._to_allocation_response(a) for a in allocations],
            backorders=[self._to_backorder_response(b) for b in backorders],
            total_quantity_required=total_required,
            total_quantity_allocated=total_allocated,
            total_quantity_fulfilled=total_fulfilled,
            total_quantity_backordered=total_backordered,
            estimated_shipment_count=shipment_count,
            estimated_shipping_cost=shipping_cost,
            is_split=is_split,
        )

    def suggest_fulfillment(
        self, db: Session, order_id: uuid.UUID
    ) -> FulfillmentSummaryResponse:
        """
        Calculate and persist recommended warehouse split for an order.
        Overwrites any previous SUGGESTED allocations.
        """
        order = db.get(Order, order_id)
        if not order:
            raise ResourceNotFoundError("Order not found")

        if order.status == OrderStatus.CANCELLED:
            raise InvalidStateTransitionError("Cannot suggest fulfillment for a cancelled order")

        quotation_lines = (
            order.quotation.lines
            if order.quotation and order.quotation.lines
            else []
        )
        if not quotation_lines:
            raise BusinessRuleViolationError("Order has no commercial lines to fulfill")

        # Prepare order lines dict
        order_lines_data = [
            {
                "quotation_line_id": line.id,
                "product_id": line.product_id,
                "quantity": line.quantity,
            }
            for line in quotation_lines
        ]

        # Gather candidates by product
        candidates_by_product: Dict[uuid.UUID, List[WarehouseCandidate]] = {}
        warehouse_weights: Dict[uuid.UUID, Decimal] = {}

        for line in quotation_lines:
            product_id = line.product_id
            if product_id not in candidates_by_product:
                inv_records = fulfillment_repository.get_inventory_for_product(
                    db, product_id, active_warehouses_only=True
                )
                candidates = []
                for inv in inv_records:
                    warehouse_weights[inv.warehouse_id] = inv.warehouse.shipping_cost_weight
                    avail = calculate_available_stock(
                        inv.quantity_on_hand, inv.quantity_reserved
                    )
                    candidates.append(
                        WarehouseCandidate(
                            warehouse_id=inv.warehouse_id,
                            name=inv.warehouse.name,
                            code=inv.warehouse.code,
                            shipping_cost_weight=inv.warehouse.shipping_cost_weight,
                            is_active=inv.warehouse.is_active,
                            available_stock=avail,
                        )
                    )
                candidates_by_product[product_id] = candidates

        # Run deterministic engine
        suggestion = fulfillment_engine.suggest_split(
            order_lines=order_lines_data,
            warehouse_candidates_by_product=candidates_by_product,
            warehouse_weights=warehouse_weights,
        )

        # Clear prior SUGGESTED allocations
        fulfillment_repository.delete_suggested_allocations(db, order_id)

        # Create new SUGGESTED allocation models
        allocation_models = []
        for alloc_prop in suggestion.allocations:
            alloc_model = FulfillmentAllocation(
                order_id=order_id,
                quotation_line_id=alloc_prop.quotation_line_id,
                warehouse_id=alloc_prop.warehouse_id,
                quantity_allocated=alloc_prop.quantity_allocated,
                quantity_fulfilled=Decimal("0.00"),
                estimated_shipping_cost=alloc_prop.estimated_shipping_cost,
                is_suggested=True,
                is_manual_override=False,
                status=FulfillmentAllocationStatus.SUGGESTED,
            )
            allocation_models.append(alloc_model)

        if allocation_models:
            fulfillment_repository.create_allocations(db, allocation_models)
        db.commit()

        return self.get_order_fulfillment(db, order_id)

    def accept_fulfillment(
        self,
        db: Session,
        order_id: uuid.UUID,
        current_user: Optional[User] = None,
    ) -> FulfillmentSummaryResponse:
        """
        Accept suggested warehouse allocations:
        - Re-verifies live inventory.
        - Reserves inventory stock.
        - Commits allocations to ACCEPTED status.
        - Creates backorders for any remaining unallocated quantities.
        - Updates order status to FULFILLMENT or PARTIALLY_FULFILLED.
        """
        order = db.get(Order, order_id)
        if not order:
            raise ResourceNotFoundError("Order not found")

        if order.status not in (OrderStatus.CONFIRMED, OrderStatus.FULFILLMENT, OrderStatus.PARTIALLY_FULFILLED):
            raise InvalidStateTransitionError(
                f"Order in status {order.status.value} cannot accept fulfillment"
            )

        suggested_allocations = [
            a
            for a in fulfillment_repository.list_allocations_for_order(db, order_id)
            if a.status == FulfillmentAllocationStatus.SUGGESTED
        ]

        if not suggested_allocations:
            # Try auto-suggesting if none present
            self.suggest_fulfillment(db, order_id)
            suggested_allocations = [
                a
                for a in fulfillment_repository.list_allocations_for_order(db, order_id)
                if a.status == FulfillmentAllocationStatus.SUGGESTED
            ]

        # Verify stock and reserve
        for alloc in suggested_allocations:
            quotation_line = db.get(QuotationLine, alloc.quotation_line_id)
            if not quotation_line:
                continue

            inv = fulfillment_repository.get_inventory_by_warehouse_and_product(
                db, alloc.warehouse_id, quotation_line.product_id, for_update=True
            )
            if not inv:
                raise InsufficientInventoryError(
                    f"No inventory record found in warehouse for product {quotation_line.product_id}"
                )

            avail = calculate_available_stock(inv.quantity_on_hand, inv.quantity_reserved)
            if avail < alloc.quantity_allocated:
                raise InsufficientInventoryError(
                    f"Stock shortage: only {avail} available in warehouse for allocation of {alloc.quantity_allocated}"
                )

            # Reserve stock
            inv.quantity_reserved += alloc.quantity_allocated
            alloc.status = FulfillmentAllocationStatus.ACCEPTED
            alloc.is_suggested = True
            db.add(inv)
            db.add(alloc)

        # Clear old open backorders to avoid duplicates
        fulfillment_repository.delete_open_backorders(db, order_id)

        # Check line totals vs allocated to generate backorders
        quotation_lines = order.quotation.lines if order.quotation else []
        new_backorders = []
        has_backorder = False

        for line in quotation_lines:
            line_allocated = sum(
                (
                    a.quantity_allocated
                    for a in suggested_allocations
                    if a.quotation_line_id == line.id
                ),
                Decimal("0.00"),
            )
            if line_allocated < line.quantity:
                shortage = line.quantity - line_allocated
                has_backorder = True
                bo = Backorder(
                    order_id=order_id,
                    quotation_line_id=line.id,
                    quantity_backordered=shortage,
                    quantity_remaining=shortage,
                    status=BackorderStatus.OPEN,
                    consolidation_requested=False,
                )
                new_backorders.append(bo)

        if new_backorders:
            fulfillment_repository.create_backorders(db, new_backorders)

        # Update order status
        if has_backorder:
            order.status = OrderStatus.PARTIALLY_FULFILLED
        else:
            order.status = OrderStatus.FULFILLMENT
        db.add(order)

        db.commit()

        audit_service.log_event(
            db=db,
            entity_type="ORDER",
            entity_id=order.id,
            action="FULFILLMENT_ACCEPT",
            user_id=current_user.id if current_user else None,
            new_values={
                "order_status": order.status.value,
                "allocations_count": len(suggested_allocations),
                "backorders_count": len(new_backorders),
            },
        )

        return self.get_order_fulfillment(db, order_id)

    def override_fulfillment(
        self,
        db: Session,
        order_id: uuid.UUID,
        request: FulfillmentOverrideRequest,
        current_user: Optional[User] = None,
    ) -> FulfillmentSummaryResponse:
        """
        Manually override order fulfillment allocations:
        - Releases previous reservations.
        - Validates stock in requested warehouses.
        - Creates accepted manual allocations.
        - Computes backorders if requested quantities are less than line quantities.
        """
        order = db.get(Order, order_id)
        if not order:
            raise ResourceNotFoundError("Order not found")

        if order.status not in (OrderStatus.CONFIRMED, OrderStatus.FULFILLMENT, OrderStatus.PARTIALLY_FULFILLED):
            raise InvalidStateTransitionError(
                f"Order in status {order.status.value} cannot accept manual fulfillment override"
            )

        existing_allocations = fulfillment_repository.list_allocations_for_order(db, order_id)

        # Release existing reservations
        for alloc in existing_allocations:
            if alloc.status == FulfillmentAllocationStatus.ACCEPTED and alloc.quantity_allocated > 0:
                qline = db.get(QuotationLine, alloc.quotation_line_id)
                if qline:
                    inv = fulfillment_repository.get_inventory_by_warehouse_and_product(
                        db, alloc.warehouse_id, qline.product_id, for_update=True
                    )
                    if inv:
                        inv.quantity_reserved = max(
                            Decimal("0.00"), inv.quantity_reserved - alloc.quantity_allocated
                        )
                        db.add(inv)
            db.delete(alloc)

        # Clear existing open backorders
        fulfillment_repository.delete_open_backorders(db, order_id)
        db.flush()

        # Validate lines and apply requested allocations
        new_allocations = []
        for item in request.allocations:
            qline = db.get(QuotationLine, item.quotation_line_id)
            if not qline or qline.quotation_id != order.quotation_id:
                raise BusinessRuleViolationError(
                    f"Quotation line {item.quotation_line_id} does not belong to this order"
                )

            warehouse = fulfillment_repository.get_warehouse_by_id(db, item.warehouse_id)
            if not warehouse or not warehouse.is_active:
                raise BusinessRuleViolationError(
                    f"Warehouse {item.warehouse_id} is inactive or does not exist"
                )

            inv = fulfillment_repository.get_inventory_by_warehouse_and_product(
                db, item.warehouse_id, qline.product_id, for_update=True
            )
            if not inv:
                raise InsufficientInventoryError(
                    f"No inventory record found in warehouse {warehouse.name} for product {qline.product_id}"
                )

            avail = calculate_available_stock(inv.quantity_on_hand, inv.quantity_reserved)
            if avail < item.quantity_allocated:
                raise InsufficientInventoryError(
                    f"Insufficient stock in {warehouse.name}: available {avail}, requested {item.quantity_allocated}"
                )

            # Reserve stock
            inv.quantity_reserved += item.quantity_allocated
            db.add(inv)

            shipping_cost = (Decimal("15.00") * warehouse.shipping_cost_weight).quantize(Decimal("0.01"))

            alloc = FulfillmentAllocation(
                order_id=order_id,
                quotation_line_id=item.quotation_line_id,
                warehouse_id=item.warehouse_id,
                quantity_allocated=item.quantity_allocated,
                quantity_fulfilled=Decimal("0.00"),
                estimated_shipping_cost=shipping_cost,
                is_suggested=False,
                is_manual_override=True,
                status=FulfillmentAllocationStatus.ACCEPTED,
            )
            new_allocations.append(alloc)

        fulfillment_repository.create_allocations(db, new_allocations)

        # Check for backorders
        quotation_lines = order.quotation.lines if order.quotation else []
        new_backorders = []
        has_backorder = False

        for line in quotation_lines:
            line_allocated = sum(
                (
                    item.quantity_allocated
                    for item in request.allocations
                    if item.quotation_line_id == line.id
                ),
                Decimal("0.00"),
            )
            if line_allocated < line.quantity:
                has_backorder = True
                shortage = line.quantity - line_allocated
                bo = Backorder(
                    order_id=order_id,
                    quotation_line_id=line.id,
                    quantity_backordered=shortage,
                    quantity_remaining=shortage,
                    status=BackorderStatus.OPEN,
                    consolidation_requested=False,
                )
                new_backorders.append(bo)

        if new_backorders:
            fulfillment_repository.create_backorders(db, new_backorders)

        if has_backorder:
            order.status = OrderStatus.PARTIALLY_FULFILLED
        else:
            order.status = OrderStatus.FULFILLMENT
        db.add(order)

        db.commit()

        audit_service.log_event(
            db=db,
            entity_type="ORDER",
            entity_id=order.id,
            action="FULFILLMENT_OVERRIDE",
            user_id=current_user.id if current_user else None,
            reason="Manual warehouse allocation override",
            new_values={
                "order_status": order.status.value,
                "allocations_count": len(new_allocations),
            },
        )

        return self.get_order_fulfillment(db, order_id)

    def update_single_allocation(
        self,
        db: Session,
        order_id: uuid.UUID,
        allocation_id: uuid.UUID,
        request: AllocationUpdateRequest,
        current_user: Optional[User] = None,
    ) -> AllocationResponse:
        """Adjust an existing allocation's warehouse or quantity."""
        alloc = fulfillment_repository.get_allocation_by_id(db, allocation_id)
        if not alloc or alloc.order_id != order_id:
            raise ResourceNotFoundError("Allocation not found for this order")

        if alloc.status == FulfillmentAllocationStatus.FULFILLED:
            raise InvalidStateTransitionError("Cannot update an already fulfilled allocation")

        quotation_line = db.get(QuotationLine, alloc.quotation_line_id)
        product_id = quotation_line.product_id

        # If changing warehouse
        target_warehouse_id = request.warehouse_id or alloc.warehouse_id
        target_quantity = (
            request.quantity_allocated
            if request.quantity_allocated is not None
            else alloc.quantity_allocated
        )

        # Release old reservation if currently accepted
        if alloc.status == FulfillmentAllocationStatus.ACCEPTED:
            old_inv = fulfillment_repository.get_inventory_by_warehouse_and_product(
                db, alloc.warehouse_id, product_id, for_update=True
            )
            if old_inv:
                old_inv.quantity_reserved = max(
                    Decimal("0.00"), old_inv.quantity_reserved - alloc.quantity_allocated
                )
                db.add(old_inv)

        # Check new inventory
        new_inv = fulfillment_repository.get_inventory_by_warehouse_and_product(
            db, target_warehouse_id, product_id, for_update=True
        )
        if not new_inv:
            raise InsufficientInventoryError("No stock record in target warehouse")

        if alloc.status == FulfillmentAllocationStatus.ACCEPTED:
            avail = calculate_available_stock(new_inv.quantity_on_hand, new_inv.quantity_reserved)
            if avail < target_quantity:
                raise InsufficientInventoryError("Insufficient stock in target warehouse")
            new_inv.quantity_reserved += target_quantity
            db.add(new_inv)

        alloc.warehouse_id = target_warehouse_id
        alloc.quantity_allocated = target_quantity
        alloc.is_manual_override = True

        wh = fulfillment_repository.get_warehouse_by_id(db, target_warehouse_id)
        if wh:
            alloc.estimated_shipping_cost = (
                Decimal("15.00") * wh.shipping_cost_weight
            ).quantize(Decimal("0.01"))

        updated = fulfillment_repository.update_allocation(db, alloc)
        db.commit()

        audit_service.log_event(
            db=db,
            entity_type="ORDER",
            entity_id=order_id,
            action="ALLOCATION_UPDATE",
            user_id=current_user.id if current_user else None,
            new_values={
                "allocation_id": str(allocation_id),
                "warehouse_id": str(target_warehouse_id),
                "quantity_allocated": str(target_quantity),
            },
        )
        return self._to_allocation_response(updated)

    def complete_fulfillment(
        self,
        db: Session,
        order_id: uuid.UUID,
        current_user: Optional[User] = None,
    ) -> FulfillmentSummaryResponse:
        """
        Fulfill accepted allocations:
        - Deducts physical on-hand stock and reserved stock.
        - Sets allocation status = FULFILLED.
        - Updates order status = FULFILLED (if no remaining backorders) or PARTIALLY_FULFILLED.
        """
        order = db.get(Order, order_id)
        if not order:
            raise ResourceNotFoundError("Order not found")

        if order.status not in (OrderStatus.FULFILLMENT, OrderStatus.PARTIALLY_FULFILLED):
            raise InvalidStateTransitionError(
                f"Order in status {order.status.value} cannot complete fulfillment"
            )

        allocations = fulfillment_repository.list_allocations_for_order(db, order_id)
        accepted_allocations = [
            a for a in allocations if a.status == FulfillmentAllocationStatus.ACCEPTED
        ]

        if not accepted_allocations:
            raise BusinessRuleViolationError("No accepted allocations available to fulfill")

        for alloc in accepted_allocations:
            qline = db.get(QuotationLine, alloc.quotation_line_id)
            if not qline:
                continue

            inv = fulfillment_repository.get_inventory_by_warehouse_and_product(
                db, alloc.warehouse_id, qline.product_id, for_update=True
            )
            if not inv:
                raise ResourceNotFoundError("Inventory record not found during fulfillment")

            # Physical stock deduction
            inv.quantity_on_hand = max(
                Decimal("0.00"), inv.quantity_on_hand - alloc.quantity_allocated
            )
            inv.quantity_reserved = max(
                Decimal("0.00"), inv.quantity_reserved - alloc.quantity_allocated
            )
            alloc.quantity_fulfilled = alloc.quantity_allocated
            alloc.status = FulfillmentAllocationStatus.FULFILLED

            db.add(inv)
            db.add(alloc)

        # Check remaining open backorders
        backorders = fulfillment_repository.get_backorders_for_order(db, order_id)
        has_open_backorders = any(
            b.status in (BackorderStatus.OPEN, BackorderStatus.CONSOLIDATION_AVAILABLE)
            and b.quantity_remaining > 0
            for b in backorders
        )

        if has_open_backorders:
            order.status = OrderStatus.PARTIALLY_FULFILLED
        else:
            order.status = OrderStatus.FULFILLED

        db.add(order)
        db.commit()

        audit_service.log_event(
            db=db,
            entity_type="ORDER",
            entity_id=order.id,
            action="FULFILLMENT_COMPLETE",
            user_id=current_user.id if current_user else None,
            new_values={
                "order_status": order.status.value,
                "fulfilled_allocations": len(accepted_allocations),
            },
        )

        return self.get_order_fulfillment(db, order_id)

    # =====================================================================
    # Backorders
    # =====================================================================

    def list_backorders(
        self,
        db: Session,
        status: Optional[BackorderStatus] = None,
        order_id: Optional[uuid.UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[BackorderResponse]:
        """List backorders with optional filters."""
        bos = fulfillment_repository.list_backorders(
            db, status=status, order_id=order_id, skip=skip, limit=limit
        )
        return [self._to_backorder_response(b) for b in bos]

    def get_backorder(self, db: Session, backorder_id: uuid.UUID) -> BackorderResponse:
        """Get backorder by UUID."""
        bo = fulfillment_repository.get_backorder_by_id(db, backorder_id)
        if not bo:
            raise ResourceNotFoundError("Backorder not found")
        return self._to_backorder_response(bo)

    def get_order_backorders(
        self, db: Session, order_id: uuid.UUID
    ) -> List[BackorderResponse]:
        """Get all backorders for a specific order."""
        bos = fulfillment_repository.get_backorders_for_order(db, order_id)
        return [self._to_backorder_response(b) for b in bos]

    def consolidate_backorder(
        self,
        db: Session,
        backorder_id: uuid.UUID,
        current_user: Optional[User] = None,
    ) -> BackorderResponse:
        """
        Consolidate newly available inventory for a backorder:
        - Searches for stock in active warehouses.
        - Allocates available stock up to backorder.quantity_remaining.
        - Creates accepted fulfillment allocation.
        - Decrements quantity_remaining.
        - If completely fulfilled, status -> CONSOLIDATED.
        """
        bo = fulfillment_repository.get_backorder_by_id(db, backorder_id)
        if not bo:
            raise ResourceNotFoundError("Backorder not found")

        if bo.status not in (BackorderStatus.OPEN, BackorderStatus.CONSOLIDATION_AVAILABLE):
            raise InvalidStateTransitionError(
                f"Backorder in status {bo.status.value} cannot be consolidated"
            )

        if bo.quantity_remaining <= Decimal("0.00"):
            bo.status = BackorderStatus.CONSOLIDATED
            db.add(bo)
            db.commit()
            return self._to_backorder_response(bo)

        qline = bo.quotation_line
        product_id = qline.product_id

        # Find active warehouses with available stock for product
        inv_records = fulfillment_repository.get_inventory_for_product(
            db, product_id, active_warehouses_only=True
        )

        candidate_inv: Optional[Inventory] = None
        candidate_avail: Decimal = Decimal("0.00")

        for inv in inv_records:
            avail = calculate_available_stock(inv.quantity_on_hand, inv.quantity_reserved)
            if avail > candidate_avail:
                candidate_inv = inv
                candidate_avail = avail

        if not candidate_inv or candidate_avail <= Decimal("0.00"):
            raise InsufficientInventoryError(
                "No stock available across warehouses to consolidate this backorder"
            )

        # Lock inventory row
        locked_inv = fulfillment_repository.get_inventory_by_warehouse_and_product(
            db, candidate_inv.warehouse_id, product_id, for_update=True
        )
        avail = calculate_available_stock(locked_inv.quantity_on_hand, locked_inv.quantity_reserved)
        if avail <= Decimal("0.00"):
            raise InsufficientInventoryError("Stock is no longer available")

        allocated_qty = min(bo.quantity_remaining, avail)
        locked_inv.quantity_reserved += allocated_qty
        db.add(locked_inv)

        # Create new accepted allocation for this consolidation
        wh = candidate_inv.warehouse
        shipping_cost = (Decimal("15.00") * wh.shipping_cost_weight).quantize(Decimal("0.01"))

        new_alloc = FulfillmentAllocation(
            order_id=bo.order_id,
            quotation_line_id=bo.quotation_line_id,
            warehouse_id=candidate_inv.warehouse_id,
            quantity_allocated=allocated_qty,
            quantity_fulfilled=Decimal("0.00"),
            estimated_shipping_cost=shipping_cost,
            is_suggested=False,
            is_manual_override=False,
            status=FulfillmentAllocationStatus.ACCEPTED,
        )
        db.add(new_alloc)

        bo.quantity_remaining -= allocated_qty
        bo.consolidation_requested = True

        if bo.quantity_remaining <= Decimal("0.00"):
            bo.status = BackorderStatus.CONSOLIDATED
        else:
            bo.status = BackorderStatus.CONSOLIDATION_AVAILABLE

        db.add(bo)
        db.commit()

        audit_service.log_event(
            db=db,
            entity_type="BACKORDER",
            entity_id=bo.id,
            action="CONSOLIDATE",
            user_id=current_user.id if current_user else None,
            new_values={
                "allocated_quantity": str(allocated_qty),
                "remaining_quantity": str(bo.quantity_remaining),
                "status": bo.status.value,
            },
        )

        return self._to_backorder_response(bo)

    def cancel_backorder(
        self,
        db: Session,
        backorder_id: uuid.UUID,
        current_user: Optional[User] = None,
    ) -> BackorderResponse:
        """Cancel an open backorder."""
        bo = fulfillment_repository.get_backorder_by_id(db, backorder_id)
        if not bo:
            raise ResourceNotFoundError("Backorder not found")

        if bo.status not in (BackorderStatus.OPEN, BackorderStatus.CONSOLIDATION_AVAILABLE):
            raise InvalidStateTransitionError(
                f"Backorder in status {bo.status.value} cannot be cancelled"
            )

        bo.status = BackorderStatus.CANCELLED
        updated = fulfillment_repository.update_backorder(db, bo)

        audit_service.log_event(
            db=db,
            entity_type="BACKORDER",
            entity_id=updated.id,
            action="CANCEL",
            user_id=current_user.id if current_user else None,
            new_values={"status": BackorderStatus.CANCELLED.value},
        )
        return self._to_backorder_response(updated)


fulfillment_service = FulfillmentService()

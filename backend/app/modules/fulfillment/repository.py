"""Fulfillment repository layer for database persistence."""

from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.common.enums import BackorderStatus, FulfillmentAllocationStatus
from app.models.backorder import Backorder
from app.models.fulfillment_allocation import FulfillmentAllocation
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.quotation_line import QuotationLine
from app.models.warehouse import Warehouse


class FulfillmentRepository:
    """Handles data persistence for Warehouses, Inventory, Allocations, and Backorders."""

    # =====================================================================
    # Warehouses
    # =====================================================================

    def list_warehouses(
        self,
        db: Session,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Warehouse]:
        """Query warehouses with optional active filter and pagination."""
        stmt = select(Warehouse)
        if is_active is not None:
            stmt = stmt.where(Warehouse.is_active == is_active)
        stmt = stmt.order_by(Warehouse.name.asc()).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    def get_warehouse_by_id(
        self, db: Session, warehouse_id: uuid.UUID
    ) -> Optional[Warehouse]:
        """Fetch warehouse by primary key UUID."""
        return db.get(Warehouse, warehouse_id)

    def get_warehouse_by_code(
        self, db: Session, code: str
    ) -> Optional[Warehouse]:
        """Fetch warehouse by unique code."""
        stmt = select(Warehouse).where(Warehouse.code == code)
        return db.scalars(stmt).first()

    def create_warehouse(self, db: Session, warehouse: Warehouse) -> Warehouse:
        """Persist a new warehouse."""
        db.add(warehouse)
        db.commit()
        db.refresh(warehouse)
        return warehouse

    def update_warehouse(self, db: Session, warehouse: Warehouse) -> Warehouse:
        """Commit updates to an existing warehouse."""
        db.add(warehouse)
        db.commit()
        db.refresh(warehouse)
        return warehouse

    # =====================================================================
    # Inventory
    # =====================================================================

    def list_inventory(
        self,
        db: Session,
        warehouse_id: Optional[uuid.UUID] = None,
        product_id: Optional[uuid.UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Inventory]:
        """Query inventory records with optional warehouse and product filters."""
        stmt = (
            select(Inventory)
            .options(
                joinedload(Inventory.warehouse),
                joinedload(Inventory.product),
            )
        )
        if warehouse_id:
            stmt = stmt.where(Inventory.warehouse_id == warehouse_id)
        if product_id:
            stmt = stmt.where(Inventory.product_id == product_id)
        stmt = stmt.order_by(Inventory.updated_at.desc()).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    def get_inventory_by_id(
        self, db: Session, inventory_id: uuid.UUID
    ) -> Optional[Inventory]:
        """Fetch single inventory record by UUID with relations loaded."""
        stmt = (
            select(Inventory)
            .options(
                joinedload(Inventory.warehouse),
                joinedload(Inventory.product),
            )
            .where(Inventory.id == inventory_id)
        )
        return db.scalars(stmt).first()

    def get_inventory_by_warehouse_and_product(
        self,
        db: Session,
        warehouse_id: uuid.UUID,
        product_id: uuid.UUID,
        for_update: bool = False,
    ) -> Optional[Inventory]:
        """Fetch inventory record by warehouse and product combination, with optional row locking."""
        stmt = (
            select(Inventory)
            .options(
                joinedload(Inventory.warehouse),
                joinedload(Inventory.product),
            )
            .where(
                Inventory.warehouse_id == warehouse_id,
                Inventory.product_id == product_id,
            )
        )
        if for_update:
            stmt = stmt.with_for_update()
        return db.scalars(stmt).first()

    def get_inventory_for_product(
        self,
        db: Session,
        product_id: uuid.UUID,
        active_warehouses_only: bool = True,
    ) -> List[Inventory]:
        """Query all inventory records for a product across warehouses."""
        stmt = (
            select(Inventory)
            .join(Warehouse, Inventory.warehouse_id == Warehouse.id)
            .options(
                joinedload(Inventory.warehouse),
                joinedload(Inventory.product),
            )
            .where(Inventory.product_id == product_id)
        )
        if active_warehouses_only:
            stmt = stmt.where(Warehouse.is_active == True)
        stmt = stmt.order_by(Warehouse.shipping_cost_weight.asc())
        return list(db.scalars(stmt).all())

    def create_inventory(self, db: Session, inventory: Inventory) -> Inventory:
        """Persist new inventory record."""
        db.add(inventory)
        db.commit()
        db.refresh(inventory)
        return inventory

    def update_inventory(self, db: Session, inventory: Inventory) -> Inventory:
        """Commit updates to an existing inventory record."""
        db.add(inventory)
        db.commit()
        db.refresh(inventory)
        return inventory

    # =====================================================================
    # Allocations
    # =====================================================================

    def list_allocations_for_order(
        self, db: Session, order_id: uuid.UUID
    ) -> List[FulfillmentAllocation]:
        """Fetch all fulfillment allocations for an order with relations eagerly loaded."""
        stmt = (
            select(FulfillmentAllocation)
            .options(
                joinedload(FulfillmentAllocation.warehouse),
                joinedload(FulfillmentAllocation.quotation_line).joinedload(QuotationLine.product),
            )
            .where(FulfillmentAllocation.order_id == order_id)
            .order_by(FulfillmentAllocation.created_at.asc())
        )
        return list(db.scalars(stmt).all())

    def get_allocation_by_id(
        self, db: Session, allocation_id: uuid.UUID
    ) -> Optional[FulfillmentAllocation]:
        """Fetch allocation by UUID."""
        stmt = (
            select(FulfillmentAllocation)
            .options(
                joinedload(FulfillmentAllocation.warehouse),
                joinedload(FulfillmentAllocation.quotation_line).joinedload(QuotationLine.product),
                joinedload(FulfillmentAllocation.order),
            )
            .where(FulfillmentAllocation.id == allocation_id)
        )
        return db.scalars(stmt).first()

    def delete_suggested_allocations(self, db: Session, order_id: uuid.UUID) -> int:
        """Delete prior allocations in SUGGESTED state when recalculating split."""
        stmt = (
            select(FulfillmentAllocation)
            .where(
                FulfillmentAllocation.order_id == order_id,
                FulfillmentAllocation.status == FulfillmentAllocationStatus.SUGGESTED,
            )
        )
        suggested = list(db.scalars(stmt).all())
        for alloc in suggested:
            db.delete(alloc)
        db.flush()
        return len(suggested)

    def create_allocations(
        self, db: Session, allocations: List[FulfillmentAllocation]
    ) -> List[FulfillmentAllocation]:
        """Bulk add allocations."""
        db.add_all(allocations)
        db.flush()
        return allocations

    def update_allocation(
        self, db: Session, allocation: FulfillmentAllocation
    ) -> FulfillmentAllocation:
        """Commit updates to an allocation."""
        db.add(allocation)
        db.commit()
        db.refresh(allocation)
        return allocation

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
    ) -> List[Backorder]:
        """List backorders with optional status and order filters."""
        stmt = (
            select(Backorder)
            .options(
                joinedload(Backorder.order),
                joinedload(Backorder.quotation_line).joinedload(QuotationLine.product),
            )
        )
        if status is not None:
            stmt = stmt.where(Backorder.status == status)
        if order_id is not None:
            stmt = stmt.where(Backorder.order_id == order_id)
        stmt = stmt.order_by(Backorder.created_at.desc()).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    def get_backorder_by_id(
        self, db: Session, backorder_id: uuid.UUID
    ) -> Optional[Backorder]:
        """Fetch backorder by UUID with relations loaded."""
        stmt = (
            select(Backorder)
            .options(
                joinedload(Backorder.order),
                joinedload(Backorder.quotation_line).joinedload(QuotationLine.product),
            )
            .where(Backorder.id == backorder_id)
        )
        return db.scalars(stmt).first()

    def get_backorders_for_order(
        self, db: Session, order_id: uuid.UUID
    ) -> List[Backorder]:
        """Query all backorders belonging to an order."""
        stmt = (
            select(Backorder)
            .options(
                joinedload(Backorder.quotation_line).joinedload(QuotationLine.product),
            )
            .where(Backorder.order_id == order_id)
            .order_by(Backorder.created_at.asc())
        )
        return list(db.scalars(stmt).all())


    def delete_open_backorders(self, db: Session, order_id: uuid.UUID) -> int:
        """Delete open backorders when recalculating or overriding allocations."""
        stmt = (
            select(Backorder)
            .where(
                Backorder.order_id == order_id,
                Backorder.status == BackorderStatus.OPEN,
            )
        )
        open_bos = list(db.scalars(stmt).all())
        for bo in open_bos:
            db.delete(bo)
        db.flush()
        return len(open_bos)

    def create_backorders(
        self, db: Session, backorders: List[Backorder]
    ) -> List[Backorder]:
        """Bulk add backorders."""
        db.add_all(backorders)
        db.flush()
        return backorders

    def update_backorder(self, db: Session, backorder: Backorder) -> Backorder:
        """Commit updates to a backorder."""
        db.add(backorder)
        db.commit()
        db.refresh(backorder)
        return backorder


fulfillment_repository = FulfillmentRepository()

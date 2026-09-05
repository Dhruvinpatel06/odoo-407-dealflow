"""Unit tests for DealFlow360 SQLAlchemy 2.x persistence models and Alembic metadata."""

from unittest.mock import patch
from sqlalchemy.orm import configure_mappers
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.environment import EnvironmentContext

from app.core.database import Base
import app.models as models
from app.common.enums import UserRole
from app.models.user import User
from app.models.auth_session import AuthSession
from app.models.customer import Customer
from app.models.customer_tier import CustomerTier
from app.models.product_category import ProductCategory
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.price_list import PriceList
from app.models.price_list_item import PriceListItem
from app.models.discount_rule import DiscountRule
from app.models.approval_policy import ApprovalPolicy
from app.models.approval_instance import ApprovalInstance
from app.models.approval_step import ApprovalStep
from app.models.quotation import Quotation
from app.models.quotation_line import QuotationLine
from app.models.order import Order
from app.models.recommendation_rule import RecommendationRule
from app.models.warehouse import Warehouse
from app.models.inventory import Inventory
from app.models.fulfillment_allocation import FulfillmentAllocation
from app.models.backorder import Backorder
from app.models.subscription_plan import SubscriptionPlan
from app.models.subscription import Subscription
from app.models.billing_schedule import BillingSchedule
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.negotiation_request import NegotiationRequest
from app.models.negotiation_comment import NegotiationComment
from app.models.deal_alert import DealAlert
from app.models.audit_log import AuditLog


EXPECTED_TABLE_COLUMNS = {
    "users": {
        "id", "name", "email", "password_hash", "role", "customer_id",
        "is_active", "created_at", "updated_at",
    },
    "auth_sessions": {
        "id", "user_id", "refresh_token_hash", "expires_at", "revoked_at",
        "created_at", "last_used_at",
    },
    "customers": {
        "id", "name", "email", "phone", "customer_tier_id", "billing_address",
        "shipping_address", "is_active", "created_at", "updated_at",
    },
    "customer_tiers": {
        "id", "name", "description", "default_discount_limit", "is_active",
        "created_at", "updated_at",
    },
    "product_categories": {
        "id", "name", "description", "is_active", "created_at", "updated_at",
    },
    "products": {
        "id", "category_id", "name", "description", "sku", "unit", "base_price",
        "cost_price", "tax_rate", "is_subscription", "is_active", "created_at",
        "updated_at",
    },
    "product_variants": {
        "id", "product_id", "attribute_name", "attribute_value", "extra_price",
        "sku", "is_active", "created_at", "updated_at",
    },
    "price_lists": {
        "id", "name", "customer_tier_id", "currency", "is_active", "created_at",
        "updated_at",
    },
    "price_list_items": {
        "id", "price_list_id", "product_id", "variant_id", "price",
        "created_at", "updated_at",
    },
    "discount_rules": {
        "id", "customer_tier_id", "category_id", "max_discount_percent",
        "priority", "is_active", "created_at", "updated_at",
    },
    "approval_policies": {
        "id", "name", "min_risk_score", "max_risk_score", "requires_manager",
        "requires_finance", "priority", "is_active", "created_at", "updated_at",
    },
    "approval_instances": {
        "id", "quotation_id", "risk_score", "status", "started_at",
        "completed_at", "created_at", "updated_at",
    },
    "approval_steps": {
        "id", "approval_instance_id", "step_order", "approver_role",
        "approver_user_id", "status", "decision_reason", "decided_at",
        "created_at", "updated_at",
    },
    "quotations": {
        "id", "quotation_number", "customer_id", "sales_rep_id", "status",
        "subtotal", "discount_amount", "order_discount_percent", "tax_amount",
        "total_amount", "total_cost", "margin_amount", "margin_percent",
        "risk_score", "approval_required", "current_approval_level",
        "sent_at", "last_activity_at", "valid_until", "created_at", "updated_at",
    },
    "quotation_lines": {
        "id", "quotation_id", "product_id", "variant_id", "description",
        "quantity", "unit_price", "discount_percent", "discount_amount",
        "tax_rate", "line_total", "unit_cost", "margin_amount", "margin_percent",
        "allowed_discount_percent", "discount_excess_percent", "created_at", "updated_at",
    },
    "orders": {
        "id", "order_number", "quotation_id", "customer_id", "status",
        "total_amount", "confirmed_at", "created_at", "updated_at",
    },
    "recommendation_rules": {
        "id", "source_product_id", "recommended_product_id", "rule_type",
        "priority", "promotion_tag", "min_margin_percent", "co_purchase_score",
        "is_promoted", "is_active", "created_at", "updated_at",
    },
    "warehouses": {
        "id", "name", "code", "address", "shipping_cost_weight",
        "replenishment_enabled", "is_active", "created_at", "updated_at",
    },
    "inventory": {
        "id", "warehouse_id", "product_id", "quantity_on_hand",
        "quantity_reserved", "reorder_level", "reorder_quantity", "updated_at",
    },
    "fulfillment_allocations": {
        "id", "order_id", "quotation_line_id", "warehouse_id",
        "quantity_allocated", "quantity_fulfilled", "estimated_shipping_cost",
        "is_suggested", "is_manual_override", "status", "created_at", "updated_at",
    },
    "backorders": {
        "id", "order_id", "quotation_line_id", "quantity_backordered",
        "quantity_remaining", "status", "consolidation_requested",
        "created_at", "updated_at",
    },
    "subscription_plans": {
        "id", "name", "billing_interval", "interval_count", "proration_method",
        "cancellation_policy", "refund_policy", "is_active", "created_at", "updated_at",
    },
    "subscriptions": {
        "id", "order_id", "quotation_line_id", "customer_id", "product_id",
        "plan_id", "quantity", "unit_price", "start_date", "next_billing_date",
        "status", "created_at", "updated_at",
    },
    "billing_schedules": {
        "id", "subscription_id", "billing_date", "amount", "status",
        "proration_amount", "created_at", "updated_at",
    },
    "invoices": {
        "id", "invoice_number", "order_id", "billing_schedule_id", "invoice_type",
        "subtotal", "tax_amount", "total_amount", "paid_amount", "status",
        "due_date", "issued_at", "created_at", "updated_at",
    },
    "payments": {
        "id", "invoice_id", "amount", "payment_method", "transaction_reference",
        "payment_date", "status", "created_at", "updated_at",
    },
    "negotiation_requests": {
        "id", "quotation_id", "customer_id", "requested_by",
        "requested_discount_percent", "requested_changes", "reason", "status",
        "created_at", "updated_at",
    },
    "negotiation_comments": {
        "id", "quotation_id", "quotation_line_id", "user_id", "comment",
        "created_at", "updated_at",
    },
    "deal_alerts": {
        "id", "quotation_id", "alert_type", "severity", "title", "message",
        "metric_value", "threshold_value", "status", "action_taken",
        "created_at", "updated_at",
    },
    "audit_logs": {
        "id", "user_id", "entity_type", "entity_id", "action", "old_values",
        "new_values", "reason", "created_at",
    },
}


def test_mapper_configuration():
    """Verify all relationship mappers configure cleanly without errors."""
    configure_mappers()


def test_exact_table_count_and_names():
    """Verify exactly 30 finalized tables exist in SQLAlchemy Base metadata."""
    metadata_tables = set(Base.metadata.tables.keys())
    assert len(metadata_tables) == 30, f"Expected 30 tables, found {len(metadata_tables)}: {metadata_tables}"
    assert metadata_tables == set(EXPECTED_TABLE_COLUMNS.keys())


def test_all_table_columns():
    """Verify every table has exactly the specified columns."""
    for table_name, expected_cols in EXPECTED_TABLE_COLUMNS.items():
        table = Base.metadata.tables[table_name]
        actual_cols = set(table.columns.keys())
        assert actual_cols == expected_cols, f"Mismatch in {table_name}: missing={expected_cols - actual_cols}, extra={actual_cols - expected_cols}"


def test_user_and_auth_session_models():
    """Verify manual-auth compatibility for User and AuthSession models."""
    user_cols = {c.name: c for c in User.__table__.columns}
    assert "email" in user_cols
    assert user_cols["email"].unique is True
    assert "password_hash" in user_cols
    assert user_cols["password_hash"].unique is not True
    assert "role" in user_cols
    assert user_cols["role"].nullable is False
    assert set(UserRole) == {
        UserRole.CUSTOMER,
        UserRole.SALES_REP,
        UserRole.SALES_MANAGER,
        UserRole.FINANCE_OPERATIONS,
        UserRole.ADMIN,
    }
    assert {e.value for e in UserRole} == {
        "CUSTOMER",
        "SALES_REP",
        "SALES_MANAGER",
        "FINANCE_OPERATIONS",
        "ADMIN",
    }
    assert "customer_id" in user_cols
    assert "is_active" in user_cols

    session_cols = {c.name: c for c in AuthSession.__table__.columns}
    assert "user_id" in session_cols
    assert "refresh_token_hash" in session_cols
    assert session_cols["refresh_token_hash"].unique is True
    assert "expires_at" in session_cols
    assert "revoked_at" in session_cols
    assert "created_at" in session_cols
    assert "last_used_at" in session_cols


def test_inventory_unique_constraint():
    """Verify inventory has unique constraint on warehouse_id + product_id."""
    constraints = [c.name for c in Inventory.__table__.constraints if hasattr(c, "columns")]
    assert "uq_inventory_warehouse_product" in constraints or any(
        {"warehouse_id", "product_id"}.issubset({col.name for col in c.columns})
        for c in Inventory.__table__.constraints
        if hasattr(c, "columns")
    )


def test_order_quotation_unique():
    """Verify orders.quotation_id has a unique constraint (1-to-1 quotation to order)."""
    quotation_col = Order.__table__.columns["quotation_id"]
    assert quotation_col.unique is True


def test_alembic_metadata_discovery():
    """Verify Alembic target_metadata contains all 30 model tables."""
    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)

    captured_metadata = []
    env_ctx = EnvironmentContext(config, script, fn=lambda r, c: [], as_sql=True)
    original_configure = env_ctx.configure

    def capture_configure(*args, **kwargs):
        if "target_metadata" in kwargs:
            captured_metadata.append(kwargs["target_metadata"])
        return original_configure(*args, **kwargs)

    with env_ctx:
        with patch.object(env_ctx, "configure", side_effect=capture_configure), \
             patch.object(env_ctx, "run_migrations"):
            script.run_env()

    assert len(captured_metadata) > 0
    discovered_tables = set(captured_metadata[0].tables.keys())
    assert discovered_tables == set(EXPECTED_TABLE_COLUMNS.keys())

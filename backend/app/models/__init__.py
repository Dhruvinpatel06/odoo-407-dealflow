"""SQLAlchemy 2.x persistence models registration.

Exports all 30 finalized DealFlow360 domain models so they are discovered
by SQLAlchemy and Alembic metadata.
"""

from app.core.database import Base
from app.models.approval_instance import ApprovalInstance
from app.models.approval_policy import ApprovalPolicy
from app.models.approval_step import ApprovalStep
from app.models.audit_log import AuditLog
from app.models.auth_session import AuthSession
from app.models.backorder import Backorder
from app.models.billing_schedule import BillingSchedule
from app.models.customer import Customer
from app.models.customer_tier import CustomerTier
from app.models.deal_alert import DealAlert
from app.models.discount_rule import DiscountRule
from app.models.fulfillment_allocation import FulfillmentAllocation
from app.models.inventory import Inventory
from app.models.invoice import Invoice
from app.models.negotiation_comment import NegotiationComment
from app.models.negotiation_request import NegotiationRequest
from app.models.order import Order
from app.models.payment import Payment
from app.models.price_list import PriceList
from app.models.price_list_item import PriceListItem
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.product_variant import ProductVariant
from app.models.quotation import Quotation
from app.models.quotation_line import QuotationLine
from app.models.recommendation_rule import RecommendationRule
from app.models.subscription import Subscription
from app.models.subscription_plan import SubscriptionPlan
from app.models.user import User
from app.models.warehouse import Warehouse

__all__ = [
    "Base",
    "User",
    "AuthSession",
    "Customer",
    "CustomerTier",
    "ProductCategory",
    "Product",
    "ProductVariant",
    "PriceList",
    "PriceListItem",
    "DiscountRule",
    "ApprovalPolicy",
    "ApprovalInstance",
    "ApprovalStep",
    "Quotation",
    "QuotationLine",
    "Order",
    "RecommendationRule",
    "Warehouse",
    "Inventory",
    "FulfillmentAllocation",
    "Backorder",
    "SubscriptionPlan",
    "Subscription",
    "BillingSchedule",
    "Invoice",
    "Payment",
    "NegotiationRequest",
    "NegotiationComment",
    "DealAlert",
    "AuditLog",
]

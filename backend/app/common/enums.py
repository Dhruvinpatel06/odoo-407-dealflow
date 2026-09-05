"""Shared enumeration types for DealFlow360."""

import enum


class UserRole(str, enum.Enum):
    CUSTOMER = "CUSTOMER"
    SALES_REP = "SALES_REP"
    SALES_MANAGER = "SALES_MANAGER"
    FINANCE_OPERATIONS = "FINANCE_OPERATIONS"
    ADMIN = "ADMIN"


class QuotationStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SENT = "SENT"
    UNDER_NEGOTIATION = "UNDER_NEGOTIATION"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REVISION_REQUIRED = "REVISION_REQUIRED"
    CONFIRMED = "CONFIRMED"


class ApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REVISION_REQUIRED = "REVISION_REQUIRED"


class ApproverRole(str, enum.Enum):
    SALES_MANAGER = "SALES_MANAGER"
    FINANCE_OPERATIONS = "FINANCE_OPERATIONS"


class OrderStatus(str, enum.Enum):
    CONFIRMED = "CONFIRMED"
    FULFILLMENT = "FULFILLMENT"
    PARTIALLY_FULFILLED = "PARTIALLY_FULFILLED"
    FULFILLED = "FULFILLED"
    BILLING = "BILLING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class RecommendationType(str, enum.Enum):
    UPSELL = "UPSELL"
    CROSS_SELL = "CROSS_SELL"


class FulfillmentAllocationStatus(str, enum.Enum):
    SUGGESTED = "SUGGESTED"
    ACCEPTED = "ACCEPTED"
    FULFILLED = "FULFILLED"
    CANCELLED = "CANCELLED"


class BackorderStatus(str, enum.Enum):
    OPEN = "OPEN"
    CONSOLIDATION_AVAILABLE = "CONSOLIDATION_AVAILABLE"
    CONSOLIDATED = "CONSOLIDATED"
    FULFILLED = "FULFILLED"
    CANCELLED = "CANCELLED"


class BillingInterval(str, enum.Enum):
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    YEARLY = "YEARLY"


class ProrationMethod(str, enum.Enum):
    DAILY_PRO_RATA = "DAILY_PRO_RATA"
    FULL_PERIOD = "FULL_PERIOD"
    NO_PRORATION = "NO_PRORATION"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    MODIFIED = "MODIFIED"
    CANCELLED = "CANCELLED"
    PAUSED = "PAUSED"


class BillingScheduleStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    INVOICED = "INVOICED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class InvoiceType(str, enum.Enum):
    ONE_TIME = "ONE_TIME"
    RECURRING = "RECURRING"
    CREDIT_NOTE = "CREDIT_NOTE"


class InvoiceStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ISSUED = "ISSUED"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class PaymentStatus(str, enum.Enum):
    RECORDED = "RECORDED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class NegotiationRequestStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    APPLIED = "APPLIED"


class DealAlertType(str, enum.Enum):
    STALLED = "STALLED"
    DISCOUNT_ANOMALY = "DISCOUNT_ANOMALY"
    DELIVERY_SLIPPAGE = "DELIVERY_SLIPPAGE"


class DealAlertSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class DealAlertStatus(str, enum.Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"

"""Unit tests for Subscriptions Engine (intervals and proration) and Billing Engine."""

from __future__ import annotations

import datetime
from decimal import Decimal

import pytest

from app.common.enums import BillingInterval, InvoiceStatus, ProrationMethod
from app.core.exceptions import BusinessRuleViolationError
from app.modules.billing.engine import billing_engine
from app.modules.subscriptions.engine import (
    calculate_next_billing_date,
    subscriptions_engine,
)


def test_next_billing_date_calculation():
    """Verify deterministic interval calculations for month, quarter, and year."""
    jan_15 = datetime.date(2026, 1, 15)
    assert calculate_next_billing_date(jan_15, BillingInterval.MONTHLY) == datetime.date(2026, 2, 15)
    assert calculate_next_billing_date(jan_15, BillingInterval.QUARTERLY) == datetime.date(2026, 4, 15)
    assert calculate_next_billing_date(jan_15, BillingInterval.YEARLY) == datetime.date(2027, 1, 15)

    # End of month handling (Jan 31 -> Feb 28)
    jan_31 = datetime.date(2026, 1, 31)
    assert calculate_next_billing_date(jan_31, BillingInterval.MONTHLY) == datetime.date(2026, 2, 28)


def test_daily_pro_rata_proration_upgrade():
    """Verify daily pro rata calculation when upgrading quantity mid-cycle."""
    start = datetime.date(2026, 1, 1)
    next_bill = datetime.date(2026, 1, 31)  # 30 days total
    mid_cycle = datetime.date(2026, 1, 16)  # 15 days remaining

    # Upgrade from 2 units ($100 each = $200) to 4 units ($100 each = $400)
    # Delta = $200. Daily rate = 200/30 = 6.6667. For 15 days = $100.00
    res = subscriptions_engine.calculate_proration(
        current_quantity=Decimal("2.00"),
        current_unit_price=Decimal("100.00"),
        new_quantity=Decimal("4.00"),
        new_unit_price=Decimal("100.00"),
        start_date=start,
        next_billing_date=next_bill,
        proration_method=ProrationMethod.DAILY_PRO_RATA,
        effective_date=mid_cycle,
    )

    assert res.current_amount == Decimal("200.00")
    assert res.new_amount == Decimal("400.00")
    assert res.days_remaining == 15
    assert res.total_period_days == 30
    assert res.proration_adjustment == Decimal("100.00")


def test_daily_pro_rata_proration_downgrade():
    """Verify daily pro rata calculation produces a negative credit when downgrading."""
    start = datetime.date(2026, 1, 1)
    next_bill = datetime.date(2026, 1, 31)  # 30 days
    mid_cycle = datetime.date(2026, 1, 16)  # 15 days remaining

    # Downgrade from 4 units ($100 each = $400) to 2 units ($100 each = $200)
    # Delta = -$200. Adjustment = -$100.00
    res = subscriptions_engine.calculate_proration(
        current_quantity=Decimal("4.00"),
        current_unit_price=Decimal("100.00"),
        new_quantity=Decimal("2.00"),
        new_unit_price=Decimal("100.00"),
        start_date=start,
        next_billing_date=next_bill,
        proration_method=ProrationMethod.DAILY_PRO_RATA,
        effective_date=mid_cycle,
    )
    assert res.proration_adjustment == Decimal("-100.00")


def test_full_period_and_no_proration():
    """Verify FULL_PERIOD and NO_PRORATION policies."""
    start = datetime.date(2026, 1, 1)
    next_bill = datetime.date(2026, 1, 31)

    full_res = subscriptions_engine.calculate_proration(
        current_quantity=Decimal("1.00"),
        current_unit_price=Decimal("50.00"),
        new_quantity=Decimal("2.00"),
        new_unit_price=Decimal("50.00"),
        start_date=start,
        next_billing_date=next_bill,
        proration_method=ProrationMethod.FULL_PERIOD,
    )
    assert full_res.proration_adjustment == Decimal("50.00")

    no_pro_res = subscriptions_engine.calculate_proration(
        current_quantity=Decimal("1.00"),
        current_unit_price=Decimal("50.00"),
        new_quantity=Decimal("2.00"),
        new_unit_price=Decimal("50.00"),
        start_date=start,
        next_billing_date=next_bill,
        proration_method=ProrationMethod.NO_PRORATION,
    )
    assert no_pro_res.proration_adjustment == Decimal("0.00")


def test_billing_engine_derive_invoice_status():
    """Verify invoice status progression according to payment rules."""
    # 0 paid after issuance -> ISSUED
    assert billing_engine.derive_invoice_status(Decimal("100.00"), Decimal("0.00"), is_issued=True) == InvoiceStatus.ISSUED
    # 0 paid before issuance -> DRAFT
    assert billing_engine.derive_invoice_status(Decimal("100.00"), Decimal("0.00"), is_issued=False) == InvoiceStatus.DRAFT
    # Partial payment -> PARTIALLY_PAID
    assert billing_engine.derive_invoice_status(Decimal("100.00"), Decimal("40.00")) == InvoiceStatus.PARTIALLY_PAID
    # Full payment -> PAID
    assert billing_engine.derive_invoice_status(Decimal("100.00"), Decimal("100.00")) == InvoiceStatus.PAID
    # Overpayment edge -> PAID
    assert billing_engine.derive_invoice_status(Decimal("100.00"), Decimal("150.00")) == InvoiceStatus.PAID


def test_billing_engine_payment_bounds_validation():
    """Verify payment validation rejects non-positive amounts and overpayments."""
    # Non-positive amount
    with pytest.raises(BusinessRuleViolationError, match="greater than zero"):
        billing_engine.validate_payment_bounds(Decimal("100.00"), Decimal("0.00"), Decimal("0.00"))

    with pytest.raises(BusinessRuleViolationError, match="greater than zero"):
        billing_engine.validate_payment_bounds(Decimal("100.00"), Decimal("0.00"), Decimal("-10.00"))

    # Valid payment
    billing_engine.validate_payment_bounds(Decimal("100.00"), Decimal("20.00"), Decimal("50.00"))

    # Overpayment: 20 + 90 = 110 > 100
    with pytest.raises(BusinessRuleViolationError, match="Overpayment is not permitted"):
        billing_engine.validate_payment_bounds(Decimal("100.00"), Decimal("20.00"), Decimal("90.00"))

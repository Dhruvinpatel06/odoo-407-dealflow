"""Deterministic Subscriptions Engine for billing intervals and proration calculations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from app.common.enums import BillingInterval, ProrationMethod


def calculate_next_billing_date(
    current_date: date, interval: BillingInterval, count: int = 1
) -> date:
    """
    Deterministically computes the next scheduled billing date based on the plan's interval.
    """
    if count < 1:
        count = 1

    if interval == BillingInterval.MONTHLY:
        total_months = current_date.month - 1 + count
        year = current_date.year + total_months // 12
        month = total_months % 12 + 1
        is_leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
        max_days = [31, 29 if is_leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]
        day = min(current_date.day, max_days)
        return date(year, month, day)

    elif interval == BillingInterval.QUARTERLY:
        total_months = current_date.month - 1 + (count * 3)
        year = current_date.year + total_months // 12
        month = total_months % 12 + 1
        is_leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
        max_days = [31, 29 if is_leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]
        day = min(current_date.day, max_days)
        return date(year, month, day)

    elif interval == BillingInterval.YEARLY:
        year = current_date.year + count
        is_leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
        day = (
            28
            if current_date.month == 2 and current_date.day == 29 and not is_leap
            else current_date.day
        )
        return date(year, current_date.month, day)

    return current_date


@dataclass
class ProrationResult:
    """Encapsulates proration calculation outputs."""

    current_amount: Decimal
    new_amount: Decimal
    days_remaining: int
    total_period_days: int
    proration_adjustment: Decimal
    proration_method: ProrationMethod
    description: str


class SubscriptionsEngine:
    """
    Deterministic subscriptions engine supporting:
    - Interval date progression.
    - Mid-cycle proration calculations (Daily Pro Rata, Full Period, No Proration).
    - Cancellation credit note estimation.
    """

    def calculate_proration(
        self,
        current_quantity: Decimal,
        current_unit_price: Decimal,
        new_quantity: Decimal,
        new_unit_price: Decimal,
        start_date: date,
        next_billing_date: date,
        proration_method: ProrationMethod,
        effective_date: Optional[date] = None,
    ) -> ProrationResult:
        """
        Calculates financial adjustment for mid-cycle changes.
        """
        eff_date = effective_date or date.today()

        total_period_days = (next_billing_date - start_date).days
        if total_period_days <= 0:
            total_period_days = 30

        days_remaining = max(0, (next_billing_date - eff_date).days)
        # Cannot exceed period length
        days_remaining = min(days_remaining, total_period_days)

        current_amount = (current_quantity * current_unit_price).quantize(Decimal("0.01"))
        new_amount = (new_quantity * new_unit_price).quantize(Decimal("0.01"))
        amount_delta = new_amount - current_amount

        if proration_method == ProrationMethod.DAILY_PRO_RATA:
            if total_period_days > 0 and days_remaining > 0:
                daily_diff = amount_delta / Decimal(str(total_period_days))
                adjustment = (daily_diff * Decimal(str(days_remaining))).quantize(Decimal("0.01"))
            else:
                adjustment = Decimal("0.00")
            desc = (
                f"Daily pro rata adjustment for {days_remaining}/{total_period_days} days remaining: "
                f"${adjustment}"
            )

        elif proration_method == ProrationMethod.FULL_PERIOD:
            adjustment = amount_delta.quantize(Decimal("0.01"))
            desc = f"Full period difference charged/credited: ${adjustment}"

        else:  # NO_PRORATION
            adjustment = Decimal("0.00")
            desc = "No proration adjustment. Changes take effect on next billing cycle."

        return ProrationResult(
            current_amount=current_amount,
            new_amount=new_amount,
            days_remaining=days_remaining,
            total_period_days=total_period_days,
            proration_adjustment=adjustment,
            proration_method=proration_method,
            description=desc,
        )

    def calculate_cancellation_refund(
        self,
        recurring_amount: Decimal,
        start_date: date,
        next_billing_date: date,
        cancellation_date: Optional[date] = None,
    ) -> Decimal:
        """Calculates unused service value for cancellation credit notes."""
        canc_date = cancellation_date or date.today()
        total_days = (next_billing_date - start_date).days
        if total_days <= 0:
            total_days = 30

        days_remaining = max(0, (next_billing_date - canc_date).days)
        if days_remaining <= 0 or total_days <= 0:
            return Decimal("0.00")

        daily_rate = recurring_amount / Decimal(str(total_days))
        return (daily_rate * Decimal(str(days_remaining))).quantize(Decimal("0.01"))


subscriptions_engine = SubscriptionsEngine()

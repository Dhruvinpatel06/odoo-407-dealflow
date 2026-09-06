"""Quotation calculation and blended discount risk engine.

This engine is authoritative for:
- Quotation line financial calculations (line totals, taxes, costs, margins)
- Quotation aggregates (subtotal, total discounts, tax amount, margin amount/percent)
- Authoritative blended discount-risk score calculation
- Approval requirement and required approval level determination
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from app.common.enums import ApproverRole
from app.models.approval_policy import ApprovalPolicy


class QuotationCalculationEngine:
    """
    Encapsulates pure, deterministic calculations for quotation line financials,
    quotation totals, blended discount-risk scoring, and approval requirements.
    """

    BLENDED_RISK_FORMULA_EXPLANATION = (
        "Blended Discount Risk Score is determined by: "
        "1. Dollar-weighted line excess (W = sum(line_value / total_value * excess)). "
        "2. Severity component (S = 0.5 * max_excess + 0.5 * W). "
        "3. Multi-line violation penalty (P = min(5.0 * (violating_lines - 1), 15.0)). "
        "4. Score = clamp(round(S * 2.0 + P, 2), 0.00, 100.00)."
    )

    # --- Line-Level Financial Calculations ---

    @staticmethod
    def calculate_line_financials(
        quantity: Decimal,
        unit_price: Decimal,
        discount_percent: Decimal,
        tax_rate: Decimal,
        unit_cost: Decimal,
    ) -> Dict[str, Decimal]:
        """
        Calculate authoritative line-level financials using Decimal arithmetic.

        Formulas:
        - gross_amount = round(quantity * unit_price, 2)
        - discount_amount = round(gross_amount * (discount_percent / 100), 2)
        - taxable_amount = gross_amount - discount_amount
        - tax_amount = round(taxable_amount * (tax_rate / 100), 2)
        - line_total = taxable_amount + tax_amount
        - cost_amount = round(quantity * unit_cost, 2)
        - margin_amount = taxable_amount - cost_amount
        - margin_percent = round((margin_amount / taxable_amount) * 100, 2) if taxable_amount > 0 else 0.00
        """
        qty = Decimal(str(quantity))
        price = Decimal(str(unit_price))
        disc_pct = Decimal(str(discount_percent))
        tax_pct = Decimal(str(tax_rate))
        cost = Decimal(str(unit_cost))

        gross_amount = round(qty * price, 2)
        discount_amount = round(gross_amount * (disc_pct / Decimal("100.00")), 2)
        taxable_amount = gross_amount - discount_amount
        tax_amount = round(taxable_amount * (tax_pct / Decimal("100.00")), 2)
        line_total = taxable_amount + tax_amount
        cost_amount = round(qty * cost, 2)
        margin_amount = taxable_amount - cost_amount

        if taxable_amount > Decimal("0.00"):
            margin_percent = round(
                (margin_amount / taxable_amount) * Decimal("100.00"), 2
            )
        else:
            margin_percent = Decimal("0.00")

        return {
            "gross_amount": gross_amount,
            "discount_amount": discount_amount,
            "taxable_amount": taxable_amount,
            "tax_amount": tax_amount,
            "line_total": line_total,
            "cost_amount": cost_amount,
            "margin_amount": margin_amount,
            "margin_percent": margin_percent,
        }

    # --- Authoritative Blended Discount Risk Calculation ---

    @classmethod
    def calculate_blended_risk_score(
        cls,
        lines_risk_inputs: List[Dict[str, Any]],
    ) -> Decimal:
        """
        Calculate the authoritative blended discount risk score for a quotation.

        Contract & Behavior:
        - Deterministic backend decision matching FR-04.3, FR-04.4, FR-04.5, FR-04.6.
        - Inputs per line:
            `quantity`: Decimal
            `unit_price`: Decimal
            `discount_excess_percent`: Decimal (>= 0.00)
        - Bounded range: [Decimal('0.00'), Decimal('100.00')]
        - Precision: 2 decimal places.

        Algorithm:
        1. Boundary check: If lines is empty, return 0.00.
        2. Aggregate line gross values V_i = quantity_i * unit_price_i and excesses E_i.
        3. If total gross value V_total == 0:
           - If max(E_i) == 0: return 0.00
           - Else: return clamp(round(max(E_i) * 2.0, 2), 0.00, 100.00)
        4. For V_total > 0:
           - Value-weighted excess W = sum((V_i / V_total) * E_i)
           - Max line excess E_max = max(E_i)
           - Violating lines count N_violating = count(E_i > 0)
           - Severity S = 0.50 * E_max + 0.50 * W
           - Multi-line penalty P = min(5.00 * max(0, N_violating - 1), 15.00)
           - Raw score = (S * 2.0) + P
           - Score = clamp(round(Raw score, 2), 0.00, 100.00)
        """
        if not lines_risk_inputs:
            return Decimal("0.00")

        total_gross = Decimal("0.00")
        max_excess = Decimal("0.00")
        violating_count = 0
        line_entries: List[Tuple[Decimal, Decimal]] = []

        for item in lines_risk_inputs:
            qty = Decimal(str(item.get("quantity", Decimal("0.00"))))
            price = Decimal(str(item.get("unit_price", Decimal("0.00"))))
            excess = Decimal(str(item.get("discount_excess_percent", Decimal("0.00"))))
            if excess < Decimal("0.00"):
                excess = Decimal("0.00")

            line_gross = round(qty * price, 2)
            total_gross += line_gross
            line_entries.append((line_gross, excess))

            if excess > max_excess:
                max_excess = excess
            if excess > Decimal("0.00"):
                violating_count += 1

        # Zero-value quotation edge case
        if total_gross <= Decimal("0.00"):
            if max_excess <= Decimal("0.00"):
                return Decimal("0.00")
            raw = max_excess * Decimal("2.0")
            bounded = max(Decimal("0.00"), min(Decimal("100.00"), round(raw, 2)))
            return bounded

        # Standard weighted case
        weighted_excess = Decimal("0.00")
        for line_gross, excess in line_entries:
            if line_gross > Decimal("0.00"):
                weight = line_gross / total_gross
                weighted_excess += weight * excess

        severity = (Decimal("0.50") * max_excess) + (Decimal("0.50") * weighted_excess)

        if violating_count > 1:
            penalty = min(
                Decimal("5.00") * Decimal(str(violating_count - 1)),
                Decimal("15.00"),
            )
        else:
            penalty = Decimal("0.00")

        raw_score = (severity * Decimal("2.0")) + penalty
        final_score = max(Decimal("0.00"), min(Decimal("100.00"), round(raw_score, 2)))
        return final_score

    # --- Approval Requirement & Level Determination ---

    @staticmethod
    def determine_approval_requirement(
        risk_score: Decimal,
        has_line_violations: bool,
        approval_policies: Optional[List[ApprovalPolicy]] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Determine whether quotation approval is required and what approval level applies.

        Rules:
        1. If active ApprovalPolicy records exist, evaluate matching policies:
           - Policy matches if min_risk_score <= risk_score <= (max_risk_score or inf).
           - Sort by priority DESC to select the winning configured policy.
           - If policy requires finance -> approval_required = True, level = 'FINANCE_OPERATIONS'
           - Else if policy requires manager -> approval_required = True, level = 'SALES_MANAGER'
           - Else -> approval_required = False, level = None
        2. Fallback if no matching policy exists or no policies configured:
           - If has_line_violations or risk_score > 0:
             approval_required = True, level = 'SALES_MANAGER'
           - Else:
             approval_required = False, level = None
        """
        active_policies = [
            p for p in (approval_policies or []) if getattr(p, "is_active", True)
        ]

        if active_policies:
            matching_policies: List[ApprovalPolicy] = []
            for policy in active_policies:
                min_score = Decimal(str(policy.min_risk_score))
                max_score = (
                    Decimal(str(policy.max_risk_score))
                    if policy.max_risk_score is not None
                    else None
                )

                if risk_score >= min_score:
                    if max_score is None or risk_score <= max_score:
                        matching_policies.append(policy)

            if matching_policies:
                # Highest priority wins
                matching_policies.sort(key=lambda p: p.priority, reverse=True)
                winning_policy = matching_policies[0]

                req_finance = bool(winning_policy.requires_finance)
                req_manager = bool(winning_policy.requires_manager)

                if req_finance:
                    return True, ApproverRole.FINANCE_OPERATIONS.value
                elif req_manager:
                    return True, ApproverRole.SALES_MANAGER.value
                else:
                    return False, None

        # Fallback baseline when no configured policy matches
        if has_line_violations or risk_score > Decimal("0.00"):
            return True, ApproverRole.SALES_MANAGER.value

        return False, None

    # --- Quotation Aggregates ---

    @staticmethod
    def calculate_quotation_aggregates(
        line_financials_list: List[Dict[str, Decimal]],
    ) -> Dict[str, Decimal]:
        """
        Aggregate line financials into quotation totals.
        """
        subtotal = Decimal("0.00")
        total_discount = Decimal("0.00")
        total_tax = Decimal("0.00")
        total_amount = Decimal("0.00")
        total_cost = Decimal("0.00")

        for item in line_financials_list:
            subtotal += item.get("gross_amount", Decimal("0.00"))
            total_discount += item.get("discount_amount", Decimal("0.00"))
            total_tax += item.get("tax_amount", Decimal("0.00"))
            total_amount += item.get("line_total", Decimal("0.00"))
            total_cost += item.get("cost_amount", Decimal("0.00"))

        subtotal = round(subtotal, 2)
        total_discount = round(total_discount, 2)
        total_tax = round(total_tax, 2)
        total_amount = round(total_amount, 2)
        total_cost = round(total_cost, 2)

        if subtotal > Decimal("0.00"):
            order_discount_percent = round(
                (total_discount / subtotal) * Decimal("100.00"), 2
            )
        else:
            order_discount_percent = Decimal("0.00")

        net_subtotal = subtotal - total_discount
        margin_amount = round(net_subtotal - total_cost, 2)

        if net_subtotal > Decimal("0.00"):
            margin_percent = round(
                (margin_amount / net_subtotal) * Decimal("100.00"), 2
            )
        else:
            margin_percent = Decimal("0.00")

        return {
            "subtotal": subtotal,
            "discount_amount": total_discount,
            "order_discount_percent": order_discount_percent,
            "tax_amount": total_tax,
            "total_amount": total_amount,
            "total_cost": total_cost,
            "margin_amount": margin_amount,
            "margin_percent": margin_percent,
        }


quotation_engine = QuotationCalculationEngine()

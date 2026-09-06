#!/usr/bin/env python3
"""
DealFlow360 mock-data generator.

Creates relationally consistent demo data for every finalized model table.
Defaults intentionally exceed the requested minimums:
  - 220 products
  - 120 quotations

Run from the DealFlow360 project root so `app.*` imports resolve:

    python scripts/generate_mock_data.py

If you save this file somewhere else, either move it to `scripts/` or run it
with the project root on PYTHONPATH.

The script does NOT delete existing application data. It uses deterministic
mock identifiers/business keys so it can detect an already-seeded run and
skip it unless --force is supplied. Existing users are preserved and their
existing password hash is reused for generated demo users, so no plaintext
password is introduced by this script.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import random
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Sequence

# ---------------------------------------------------------------------------
# Make `app` importable when the script lives in scripts/.
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session, sessionmaker

# Importing app.models registers every model with SQLAlchemy/Alembic metadata.
from app.models import (  # noqa: E402
    ApprovalInstance,
    ApprovalPolicy,
    ApprovalStep,
    AuditLog,
    AuthSession,
    Backorder,
    BillingSchedule,
    Customer,
    CustomerTier,
    DealAlert,
    DiscountRule,
    FulfillmentAllocation,
    Inventory,
    Invoice,
    NegotiationComment,
    NegotiationRequest,
    Order,
    Payment,
    PriceList,
    PriceListItem,
    Product,
    ProductCategory,
    ProductVariant,
    Quotation,
    QuotationLine,
    RecommendationRule,
    Subscription,
    SubscriptionPlan,
    User,
    Warehouse,
)
from app.common.enums import (  # noqa: E402
    ApprovalStatus,
    ApproverRole,
    BackorderStatus,
    BillingInterval,
    BillingScheduleStatus,
    DealAlertSeverity,
    DealAlertStatus,
    DealAlertType,
    FulfillmentAllocationStatus,
    InvoiceStatus,
    InvoiceType,
    NegotiationRequestStatus,
    OrderStatus,
    PaymentStatus,
    ProrationMethod,
    QuotationStatus,
    RecommendationType,
    SubscriptionStatus,
    UserRole,
)


MOCK_NAMESPACE = uuid.UUID("6f9c1f5c-9a45-4c0d-b3b1-0d7d7c360360")
MOCK_MARKER = "DF360-MOCK"
DATASET_SEED = 360


def dataset_tag() -> str:
    return str(DATASET_SEED)


def deterministic_uuid(kind: str, index: int) -> uuid.UUID:
    return uuid.uuid5(MOCK_NAMESPACE, f"{DATASET_SEED}:{kind}:{index}")


def now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def money(value: Decimal | float | int) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def clamp(value: Decimal, low: Decimal, high: Decimal) -> Decimal:
    return max(low, min(high, value))


def enum_members(enum_cls: type[Enum]) -> list[Enum]:
    return list(enum_cls)


def enum_by_name(enum_cls: type[Enum], *preferred: str, fallback_index: int = 0) -> Enum:
    """Pick a member by NAME, with a safe fallback for future enum changes."""
    members = enum_members(enum_cls)
    if not members:
        raise RuntimeError(f"Enum {enum_cls.__name__} has no members")
    normalized = {m.name.upper(): m for m in members}
    for candidate in preferred:
        member = normalized.get(candidate.upper())
        if member is not None:
            return member
    return members[fallback_index % len(members)]


def enum_cycle(enum_cls: type[Enum], index: int) -> Enum:
    members = enum_members(enum_cls)
    if not members:
        raise RuntimeError(f"Enum {enum_cls.__name__} has no members")
    return members[index % len(members)]


def has_enum_name(enum_cls: type[Enum], *names: str) -> bool:
    wanted = {n.upper() for n in names}
    return any(m.name.upper() in wanted for m in enum_members(enum_cls))


def status_or_first(enum_cls: type[Enum], *names: str) -> Enum:
    return enum_by_name(enum_cls, *names)


def role_matches(role: Enum, *names: str) -> bool:
    return role.name.upper() in {n.upper() for n in names}


def make_engine(database_url: str):
    # pool_pre_ping is useful when this script is run against a local/dev DB
    # that may have been idle for a while.
    return create_engine(database_url, pool_pre_ping=True)


def get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise SystemExit(
            "DATABASE_URL is not set. Load your DealFlow360 .env first, "
            "or export DATABASE_URL before running the generator."
        )
    return url


def seed_base_users(session: Session, customers: Sequence[Customer], rng: random.Random, count: int) -> list[User]:
    """Create demo users while preserving the real/admin users already present."""
    existing = list(session.scalars(select(User)).all())
    if not existing:
        raise SystemExit(
            "No users exist. Create the first DealFlow360 admin user before "
            "running this mock-data generator."
        )

    # Reuse an existing password hash. This keeps the script independent of
    # the project's chosen password hashing implementation.
    password_hash = existing[0].password_hash
    existing_mock = list(
        session.scalars(
            select(User).where(User.email.like("mock.df360.%@example.test"))
        ).all()
    )
    if len(existing_mock) >= count:
        return existing

    roles = enum_members(UserRole)
    customer_roles = [
        r for r in roles if "CUSTOMER" in r.name.upper()
    ]
    internal_roles = [
        r for r in roles if "CUSTOMER" not in r.name.upper()
    ] or roles

    created = []
    existing_count = len(existing_mock)
    for i in range(existing_count, count):
        role = (customer_roles or internal_roles)[i % len(customer_roles or internal_roles)]
        customer_id = customers[i % len(customers)].id if role in customer_roles else None
        user = User(
            id=deterministic_uuid("user", i),
            name=f"{MOCK_MARKER} User {i + 1:03d}",
            email=f"mock.df360.{DATASET_SEED}.{i + 1:03d}@example.test",
            password_hash=password_hash,
            role=role,
            customer_id=customer_id,
            is_active=True,
            created_at=now_utc() - timedelta(days=rng.randint(1, 180)),
            updated_at=now_utc(),
        )
        session.add(user)
        created.append(user)
    session.flush()
    return existing + created


def seed_customer_tiers(session: Session, count: int) -> list[CustomerTier]:
    names = ["Bronze", "Silver", "Gold", "Platinum", "Enterprise", "Strategic"]
    tiers: list[CustomerTier] = []
    for i in range(count):
        tiers.append(
            CustomerTier(
                id=deterministic_uuid("customer-tier", i),
                name=f"{MOCK_MARKER} {DATASET_SEED} {names[i % len(names)]} {i + 1}",
                description=f"Demo customer tier {i + 1} for DealFlow360 testing.",
                default_discount_limit=money(5 + (i % 6) * 3),
                is_active=True,
                created_at=now_utc() - timedelta(days=200 - i),
                updated_at=now_utc(),
            )
        )
    session.add_all(tiers)
    session.flush()
    return tiers


def seed_customers(session: Session, tiers: Sequence[CustomerTier], rng: random.Random, count: int) -> list[Customer]:
    customers: list[Customer] = []
    cities = ["Ahmedabad", "Mumbai", "Bengaluru", "Delhi", "Pune", "Hyderabad", "Chennai", "Jaipur"]
    for i in range(count):
        city = cities[i % len(cities)]
        customers.append(
            Customer(
                id=deterministic_uuid("customer", i),
                name=f"{MOCK_MARKER} {DATASET_SEED} Customer {i + 1:03d}",
                email=f"customer.{DATASET_SEED}.{i + 1:03d}@mock-dealflow.example",
                phone=f"+91-98{rng.randint(10000000, 99999999)}",
                customer_tier_id=tiers[i % len(tiers)].id,
                billing_address=f"{100 + i} Business Park, {city}",
                shipping_address=f"{200 + i} Logistics Road, {city}",
                is_active=i % 25 != 0,
                created_at=now_utc() - timedelta(days=rng.randint(1, 240)),
                updated_at=now_utc(),
            )
        )
    session.add_all(customers)
    session.flush()
    return customers


def seed_categories(session: Session, count: int) -> list[ProductCategory]:
    base = [
        "Cloud Software", "Hardware", "Networking", "Security", "Data & Analytics",
        "Productivity", "Professional Services", "Support", "Infrastructure", "Accessories",
    ]
    categories: list[ProductCategory] = []
    for i in range(count):
        categories.append(
            ProductCategory(
                id=deterministic_uuid("category", i),
                name=f"{MOCK_MARKER} {DATASET_SEED} {base[i % len(base)]} {i + 1}",
                description=f"Demo catalog category {i + 1}.",
                is_active=True,
                created_at=now_utc() - timedelta(days=180 - i),
                updated_at=now_utc(),
            )
        )
    session.add_all(categories)
    session.flush()
    return categories


def seed_products(session: Session, categories: Sequence[ProductCategory], rng: random.Random, count: int) -> list[Product]:
    products: list[Product] = []
    units = ["unit", "license", "seat", "hour", "month", "pack"]
    for i in range(count):
        is_subscription = i % 7 == 0
        cost = money(rng.uniform(20, 2500))
        margin = Decimal(str(rng.uniform(0.18, 0.48)))
        base_price = money(cost * (Decimal("1.00") + margin))
        tax_rate = money([5, 12, 18, 28][i % 4])
        products.append(
            Product(
                id=deterministic_uuid("product", i),
                category_id=categories[i % len(categories)].id,
                name=f"{MOCK_MARKER} Product {i + 1:03d}",
                description=f"Demo product {i + 1} with realistic pricing, cost and tax snapshots.",
                sku=f"DF360-MOCK-{DATASET_SEED}-{i + 1:05d}",
                unit=units[i % len(units)],
                base_price=base_price,
                cost_price=cost,
                tax_rate=tax_rate,
                is_subscription=is_subscription,
                is_active=i % 31 != 0,
                created_at=now_utc() - timedelta(days=rng.randint(1, 365)),
                updated_at=now_utc(),
            )
        )
    session.add_all(products)
    session.flush()
    return products


def seed_variants(session: Session, products: Sequence[Product], rng: random.Random) -> list[ProductVariant]:
    variants: list[ProductVariant] = []
    attributes = [
        ("Size", ["Small", "Medium", "Large"]),
        ("Edition", ["Standard", "Professional", "Enterprise"]),
        ("Pack", ["5", "10", "25"]),
        ("Term", ["Monthly", "Annual"]),
    ]
    for i, product in enumerate(products):
        # Most products get 1 variant, every third gets 2.
        variant_count = 2 if i % 3 == 0 else 1
        for j in range(variant_count):
            attr_name, values = attributes[i % len(attributes)]
            value = values[j % len(values)]
            variants.append(
                ProductVariant(
                    id=deterministic_uuid("variant", i * 2 + j),
                    product_id=product.id,
                    attribute_name=attr_name,
                    attribute_value=value,
                    extra_price=money(rng.uniform(0, 250)),
                    sku=f"{product.sku}-V{j + 1}",
                    is_active=True,
                    created_at=now_utc() - timedelta(days=rng.randint(1, 300)),
                    updated_at=now_utc(),
                )
            )
    session.add_all(variants)
    session.flush()
    return variants


def seed_price_lists(session: Session, tiers: Sequence[CustomerTier], count: int) -> list[PriceList]:
    currencies = ["INR", "USD", "EUR"]
    price_lists: list[PriceList] = []
    for i in range(count):
        price_lists.append(
            PriceList(
                id=deterministic_uuid("price-list", i),
                name=f"{MOCK_MARKER} {DATASET_SEED} Price List {i + 1:02d}",
                customer_tier_id=tiers[i % len(tiers)].id if i % 5 != 0 else None,
                currency=currencies[i % len(currencies)],
                is_active=True,
                created_at=now_utc() - timedelta(days=120 - i),
                updated_at=now_utc(),
            )
        )
    session.add_all(price_lists)
    session.flush()
    return price_lists


def seed_price_list_items(session: Session, price_lists: Sequence[PriceList], products: Sequence[Product], variants: Sequence[ProductVariant], rng: random.Random) -> list[PriceListItem]:
    variant_by_product: dict[uuid.UUID, list[ProductVariant]] = {}
    for variant in variants:
        variant_by_product.setdefault(variant.product_id, []).append(variant)

    items: list[PriceListItem] = []
    index = 0
    # Each price list receives every 4th product, resulting in substantial catalog data.
    for p_idx, price_list in enumerate(price_lists):
        for product in products[p_idx % 4 :: 4]:
            price = money(product.base_price * Decimal(str(rng.uniform(0.90, 1.08))))
            items.append(
                PriceListItem(
                    id=deterministic_uuid("price-list-item", index),
                    price_list_id=price_list.id,
                    product_id=product.id,
                    variant_id=(variant_by_product.get(product.id) or [None])[0].id
                    if variant_by_product.get(product.id)
                    else None,
                    price=price,
                    created_at=now_utc() - timedelta(days=rng.randint(1, 120)),
                    updated_at=now_utc(),
                )
            )
            index += 1
    session.add_all(items)
    session.flush()
    return items


def seed_discount_rules(session: Session, tiers: Sequence[CustomerTier], categories: Sequence[ProductCategory], count: int) -> list[DiscountRule]:
    rules: list[DiscountRule] = []
    for i in range(count):
        rules.append(
            DiscountRule(
                id=deterministic_uuid("discount-rule", i),
                customer_tier_id=tiers[i % len(tiers)].id if i % 3 != 0 else None,
                category_id=categories[i % len(categories)].id if i % 4 != 0 else None,
                max_discount_percent=money(5 + (i % 8) * 2.5),
                priority=i % 10,
                is_active=True,
                created_at=now_utc() - timedelta(days=rng_global.randint(1, 180)),
                updated_at=now_utc(),
            )
        )
    session.add_all(rules)
    session.flush()
    return rules


def seed_approval_policies(session: Session, count: int) -> list[ApprovalPolicy]:
    policies: list[ApprovalPolicy] = []
    ranges = [(0, 20, False, False), (20, 45, True, False), (45, 70, True, True), (70, 100, True, True)]
    for i in range(count):
        low, high, manager, finance = ranges[i % len(ranges)]
        policies.append(
            ApprovalPolicy(
                id=deterministic_uuid("approval-policy", i),
                name=f"{MOCK_MARKER} {DATASET_SEED} Risk Policy {i + 1:02d}",
                min_risk_score=money(low),
                max_risk_score=money(high),
                requires_manager=manager,
                requires_finance=finance,
                priority=i,
                is_active=True,
                created_at=now_utc() - timedelta(days=150 - i),
                updated_at=now_utc(),
            )
        )
    session.add_all(policies)
    session.flush()
    return policies


def seed_warehouses(session: Session, count: int) -> list[Warehouse]:
    cities = ["Ahmedabad", "Mumbai", "Bengaluru", "Delhi"]
    warehouses: list[Warehouse] = []
    for i in range(count):
        warehouses.append(
            Warehouse(
                id=deterministic_uuid("warehouse", i),
                name=f"{MOCK_MARKER} {DATASET_SEED} Warehouse {i + 1:02d}",
                code=f"DFM-WH-{DATASET_SEED}-{i + 1:02d}",
                address=f"{500 + i} Fulfillment Avenue, {cities[i % len(cities)]}",
                shipping_cost_weight=money(1 + i * 0.25),
                replenishment_enabled=i % 2 == 0,
                is_active=True,
                created_at=now_utc() - timedelta(days=180 - i),
                updated_at=now_utc(),
            )
        )
    session.add_all(warehouses)
    session.flush()
    return warehouses


def seed_inventory(session: Session, warehouses: Sequence[Warehouse], products: Sequence[Product], rng: random.Random) -> list[Inventory]:
    records: list[Inventory] = []
    index = 0
    # Every warehouse has every 5th product. UniqueConstraint remains satisfied.
    for w_idx, warehouse in enumerate(warehouses):
        for product in products[w_idx % 5 :: 5]:
            on_hand = Decimal(rng.randint(0, 500))
            reserved = Decimal(rng.randint(0, int(on_hand))) if on_hand else Decimal("0")
            records.append(
                Inventory(
                    id=deterministic_uuid("inventory", index),
                    warehouse_id=warehouse.id,
                    product_id=product.id,
                    quantity_on_hand=on_hand,
                    quantity_reserved=reserved,
                    reorder_level=Decimal(rng.randint(10, 100)),
                    reorder_quantity=Decimal(rng.randint(50, 250)),
                    updated_at=now_utc(),
                )
            )
            index += 1
    session.add_all(records)
    session.flush()
    return records


def seed_subscription_plans(session: Session, count: int) -> list[SubscriptionPlan]:
    plans: list[SubscriptionPlan] = []
    for i in range(count):
        plans.append(
            SubscriptionPlan(
                id=deterministic_uuid("subscription-plan", i),
                name=f"{MOCK_MARKER} {DATASET_SEED} Subscription Plan {i + 1:02d}",
                billing_interval=enum_cycle(BillingInterval, i),
                interval_count=1 if i % 3 else 12,
                proration_method=enum_cycle(ProrationMethod, i),
                cancellation_policy=["30-day notice", "Immediate", "End of term"][i % 3],
                refund_policy=["No refund", "Prorated", "30-day refund"][i % 3],
                is_active=True,
                created_at=now_utc() - timedelta(days=120 - i),
                updated_at=now_utc(),
            )
        )
    session.add_all(plans)
    session.flush()
    return plans


def build_quote_statuses(count: int) -> list[Enum]:
    members = enum_members(QuotationStatus)
    preferred = [
        "DRAFT", "SENT", "PENDING_APPROVAL", "REVISION_REQUIRED",
        "APPROVED", "CONFIRMED", "REJECTED", "EXPIRED",
    ]
    ordered = []
    for name in preferred:
        member = next((m for m in members if m.name.upper() == name), None)
        if member and member not in ordered:
            ordered.append(member)
    for member in members:
        if member not in ordered:
            ordered.append(member)
    return [ordered[i % len(ordered)] for i in range(count)]


def is_confirmable_quote(status: Enum) -> bool:
    return status.name.upper() in {
        "CONFIRMED", "ACCEPTED", "WON", "APPROVED",
    }


def seed_quotations_and_lines(
    session: Session,
    customers: Sequence[Customer],
    sales_users: Sequence[User],
    products: Sequence[Product],
    variants: Sequence[ProductVariant],
    tiers: Sequence[CustomerTier],
    rng: random.Random,
    count: int,
) -> tuple[list[Quotation], list[QuotationLine]]:
    variant_by_product: dict[uuid.UUID, list[ProductVariant]] = {}
    for variant in variants:
        variant_by_product.setdefault(variant.product_id, []).append(variant)

    # Use only users that are safe sales-rep candidates; the model itself does not
    # constrain role, so fall back to all existing users if necessary.
    reps = list(sales_users) or list(session.scalars(select(User)).all())
    quote_statuses = build_quote_statuses(count)
    quotations: list[Quotation] = []
    lines: list[QuotationLine] = []

    for i in range(count):
        created = now_utc() - timedelta(days=rng.randint(1, 180), hours=rng.randint(0, 12))
        status = quote_statuses[i]
        line_count = rng.randint(1, 5)
        customer = customers[i % len(customers)]
        rep = reps[i % len(reps)]

        q_lines: list[QuotationLine] = []
        subtotal = Decimal("0.00")
        discount_amount = Decimal("0.00")
        tax_amount = Decimal("0.00")
        total_cost = Decimal("0.00")

        for j in range(line_count):
            product = products[(i * 7 + j * 13) % len(products)]
            variant = (variant_by_product.get(product.id) or [None])[(i + j) % max(1, len(variant_by_product.get(product.id) or [None]))]
            quantity = Decimal(rng.randint(1, 25))
            unit_price = money(product.base_price + (variant.extra_price if variant else Decimal("0")))

            # Deliberately include some risky/high-discount scenarios.
            if i % 11 == 0:
                discount_pct = money(rng.uniform(12, 24))
            else:
                discount_pct = money(rng.uniform(0, 10))
            allowed = tiers[i % len(tiers)].default_discount_limit
            discount_excess = max(Decimal("0.00"), discount_pct - allowed)
            gross = money(quantity * unit_price)
            line_discount = money(gross * discount_pct / Decimal("100"))
            net = money(gross - line_discount)
            tax = money(net * product.tax_rate / Decimal("100"))
            cost = money(quantity * product.cost_price)
            margin = money(net - cost)
            margin_pct = money((margin / net * Decimal("100")) if net else 0)

            line = QuotationLine(
                id=deterministic_uuid("quotation-line", i * 6 + j),
                quotation_id=deterministic_uuid("quotation", i),
                product_id=product.id,
                variant_id=variant.id if variant else None,
                description=f"{product.name} - demo quote line {j + 1}",
                quantity=quantity,
                unit_price=unit_price,
                discount_percent=discount_pct,
                discount_amount=line_discount,
                tax_rate=product.tax_rate,
                line_total=money(net + tax),
                unit_cost=product.cost_price,
                margin_amount=margin,
                margin_percent=margin_pct,
                allowed_discount_percent=allowed,
                discount_excess_percent=discount_excess,
                created_at=created,
                updated_at=created,
            )
            q_lines.append(line)
            lines.append(line)
            subtotal += gross
            discount_amount += line_discount
            tax_amount += tax
            total_cost += cost

        subtotal = money(subtotal)
        discount_amount = money(discount_amount)
        tax_amount = money(tax_amount)
        total_amount = money(subtotal - discount_amount + tax_amount)
        margin_amount = money(total_amount - total_cost)
        margin_percent = money((margin_amount / total_amount * Decimal("100")) if total_amount else 0)
        risk = money(clamp(
            Decimal("10")
            + (Decimal("55") - margin_percent) * Decimal("0.7")
            + (Decimal("8") if discount_amount > subtotal * Decimal("0.12") else Decimal("0"))
            + Decimal(str(rng.uniform(-5, 8))),
            Decimal("0"), Decimal("100"),
        ))
        approval_required = risk >= Decimal("20") or any(l.discount_excess_percent > 0 for l in q_lines)
        approval_level = "FINANCE" if risk >= Decimal("45") else ("MANAGER" if approval_required else None)
        sent_at = created + timedelta(hours=rng.randint(2, 72)) if status.name.upper() not in {"DRAFT"} else None
        last_activity = created + timedelta(days=rng.randint(0, 10))
        valid_until = (created.date() + timedelta(days=rng.randint(15, 45))) if status.name.upper() not in {"DRAFT"} else None

        quotation = Quotation(
            id=deterministic_uuid("quotation", i),
            quotation_number=f"DF360-Q-{DATASET_SEED}-{i + 1:05d}",
            customer_id=customer.id,
            sales_rep_id=rep.id,
            status=status,
            subtotal=subtotal,
            discount_amount=discount_amount,
            order_discount_percent=money((discount_amount / subtotal * Decimal("100")) if subtotal else 0),
            tax_amount=tax_amount,
            total_amount=total_amount,
            total_cost=total_cost,
            margin_amount=margin_amount,
            margin_percent=margin_percent,
            risk_score=risk,
            approval_required=approval_required,
            current_approval_level=approval_level,
            sent_at=sent_at,
            last_activity_at=last_activity,
            valid_until=valid_until,
            created_at=created,
            updated_at=last_activity,
        )
        quotations.append(quotation)
        session.add(quotation)

    session.flush()
    session.add_all(lines)
    session.flush()
    return quotations, lines


def seed_approvals(session: Session, quotations: Sequence[Quotation], users: Sequence[User], rng: random.Random) -> tuple[list[ApprovalInstance], int]:
    manager = next((u for u in users if "MANAGER" in u.role.name.upper()), users[0])
    finance = next((u for u in users if "FINANCE" in u.role.name.upper()), users[-1])
    instances: list[ApprovalInstance] = []
    step_index = 0
    for i, quotation in enumerate(quotations):
        if not quotation.approval_required and i % 9 != 0:
            continue
        # Some negotiated/risky quotes intentionally receive a second approval instance.
        instance_count = 2 if i % 17 == 0 else 1
        for n in range(instance_count):
            risk = quotation.risk_score + Decimal(str(n * 3))
            if i % 17 == 0 and n == 0:
                status = status_or_first(ApprovalStatus, "REJECTED", "COMPLETED", "APPROVED")
            elif is_confirmable_quote(quotation.status):
                status = status_or_first(ApprovalStatus, "APPROVED", "COMPLETED", "PENDING")
            else:
                status = status_or_first(ApprovalStatus, "PENDING", "IN_PROGRESS", "SUBMITTED")
            started = quotation.created_at + timedelta(hours=2 + n * 8)
            completed = started + timedelta(hours=rng.randint(2, 36)) if status.name.upper() not in {"PENDING", "IN_PROGRESS", "SUBMITTED"} else None
            instance = ApprovalInstance(
                id=deterministic_uuid("approval-instance", i * 2 + n),
                quotation_id=quotation.id,
                risk_score=money(risk),
                status=status,
                started_at=started,
                completed_at=completed,
                created_at=started,
                updated_at=completed or started,
            )
            session.add(instance)
            instances.append(instance)
            session.flush()

            needs_finance = risk >= Decimal("45")
            roles: list[Enum] = []
            manager_role = enum_by_name(ApproverRole, "MANAGER", "SALES_MANAGER", fallback_index=0)
            finance_role = enum_by_name(ApproverRole, "FINANCE", "FINANCE_MANAGER", fallback_index=1)
            roles.append(manager_role)
            if needs_finance:
                roles.append(finance_role)
            for order, role in enumerate(roles, start=1):
                if order == 1 and status.name.upper() in {"PENDING", "IN_PROGRESS", "SUBMITTED"}:
                    step_status = status_or_first(ApprovalStatus, "PENDING", "IN_PROGRESS", "SUBMITTED")
                    approver = manager
                elif order == 2 and status.name.upper() in {"PENDING", "IN_PROGRESS", "SUBMITTED"}:
                    step_status = status_or_first(ApprovalStatus, "PENDING", "IN_PROGRESS", "SUBMITTED")
                    approver = finance
                else:
                    step_status = status
                    approver = manager if order == 1 else finance
                session.add(
                    ApprovalStep(
                        id=deterministic_uuid("approval-step", step_index),
                        approval_instance_id=instance.id,
                        step_order=order,
                        approver_role=role,
                        approver_user_id=approver.id,
                        status=step_status,
                        decision_reason=("Margin/discount risk reviewed in demo data." if step_status != status_or_first(ApprovalStatus, "PENDING", "IN_PROGRESS", "SUBMITTED") else None),
                        decided_at=completed if step_status.name.upper() not in {"PENDING", "IN_PROGRESS", "SUBMITTED"} else None,
                        created_at=started,
                        updated_at=completed or started,
                    )
                )
                step_index += 1
    session.flush()
    return instances, step_index


def seed_negotiations(session: Session, quotations: Sequence[Quotation], customers: Sequence[Customer], users: Sequence[User], lines: Sequence[QuotationLine], rng: random.Random) -> tuple[list[NegotiationRequest], int]:
    by_quote: dict[uuid.UUID, list[QuotationLine]] = {}
    for line in lines:
        by_quote.setdefault(line.quotation_id, []).append(line)

    requests: list[NegotiationRequest] = []
    comments: list[NegotiationComment] = []
    customer_users = [u for u in users if "CUSTOMER" in u.role.name.upper()] or list(users)
    internal_users = [u for u in users if "CUSTOMER" not in u.role.name.upper()] or list(users)

    request_idx = 0
    comment_idx = 0
    for i, quotation in enumerate(quotations):
        if i % 4 != 0:
            continue
        customer = customers[i % len(customers)]
        requester = customer_users[i % len(customer_users)]
        requested_discount = money(rng.uniform(5, 20))
        status = enum_by_name(
            NegotiationRequestStatus,
            "APPROVED" if i % 3 == 0 else "SUBMITTED",
            "PENDING",
            fallback_index=i,
        )
        if i % 9 == 0:
            status = enum_by_name(NegotiationRequestStatus, "REJECTED", "CANCELLED", fallback_index=2)
        request = NegotiationRequest(
            id=deterministic_uuid("negotiation-request", request_idx),
            quotation_id=quotation.id,
            customer_id=customer.id,
            requested_by=requester.id,
            requested_discount_percent=requested_discount,
            requested_changes={
                "discount_percent": float(requested_discount),
                "requested_delivery_days": 7 + (i % 14),
                "note": "Demo negotiation request",
            },
            reason="Customer requested improved commercial terms for demo scenario.",
            status=status,
            created_at=quotation.created_at + timedelta(days=1),
            updated_at=quotation.created_at + timedelta(days=2),
        )
        session.add(request)
        requests.append(request)
        request_idx += 1

        for c in range(1 + (i % 3 == 0)):
            line_list = by_quote.get(quotation.id, [])
            line = line_list[c % len(line_list)] if line_list else None
            commenter = requester if c % 2 == 0 else internal_users[(i + c) % len(internal_users)]
            session.add(
                NegotiationComment(
                    id=deterministic_uuid("negotiation-comment", comment_idx),
                    quotation_id=quotation.id,
                    quotation_line_id=line.id if line else None,
                    user_id=commenter.id,
                    comment=(
                        "Customer asks whether volume pricing can be improved."
                        if c % 2 == 0
                        else "Sales team is reviewing margin impact and approval requirements."
                    ),
                    created_at=quotation.created_at + timedelta(days=1, hours=c + 1),
                    updated_at=quotation.created_at + timedelta(days=1, hours=c + 2),
                )
            )
            comment_idx += 1
    session.flush()
    return requests, comment_idx


def seed_orders_and_fulfillment(
    session: Session,
    quotations: Sequence[Quotation],
    lines: Sequence[QuotationLine],
    warehouses: Sequence[Warehouse],
    rng: random.Random,
) -> tuple[list[Order], list[FulfillmentAllocation], list[Backorder]]:
    lines_by_quote: dict[uuid.UUID, list[QuotationLine]] = {}
    for line in lines:
        lines_by_quote.setdefault(line.quotation_id, []).append(line)

    orders: list[Order] = []
    allocations: list[FulfillmentAllocation] = []
    backorders: list[Backorder] = []
    alloc_idx = 0
    back_idx = 0

    eligible = [q for q in quotations if is_confirmable_quote(q.status)]
    for i, quotation in enumerate(eligible):
        order = Order(
            id=deterministic_uuid("order", i),
            order_number=f"DF360-O-{DATASET_SEED}-{i + 1:05d}",
            quotation_id=quotation.id,
            customer_id=quotation.customer_id,
            status=enum_cycle(OrderStatus, i),
            total_amount=quotation.total_amount,
            confirmed_at=quotation.updated_at,
            created_at=quotation.updated_at,
            updated_at=now_utc(),
        )
        session.add(order)
        orders.append(order)
    session.flush()

    for i, order in enumerate(orders):
        q_lines = lines_by_quote.get(order.quotation_id, [])
        for j, line in enumerate(q_lines):
            qty = line.quantity
            # Roughly one quarter of allocations have a shortage/backorder.
            if (i + j) % 4 == 0 and qty > Decimal("2"):
                allocated = (qty * Decimal("0.60")).quantize(Decimal("0.01"))
                fulfilled = (allocated * Decimal("0.70")).quantize(Decimal("0.01"))
                shortage = qty - allocated
                backorder_status = enum_by_name(BackorderStatus, "OPEN", "PARTIALLY_FULFILLED", "PENDING", fallback_index=back_idx)
                session.add(
                    Backorder(
                        id=deterministic_uuid("backorder", back_idx),
                        order_id=order.id,
                        quotation_line_id=line.id,
                        quantity_backordered=shortage,
                        quantity_remaining=shortage,
                        status=backorder_status,
                        consolidation_requested=back_idx % 3 == 0,
                        created_at=order.created_at,
                        updated_at=now_utc(),
                    )
                )
                backorders.append(backorder_status)  # replaced below; keeps count tracking simple
                back_idx += 1
            else:
                allocated = qty
                fulfilled = qty if (i + j) % 3 != 0 else money(qty * Decimal("0.50"))

            warehouse = warehouses[(i + j) % len(warehouses)]
            alloc_status = enum_by_name(
                FulfillmentAllocationStatus,
                "FULFILLED" if fulfilled >= allocated else "PARTIALLY_FULFILLED",
                "ALLOCATED",
                "SUGGESTED",
                fallback_index=alloc_idx,
            )
            session.add(
                FulfillmentAllocation(
                    id=deterministic_uuid("fulfillment-allocation", alloc_idx),
                    order_id=order.id,
                    quotation_line_id=line.id,
                    warehouse_id=warehouse.id,
                    quantity_allocated=allocated,
                    quantity_fulfilled=fulfilled,
                    estimated_shipping_cost=money(25 + rng.uniform(0, 150)),
                    is_suggested=alloc_idx % 2 == 0,
                    is_manual_override=alloc_idx % 7 == 0,
                    status=alloc_status,
                    created_at=order.created_at,
                    updated_at=now_utc(),
                )
            )
            allocations.append(alloc_status)
            alloc_idx += 1
    session.flush()

    # Fetch the actual generated backorders for return typing.
    actual_backorders = list(session.scalars(select(Backorder).where(Backorder.order_id.in_([o.id for o in orders]))).all()) if orders else []
    return orders, allocations, actual_backorders


def seed_subscriptions_billing(
    session: Session,
    orders: Sequence[Order],
    quotations: Sequence[Quotation],
    lines: Sequence[QuotationLine],
    products: Sequence[Product],
    plans: Sequence[SubscriptionPlan],
    rng: random.Random,
) -> tuple[list[Subscription], list[BillingSchedule], list[Invoice], list[Payment]]:
    quote_by_id = {q.id: q for q in quotations}
    products_by_id = {p.id: p for p in products}
    subscriptions: list[Subscription] = []
    schedules: list[BillingSchedule] = []
    invoices: list[Invoice] = []
    payments: list[Payment] = []
    subscription_lines = [
        line for line in lines if products_by_id[line.product_id].is_subscription
    ]
    sub_idx = 0
    schedule_idx = 0
    invoice_idx = 0
    payment_idx = 0

    for order in orders:
        q = quote_by_id[order.quotation_id]
        q_lines = [l for l in subscription_lines if l.quotation_id == q.id]
        for line in q_lines:
            product = products_by_id[line.product_id]
            plan = plans[sub_idx % len(plans)]
            start = order.confirmed_at.date()
            next_bill = start + timedelta(days=30 if sub_idx % 2 == 0 else 365)
            sub_status = enum_by_name(SubscriptionStatus, "ACTIVE", "PAUSED", "CANCELLED", fallback_index=sub_idx)
            subscription = Subscription(
                id=deterministic_uuid("subscription", sub_idx),
                order_id=order.id,
                quotation_line_id=line.id,
                customer_id=q.customer_id,
                product_id=product.id,
                plan_id=plan.id,
                quantity=line.quantity,
                unit_price=line.unit_price,
                start_date=start,
                next_billing_date=next_bill,
                status=sub_status,
                created_at=order.created_at,
                updated_at=now_utc(),
            )
            session.add(subscription)
            subscriptions.append(subscription)
            session.flush()

            # Two schedule entries per subscription gives useful recurring billing data.
            for n in range(2):
                bill_date = next_bill + timedelta(days=30 * n)
                sched_status = enum_by_name(
                    BillingScheduleStatus,
                    "INVOICED" if n == 0 else "SCHEDULED",
                    "PENDING",
                    fallback_index=schedule_idx,
                )
                schedule = BillingSchedule(
                    id=deterministic_uuid("billing-schedule", schedule_idx),
                    subscription_id=subscription.id,
                    billing_date=bill_date,
                    amount=money(line.quantity * line.unit_price),
                    status=sched_status,
                    proration_amount=money(rng.uniform(0, 100)) if n == 0 else Decimal("0.00"),
                    created_at=order.created_at,
                    updated_at=now_utc(),
                )
                session.add(schedule)
                schedules.append(schedule)
                schedule_idx += 1

            sub_idx += 1

    session.flush()

    # One-time invoice for each order.
    for i, order in enumerate(orders):
        issued = order.confirmed_at + timedelta(days=1)
        total = money(order.total_amount)
        paid = Decimal("0.00")
        if i % 5 == 0:
            paid = total
        elif i % 5 in {1, 2}:
            paid = money(total * Decimal("0.40"))
        invoice_status = (
            enum_by_name(InvoiceStatus, "PAID", "PARTIALLY_PAID", "ISSUED", fallback_index=i)
            if paid > 0
            else enum_by_name(InvoiceStatus, "ISSUED", "OPEN", "DRAFT", fallback_index=i)
        )
        invoice = Invoice(
            id=deterministic_uuid("invoice", invoice_idx),
            invoice_number=f"DF360-INV-{DATASET_SEED}-{invoice_idx + 1:05d}",
            order_id=order.id,
            billing_schedule_id=None,
            invoice_type=enum_by_name(InvoiceType, "ONE_TIME", "STANDARD", fallback_index=0),
            subtotal=money(total * Decimal("0.85")),
            tax_amount=money(total * Decimal("0.15")),
            total_amount=total,
            paid_amount=paid,
            status=invoice_status,
            due_date=(issued.date() + timedelta(days=30)),
            issued_at=issued,
            created_at=issued,
            updated_at=now_utc(),
        )
        session.add(invoice)
        invoices.append(invoice)
        session.flush()

        if paid > 0:
            payment = Payment(
                id=deterministic_uuid("payment", payment_idx),
                invoice_id=invoice.id,
                amount=paid,
                payment_method=["Bank Transfer", "Credit Card", "UPI", "Wire Transfer"][i % 4],
                transaction_reference=f"DF360-TXN-{DATASET_SEED}-{payment_idx + 1:06d}",
                payment_date=issued + timedelta(days=min(20, i % 20)),
                status=enum_by_name(PaymentStatus, "RECORDED", "COMPLETED", "SETTLED", fallback_index=i),
                created_at=issued,
                updated_at=now_utc(),
            )
            session.add(payment)
            payments.append(payment)
            payment_idx += 1
        invoice_idx += 1

    # Recurring invoices from the first schedule of selected subscriptions.
    for i, schedule in enumerate(schedules):
        if i % 3 != 0:
            continue
        sub = session.get(Subscription, schedule.subscription_id)
        if not sub:
            continue
        order = session.get(Order, sub.order_id)
        if not order:
            continue
        total = money(schedule.amount + schedule.proration_amount)
        invoice = Invoice(
            id=deterministic_uuid("invoice", invoice_idx),
            invoice_number=f"DF360-INV-{DATASET_SEED}-{invoice_idx + 1:05d}",
            order_id=order.id,
            billing_schedule_id=schedule.id,
            invoice_type=enum_by_name(InvoiceType, "RECURRING", "SUBSCRIPTION", fallback_index=1),
            subtotal=money(total * Decimal("0.85")),
            tax_amount=money(total * Decimal("0.15")),
            total_amount=total,
            paid_amount=Decimal("0.00"),
            status=enum_by_name(InvoiceStatus, "ISSUED", "OPEN", "DRAFT", fallback_index=1),
            due_date=schedule.billing_date + timedelta(days=15),
            issued_at=now_utc(),
            created_at=now_utc(),
            updated_at=now_utc(),
        )
        session.add(invoice)
        invoices.append(invoice)
        invoice_idx += 1

    # A few credit notes demonstrate the hybrid billing design.
    for i, order in enumerate(orders):
        if i % 10 != 0:
            continue
        amount = money(order.total_amount * Decimal("0.10"))
        invoice = Invoice(
            id=deterministic_uuid("invoice", invoice_idx),
            invoice_number=f"DF360-CN-{DATASET_SEED}-{i + 1:05d}",
            order_id=order.id,
            billing_schedule_id=None,
            invoice_type=enum_by_name(InvoiceType, "CREDIT_NOTE", "CREDIT", fallback_index=2),
            subtotal=-amount,
            tax_amount=Decimal("0.00"),
            total_amount=-amount,
            paid_amount=Decimal("0.00"),
            status=enum_by_name(InvoiceStatus, "ISSUED", "OPEN", "DRAFT", fallback_index=0),
            due_date=None,
            issued_at=now_utc(),
            created_at=now_utc(),
            updated_at=now_utc(),
        )
        session.add(invoice)
        invoices.append(invoice)
        invoice_idx += 1

    session.flush()
    return subscriptions, schedules, invoices, payments


def seed_recommendations(session: Session, products: Sequence[Product], count: int) -> list[RecommendationRule]:
    rules: list[RecommendationRule] = []
    for i in range(count):
        source_idx = i % len(products)
        target_idx = (source_idx + 1 + (i % 17)) % len(products)
        if source_idx == target_idx:
            target_idx = (target_idx + 1) % len(products)
        rules.append(
            RecommendationRule(
                id=deterministic_uuid("recommendation-rule", i),
                source_product_id=products[source_idx].id,
                recommended_product_id=products[target_idx].id,
                rule_type=enum_cycle(RecommendationType, i),
                priority=i % 10,
                promotion_tag=["UPSELL", "CROSS_SELL", "BUNDLE", None][i % 4],
                min_margin_percent=money(20 + (i % 6) * 5) if i % 3 else None,
                co_purchase_score=money(40 + (i % 60)) if i % 2 == 0 else None,
                is_promoted=i % 5 == 0,
                is_active=True,
                created_at=now_utc() - timedelta(days=90 - i % 30),
                updated_at=now_utc(),
            )
        )
    session.add_all(rules)
    session.flush()
    return rules


def seed_alerts(session: Session, quotations: Sequence[Quotation], count: int) -> list[DealAlert]:
    alerts: list[DealAlert] = []
    for i in range(count):
        q = quotations[i % len(quotations)]
        if i % 3 == 0:
            alert_name = "HIGH_DISCOUNT"
            title = "Discount exceeds allowed limit"
            message = "Demo alert: requested discount is above the customer/category ceiling."
            metric = q.order_discount_percent
            threshold = Decimal("10.00")
        elif i % 3 == 1:
            alert_name = "STALE_DEAL"
            title = "Deal has low recent activity"
            message = "Demo alert: quotation activity has stalled and should be reviewed."
            metric = Decimal(str((now_utc() - q.last_activity_at).days))
            threshold = Decimal("7.00")
        else:
            alert_name = "LOW_MARGIN"
            title = "Quotation margin is below target"
            message = "Demo alert: projected margin is lower than the configured target."
            metric = q.margin_percent
            threshold = Decimal("20.00")
        alert_type = enum_by_name(DealAlertType, alert_name, "DISCOUNT_RISK", "MARGIN_RISK", "STALE_DEAL", fallback_index=i)
        severity = enum_by_name(DealAlertSeverity, "CRITICAL" if q.risk_score >= 70 else "HIGH" if q.risk_score >= 45 else "MEDIUM", "LOW", fallback_index=i)
        status = enum_by_name(DealAlertStatus, "OPEN", "ACKNOWLEDGED", "RESOLVED", fallback_index=i)
        alerts.append(
            DealAlert(
                id=deterministic_uuid("deal-alert", i),
                quotation_id=q.id,
                alert_type=alert_type,
                severity=severity,
                title=f"{MOCK_MARKER}: {title}",
                message=message,
                metric_value=money(metric),
                threshold_value=money(threshold),
                status=status,
                action_taken="Reviewed by sales team" if status.name.upper() == "RESOLVED" else None,
                created_at=q.last_activity_at,
                updated_at=now_utc(),
            )
        )
    session.add_all(alerts)
    session.flush()
    return alerts


def seed_audit_logs(
    session: Session,
    users: Sequence[User],
    quotations: Sequence[Quotation],
    orders: Sequence[Order],
    invoices: Sequence[Invoice],
    count: int,
) -> list[AuditLog]:
    entities: list[tuple[str, uuid.UUID, str]] = []
    entities.extend(("quotation", q.id, "quotation.updated") for q in quotations)
    entities.extend(("order", o.id, "order.confirmed") for o in orders)
    entities.extend(("invoice", i.id, "invoice.issued") for i in invoices)
    logs: list[AuditLog] = []
    for i in range(count):
        entity_type, entity_id, action = entities[i % len(entities)]
        user = users[i % len(users)]
        logs.append(
            AuditLog(
                id=deterministic_uuid("audit-log", i),
                user_id=user.id,
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                old_values={"source": "mock", "sequence": max(0, i - 1)},
                new_values={"source": "mock", "sequence": i},
                reason="Seeded DealFlow360 demo audit event.",
                created_at=now_utc() - timedelta(hours=i),
            )
        )
    session.add_all(logs)
    session.flush()
    return logs


def seed_auth_sessions(session: Session, users: Sequence[User], count: int) -> list[AuthSession]:
    sessions: list[AuthSession] = []
    for i, user in enumerate(users[:count]):
        token_hash = hashlib.sha256(f"{MOCK_MARKER}:refresh:{i}".encode()).hexdigest()
        created = now_utc() - timedelta(days=i % 30)
        sessions.append(
            AuthSession(
                id=deterministic_uuid("auth-session", i),
                user_id=user.id,
                refresh_token_hash=token_hash,
                expires_at=created + timedelta(days=30),
                revoked_at=(created + timedelta(days=1) if i % 11 == 0 else None),
                created_at=created,
                last_used_at=(created + timedelta(hours=3) if i % 4 != 0 else None),
            )
        )
    session.add_all(sessions)
    session.flush()
    return sessions


def mock_data_exists(session: Session) -> bool:
    prefix = f"DF360-Q-{DATASET_SEED}-"
    return session.scalar(
        select(Quotation.id).where(Quotation.quotation_number.like(prefix + "%")).limit(1)
    ) is not None


def seed_all(args: argparse.Namespace) -> dict[str, int]:
    rng = random.Random(args.seed)
    engine = make_engine(args.database_url)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    with SessionLocal() as session:
        if mock_data_exists(session):
            raise SystemExit(
                f"Mock dataset for seed {DATASET_SEED} already exists. Use a different --seed "
                "to create another independent dataset."
            )

        # Seed in FK-safe dependency order.
        tiers = seed_customer_tiers(session, args.customer_tiers)
        customers = seed_customers(session, tiers, rng, args.customers)
        categories = seed_categories(session, args.categories)
        products = seed_products(session, categories, rng, args.products)
        variants = seed_variants(session, products, rng)
        price_lists = seed_price_lists(session, tiers, args.price_lists)
        price_list_items = seed_price_list_items(session, price_lists, products, variants, rng)
        discount_rules = seed_discount_rules(session, tiers, categories, args.discount_rules)
        approval_policies = seed_approval_policies(session, args.approval_policies)
        warehouses = seed_warehouses(session, args.warehouses)
        inventory = seed_inventory(session, warehouses, products, rng)
        plans = seed_subscription_plans(session, args.subscription_plans)

        users = seed_base_users(session, customers, rng, args.users)
        # Prefer internal users for sales representatives.
        sales_users = [u for u in users if "CUSTOMER" not in u.role.name.upper() and u.is_active]
        if not sales_users:
            sales_users = users
        auth_sessions = seed_auth_sessions(session, users, args.auth_sessions)

        quotations, quote_lines = seed_quotations_and_lines(
            session, customers, sales_users, products, variants, tiers, rng, args.quotations
        )
        approval_instances, approval_step_count = seed_approvals(session, quotations, users, rng)
        negotiation_requests, negotiation_comment_count = seed_negotiations(session, quotations, customers, users, quote_lines, rng)
        orders, allocations, backorders = seed_orders_and_fulfillment(
            session, quotations, quote_lines, warehouses, rng
        )
        subscriptions, billing_schedules, invoices, payments = seed_subscriptions_billing(
            session, orders, quotations, quote_lines, products, plans, rng
        )
        recommendations = seed_recommendations(session, products, args.recommendation_rules)
        alerts = seed_alerts(session, quotations, args.deal_alerts)
        audit_logs = seed_audit_logs(session, users, quotations, orders, invoices, args.audit_logs)

        session.commit()

    return {
        "customer_tiers": len(tiers),
        "customers": len(customers),
        "users": len(users),
        "auth_sessions": len(auth_sessions),
        "product_categories": len(categories),
        "products": len(products),
        "product_variants": len(variants),
        "price_lists": len(price_lists),
        "price_list_items": len(price_list_items),
        "discount_rules": len(discount_rules),
        "approval_policies": len(approval_policies),
        "approval_instances": len(approval_instances),
        "approval_steps": approval_step_count,
        "quotations": len(quotations),
        "quotation_lines": len(quote_lines),
        "orders": len(orders),
        "warehouses": len(warehouses),
        "inventory": len(inventory),
        "fulfillment_allocations": len(allocations),
        "backorders": len(backorders),
        "subscription_plans": len(plans),
        "subscriptions": len(subscriptions),
        "billing_schedules": len(billing_schedules),
        "invoices": len(invoices),
        "payments": len(payments),
        "recommendation_rules": len(recommendations),
        "negotiation_requests": len(negotiation_requests),
        "negotiation_comments": negotiation_comment_count,
        "deal_alerts": len(alerts),
        "audit_logs": len(audit_logs),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate relationally consistent DealFlow360 mock data.")
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL"), help="SQLAlchemy DATABASE_URL. Defaults to $DATABASE_URL.")
    parser.add_argument("--seed", type=int, default=360, help="Random seed for reproducible values.")
    parser.add_argument("--customer-tiers", type=int, default=6)
    parser.add_argument("--customers", type=int, default=80)
    parser.add_argument("--users", type=int, default=16)
    parser.add_argument("--auth-sessions", type=int, default=12)
    parser.add_argument("--categories", type=int, default=10)
    parser.add_argument("--products", type=int, default=220)
    parser.add_argument("--price-lists", type=int, default=6)
    parser.add_argument("--discount-rules", type=int, default=24)
    parser.add_argument("--approval-policies", type=int, default=6)
    parser.add_argument("--warehouses", type=int, default=4)
    parser.add_argument("--subscription-plans", type=int, default=6)
    parser.add_argument("--quotations", type=int, default=120)
    parser.add_argument("--recommendation-rules", type=int, default=80)
    parser.add_argument("--deal-alerts", type=int, default=70)
    parser.add_argument("--audit-logs", type=int, default=350)
    args = parser.parse_args()
    if not args.database_url:
        parser.error("DATABASE_URL is not set. Export it or pass --database-url.")
    return args


# Module-level RNG is used only for a few small configuration tables.
rng_global = random.Random(360)


if __name__ == "__main__":
    args = parse_args()
    DATASET_SEED = args.seed
    counts = seed_all(args)
    print("\nDealFlow360 mock data generated successfully.\n")
    for table, count in counts.items():
        print(f"  {table:25s} {count:>6}")
    print("\nMinimum requested: 200 products, 100 quotations")
    print("Generated by default: 220 products, 120 quotations")

"""Tests for Customer creation, listing/search, detail retrieval, update, deactivation, quotation history, and order history endpoints."""

import uuid
from datetime import date
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.common.enums import (
    BillingInterval,
    OrderStatus,
    ProrationMethod,
    QuotationStatus,
    SubscriptionStatus,
    UserRole,
)
from app.core.security import create_access_token
from app.models.customer import Customer
from app.models.customer_tier import CustomerTier
from app.models.order import Order
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.quotation import Quotation
from app.models.quotation_line import QuotationLine
from app.models.subscription import Subscription
from app.models.subscription_plan import SubscriptionPlan
from app.models.user import User


def _create_auth_headers(user: User) -> dict:
    """Helper to generate Authorization header for a given user."""
    token = create_access_token(user_id=user.id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


def test_create_customer_success(client: TestClient, admin_user: User, db: Session):
    """Verify creating a B2B customer with valid active customer tier."""
    tier = CustomerTier(
        name="Enterprise Tier",
        default_discount_limit=Decimal("20.00"),
        is_active=True,
    )
    db.add(tier)
    db.commit()
    db.refresh(tier)

    headers = _create_auth_headers(admin_user)
    payload = {
        "name": "Global Tech Corp",
        "email": "contact@globaltech.com",
        "phone": "+1-555-0199",
        "customer_tier_id": str(tier.id),
        "billing_address": "100 Tech Blvd, Suite 400, San Francisco, CA",
        "shipping_address": "100 Tech Blvd, Dock 2, San Francisco, CA",
        "is_active": True,
    }

    response = client.post("/api/v1/customers", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()

    assert "id" in data
    assert data["name"] == "Global Tech Corp"
    assert data["email"] == "contact@globaltech.com"
    assert data["phone"] == "+1-555-0199"
    assert data["customer_tier_id"] == str(tier.id)
    assert data["billing_address"] == "100 Tech Blvd, Suite 400, San Francisco, CA"
    assert data["shipping_address"] == "100 Tech Blvd, Dock 2, San Francisco, CA"
    assert data["is_active"] is True
    assert "created_at" in data
    assert "updated_at" in data

    # Verify database persistence
    customer_in_db = db.get(Customer, uuid.UUID(data["id"]))
    assert customer_in_db is not None
    assert customer_in_db.name == "Global Tech Corp"
    assert customer_in_db.customer_tier_id == tier.id


def test_create_customer_by_sales_rep(client: TestClient, test_user: User, db: Session):
    """Verify SALES_REP can create a customer record."""
    tier = CustomerTier(
        name="Standard Tier",
        default_discount_limit=Decimal("10.00"),
        is_active=True,
    )
    db.add(tier)
    db.commit()
    db.refresh(tier)

    headers = _create_auth_headers(test_user)
    payload = {
        "name": "Acme Industries",
        "customer_tier_id": str(tier.id),
    }

    response = client.post("/api/v1/customers", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Acme Industries"
    assert data["customer_tier_id"] == str(tier.id)
    assert data["email"] is None
    assert data["is_active"] is True


def test_create_customer_nonexistent_tier_fails(client: TestClient, admin_user: User):
    """Verify assigning a non-existent customer tier returns 404."""
    headers = _create_auth_headers(admin_user)
    payload = {
        "name": "Orphan Customer",
        "customer_tier_id": str(uuid.uuid4()),
    }
    response = client.post("/api/v1/customers", json=payload, headers=headers)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_create_customer_inactive_tier_fails(client: TestClient, admin_user: User, db: Session):
    """Verify assigning an inactive customer tier returns 400."""
    tier = CustomerTier(
        name="Deprecated Tier",
        default_discount_limit=Decimal("5.00"),
        is_active=False,
    )
    db.add(tier)
    db.commit()
    db.refresh(tier)

    headers = _create_auth_headers(admin_user)
    payload = {
        "name": "Customer With Inactive Tier",
        "customer_tier_id": str(tier.id),
    }
    response = client.post("/api/v1/customers", json=payload, headers=headers)
    assert response.status_code == 400
    assert "inactive" in response.json()["detail"].lower()


def test_create_customer_unauthorized_and_forbidden(client: TestClient, db: Session):
    """Verify unauthenticated requests return 401 and CUSTOMER users return 403."""
    tier = CustomerTier(
        name="General Tier",
        default_discount_limit=Decimal("5.00"),
        is_active=True,
    )
    db.add(tier)
    db.commit()
    db.refresh(tier)

    payload = {
        "name": "Unauthorized Attempt",
        "customer_tier_id": str(tier.id),
    }

    # Unauthenticated
    resp_unauth = client.post("/api/v1/customers", json=payload)
    assert resp_unauth.status_code == 401

    # Authenticated as CUSTOMER role
    customer_user = User(
        name="Portal User",
        email="portal.user@customer.local",
        password_hash="fakehash",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db.add(customer_user)
    db.commit()
    db.refresh(customer_user)

    customer_headers = _create_auth_headers(customer_user)
    resp_cust = client.post("/api/v1/customers", json=payload, headers=customer_headers)
    assert resp_cust.status_code == 403


def test_list_customers_default_active_only(client: TestClient, test_user: User, db: Session):
    """Verify GET /api/v1/customers defaults to returning only active customers."""
    tier = CustomerTier(
        name="Tier List Test",
        default_discount_limit=Decimal("15.00"),
        is_active=True,
    )
    db.add(tier)
    db.commit()

    active_cust = Customer(
        name="Active Alpha Corp",
        email="alpha@test.com",
        customer_tier_id=tier.id,
        is_active=True,
    )
    inactive_cust = Customer(
        name="Inactive Beta Corp",
        email="beta@test.com",
        customer_tier_id=tier.id,
        is_active=False,
    )
    db.add_all([active_cust, inactive_cust])
    db.commit()

    headers = _create_auth_headers(test_user)
    response = client.get("/api/v1/customers", headers=headers)
    assert response.status_code == 200
    data = response.json()

    names = [c["name"] for c in data]
    assert "Active Alpha Corp" in names
    assert "Inactive Beta Corp" not in names


def test_list_customers_explicit_inactive_filter(client: TestClient, test_user: User, db: Session):
    """Verify GET /api/v1/customers?is_active=false returns inactive customers."""
    tier = CustomerTier(
        name="Tier Filter Test",
        default_discount_limit=Decimal("15.00"),
        is_active=True,
    )
    db.add(tier)
    db.commit()

    active_cust = Customer(
        name="Active Gamma Corp",
        customer_tier_id=tier.id,
        is_active=True,
    )
    inactive_cust = Customer(
        name="Inactive Delta Corp",
        customer_tier_id=tier.id,
        is_active=False,
    )
    db.add_all([active_cust, inactive_cust])
    db.commit()

    headers = _create_auth_headers(test_user)
    response = client.get("/api/v1/customers?is_active=false", headers=headers)
    assert response.status_code == 200
    data = response.json()

    names = [c["name"] for c in data]
    assert "Inactive Delta Corp" in names
    assert "Active Gamma Corp" not in names


def test_list_customers_search(client: TestClient, test_user: User, db: Session):
    """Verify search filter across customer name, email, and phone."""
    tier = CustomerTier(
        name="Tier Search Test",
        default_discount_limit=Decimal("10.00"),
        is_active=True,
    )
    db.add(tier)
    db.commit()

    c1 = Customer(
        name="Starlight Logistics",
        email="billing@starlight.io",
        phone="+1-555-8888",
        customer_tier_id=tier.id,
        is_active=True,
    )
    c2 = Customer(
        name="Apex Manufacturing",
        email="info@apex.com",
        phone="+1-555-9999",
        customer_tier_id=tier.id,
        is_active=True,
    )
    db.add_all([c1, c2])
    db.commit()

    headers = _create_auth_headers(test_user)

    # Search by name substring
    r_name = client.get("/api/v1/customers?search=starlight", headers=headers)
    assert r_name.status_code == 200
    assert len(r_name.json()) == 1
    assert r_name.json()[0]["name"] == "Starlight Logistics"

    # Search by email substring
    r_email = client.get("/api/v1/customers?search=apex.com", headers=headers)
    assert r_email.status_code == 200
    assert len(r_email.json()) == 1
    assert r_email.json()[0]["name"] == "Apex Manufacturing"

    # Search by phone substring
    r_phone = client.get("/api/v1/customers?search=8888", headers=headers)
    assert r_phone.status_code == 200
    assert len(r_phone.json()) == 1
    assert r_phone.json()[0]["name"] == "Starlight Logistics"


def test_list_customers_by_tier(client: TestClient, test_user: User, db: Session):
    """Verify filtering customers by customer_tier_id."""
    tier1 = CustomerTier(name="Tier 1", default_discount_limit=Decimal("5.00"), is_active=True)
    tier2 = CustomerTier(name="Tier 2", default_discount_limit=Decimal("10.00"), is_active=True)
    db.add_all([tier1, tier2])
    db.commit()

    cust1 = Customer(name="Tier 1 Customer", customer_tier_id=tier1.id, is_active=True)
    cust2 = Customer(name="Tier 2 Customer", customer_tier_id=tier2.id, is_active=True)
    db.add_all([cust1, cust2])
    db.commit()

    headers = _create_auth_headers(test_user)
    response = client.get(f"/api/v1/customers?customer_tier_id={tier1.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert all(c["customer_tier_id"] == str(tier1.id) for c in data)
    assert any(c["name"] == "Tier 1 Customer" for c in data)
    assert not any(c["name"] == "Tier 2 Customer" for c in data)


def test_get_customer_detail_success(client: TestClient, test_user: User, db: Session):
    """Verify retrieving customer details with associated customer tier."""
    tier = CustomerTier(
        name="Gold VIP",
        description="Premium Gold Tier",
        default_discount_limit=Decimal("18.00"),
        is_active=True,
    )
    db.add(tier)
    db.commit()

    customer = Customer(
        name="Nexus Enterprise",
        email="nexus@enterprise.com",
        phone="+1-555-1234",
        customer_tier_id=tier.id,
        billing_address="500 Oracle Pkwy",
        shipping_address="500 Oracle Pkwy, Bldg A",
        is_active=True,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)

    headers = _create_auth_headers(test_user)
    response = client.get(f"/api/v1/customers/{customer.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()

    # Verify customer fields
    assert data["id"] == str(customer.id)
    assert data["name"] == "Nexus Enterprise"
    assert data["email"] == "nexus@enterprise.com"
    assert data["phone"] == "+1-555-1234"
    assert data["customer_tier_id"] == str(tier.id)
    assert data["billing_address"] == "500 Oracle Pkwy"
    assert data["shipping_address"] == "500 Oracle Pkwy, Bldg A"
    assert data["is_active"] is True

    # Verify associated tier is included
    assert "tier" in data
    assert data["tier"] is not None
    assert data["tier"]["id"] == str(tier.id)
    assert data["tier"]["name"] == "Gold VIP"
    assert data["tier"]["description"] == "Premium Gold Tier"
    assert Decimal(str(data["tier"]["default_discount_limit"])) == Decimal("18.00")


def test_get_customer_detail_not_found(client: TestClient, test_user: User):
    """Verify retrieving non-existent customer returns 404."""
    headers = _create_auth_headers(test_user)
    non_existent = str(uuid.uuid4())
    response = client.get(f"/api/v1/customers/{non_existent}", headers=headers)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_customer_detail_permissions(client: TestClient, db: Session):
    """Verify unauthorized and forbidden access to customer details."""
    tier = CustomerTier(name="Tier Perm", default_discount_limit=Decimal("5.00"), is_active=True)
    db.add(tier)
    db.commit()

    customer = Customer(name="Perm Customer", customer_tier_id=tier.id, is_active=True)
    db.add(customer)
    db.commit()

    # Unauthenticated -> 401
    resp_unauth = client.get(f"/api/v1/customers/{customer.id}")
    assert resp_unauth.status_code == 401

    # CUSTOMER role -> 403
    cust_user = User(
        name="Portal User",
        email="perm.cust@test.local",
        password_hash="fakehash",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db.add(cust_user)
    db.commit()
    cust_headers = _create_auth_headers(cust_user)

    resp_cust = client.get(f"/api/v1/customers/{customer.id}", headers=cust_headers)
    assert resp_cust.status_code == 403


def test_update_customer_success(client: TestClient, test_user: User, db: Session):
    """Verify partial updates of customer fields via PATCH /api/v1/customers/{id}."""
    tier = CustomerTier(name="Tier Patch", default_discount_limit=Decimal("5.00"), is_active=True)
    db.add(tier)
    db.commit()

    customer = Customer(
        name="Initial Customer Name",
        email="initial@test.com",
        phone="555-0001",
        customer_tier_id=tier.id,
        is_active=True,
    )
    db.add(customer)
    db.commit()

    headers = _create_auth_headers(test_user)
    patch_payload = {
        "name": "Updated Customer Name",
        "email": "updated@test.com",
        "billing_address": "777 New Address",
    }
    response = client.patch(f"/api/v1/customers/{customer.id}", json=patch_payload, headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(customer.id)
    assert data["name"] == "Updated Customer Name"
    assert data["email"] == "updated@test.com"
    assert data["billing_address"] == "777 New Address"
    # Unmodified fields remain unchanged
    assert data["phone"] == "555-0001"
    assert data["customer_tier_id"] == str(tier.id)
    assert data["is_active"] is True


def test_update_customer_change_tier_success(client: TestClient, admin_user: User, db: Session):
    """Verify changing customer tier to another existing active tier."""
    tier1 = CustomerTier(name="Initial Tier", default_discount_limit=Decimal("5.00"), is_active=True)
    tier2 = CustomerTier(name="Upgraded Tier", default_discount_limit=Decimal("25.00"), is_active=True)
    db.add_all([tier1, tier2])
    db.commit()

    customer = Customer(
        name="Tier Changing Customer",
        customer_tier_id=tier1.id,
        is_active=True,
    )
    db.add(customer)
    db.commit()

    headers = _create_auth_headers(admin_user)
    patch_payload = {
        "customer_tier_id": str(tier2.id),
    }
    response = client.patch(f"/api/v1/customers/{customer.id}", json=patch_payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["customer_tier_id"] == str(tier2.id)


def test_update_customer_change_tier_invalid_fails(client: TestClient, admin_user: User, db: Session):
    """Verify updating to a non-existent or inactive tier fails."""
    tier_active = CustomerTier(name="Tier Active", default_discount_limit=Decimal("5.00"), is_active=True)
    tier_inactive = CustomerTier(name="Tier Inactive", default_discount_limit=Decimal("5.00"), is_active=False)
    db.add_all([tier_active, tier_inactive])
    db.commit()

    customer = Customer(name="Customer For Tier Fail", customer_tier_id=tier_active.id, is_active=True)
    db.add(customer)
    db.commit()

    headers = _create_auth_headers(admin_user)

    # Inactive tier -> 400
    resp_inactive = client.patch(
        f"/api/v1/customers/{customer.id}",
        json={"customer_tier_id": str(tier_inactive.id)},
        headers=headers,
    )
    assert resp_inactive.status_code == 400

    # Non-existent tier -> 404
    resp_nonexistent = client.patch(
        f"/api/v1/customers/{customer.id}",
        json={"customer_tier_id": str(uuid.uuid4())},
        headers=headers,
    )
    assert resp_nonexistent.status_code == 404


def test_update_customer_not_found(client: TestClient, admin_user: User):
    """Verify updating non-existent customer returns 404."""
    headers = _create_auth_headers(admin_user)
    non_existent = str(uuid.uuid4())
    response = client.patch(f"/api/v1/customers/{non_existent}", json={"name": "New Name"}, headers=headers)
    assert response.status_code == 404


def test_deactivate_customer_success(client: TestClient, admin_user: User, db: Session):
    """Verify DELETE /api/v1/customers/{id} performs logical deactivation."""
    tier = CustomerTier(name="Deact Tier", default_discount_limit=Decimal("5.00"), is_active=True)
    db.add(tier)
    db.commit()

    customer = Customer(name="Customer To Deactivate", customer_tier_id=tier.id, is_active=True)
    db.add(customer)
    db.commit()
    db.refresh(customer)

    headers = _create_auth_headers(admin_user)
    response = client.delete(f"/api/v1/customers/{customer.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(customer.id)
    assert data["is_active"] is False

    # Verify customer still exists in DB and is marked inactive
    cust_in_db = db.get(Customer, customer.id)
    assert cust_in_db is not None
    assert cust_in_db.is_active is False

    # Verify excluded from normal active customer queries
    list_resp = client.get("/api/v1/customers", headers=headers)
    assert list_resp.status_code == 200
    active_ids = [c["id"] for c in list_resp.json()]
    assert str(customer.id) not in active_ids


def test_deactivate_referenced_customer_preserves_history(client: TestClient, admin_user: User, db: Session):
    """
    Verify that a customer referenced by existing business records (e.g. User)
    is safely logically deactivated and not physically deleted.
    """
    tier = CustomerTier(name="Ref Tier", default_discount_limit=Decimal("5.00"), is_active=True)
    db.add(tier)
    db.commit()

    customer = Customer(name="Referenced Company", customer_tier_id=tier.id, is_active=True)
    db.add(customer)
    db.commit()

    # User referencing customer
    contact = User(
        name="Company Contact",
        email="contact@referenced.com",
        password_hash="fakehash",
        role=UserRole.CUSTOMER,
        customer_id=customer.id,
        is_active=True,
    )
    db.add(contact)
    db.commit()

    headers = _create_auth_headers(admin_user)
    response = client.delete(f"/api/v1/customers/{customer.id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["is_active"] is False

    # Row is preserved in database
    cust_in_db = db.get(Customer, customer.id)
    assert cust_in_db is not None
    assert cust_in_db.is_active is False


def test_deactivate_customer_not_found(client: TestClient, admin_user: User):
    """Verify deactivating non-existent customer returns 404."""
    headers = _create_auth_headers(admin_user)
    non_existent = str(uuid.uuid4())
    response = client.delete(f"/api/v1/customers/{non_existent}", headers=headers)
    assert response.status_code == 404


def test_deactivate_customer_permissions(client: TestClient, test_user: User, db: Session):
    """Verify SALES_REP cannot deactivate customer (403), requires manager/admin."""
    tier = CustomerTier(name="Perm Tier", default_discount_limit=Decimal("5.00"), is_active=True)
    db.add(tier)
    db.commit()

    customer = Customer(name="Deact Perm Customer", customer_tier_id=tier.id, is_active=True)
    db.add(customer)
    db.commit()

    rep_headers = _create_auth_headers(test_user)
    response = client.delete(f"/api/v1/customers/{customer.id}", headers=rep_headers)
    assert response.status_code == 403


def test_get_customer_quotations_success(client: TestClient, test_user: User, db: Session):
    """Verify retrieving quotation history belonging to a customer."""
    tier = CustomerTier(name="Quote Tier", default_discount_limit=Decimal("10.00"), is_active=True)
    db.add(tier)
    db.commit()

    c1 = Customer(name="Quotation Customer 1", customer_tier_id=tier.id, is_active=True)
    c2 = Customer(name="Quotation Customer 2", customer_tier_id=tier.id, is_active=True)
    db.add_all([c1, c2])
    db.commit()

    q1 = Quotation(
        quotation_number="QT-0001",
        customer_id=c1.id,
        sales_rep_id=test_user.id,
        status=QuotationStatus.DRAFT,
        subtotal=Decimal("1000.00"),
        total_amount=Decimal("1100.00"),
    )
    q2 = Quotation(
        quotation_number="QT-0002",
        customer_id=c1.id,
        sales_rep_id=test_user.id,
        status=QuotationStatus.CONFIRMED,
        subtotal=Decimal("2000.00"),
        total_amount=Decimal("2200.00"),
    )
    q_other = Quotation(
        quotation_number="QT-OTHER",
        customer_id=c2.id,
        sales_rep_id=test_user.id,
        status=QuotationStatus.DRAFT,
        subtotal=Decimal("500.00"),
        total_amount=Decimal("550.00"),
    )
    db.add_all([q1, q2, q_other])
    db.commit()

    headers = _create_auth_headers(test_user)
    response = client.get(f"/api/v1/customers/{c1.id}/quotations", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    quote_numbers = [q["quotation_number"] for q in data]
    assert "QT-0001" in quote_numbers
    assert "QT-0002" in quote_numbers
    assert "QT-OTHER" not in quote_numbers
    for item in data:
        assert item["customer_id"] == str(c1.id)


def test_get_customer_quotations_empty_list(client: TestClient, test_user: User, db: Session):
    """Verify retrieving quotations for a customer with no quotes returns an empty list."""
    tier = CustomerTier(name="Empty Quote Tier", default_discount_limit=Decimal("10.00"), is_active=True)
    db.add(tier)
    db.commit()

    customer = Customer(name="No Quotes Customer", customer_tier_id=tier.id, is_active=True)
    db.add(customer)
    db.commit()

    headers = _create_auth_headers(test_user)
    response = client.get(f"/api/v1/customers/{customer.id}/quotations", headers=headers)
    assert response.status_code == 200
    assert response.json() == []


def test_get_customer_quotations_customer_not_found(client: TestClient, test_user: User):
    """Verify retrieving quotations for a non-existent customer returns 404."""
    headers = _create_auth_headers(test_user)
    non_existent = str(uuid.uuid4())
    response = client.get(f"/api/v1/customers/{non_existent}/quotations", headers=headers)
    assert response.status_code == 404
    assert "customer not found" in response.json()["detail"].lower()


def test_get_customer_quotations_permissions(client: TestClient, db: Session):
    """Verify unauthorized and forbidden access to customer quotation history."""
    tier = CustomerTier(name="Quote Perm Tier", default_discount_limit=Decimal("5.00"), is_active=True)
    db.add(tier)
    db.commit()

    customer = Customer(name="Quote Perm Customer", customer_tier_id=tier.id, is_active=True)
    db.add(customer)
    db.commit()

    # Unauthenticated -> 401
    resp_unauth = client.get(f"/api/v1/customers/{customer.id}/quotations")
    assert resp_unauth.status_code == 401

    # CUSTOMER role -> 403
    cust_user = User(
        name="Customer User",
        email="quote.cust@test.local",
        password_hash="fakehash",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db.add(cust_user)
    db.commit()
    cust_headers = _create_auth_headers(cust_user)

    resp_cust = client.get(f"/api/v1/customers/{customer.id}/quotations", headers=cust_headers)
    assert resp_cust.status_code == 403


def test_get_customer_orders_success(client: TestClient, test_user: User, db: Session):
    """Verify retrieving order history belonging to a customer."""
    tier = CustomerTier(name="Order Tier", default_discount_limit=Decimal("10.00"), is_active=True)
    db.add(tier)
    db.commit()

    c1 = Customer(name="Order Customer 1", customer_tier_id=tier.id, is_active=True)
    c2 = Customer(name="Order Customer 2", customer_tier_id=tier.id, is_active=True)
    db.add_all([c1, c2])
    db.commit()

    # Quotations for foreign key constraint
    q1 = Quotation(
        quotation_number="QT-ORD-1",
        customer_id=c1.id,
        sales_rep_id=test_user.id,
        status=QuotationStatus.CONFIRMED,
        subtotal=Decimal("1500.00"),
        total_amount=Decimal("1650.00"),
    )
    q2 = Quotation(
        quotation_number="QT-ORD-2",
        customer_id=c1.id,
        sales_rep_id=test_user.id,
        status=QuotationStatus.CONFIRMED,
        subtotal=Decimal("3000.00"),
        total_amount=Decimal("3300.00"),
    )
    q_other = Quotation(
        quotation_number="QT-ORD-OTHER",
        customer_id=c2.id,
        sales_rep_id=test_user.id,
        status=QuotationStatus.CONFIRMED,
        subtotal=Decimal("700.00"),
        total_amount=Decimal("770.00"),
    )
    db.add_all([q1, q2, q_other])
    db.commit()

    o1 = Order(
        order_number="SO-0001",
        quotation_id=q1.id,
        customer_id=c1.id,
        status=OrderStatus.CONFIRMED,
        total_amount=Decimal("1650.00"),
    )
    o2 = Order(
        order_number="SO-0002",
        quotation_id=q2.id,
        customer_id=c1.id,
        status=OrderStatus.PARTIALLY_FULFILLED,
        total_amount=Decimal("3300.00"),
    )
    o_other = Order(
        order_number="SO-OTHER",
        quotation_id=q_other.id,
        customer_id=c2.id,
        status=OrderStatus.CONFIRMED,
        total_amount=Decimal("770.00"),
    )
    db.add_all([o1, o2, o_other])
    db.commit()

    headers = _create_auth_headers(test_user)
    response = client.get(f"/api/v1/customers/{c1.id}/orders", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    order_numbers = [o["order_number"] for o in data]
    assert "SO-0001" in order_numbers
    assert "SO-0002" in order_numbers
    assert "SO-OTHER" not in order_numbers
    for item in data:
        assert item["customer_id"] == str(c1.id)


def test_get_customer_orders_empty_list(client: TestClient, test_user: User, db: Session):
    """Verify retrieving orders for a customer with no orders returns an empty list."""
    tier = CustomerTier(name="Empty Order Tier", default_discount_limit=Decimal("10.00"), is_active=True)
    db.add(tier)
    db.commit()

    customer = Customer(name="No Orders Customer", customer_tier_id=tier.id, is_active=True)
    db.add(customer)
    db.commit()

    headers = _create_auth_headers(test_user)
    response = client.get(f"/api/v1/customers/{customer.id}/orders", headers=headers)
    assert response.status_code == 200
    assert response.json() == []


def test_get_customer_orders_customer_not_found(client: TestClient, test_user: User):
    """Verify retrieving orders for a non-existent customer returns 404."""
    headers = _create_auth_headers(test_user)
    non_existent = str(uuid.uuid4())
    response = client.get(f"/api/v1/customers/{non_existent}/orders", headers=headers)
    assert response.status_code == 404
    assert "customer not found" in response.json()["detail"].lower()


def test_get_customer_orders_permissions(client: TestClient, db: Session):
    """Verify unauthorized and forbidden access to customer order history."""
    tier = CustomerTier(name="Order Perm Tier", default_discount_limit=Decimal("5.00"), is_active=True)
    db.add(tier)
    db.commit()

    customer = Customer(name="Order Perm Customer", customer_tier_id=tier.id, is_active=True)
    db.add(customer)
    db.commit()

    # Unauthenticated -> 401
    resp_unauth = client.get(f"/api/v1/customers/{customer.id}/orders")
    assert resp_unauth.status_code == 401

    # CUSTOMER role -> 403
    cust_user = User(
        name="Order Customer User",
        email="order.cust@test.local",
        password_hash="fakehash",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db.add(cust_user)
    db.commit()
    cust_headers = _create_auth_headers(cust_user)

    resp_cust = client.get(f"/api/v1/customers/{customer.id}/orders", headers=cust_headers)
    assert resp_cust.status_code == 403


def test_get_customer_subscriptions_success(client: TestClient, test_user: User, db: Session):
    """Verify retrieving subscription history belonging to a customer."""
    tier = CustomerTier(name="Sub Tier", default_discount_limit=Decimal("10.00"), is_active=True)
    db.add(tier)
    db.commit()

    c1 = Customer(name="Sub Customer 1", customer_tier_id=tier.id, is_active=True)
    c2 = Customer(name="Sub Customer 2", customer_tier_id=tier.id, is_active=True)
    db.add_all([c1, c2])
    db.commit()

    cat = ProductCategory(name=f"Sub Category {uuid.uuid4().hex[:6]}", is_active=True)
    db.add(cat)
    db.commit()

    prod = Product(
        category_id=cat.id,
        name="SaaS Product",
        sku=f"SKU-SUB-{uuid.uuid4().hex[:6]}",
        unit="month",
        base_price=Decimal("100.00"),
        cost_price=Decimal("20.00"),
        tax_rate=Decimal("10.00"),
        is_subscription=True,
        is_active=True,
    )
    plan = SubscriptionPlan(
        name="Monthly Standard",
        billing_interval=BillingInterval.MONTHLY,
        interval_count=1,
        proration_method=ProrationMethod.DAILY_PRO_RATA,
        cancellation_policy="immediate",
        refund_policy="pro_rata",
        is_active=True,
    )
    db.add_all([prod, plan])
    db.commit()

    q1 = Quotation(
        quotation_number=f"QT-SUB-1-{uuid.uuid4().hex[:4]}",
        customer_id=c1.id,
        sales_rep_id=test_user.id,
        status=QuotationStatus.CONFIRMED,
        subtotal=Decimal("500.00"),
        total_amount=Decimal("550.00"),
    )
    q2 = Quotation(
        quotation_number=f"QT-SUB-2-{uuid.uuid4().hex[:4]}",
        customer_id=c2.id,
        sales_rep_id=test_user.id,
        status=QuotationStatus.CONFIRMED,
        subtotal=Decimal("300.00"),
        total_amount=Decimal("330.00"),
    )
    db.add_all([q1, q2])
    db.commit()

    ql1 = QuotationLine(
        quotation_id=q1.id,
        product_id=prod.id,
        quantity=Decimal("5.00"),
        unit_price=Decimal("100.00"),
        discount_percent=Decimal("0.00"),
        discount_amount=Decimal("0.00"),
        tax_rate=Decimal("10.00"),
        line_total=Decimal("550.00"),
        unit_cost=Decimal("20.00"),
        margin_amount=Decimal("400.00"),
        margin_percent=Decimal("80.00"),
        allowed_discount_percent=Decimal("10.00"),
    )
    ql2 = QuotationLine(
        quotation_id=q2.id,
        product_id=prod.id,
        quantity=Decimal("3.00"),
        unit_price=Decimal("100.00"),
        discount_percent=Decimal("0.00"),
        discount_amount=Decimal("0.00"),
        tax_rate=Decimal("10.00"),
        line_total=Decimal("330.00"),
        unit_cost=Decimal("20.00"),
        margin_amount=Decimal("240.00"),
        margin_percent=Decimal("80.00"),
        allowed_discount_percent=Decimal("10.00"),
    )
    db.add_all([ql1, ql2])
    db.commit()

    o1 = Order(
        order_number=f"SO-SUB-1-{uuid.uuid4().hex[:4]}",
        quotation_id=q1.id,
        customer_id=c1.id,
        status=OrderStatus.CONFIRMED,
        total_amount=Decimal("550.00"),
    )
    o2 = Order(
        order_number=f"SO-SUB-2-{uuid.uuid4().hex[:4]}",
        quotation_id=q2.id,
        customer_id=c2.id,
        status=OrderStatus.CONFIRMED,
        total_amount=Decimal("330.00"),
    )
    db.add_all([o1, o2])
    db.commit()

    s1 = Subscription(
        order_id=o1.id,
        quotation_line_id=ql1.id,
        customer_id=c1.id,
        product_id=prod.id,
        plan_id=plan.id,
        quantity=Decimal("5.00"),
        unit_price=Decimal("100.00"),
        start_date=date(2026, 1, 1),
        next_billing_date=date(2026, 2, 1),
        status=SubscriptionStatus.ACTIVE,
    )
    s2 = Subscription(
        order_id=o1.id,
        quotation_line_id=ql1.id,
        customer_id=c1.id,
        product_id=prod.id,
        plan_id=plan.id,
        quantity=Decimal("2.00"),
        unit_price=Decimal("100.00"),
        start_date=date(2026, 2, 1),
        next_billing_date=date(2026, 3, 1),
        status=SubscriptionStatus.PAUSED,
    )
    s_other = Subscription(
        order_id=o2.id,
        quotation_line_id=ql2.id,
        customer_id=c2.id,
        product_id=prod.id,
        plan_id=plan.id,
        quantity=Decimal("3.00"),
        unit_price=Decimal("100.00"),
        start_date=date(2026, 1, 1),
        next_billing_date=date(2026, 2, 1),
        status=SubscriptionStatus.ACTIVE,
    )
    db.add_all([s1, s2, s_other])
    db.commit()

    headers = _create_auth_headers(test_user)
    response = client.get(f"/api/v1/customers/{c1.id}/subscriptions", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    returned_ids = [item["id"] for item in data]
    assert str(s1.id) in returned_ids
    assert str(s2.id) in returned_ids
    assert str(s_other.id) not in returned_ids
    # Verify fields
    item = next(i for i in data if i["id"] == str(s1.id))
    assert item["customer_id"] == str(c1.id)
    assert item["order_id"] == str(o1.id)
    assert item["product_id"] == str(prod.id)
    assert item["plan_id"] == str(plan.id)
    assert item["status"] == "ACTIVE"
    assert item["start_date"] == "2026-01-01"
    assert item["next_billing_date"] == "2026-02-01"
    assert float(item["unit_price"]) == 100.00


def test_get_customer_subscriptions_empty_list(client: TestClient, test_user: User, db: Session):
    """Verify customer with no subscriptions returns an empty list."""
    tier = CustomerTier(name="Empty Sub Tier", default_discount_limit=Decimal("5.00"), is_active=True)
    db.add(tier)
    db.commit()

    customer = Customer(name="Empty Sub Customer", customer_tier_id=tier.id, is_active=True)
    db.add(customer)
    db.commit()

    headers = _create_auth_headers(test_user)
    response = client.get(f"/api/v1/customers/{customer.id}/subscriptions", headers=headers)
    assert response.status_code == 200
    assert response.json() == []


def test_get_customer_subscriptions_customer_not_found(client: TestClient, test_user: User):
    """Verify retrieving subscriptions for a non-existent customer returns 404."""
    headers = _create_auth_headers(test_user)
    non_existent = str(uuid.uuid4())
    response = client.get(f"/api/v1/customers/{non_existent}/subscriptions", headers=headers)
    assert response.status_code == 404
    assert "customer not found" in response.json()["detail"].lower()


def test_get_customer_subscriptions_permissions(client: TestClient, db: Session):
    """Verify unauthorized and forbidden access to customer subscription history."""
    tier = CustomerTier(name="Sub Perm Tier", default_discount_limit=Decimal("5.00"), is_active=True)
    db.add(tier)
    db.commit()

    customer = Customer(name="Sub Perm Customer", customer_tier_id=tier.id, is_active=True)
    db.add(customer)
    db.commit()

    # Unauthenticated -> 401
    resp_unauth = client.get(f"/api/v1/customers/{customer.id}/subscriptions")
    assert resp_unauth.status_code == 401

    # CUSTOMER role -> 403
    cust_user = User(
        name="Sub Customer User",
        email="sub.cust@test.local",
        password_hash="fakehash",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db.add(cust_user)
    db.commit()
    cust_headers = _create_auth_headers(cust_user)

    resp_cust = client.get(f"/api/v1/customers/{customer.id}/subscriptions", headers=cust_headers)
    assert resp_cust.status_code == 403


def test_customer_endpoints_role_based_matrix(client: TestClient, admin_user: User, db: Session):
    """
    Step 11 Authorization Test:
    Verify the complete role-based authorization matrix for all internal Customer endpoints.
    - CUSTOMER role: 403 on all internal endpoints.
    - FINANCE_OPERATIONS: 200 on read endpoints (list, details, quotes, orders, subs); 403 on write (create, update, delete).
    - SALES_REP: 200/201 on create, update, list, details, quotes, orders, subs; 403 on delete.
    - SALES_MANAGER: 200/201 on create, update, delete, list, details, quotes, orders, subs.
    - ADMIN: 200/201 on all endpoints.
    """
    tier = CustomerTier(name="Matrix Tier", default_discount_limit=Decimal("10.00"), is_active=True)
    db.add(tier)
    db.commit()

    customer = Customer(
        name="Matrix Customer",
        customer_tier_id=tier.id,
        email="matrix@test.local",
        is_active=True,
    )
    db.add(customer)
    db.commit()

    # Create users for each role
    manager_user = User(
        name="Manager User",
        email=f"mgr-{uuid.uuid4().hex[:6]}@test.local",
        password_hash="fakehash",
        role=UserRole.SALES_MANAGER,
        is_active=True,
    )
    rep_user = User(
        name="Rep User",
        email=f"rep-{uuid.uuid4().hex[:6]}@test.local",
        password_hash="fakehash",
        role=UserRole.SALES_REP,
        is_active=True,
    )
    finance_user = User(
        name="Finance User",
        email=f"fin-{uuid.uuid4().hex[:6]}@test.local",
        password_hash="fakehash",
        role=UserRole.FINANCE_OPERATIONS,
        is_active=True,
    )
    cust_user = User(
        name="Customer User",
        email=f"cust-{uuid.uuid4().hex[:6]}@test.local",
        password_hash="fakehash",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db.add_all([manager_user, rep_user, finance_user, cust_user])
    db.commit()

    admin_h = _create_auth_headers(admin_user)
    manager_h = _create_auth_headers(manager_user)
    rep_h = _create_auth_headers(rep_user)
    finance_h = _create_auth_headers(finance_user)
    cust_h = _create_auth_headers(cust_user)

    create_payload = {"name": f"New Cust {uuid.uuid4().hex[:4]}", "customer_tier_id": str(tier.id)}

    # 1. CUSTOMER: Blocked from ALL internal endpoints
    assert client.get("/api/v1/customers", headers=cust_h).status_code == 403
    assert client.post("/api/v1/customers", json=create_payload, headers=cust_h).status_code == 403
    assert client.get(f"/api/v1/customers/{customer.id}", headers=cust_h).status_code == 403
    assert client.patch(f"/api/v1/customers/{customer.id}", json={"name": "Cust Try"}, headers=cust_h).status_code == 403
    assert client.delete(f"/api/v1/customers/{customer.id}", headers=cust_h).status_code == 403
    assert client.get(f"/api/v1/customers/{customer.id}/quotations", headers=cust_h).status_code == 403
    assert client.get(f"/api/v1/customers/{customer.id}/orders", headers=cust_h).status_code == 403
    assert client.get(f"/api/v1/customers/{customer.id}/subscriptions", headers=cust_h).status_code == 403

    # 2. FINANCE_OPERATIONS: Allowed on reads, Forbidden on writes (create, update, delete)
    assert client.get("/api/v1/customers", headers=finance_h).status_code == 200
    assert client.get(f"/api/v1/customers/{customer.id}", headers=finance_h).status_code == 200
    assert client.get(f"/api/v1/customers/{customer.id}/quotations", headers=finance_h).status_code == 200
    assert client.get(f"/api/v1/customers/{customer.id}/orders", headers=finance_h).status_code == 200
    assert client.get(f"/api/v1/customers/{customer.id}/subscriptions", headers=finance_h).status_code == 200

    assert client.post("/api/v1/customers", json=create_payload, headers=finance_h).status_code == 403
    assert client.patch(f"/api/v1/customers/{customer.id}", json={"name": "Fin Try"}, headers=finance_h).status_code == 403
    assert client.delete(f"/api/v1/customers/{customer.id}", headers=finance_h).status_code == 403

    # 3. SALES_REP: Allowed on create, update, reads; Forbidden on delete
    assert client.get("/api/v1/customers", headers=rep_h).status_code == 200
    assert client.get(f"/api/v1/customers/{customer.id}", headers=rep_h).status_code == 200
    assert client.patch(f"/api/v1/customers/{customer.id}", json={"name": "Rep Updated"}, headers=rep_h).status_code == 200
    assert client.delete(f"/api/v1/customers/{customer.id}", headers=rep_h).status_code == 403

    # 4. SALES_MANAGER: Allowed on create, update, delete, reads
    assert client.get("/api/v1/customers", headers=manager_h).status_code == 200
    assert client.get(f"/api/v1/customers/{customer.id}", headers=manager_h).status_code == 200
    assert client.patch(f"/api/v1/customers/{customer.id}", json={"name": "Mgr Updated"}, headers=manager_h).status_code == 200

    # Test create by manager
    create_mgr_payload = {"name": f"Manager Created {uuid.uuid4().hex[:4]}", "customer_tier_id": str(tier.id)}
    mgr_create_resp = client.post("/api/v1/customers", json=create_mgr_payload, headers=manager_h)
    assert mgr_create_resp.status_code == 201
    mgr_created_id = mgr_create_resp.json()["id"]

    # Test delete by manager
    assert client.delete(f"/api/v1/customers/{mgr_created_id}", headers=manager_h).status_code == 200

    # 5. ADMIN: Allowed on all operations
    assert client.get("/api/v1/customers", headers=admin_h).status_code == 200
    assert client.get(f"/api/v1/customers/{customer.id}", headers=admin_h).status_code == 200
    assert client.patch(f"/api/v1/customers/{customer.id}", json={"name": "Admin Updated"}, headers=admin_h).status_code == 200
    assert client.delete(f"/api/v1/customers/{customer.id}", headers=admin_h).status_code == 200

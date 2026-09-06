"""Comprehensive tests for DealFlow360 Customer <-> User synchronization,
1-to-1 relationship integrity, B2B customer preservation, quotation resolution, and RBAC isolation.
"""

import uuid
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.common.enums import QuotationStatus, UserRole
from app.core.security import create_access_token, hash_password
from app.models.customer import Customer
from app.models.customer_tier import CustomerTier
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.quotation import Quotation
from app.models.user import User
from app.modules.customers.service import customer_service
from app.modules.users.schemas import UserCreateRequest
from app.modules.users.service import user_service


def _auth_headers(user: User) -> dict:
    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    token = create_access_token(user_id=user.id, role=role_str)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def active_tier(db: Session) -> CustomerTier:
    tier = CustomerTier(
        name=f"Standard Tier {uuid.uuid4().hex[:6]}",
        default_discount_limit=Decimal("10.00"),
        is_active=True,
    )
    db.add(tier)
    db.commit()
    db.refresh(tier)
    return tier


# ====================================================================
# A. CUSTOMER USER CREATION
# ====================================================================


def test_customer_user_creation_via_signup_creates_and_links_customer(
    client: TestClient, db: Session, active_tier: CustomerTier
):
    """Verify that public signup creates user with role CUSTOMER and automatically creates linked Customer record."""
    email = f"customer_{uuid.uuid4().hex[:6]}@example.com"
    payload = {
        "name": "Acme Buyer",
        "email": email,
        "password": "BuyerSecure123!",
    }
    response = client.post("/api/v1/auth/signup", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["role"] == UserRole.CUSTOMER.value
    assert data["customer_id"] is not None

    user = db.scalars(select(User).where(User.email == email)).first()
    assert user is not None
    assert user.customer_id is not None

    customer = db.get(Customer, user.customer_id)
    assert customer is not None
    assert customer.name == "Acme Buyer"
    assert customer.email == email
    assert customer.is_active is True
    assert customer.customer_tier_id is not None
    assert customer.user_id == user.id
    assert customer.user == user


def test_customer_user_creation_via_admin_api_creates_and_links_customer(
    client: TestClient, admin_user: User, db: Session, active_tier: CustomerTier
):
    """Verify that admin user creation endpoint creates user and automatically creates linked Customer record."""
    headers = _auth_headers(admin_user)
    email = f"client_{uuid.uuid4().hex[:6]}@example.com"
    payload = {
        "name": "Direct Client",
        "email": email,
        "password": "ClientSecure123!",
        "role": UserRole.CUSTOMER.value,
        "is_active": True,
    }
    response = client.post("/api/v1/users", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()

    assert data["role"] == UserRole.CUSTOMER.value
    assert data["customer_id"] is not None

    user = db.scalars(select(User).where(User.email == email)).first()
    assert user is not None
    assert user.customer is not None
    assert user.customer.name == "Direct Client"
    assert user.customer.email == email


# ====================================================================
# B. NON-CUSTOMER USER CREATION
# ====================================================================


@pytest.mark.parametrize(
    "role",
    [
        UserRole.ADMIN,
        UserRole.SALES_REP,
        UserRole.SALES_MANAGER,
        UserRole.FINANCE_OPERATIONS,
    ],
)
def test_non_customer_user_creation_does_not_create_customer(
    client: TestClient, admin_user: User, db: Session, role: UserRole
):
    """Verify that internal users never create or hold a customer record."""
    headers = _auth_headers(admin_user)
    email = f"staff_{role.value.lower()}_{uuid.uuid4().hex[:6]}@dealflow360.local"
    payload = {
        "name": f"Staff {role.value}",
        "email": email,
        "password": "StaffSecure123!",
        "role": role.value,
        "is_active": True,
    }
    response = client.post("/api/v1/users", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()

    assert data["customer_id"] is None

    user = db.scalars(select(User).where(User.email == email)).first()
    assert user is not None
    assert user.customer_id is None
    assert user.customer is None

    # Check that no customer record was created with this email
    matching_customer = db.scalars(
        select(Customer).where(Customer.email == email)
    ).first()
    assert matching_customer is None


# ====================================================================
# C. EXISTING CUSTOMER USER WITH NO CUSTOMER RECORD
# ====================================================================


def test_existing_customer_user_without_customer_record_is_synchronized(
    db: Session, active_tier: CustomerTier
):
    """Verify that an existing CUSTOMER user with customer_id=None gets synchronized."""
    email = f"orphan_{uuid.uuid4().hex[:6]}@example.com"
    orphan_user = User(
        name="Orphan Customer",
        email=email,
        password_hash=hash_password("Pass123!"),
        role=UserRole.CUSTOMER,
        customer_id=None,
        is_active=True,
    )
    db.add(orphan_user)
    db.commit()
    db.refresh(orphan_user)

    assert orphan_user.customer_id is None

    # Run synchronization
    customer = customer_service.ensure_customer_for_user(db, orphan_user)
    db.commit()
    db.refresh(orphan_user)

    assert customer is not None
    assert orphan_user.customer_id == customer.id
    assert customer.email == email
    assert customer.name == "Orphan Customer"
    assert customer.user_id == orphan_user.id


# ====================================================================
# D. EXISTING CUSTOMER + USER WITH MATCHING EMAIL
# ====================================================================


def test_existing_customer_and_matching_user_are_associated_without_duplicate(
    db: Session, active_tier: CustomerTier
):
    """Verify that if a Customer business record already exists with the same email, it gets linked rather than duplicated."""
    email = f"shared_{uuid.uuid4().hex[:6]}@example.com"
    existing_customer = Customer(
        name="Existing Org",
        email=email,
        customer_tier_id=active_tier.id,
        is_active=True,
    )
    db.add(existing_customer)
    db.commit()
    db.refresh(existing_customer)

    # Now create user with the same email
    user = User(
        name="Org Contact",
        email=email,
        password_hash=hash_password("Pass123!"),
        role=UserRole.CUSTOMER,
        customer_id=None,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    customer_service.ensure_customer_for_user(db, user)
    db.commit()
    db.refresh(user)

    # Must be linked to existing_customer, not a newly generated one
    assert user.customer_id == existing_customer.id
    assert user.customer.id == existing_customer.id
    assert existing_customer.user_id == user.id

    # Verify no duplicate customers exist with this email
    count = len(
        db.scalars(select(Customer).where(Customer.email == email)).all()
    )
    assert count == 1


# ====================================================================
# E. DUPLICATE PREVENTION & IDEMPOTENCE
# ====================================================================


def test_repeated_synchronization_is_idempotent(
    db: Session, active_tier: CustomerTier
):
    """Verify that calling synchronization multiple times does not create duplicates."""
    email = f"idempotent_{uuid.uuid4().hex[:6]}@example.com"
    user = User(
        name="Repeat User",
        email=email,
        password_hash=hash_password("Pass123!"),
        role=UserRole.CUSTOMER,
        customer_id=None,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Run sync 3 times
    cust1 = customer_service.ensure_customer_for_user(db, user)
    cust2 = customer_service.ensure_customer_for_user(db, user)
    customer_service.sync_all_customer_users(db)

    db.commit()
    db.refresh(user)

    assert cust1.id == cust2.id
    assert user.customer_id == cust1.id

    total = len(
        db.scalars(select(Customer).where(Customer.email == email)).all()
    )
    assert total == 1


def test_database_uniqueness_enforces_one_to_one(
    db: Session, active_tier: CustomerTier
):
    """Verify that the database unique constraint prevents two users from sharing the same customer_id."""
    customer = Customer(
        name="Unique Org",
        email=f"unique_{uuid.uuid4().hex[:6]}@example.com",
        customer_tier_id=active_tier.id,
        is_active=True,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)

    user1 = User(
        name="User 1",
        email=f"u1_{uuid.uuid4().hex[:6]}@example.com",
        password_hash=hash_password("Pass123!"),
        role=UserRole.CUSTOMER,
        customer_id=customer.id,
        is_active=True,
    )
    db.add(user1)
    db.commit()

    user2 = User(
        name="User 2",
        email=f"u2_{uuid.uuid4().hex[:6]}@example.com",
        password_hash=hash_password("Pass123!"),
        role=UserRole.CUSTOMER,
        customer_id=customer.id,
        is_active=True,
    )
    db.add(user2)

    with pytest.raises(IntegrityError):
        db.commit()

    db.rollback()


# ====================================================================
# F. B2B CUSTOMER PRESERVATION (NO LOGIN USER)
# ====================================================================


def test_b2b_customer_without_login_user_works_normally(
    client: TestClient, admin_user: User, db: Session, active_tier: CustomerTier
):
    """Verify B2B customer creation without a login user works and maintains user_id=None."""
    headers = _auth_headers(admin_user)
    payload = {
        "name": "Pure Enterprise Inc",
        "email": f"b2b_{uuid.uuid4().hex[:6]}@enterprise.com",
        "customer_tier_id": str(active_tier.id),
        "is_active": True,
    }
    response = client.post("/api/v1/customers", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()

    assert data["name"] == "Pure Enterprise Inc"
    assert data["user_id"] is None

    customer = db.get(Customer, uuid.UUID(data["id"]))
    assert customer is not None
    assert customer.user is None
    assert customer.user_id is None
    assert customer.users == []


# ====================================================================
# G. QUOTATION INTEGRATION
# ====================================================================


def test_quotation_references_customer_id_not_user_id(
    client: TestClient, admin_user: User, db: Session, active_tier: CustomerTier
):
    """Verify quotation creation references the business customer_id."""
    headers = _auth_headers(admin_user)

    # 1. Create CUSTOMER user
    cust_email = f"buyer_{uuid.uuid4().hex[:6]}@buyer.com"
    req = UserCreateRequest(
        name="Purchasing Buyer",
        email=cust_email,
        password="BuyerPass123!",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    cust_user = user_service.create_user(db, req)
    assert cust_user.customer_id is not None
    assert cust_user.id != cust_user.customer_id

    # 2. Create product & category
    category = ProductCategory(
        name=f"Cat-{uuid.uuid4().hex[:6]}",
        is_active=True,
    )
    db.add(category)
    db.commit()
    db.refresh(category)

    product = Product(
        name="Standard Server",
        sku=f"SRV-{uuid.uuid4().hex[:6]}",
        category_id=category.id,
        unit="Units",
        base_price=Decimal("1500.00"),
        cost_price=Decimal("900.00"),
        tax_rate=Decimal("10.00"),
        is_active=True,
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    # 3. Create Quotation for the Customer
    quote_payload = {
        "customer_id": str(cust_user.customer_id),
        "notes": "Quote for purchasing buyer",
    }
    response = client.post("/api/v1/quotations", json=quote_payload, headers=headers)
    assert response.status_code == 201
    q_data = response.json()

    assert q_data["customer_id"] == str(cust_user.customer_id)
    assert q_data["customer_id"] != str(cust_user.id)

    # Verify in database
    quote = db.get(Quotation, uuid.UUID(q_data["id"]))
    assert quote is not None
    assert quote.customer_id == cust_user.customer_id
    assert quote.customer.id == cust_user.customer.id


# ====================================================================
# H. AUTHORIZATION & CUSTOMER SELF-SERVICE ISOLATION
# ====================================================================


def test_customer_self_service_and_data_isolation(
    client: TestClient, admin_user: User, db: Session, active_tier: CustomerTier
):
    """
    Verify customer users can access their own profile and quotations,
    while being strictly forbidden from accessing another customer's data.
    """
    admin_headers = _auth_headers(admin_user)

    # Create Customer User 1
    req1 = UserCreateRequest(
        name="Customer Alice",
        email=f"alice_{uuid.uuid4().hex[:6]}@example.com",
        password="AlicePass123!",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    alice = user_service.create_user(db, req1)
    alice_headers = _auth_headers(alice)

    # Create Customer User 2
    req2 = UserCreateRequest(
        name="Customer Bob",
        email=f"bob_{uuid.uuid4().hex[:6]}@example.com",
        password="BobPass123!",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    bob = user_service.create_user(db, req2)
    bob_headers = _auth_headers(bob)

    # 1. Alice can access /customers/me
    res_me = client.get("/api/v1/customers/me", headers=alice_headers)
    assert res_me.status_code == 200
    assert res_me.json()["id"] == str(alice.customer_id)

    # 2. Alice can access /customers/{alice.customer_id}
    res_alice_own = client.get(
        f"/api/v1/customers/{alice.customer_id}", headers=alice_headers
    )
    assert res_alice_own.status_code == 200
    assert res_alice_own.json()["id"] == str(alice.customer_id)

    # 3. Alice CANNOT access /customers/{bob.customer_id} (403 Forbidden)
    res_alice_on_bob = client.get(
        f"/api/v1/customers/{bob.customer_id}", headers=alice_headers
    )
    assert res_alice_on_bob.status_code == 403

    # 4. Create Quotation for Alice and Quotation for Bob
    q1_res = client.post(
        "/api/v1/quotations",
        json={"customer_id": str(alice.customer_id)},
        headers=admin_headers,
    )
    assert q1_res.status_code == 201
    alice_quote_id = q1_res.json()["id"]

    q2_res = client.post(
        "/api/v1/quotations",
        json={"customer_id": str(bob.customer_id)},
        headers=admin_headers,
    )
    assert q2_res.status_code == 201
    bob_quote_id = q2_res.json()["id"]

    # 5. Alice lists quotations: must only see Alice's quotation
    list_res = client.get("/api/v1/quotations", headers=alice_headers)
    assert list_res.status_code == 200
    quotes = list_res.json()
    assert all(q["customer_id"] == str(alice.customer_id) for q in quotes)
    assert any(q["id"] == alice_quote_id for q in quotes)
    assert not any(q["id"] == bob_quote_id for q in quotes)

    # 6. Alice can get own quotation details
    get_q_res = client.get(
        f"/api/v1/quotations/{alice_quote_id}", headers=alice_headers
    )
    assert get_q_res.status_code == 200

    # 7. Alice CANNOT get Bob's quotation details (403 Forbidden)
    get_bob_q_res = client.get(
        f"/api/v1/quotations/{bob_quote_id}", headers=alice_headers
    )
    assert get_bob_q_res.status_code == 403


# ====================================================================
# I. TRANSACTION SAFETY ON CREATION FAILURE
# ====================================================================


def test_transaction_safety_on_customer_creation_failure(
    db: Session, monkeypatch
):
    """Verify that if customer creation fails during CUSTOMER user creation, no orphaned User is committed."""
    email = f"fail_{uuid.uuid4().hex[:6]}@example.com"
    req = UserCreateRequest(
        name="Failing Customer",
        email=email,
        password="SecurePass123!",
        role=UserRole.CUSTOMER,
        is_active=True,
    )

    def _broken_ensure(*args, **kwargs):
        raise RuntimeError("Simulated failure creating customer business entity")

    monkeypatch.setattr(customer_service, "ensure_customer_for_user", _broken_ensure)

    with pytest.raises(RuntimeError, match="Simulated failure"):
        user_service.create_user(db, req)

    # Verify no orphan user exists in the database
    orphan = db.scalars(select(User).where(User.email == email)).first()
    assert orphan is None

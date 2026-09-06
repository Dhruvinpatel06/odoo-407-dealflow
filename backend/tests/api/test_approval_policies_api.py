"""Comprehensive API tests for the Approval Policies configuration module."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.security import create_access_token, hash_password
from app.models.approval_policy import ApprovalPolicy
from app.models.audit_log import AuditLog
from app.models.user import User


def _create_auth_headers(user: User) -> dict:
    """Helper to generate Authorization header for a given user."""
    token = create_access_token(user_id=user.id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sales_manager_user(db: Session) -> User:
    """Fixture providing an active SALES_MANAGER user."""
    user = User(
        name="Sales Manager",
        email=f"manager-{uuid.uuid4().hex[:6]}@dealflow360.local",
        password_hash=hash_password("Password123!"),
        role=UserRole.SALES_MANAGER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def finance_user(db: Session) -> User:
    """Fixture providing an active FINANCE_OPERATIONS user."""
    user = User(
        name="Finance Operations",
        email=f"finance-{uuid.uuid4().hex[:6]}@dealflow360.local",
        password_hash=hash_password("Password123!"),
        role=UserRole.FINANCE_OPERATIONS,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def customer_user(db: Session) -> User:
    """Fixture providing an active CUSTOMER user."""
    user = User(
        name="External Customer",
        email=f"customer-{uuid.uuid4().hex[:6]}@external.local",
        password_hash=hash_password("Password123!"),
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


class TestApprovalPoliciesCRUD:
    """Tests for CRUD endpoints of approval policies."""

    def test_list_approval_policies_empty(
        self, client: TestClient, admin_user: User
    ):
        """Verify listing approval policies returns 200 and empty list when none exist."""
        headers = _create_auth_headers(admin_user)
        response = client.get("/api/v1/approval-policies", headers=headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_create_approval_policy_admin_success(
        self, client: TestClient, admin_user: User, db: Session
    ):
        """Verify Admin can create an approval policy with full audit logging."""
        headers = _create_auth_headers(admin_user)
        payload = {
            "name": "Standard Low Risk",
            "min_risk_score": "0.00",
            "max_risk_score": "20.00",
            "requires_manager": False,
            "requires_finance": False,
            "priority": 5,
            "is_active": True,
        }
        response = client.post(
            "/api/v1/approval-policies", json=payload, headers=headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Standard Low Risk"
        assert Decimal(data["min_risk_score"]) == Decimal("0.00")
        assert Decimal(data["max_risk_score"]) == Decimal("20.00")
        assert data["requires_manager"] is False
        assert data["requires_finance"] is False
        assert data["priority"] == 5
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

        # Verify audit log recorded
        audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.entity_type == "APPROVAL_POLICY",
                AuditLog.entity_id == uuid.UUID(data["id"]),
            )
            .first()
        )
        assert audit is not None
        assert audit.action == "CREATE"
        assert audit.user_id == admin_user.id

    def test_create_approval_policy_sales_manager_success(
        self, client: TestClient, sales_manager_user: User
    ):
        """Verify Sales Manager can configure an approval policy with Manager requirement."""
        headers = _create_auth_headers(sales_manager_user)
        payload = {
            "name": "Medium Risk Manager Approval",
            "min_risk_score": "20.01",
            "max_risk_score": "50.00",
            "requires_manager": True,
            "requires_finance": False,
            "priority": 10,
            "is_active": True,
        }
        response = client.post(
            "/api/v1/approval-policies", json=payload, headers=headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["requires_manager"] is True
        assert data["requires_finance"] is False

    def test_create_approval_policy_dual_level(
        self, client: TestClient, admin_user: User
    ):
        """Verify creation of dual Manager + Finance approval policy with unbounded upper score."""
        headers = _create_auth_headers(admin_user)
        payload = {
            "name": "High Risk Dual Approval",
            "min_risk_score": "50.01",
            "max_risk_score": None,
            "requires_manager": True,
            "requires_finance": True,
            "priority": 20,
        }
        response = client.post(
            "/api/v1/approval-policies", json=payload, headers=headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["max_risk_score"] is None
        assert data["requires_manager"] is True
        assert data["requires_finance"] is True

    def test_get_approval_policy_by_id(
        self, client: TestClient, admin_user: User
    ):
        """Verify retrieving policy by ID."""
        headers = _create_auth_headers(admin_user)
        created = client.post(
            "/api/v1/approval-policies",
            json={
                "name": "Get Test Policy",
                "min_risk_score": "5.00",
                "max_risk_score": "15.00",
                "requires_manager": True,
            },
            headers=headers,
        ).json()

        policy_id = created["id"]
        response = client.get(
            f"/api/v1/approval-policies/{policy_id}", headers=headers
        )
        assert response.status_code == 200
        assert response.json()["id"] == policy_id
        assert response.json()["name"] == "Get Test Policy"

    def test_get_approval_policy_not_found(
        self, client: TestClient, admin_user: User
    ):
        """Verify 404 on non-existent policy UUID."""
        headers = _create_auth_headers(admin_user)
        random_id = uuid.uuid4()
        response = client.get(
            f"/api/v1/approval-policies/{random_id}", headers=headers
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_list_approval_policies_ordering_and_filtering(
        self, client: TestClient, admin_user: User
    ):
        """Verify policies are listed ordered by priority DESC, and filterable by is_active."""
        headers = _create_auth_headers(admin_user)
        # Create 3 policies with different priorities and active states
        client.post(
            "/api/v1/approval-policies",
            json={
                "name": "Low Priority",
                "min_risk_score": "1.00",
                "priority": 1,
                "is_active": True,
            },
            headers=headers,
        )
        client.post(
            "/api/v1/approval-policies",
            json={
                "name": "High Priority",
                "min_risk_score": "10.00",
                "priority": 100,
                "is_active": True,
            },
            headers=headers,
        )
        client.post(
            "/api/v1/approval-policies",
            json={
                "name": "Inactive Policy",
                "min_risk_score": "20.00",
                "priority": 50,
                "is_active": False,
            },
            headers=headers,
        )

        # List all
        resp_all = client.get("/api/v1/approval-policies", headers=headers)
        assert resp_all.status_code == 200
        all_items = resp_all.json()
        assert len(all_items) >= 3
        # Ensure highest priority is first
        assert all_items[0]["name"] == "High Priority"

        # List active only
        resp_active = client.get(
            "/api/v1/approval-policies?is_active=true", headers=headers
        )
        assert resp_active.status_code == 200
        active_names = [p["name"] for p in resp_active.json()]
        assert "Inactive Policy" not in active_names
        assert "High Priority" in active_names
        assert "Low Priority" in active_names

        # List inactive only
        resp_inactive = client.get(
            "/api/v1/approval-policies?is_active=false", headers=headers
        )
        assert resp_inactive.status_code == 200
        inactive_names = [p["name"] for p in resp_inactive.json()]
        assert "Inactive Policy" in inactive_names
        assert "High Priority" not in inactive_names

    def test_update_approval_policy_success(
        self, client: TestClient, admin_user: User, db: Session
    ):
        """Verify PATCH updates fields and logs an UPDATE audit event."""
        headers = _create_auth_headers(admin_user)
        created = client.post(
            "/api/v1/approval-policies",
            json={
                "name": "Original Policy Name",
                "min_risk_score": "10.00",
                "max_risk_score": "20.00",
                "requires_manager": False,
                "priority": 2,
            },
            headers=headers,
        ).json()

        policy_id = created["id"]
        patch_payload = {
            "name": "Updated Policy Name",
            "requires_manager": True,
            "priority": 15,
        }
        patch_resp = client.patch(
            f"/api/v1/approval-policies/{policy_id}",
            json=patch_payload,
            headers=headers,
        )
        assert patch_resp.status_code == 200
        updated = patch_resp.json()
        assert updated["name"] == "Updated Policy Name"
        assert updated["requires_manager"] is True
        assert updated["priority"] == 15
        assert Decimal(updated["min_risk_score"]) == Decimal("10.00")

        # Verify audit log has UPDATE action
        audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.entity_type == "APPROVAL_POLICY",
                AuditLog.entity_id == uuid.UUID(policy_id),
                AuditLog.action == "UPDATE",
            )
            .first()
        )
        assert audit is not None
        assert audit.old_values["name"] == "Original Policy Name"
        assert audit.new_values["name"] == "Updated Policy Name"

    def test_delete_approval_policy_deactivates(
        self, client: TestClient, sales_manager_user: User, db: Session
    ):
        """Verify DELETE logically deactivates policy (returns 200, sets is_active=False) and logs DEACTIVATE audit."""
        headers = _create_auth_headers(sales_manager_user)
        created = client.post(
            "/api/v1/approval-policies",
            json={
                "name": "Policy to Deactivate",
                "min_risk_score": "30.00",
                "requires_manager": True,
            },
            headers=headers,
        ).json()

        policy_id = created["id"]
        del_resp = client.delete(
            f"/api/v1/approval-policies/{policy_id}", headers=headers
        )
        assert del_resp.status_code == 200
        assert del_resp.json()["is_active"] is False

        # Verify subsequent GET returns is_active=False
        get_resp = client.get(
            f"/api/v1/approval-policies/{policy_id}", headers=headers
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["is_active"] is False

        # Verify DEACTIVATE audit log
        audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.entity_type == "APPROVAL_POLICY",
                AuditLog.entity_id == uuid.UUID(policy_id),
                AuditLog.action == "DEACTIVATE",
            )
            .first()
        )
        assert audit is not None


class TestApprovalPoliciesValidation:
    """Tests for policy validation rules and constraints."""

    def test_reject_empty_or_whitespace_name(
        self, client: TestClient, admin_user: User
    ):
        """Verify whitespace-only or empty name is rejected with 422."""
        headers = _create_auth_headers(admin_user)
        response = client.post(
            "/api/v1/approval-policies",
            json={"name": "   ", "min_risk_score": "5.00"},
            headers=headers,
        )
        assert response.status_code == 422

    def test_reject_negative_min_risk_score(
        self, client: TestClient, admin_user: User
    ):
        """Verify negative min_risk_score is rejected with 422."""
        headers = _create_auth_headers(admin_user)
        response = client.post(
            "/api/v1/approval-policies",
            json={"name": "Negative Score", "min_risk_score": "-1.00"},
            headers=headers,
        )
        assert response.status_code == 422

    def test_reject_max_less_than_min_risk_score(
        self, client: TestClient, admin_user: User
    ):
        """Verify max_risk_score < min_risk_score is rejected with 422."""
        headers = _create_auth_headers(admin_user)
        response = client.post(
            "/api/v1/approval-policies",
            json={
                "name": "Inverted Score Range",
                "min_risk_score": "50.00",
                "max_risk_score": "30.00",
            },
            headers=headers,
        )
        assert response.status_code == 422
        assert "greater than or equal to min_risk_score" in response.text

    def test_reject_finance_without_manager_approval(
        self, client: TestClient, admin_user: User
    ):
        """Verify sequential approval invariant: Finance requires Sales Manager approval."""
        headers = _create_auth_headers(admin_user)
        response = client.post(
            "/api/v1/approval-policies",
            json={
                "name": "Invalid Finance Only Policy",
                "min_risk_score": "10.00",
                "requires_manager": False,
                "requires_finance": True,
            },
            headers=headers,
        )
        assert response.status_code == 422
        assert (
            "Finance approval requires Sales Manager approval in the sequence"
            in response.text
        )

    def test_reject_duplicate_active_policy_name(
        self, client: TestClient, admin_user: User
    ):
        """Verify creating two active policies with the same name returns 400."""
        headers = _create_auth_headers(admin_user)
        client.post(
            "/api/v1/approval-policies",
            json={"name": "Unique Name Policy", "min_risk_score": "5.00"},
            headers=headers,
        )
        duplicate_resp = client.post(
            "/api/v1/approval-policies",
            json={"name": "Unique Name Policy", "min_risk_score": "10.00"},
            headers=headers,
        )
        assert duplicate_resp.status_code == 400
        assert "already exists" in duplicate_resp.json()["detail"].lower()

    def test_reject_invalid_update_combinations(
        self, client: TestClient, admin_user: User
    ):
        """Verify PATCH rejects invalid configurations that break score bounds or approval invariants."""
        headers = _create_auth_headers(admin_user)
        created = client.post(
            "/api/v1/approval-policies",
            json={
                "name": "Valid Baseline",
                "min_risk_score": "20.00",
                "max_risk_score": "40.00",
                "requires_manager": True,
                "requires_finance": False,
            },
            headers=headers,
        ).json()
        policy_id = created["id"]

        # Attempt to make max < min
        patch_resp = client.patch(
            f"/api/v1/approval-policies/{policy_id}",
            json={"max_risk_score": "10.00"},
            headers=headers,
        )
        assert patch_resp.status_code in (400, 422)

        # Attempt to set finance=True and manager=False
        patch_resp2 = client.patch(
            f"/api/v1/approval-policies/{policy_id}",
            json={"requires_manager": False, "requires_finance": True},
            headers=headers,
        )
        assert patch_resp2.status_code in (400, 422)


class TestApprovalPoliciesRBAC:
    """Tests for Role-Based Access Control matrix on approval policies."""

    def test_unauthenticated_request_returns_401(self, client: TestClient):
        """Verify unauthenticated requests are rejected with 401."""
        assert client.get("/api/v1/approval-policies").status_code == 401
        assert (
            client.post(
                "/api/v1/approval-policies", json={"name": "Test"}
            ).status_code
            == 401
        )
        assert (
            client.get(f"/api/v1/approval-policies/{uuid.uuid4()}").status_code
            == 401
        )
        assert (
            client.patch(
                f"/api/v1/approval-policies/{uuid.uuid4()}", json={}
            ).status_code
            == 401
        )
        assert (
            client.delete(
                f"/api/v1/approval-policies/{uuid.uuid4()}"
            ).status_code
            == 401
        )

    def test_sales_rep_can_read_but_not_mutate(
        self, client: TestClient, test_user: User, admin_user: User
    ):
        """Verify Sales Rep can read approval policies but is forbidden from mutating them."""
        # Create policy as Admin first
        admin_headers = _create_auth_headers(admin_user)
        created = client.post(
            "/api/v1/approval-policies",
            json={"name": "Visible to Rep", "min_risk_score": "5.00"},
            headers=admin_headers,
        ).json()
        policy_id = created["id"]

        rep_headers = _create_auth_headers(test_user)
        # Rep can list
        assert (
            client.get(
                "/api/v1/approval-policies", headers=rep_headers
            ).status_code
            == 200
        )
        # Rep can get detail
        assert (
            client.get(
                f"/api/v1/approval-policies/{policy_id}", headers=rep_headers
            ).status_code
            == 200
        )
        # Rep cannot create -> 403
        assert (
            client.post(
                "/api/v1/approval-policies",
                json={"name": "Rep Policy", "min_risk_score": "1.00"},
                headers=rep_headers,
            ).status_code
            == 403
        )
        # Rep cannot update -> 403
        assert (
            client.patch(
                f"/api/v1/approval-policies/{policy_id}",
                json={"name": "New Name"},
                headers=rep_headers,
            ).status_code
            == 403
        )
        # Rep cannot delete -> 403
        assert (
            client.delete(
                f"/api/v1/approval-policies/{policy_id}", headers=rep_headers
            ).status_code
            == 403
        )

    def test_finance_user_can_read_but_not_mutate(
        self, client: TestClient, finance_user: User, admin_user: User
    ):
        """Verify Finance user can read policies but cannot mutate them."""
        admin_headers = _create_auth_headers(admin_user)
        created = client.post(
            "/api/v1/approval-policies",
            json={"name": "Finance Read Test", "min_risk_score": "5.00"},
            headers=admin_headers,
        ).json()
        policy_id = created["id"]

        fin_headers = _create_auth_headers(finance_user)
        assert (
            client.get(
                "/api/v1/approval-policies", headers=fin_headers
            ).status_code
            == 200
        )
        assert (
            client.get(
                f"/api/v1/approval-policies/{policy_id}", headers=fin_headers
            ).status_code
            == 200
        )
        assert (
            client.post(
                "/api/v1/approval-policies",
                json={"name": "Fin Policy", "min_risk_score": "1.00"},
                headers=fin_headers,
            ).status_code
            == 403
        )
        assert (
            client.patch(
                f"/api/v1/approval-policies/{policy_id}",
                json={"priority": 99},
                headers=fin_headers,
            ).status_code
            == 403
        )
        assert (
            client.delete(
                f"/api/v1/approval-policies/{policy_id}", headers=fin_headers
            ).status_code
            == 403
        )

    def test_customer_role_forbidden_on_all_endpoints(
        self, client: TestClient, customer_user: User, admin_user: User
    ):
        """Verify external Customer role is forbidden from all approval policy endpoints."""
        admin_headers = _create_auth_headers(admin_user)
        created = client.post(
            "/api/v1/approval-policies",
            json={"name": "Hidden From Customer", "min_risk_score": "5.00"},
            headers=admin_headers,
        ).json()
        policy_id = created["id"]

        cust_headers = _create_auth_headers(customer_user)
        assert (
            client.get(
                "/api/v1/approval-policies", headers=cust_headers
            ).status_code
            == 403
        )
        assert (
            client.get(
                f"/api/v1/approval-policies/{policy_id}", headers=cust_headers
            ).status_code
            == 403
        )
        assert (
            client.post(
                "/api/v1/approval-policies",
                json={"name": "Cust Policy", "min_risk_score": "1.00"},
                headers=cust_headers,
            ).status_code
            == 403
        )
        assert (
            client.patch(
                f"/api/v1/approval-policies/{policy_id}",
                json={"name": "Hack"},
                headers=cust_headers,
            ).status_code
            == 403
        )
        assert (
            client.delete(
                f"/api/v1/approval-policies/{policy_id}", headers=cust_headers
            ).status_code
            == 403
        )

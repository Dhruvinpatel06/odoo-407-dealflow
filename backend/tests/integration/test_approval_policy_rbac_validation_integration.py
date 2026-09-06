"""Integration tests for DealFlow360 Approval Policy RBAC, Business Validation, and Audit.

Step 2 verification suite covering:
1. Complete RBAC authorization matrix (ADMIN, SALES_MANAGER, SALES_REP, FINANCE_OPERATIONS, CUSTOMER, Inactive, Unauthenticated)
2. Business validation rules (score ranges, sequence invariant, active name collisions, conflicting range/priority)
3. Operational lifecycle (activation, deactivation, idempotency)
4. Audit trail integrity (CREATE, UPDATE, ACTIVATE, DEACTIVATE, and rejection of false audits on failure)
5. Configuration vs Execution separation
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.security import create_access_token, hash_password
from app.models.approval_instance import ApprovalInstance
from app.models.approval_policy import ApprovalPolicy
from app.models.approval_step import ApprovalStep
from app.models.audit_log import AuditLog
from app.models.quotation import Quotation
from app.models.user import User


def _auth_headers(user: User) -> dict:
    """Generate authorization header with Bearer token."""
    token = create_access_token(user_id=user.id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_user(db: Session) -> User:
    user = User(
        name="Admin User",
        email=f"admin-{uuid.uuid4().hex[:6]}@dealflow360.local",
        password_hash=hash_password("Password123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def sales_manager_user(db: Session) -> User:
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
def sales_rep_user(db: Session) -> User:
    user = User(
        name="Sales Rep",
        email=f"rep-{uuid.uuid4().hex[:6]}@dealflow360.local",
        password_hash=hash_password("Password123!"),
        role=UserRole.SALES_REP,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def finance_user(db: Session) -> User:
    user = User(
        name="Finance Operations",
        email=f"fin-{uuid.uuid4().hex[:6]}@dealflow360.local",
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
    user = User(
        name="Customer User",
        email=f"cust-{uuid.uuid4().hex[:6]}@client.local",
        password_hash=hash_password("Password123!"),
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def inactive_user(db: Session) -> User:
    user = User(
        name="Inactive Manager",
        email=f"inactive-{uuid.uuid4().hex[:6]}@dealflow360.local",
        password_hash=hash_password("Password123!"),
        role=UserRole.SALES_MANAGER,
        is_active=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ==============================================================================
# 1. RBAC Matrix Tests
# ==============================================================================


class TestApprovalPolicyRBACMatrix:
    """Comprehensive verification of role-based permissions on approval-policies endpoints."""

    def test_admin_has_full_crud_access(
        self, client: TestClient, admin_user: User
    ):
        """Admin can list, create, view, update, and deactivate policies."""
        headers = _auth_headers(admin_user)
        # Create
        create_res = client.post(
            "/api/v1/approval-policies",
            json={
                "name": f"Admin Policy {uuid.uuid4().hex[:6]}",
                "min_risk_score": "0.00",
                "max_risk_score": "10.00",
                "requires_manager": False,
            },
            headers=headers,
        )
        assert create_res.status_code == 201
        policy_id = create_res.json()["id"]

        # List
        assert (
            client.get("/api/v1/approval-policies", headers=headers).status_code
            == 200
        )
        # Get
        assert (
            client.get(
                f"/api/v1/approval-policies/{policy_id}", headers=headers
            ).status_code
            == 200
        )
        # Patch
        assert (
            client.patch(
                f"/api/v1/approval-policies/{policy_id}",
                json={"priority": 10},
                headers=headers,
            ).status_code
            == 200
        )
        # Delete
        assert (
            client.delete(
                f"/api/v1/approval-policies/{policy_id}", headers=headers
            ).status_code
            == 200
        )

    def test_sales_manager_has_full_crud_access(
        self, client: TestClient, sales_manager_user: User
    ):
        """Sales Manager can configure and manage approval policies (FR-05.1)."""
        headers = _auth_headers(sales_manager_user)
        create_res = client.post(
            "/api/v1/approval-policies",
            json={
                "name": f"Manager Policy {uuid.uuid4().hex[:6]}",
                "min_risk_score": "10.01",
                "max_risk_score": "30.00",
                "requires_manager": True,
            },
            headers=headers,
        )
        assert create_res.status_code == 201
        policy_id = create_res.json()["id"]

        assert (
            client.get("/api/v1/approval-policies", headers=headers).status_code
            == 200
        )
        assert (
            client.get(
                f"/api/v1/approval-policies/{policy_id}", headers=headers
            ).status_code
            == 200
        )
        assert (
            client.patch(
                f"/api/v1/approval-policies/{policy_id}",
                json={"priority": 5},
                headers=headers,
            ).status_code
            == 200
        )
        assert (
            client.delete(
                f"/api/v1/approval-policies/{policy_id}", headers=headers
            ).status_code
            == 200
        )

    def test_sales_rep_read_only_access(
        self, client: TestClient, sales_rep_user: User, admin_user: User
    ):
        """Sales Reps can inspect policy details but cannot create, modify, or delete them."""
        # Create as Admin
        admin_h = _auth_headers(admin_user)
        policy = client.post(
            "/api/v1/approval-policies",
            json={
                "name": f"Rep Inspect Policy {uuid.uuid4().hex[:6]}",
                "min_risk_score": "5.00",
            },
            headers=admin_h,
        ).json()
        policy_id = policy["id"]

        rep_h = _auth_headers(sales_rep_user)
        # Read endpoints permitted
        assert (
            client.get("/api/v1/approval-policies", headers=rep_h).status_code
            == 200
        )
        assert (
            client.get(
                f"/api/v1/approval-policies/{policy_id}", headers=rep_h
            ).status_code
            == 200
        )

        # Mutation endpoints strictly forbidden (403)
        assert (
            client.post(
                "/api/v1/approval-policies",
                json={"name": "Rep Illegal", "min_risk_score": "1.00"},
                headers=rep_h,
            ).status_code
            == 403
        )
        assert (
            client.patch(
                f"/api/v1/approval-policies/{policy_id}",
                json={"priority": 99},
                headers=rep_h,
            ).status_code
            == 403
        )
        assert (
            client.delete(
                f"/api/v1/approval-policies/{policy_id}", headers=rep_h
            ).status_code
            == 403
        )

    def test_finance_operations_read_only_access(
        self, client: TestClient, finance_user: User, admin_user: User
    ):
        """Finance/Operations can read policies but cannot configure them."""
        admin_h = _auth_headers(admin_user)
        policy = client.post(
            "/api/v1/approval-policies",
            json={
                "name": f"Finance Inspect Policy {uuid.uuid4().hex[:6]}",
                "min_risk_score": "5.00",
            },
            headers=admin_h,
        ).json()
        policy_id = policy["id"]

        fin_h = _auth_headers(finance_user)
        assert (
            client.get("/api/v1/approval-policies", headers=fin_h).status_code
            == 200
        )
        assert (
            client.get(
                f"/api/v1/approval-policies/{policy_id}", headers=fin_h
            ).status_code
            == 200
        )
        assert (
            client.post(
                "/api/v1/approval-policies",
                json={"name": "Fin Illegal", "min_risk_score": "1.00"},
                headers=fin_h,
            ).status_code
            == 403
        )
        assert (
            client.patch(
                f"/api/v1/approval-policies/{policy_id}",
                json={"priority": 99},
                headers=fin_h,
            ).status_code
            == 403
        )
        assert (
            client.delete(
                f"/api/v1/approval-policies/{policy_id}", headers=fin_h
            ).status_code
            == 403
        )

    def test_customer_role_forbidden_on_all_endpoints(
        self, client: TestClient, customer_user: User
    ):
        """External customers have no visibility into backend approval policy configurations."""
        cust_h = _auth_headers(customer_user)
        fake_id = uuid.uuid4()

        assert (
            client.get("/api/v1/approval-policies", headers=cust_h).status_code
            == 403
        )
        assert (
            client.get(
                f"/api/v1/approval-policies/{fake_id}", headers=cust_h
            ).status_code
            == 403
        )
        assert (
            client.post(
                "/api/v1/approval-policies",
                json={"name": "Cust Illegal", "min_risk_score": "1.00"},
                headers=cust_h,
            ).status_code
            == 403
        )
        assert (
            client.patch(
                f"/api/v1/approval-policies/{fake_id}",
                json={"name": "Cust Hack"},
                headers=cust_h,
            ).status_code
            == 403
        )
        assert (
            client.delete(
                f"/api/v1/approval-policies/{fake_id}", headers=cust_h
            ).status_code
            == 403
        )

    def test_inactive_user_rejected_with_401(
        self, client: TestClient, inactive_user: User
    ):
        """Inactive accounts are rejected immediately by authentication dependency."""
        headers = _auth_headers(inactive_user)
        assert (
            client.get("/api/v1/approval-policies", headers=headers).status_code
            == 401
        )
        assert (
            client.post(
                "/api/v1/approval-policies",
                json={"name": "Inactive Policy", "min_risk_score": "1.00"},
                headers=headers,
            ).status_code
            == 401
        )

    def test_unauthenticated_requests_rejected_with_401(
        self, client: TestClient
    ):
        """Missing or malformed Authorization header produces 401."""
        assert client.get("/api/v1/approval-policies").status_code == 401
        assert (
            client.get(
                f"/api/v1/approval-policies/{uuid.uuid4()}"
            ).status_code
            == 401
        )
        assert (
            client.post(
                "/api/v1/approval-policies", json={"name": "No Auth"}
            ).status_code
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

        # Malformed bearer token
        bad_h = {"Authorization": "Bearer invalid.jwt.token"}
        assert (
            client.get("/api/v1/approval-policies", headers=bad_h).status_code
            == 401
        )


# ==============================================================================
# 2. Business Validation Tests
# ==============================================================================


class TestApprovalPolicyBusinessValidation:
    """Rigorous verification of business constraints, invariants, and edge cases."""

    def test_valid_approval_chain_behaviors(
        self, client: TestClient, admin_user: User
    ):
        """Verify all three supported policy behaviors from API contract."""
        headers = _auth_headers(admin_user)

        # 1. No approval required
        res1 = client.post(
            "/api/v1/approval-policies",
            json={
                "name": f"Behavior 1 {uuid.uuid4().hex[:6]}",
                "min_risk_score": "0.00",
                "max_risk_score": "10.00",
                "requires_manager": False,
                "requires_finance": False,
                "priority": 1,
            },
            headers=headers,
        )
        assert res1.status_code == 201

        # 2. Sales Manager approval
        res2 = client.post(
            "/api/v1/approval-policies",
            json={
                "name": f"Behavior 2 {uuid.uuid4().hex[:6]}",
                "min_risk_score": "10.01",
                "max_risk_score": "50.00",
                "requires_manager": True,
                "requires_finance": False,
                "priority": 2,
            },
            headers=headers,
        )
        assert res2.status_code == 201

        # 3. Sales Manager followed by Finance approval
        res3 = client.post(
            "/api/v1/approval-policies",
            json={
                "name": f"Behavior 3 {uuid.uuid4().hex[:6]}",
                "min_risk_score": "50.01",
                "max_risk_score": None,
                "requires_manager": True,
                "requires_finance": True,
                "priority": 3,
            },
            headers=headers,
        )
        assert res3.status_code == 201

    def test_reject_finance_without_manager_on_create(
        self, client: TestClient, admin_user: User
    ):
        """Finance approval cannot be standalone in the approval chain."""
        headers = _auth_headers(admin_user)
        res = client.post(
            "/api/v1/approval-policies",
            json={
                "name": "Finance Only",
                "min_risk_score": "20.00",
                "requires_manager": False,
                "requires_finance": True,
            },
            headers=headers,
        )
        assert res.status_code == 422
        assert (
            "Finance approval requires Sales Manager approval in the sequence"
            in res.text
        )

    def test_reject_finance_without_manager_on_update(
        self, client: TestClient, admin_user: User
    ):
        """Updating requires_manager to False when requires_finance is True is rejected."""
        headers = _auth_headers(admin_user)
        created = client.post(
            "/api/v1/approval-policies",
            json={
                "name": f"Dual Policy {uuid.uuid4().hex[:6]}",
                "min_risk_score": "40.00",
                "requires_manager": True,
                "requires_finance": True,
            },
            headers=headers,
        ).json()
        policy_id = created["id"]

        # Attempt to set requires_manager = False while finance remains True
        res = client.patch(
            f"/api/v1/approval-policies/{policy_id}",
            json={"requires_manager": False},
            headers=headers,
        )
        assert res.status_code in (400, 422)
        assert "Finance approval requires Sales Manager approval" in res.text

    def test_reject_inverted_scores_on_create_and_update(
        self, client: TestClient, admin_user: User
    ):
        """max_risk_score must not be less than min_risk_score."""
        headers = _auth_headers(admin_user)
        # On create
        res_create = client.post(
            "/api/v1/approval-policies",
            json={
                "name": "Inverted Range",
                "min_risk_score": "60.00",
                "max_risk_score": "30.00",
            },
            headers=headers,
        )
        assert res_create.status_code == 422
        assert "greater than or equal to min_risk_score" in res_create.text

        # Create valid baseline
        created = client.post(
            "/api/v1/approval-policies",
            json={
                "name": f"Valid Range {uuid.uuid4().hex[:6]}",
                "min_risk_score": "20.00",
                "max_risk_score": "40.00",
            },
            headers=headers,
        ).json()
        policy_id = created["id"]

        # Raise min above current max
        res_patch1 = client.patch(
            f"/api/v1/approval-policies/{policy_id}",
            json={"min_risk_score": "50.00"},
            headers=headers,
        )
        assert res_patch1.status_code in (400, 422)

        # Lower max below current min
        res_patch2 = client.patch(
            f"/api/v1/approval-policies/{policy_id}",
            json={"max_risk_score": "10.00"},
            headers=headers,
        )
        assert res_patch2.status_code in (400, 422)

    def test_reject_conflicting_active_policy_range_and_priority(
        self, client: TestClient, admin_user: User
    ):
        """Active policies with identical risk ranges and priority must be rejected."""
        headers = _auth_headers(admin_user)
        # Create first policy
        client.post(
            "/api/v1/approval-policies",
            json={
                "name": "First Standard Policy",
                "min_risk_score": "15.00",
                "max_risk_score": "35.00",
                "priority": 10,
                "is_active": True,
            },
            headers=headers,
        )

        # Attempt to create duplicate with identical range and priority
        res_dup = client.post(
            "/api/v1/approval-policies",
            json={
                "name": "Conflicting Second Policy",
                "min_risk_score": "15.00",
                "max_risk_score": "35.00",
                "priority": 10,
                "is_active": True,
            },
            headers=headers,
        )
        assert res_dup.status_code == 400
        assert "already covers the identical risk score range" in res_dup.text

    def test_allow_identical_range_if_priorities_differ(
        self, client: TestClient, admin_user: User
    ):
        """Policies covering the same risk range are valid if priorities differ (deterministic tie-breaking)."""
        headers = _auth_headers(admin_user)
        res1 = client.post(
            "/api/v1/approval-policies",
            json={
                "name": f"Priority 10 {uuid.uuid4().hex[:6]}",
                "min_risk_score": "20.00",
                "max_risk_score": "40.00",
                "priority": 10,
            },
            headers=headers,
        )
        assert res1.status_code == 201

        res2 = client.post(
            "/api/v1/approval-policies",
            json={
                "name": f"Priority 20 {uuid.uuid4().hex[:6]}",
                "min_risk_score": "20.00",
                "max_risk_score": "40.00",
                "priority": 20,
            },
            headers=headers,
        )
        assert res2.status_code == 201

    def test_reactivation_enforces_name_uniqueness(
        self, client: TestClient, admin_user: User
    ):
        """Activating an inactive policy must not create duplicate active names."""
        headers = _auth_headers(admin_user)
        shared_name = f"Shared Name {uuid.uuid4().hex[:6]}"

        # Create active policy
        client.post(
            "/api/v1/approval-policies",
            json={
                "name": shared_name,
                "min_risk_score": "1.00",
                "is_active": True,
            },
            headers=headers,
        )

        # Create inactive policy with different name
        inactive_pol = client.post(
            "/api/v1/approval-policies",
            json={
                "name": f"Other Inactive {uuid.uuid4().hex[:6]}",
                "min_risk_score": "2.00",
                "is_active": False,
            },
            headers=headers,
        ).json()
        inactive_id = inactive_pol["id"]

        # Try to rename and activate with the shared active name
        res = client.patch(
            f"/api/v1/approval-policies/{inactive_id}",
            json={"name": shared_name, "is_active": True},
            headers=headers,
        )
        assert res.status_code == 400
        assert "already exists" in res.text


# ==============================================================================
# 3. Audit Logging Integrity Tests
# ==============================================================================


class TestApprovalPolicyAuditIntegration:
    """Verify authoritative audit records for every configuration transition."""

    def test_audit_lifecycle_events(
        self, client: TestClient, admin_user: User, db: Session
    ):
        """Verify CREATE, UPDATE, DEACTIVATE, and ACTIVATE audit records."""
        headers = _auth_headers(admin_user)

        # 1. CREATE
        created = client.post(
            "/api/v1/approval-policies",
            json={
                "name": f"Audit Policy {uuid.uuid4().hex[:6]}",
                "min_risk_score": "10.00",
                "requires_manager": True,
            },
            headers=headers,
        ).json()
        policy_id = uuid.UUID(created["id"])

        create_audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.entity_type == "APPROVAL_POLICY",
                AuditLog.entity_id == policy_id,
                AuditLog.action == "CREATE",
            )
            .first()
        )
        assert create_audit is not None
        assert create_audit.user_id == admin_user.id
        assert create_audit.old_values is None
        assert create_audit.new_values["requires_manager"] is True

        # 2. UPDATE
        client.patch(
            f"/api/v1/approval-policies/{policy_id}",
            json={"priority": 12},
            headers=headers,
        )
        update_audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.entity_type == "APPROVAL_POLICY",
                AuditLog.entity_id == policy_id,
                AuditLog.action == "UPDATE",
            )
            .first()
        )
        assert update_audit is not None
        assert update_audit.old_values["priority"] == 0
        assert update_audit.new_values["priority"] == 12

        # 3. DEACTIVATE via DELETE endpoint
        client.delete(
            f"/api/v1/approval-policies/{policy_id}", headers=headers
        )
        deact_audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.entity_type == "APPROVAL_POLICY",
                AuditLog.entity_id == policy_id,
                AuditLog.action == "DEACTIVATE",
            )
            .first()
        )
        assert deact_audit is not None
        assert deact_audit.old_values["is_active"] is True
        assert deact_audit.new_values["is_active"] is False

        # 4. ACTIVATE via PATCH endpoint
        client.patch(
            f"/api/v1/approval-policies/{policy_id}",
            json={"is_active": True},
            headers=headers,
        )
        act_audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.entity_type == "APPROVAL_POLICY",
                AuditLog.entity_id == policy_id,
                AuditLog.action == "ACTIVATE",
            )
            .first()
        )
        assert act_audit is not None
        assert act_audit.old_values["is_active"] is False
        assert act_audit.new_values["is_active"] is True

    def test_no_false_audit_logs_on_validation_failure(
        self, client: TestClient, admin_user: User, db: Session
    ):
        """Failed operations must not write orphaned audit records to the database."""
        headers = _auth_headers(admin_user)
        initial_audit_count = db.query(AuditLog).count()

        # Rejected create
        client.post(
            "/api/v1/approval-policies",
            json={"name": "Bad Policy", "min_risk_score": "-10.00"},
            headers=headers,
        )

        # Rejected finance invariant
        client.post(
            "/api/v1/approval-policies",
            json={
                "name": "Bad Finance",
                "min_risk_score": "10.00",
                "requires_manager": False,
                "requires_finance": True,
            },
            headers=headers,
        )

        final_audit_count = db.query(AuditLog).count()
        assert final_audit_count == initial_audit_count


# ==============================================================================
# 4. Configuration vs Execution Separation Tests
# ==============================================================================


class TestConfigurationExecutionSeparation:
    """Verify policy configuration operations have no side-effects on approval execution."""

    def test_policy_crud_does_not_mutate_execution_tables(
        self, client: TestClient, admin_user: User, db: Session
    ):
        """Policy creation/update/deletion must never create approval instances or steps."""
        initial_instances = db.query(ApprovalInstance).count()
        initial_steps = db.query(ApprovalStep).count()
        initial_quotations = db.query(Quotation).count()

        headers = _auth_headers(admin_user)
        # Create policy
        p = client.post(
            "/api/v1/approval-policies",
            json={
                "name": f"Isolated Policy {uuid.uuid4().hex[:6]}",
                "min_risk_score": "25.00",
                "requires_manager": True,
            },
            headers=headers,
        ).json()

        # Update policy
        client.patch(
            f"/api/v1/approval-policies/{p['id']}",
            json={"priority": 10},
            headers=headers,
        )

        # Deactivate policy
        client.delete(f"/api/v1/approval-policies/{p['id']}", headers=headers)

        # Verify zero side-effects on execution models
        assert db.query(ApprovalInstance).count() == initial_instances
        assert db.query(ApprovalStep).count() == initial_steps
        assert db.query(Quotation).count() == initial_quotations

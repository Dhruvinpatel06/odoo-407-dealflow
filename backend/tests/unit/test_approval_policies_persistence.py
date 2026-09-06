"""Persistence-level unit tests for the ApprovalPolicy model and database schema foundation."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import Base
from app.models.approval_policy import ApprovalPolicy


def test_approval_policy_persistence_minimal(db: Session):
    """Verify ApprovalPolicy can be persisted with minimal required fields and appropriate defaults."""
    policy = ApprovalPolicy(
        name=f"Standard Low Risk {uuid.uuid4().hex[:6]}",
        min_risk_score=Decimal("0.00"),
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)

    assert policy.id is not None
    assert isinstance(policy.id, uuid.UUID)
    assert policy.min_risk_score == Decimal("0.00")
    assert policy.max_risk_score is None
    assert policy.requires_manager is False
    assert policy.requires_finance is False
    assert policy.priority == 0
    assert policy.is_active is True
    assert policy.created_at is not None
    assert policy.updated_at is not None


def test_approval_policy_persistence_full(db: Session):
    """Verify ApprovalPolicy can be persisted with all explicit attributes."""
    policy = ApprovalPolicy(
        name=f"High Risk Dual Approval {uuid.uuid4().hex[:6]}",
        min_risk_score=Decimal("50.00"),
        max_risk_score=Decimal("100.00"),
        requires_manager=True,
        requires_finance=True,
        priority=20,
        is_active=True,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)

    assert policy.name.startswith("High Risk Dual Approval")
    assert policy.min_risk_score == Decimal("50.00")
    assert policy.max_risk_score == Decimal("100.00")
    assert policy.requires_manager is True
    assert policy.requires_finance is True
    assert policy.priority == 20
    assert policy.is_active is True


def test_approval_policy_update_persistence(db: Session):
    """Verify ApprovalPolicy attributes can be modified and persisted."""
    policy = ApprovalPolicy(
        name=f"Manager Policy {uuid.uuid4().hex[:6]}",
        min_risk_score=Decimal("10.00"),
        max_risk_score=Decimal("40.00"),
        requires_manager=True,
        requires_finance=False,
        priority=5,
        is_active=True,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)

    policy.name = "Updated Manager Policy"
    policy.max_risk_score = Decimal("45.00")
    policy.priority = 8
    db.commit()
    db.refresh(policy)

    assert policy.name == "Updated Manager Policy"
    assert policy.max_risk_score == Decimal("45.00")
    assert policy.priority == 8


def test_approval_policy_deactivation_persistence(db: Session):
    """Verify logical deactivation persists correctly."""
    policy = ApprovalPolicy(
        name=f"Obsolete Policy {uuid.uuid4().hex[:6]}",
        min_risk_score=Decimal("15.00"),
        is_active=True,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)

    policy.is_active = False
    db.commit()
    db.refresh(policy)

    assert policy.is_active is False


def test_approval_policy_required_fields_enforced(db: Session):
    """Verify required field min_risk_score cannot be null in database."""
    policy = ApprovalPolicy(
        name="Invalid Policy",
        min_risk_score=None,  # type: ignore
    )
    db.add(policy)
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            db.flush()


def test_approval_policy_database_schema_contract():
    """Verify table name, columns, nullability, and primary key definition match finalized schema."""
    table = Base.metadata.tables.get("approval_policies")
    assert table is not None, "Table 'approval_policies' must exist in Base.metadata"

    expected_columns = {
        "id": (False, True),  # (nullable, is_pk)
        "name": (False, False),
        "min_risk_score": (False, False),
        "max_risk_score": (True, False),
        "requires_manager": (False, False),
        "requires_finance": (False, False),
        "priority": (False, False),
        "is_active": (False, False),
        "created_at": (False, False),
        "updated_at": (False, False),
    }

    assert set(table.columns.keys()) == set(expected_columns.keys())

    for col_name, (expected_nullable, expected_pk) in expected_columns.items():
        col = table.columns[col_name]
        assert col.nullable is expected_nullable, f"Column {col_name} nullable mismatch"
        assert col.primary_key is expected_pk, f"Column {col_name} PK mismatch"

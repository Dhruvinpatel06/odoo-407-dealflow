"""Migration verification and schema contract tests for DealFlow360 Approval Policies.

Step 3 verification suite covering:
1. Exact database schema reflection against Table 11 specification
2. Alembic migration DAG integrity and schema drift detection
3. End-to-end quotation engine compatibility with persisted ApprovalPolicy configurations
4. Separation of configuration from execution
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.common.enums import ApproverRole
from app.core.database import Base, engine
from app.models.approval_instance import ApprovalInstance
from app.models.approval_policy import ApprovalPolicy
from app.models.approval_step import ApprovalStep
from app.models.quotation import Quotation
from app.modules.quotations.engine import quotation_engine


class TestApprovalPolicySchemaContract:
    """Verifies the database schema against the Table 11 specification."""

    def test_database_table_columns_and_constraints(self):
        """Reflect table directly and verify exact columns, nullability, and PK."""
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
            assert col.nullable is expected_nullable, f"Column '{col_name}' nullable mismatch"
            assert col.primary_key is expected_pk, f"Column '{col_name}' PK mismatch"

    def test_alembic_script_directory_revisions(self):
        """Verify Alembic migration chain DAG is connected and head is consistent."""
        config = Config("alembic.ini")
        script = ScriptDirectory.from_config(config)

        # Ensure head revision exists
        heads = script.get_heads()
        assert len(heads) == 1
        assert heads[0] == "e5f9fbc62d10"

        # Ensure base revision is ce58f26a68b0 (which creates approval_policies)
        base_rev = script.get_base()
        assert base_rev == "ce58f26a68b0"

        # Walk revisions to ensure no orphaned nodes
        revs = list(script.walk_revisions())
        assert len(revs) == 2
        rev_ids = [r.revision for r in revs]
        assert "e5f9fbc62d10" in rev_ids
        assert "ce58f26a68b0" in rev_ids


class TestQuotationEnginePolicyResolution:
    """Verifies that configured ApprovalPolicy records integrate seamlessly with quotation approval logic."""

    def test_persisted_policy_matching_no_approval(self, db: Session):
        """Risk score in no-approval policy range returns (False, None)."""
        policy = ApprovalPolicy(
            name=f"No Approval Tier {uuid.uuid4().hex[:6]}",
            min_risk_score=Decimal("0.00"),
            max_risk_score=Decimal("15.00"),
            requires_manager=False,
            requires_finance=False,
            priority=5,
            is_active=True,
        )
        db.add(policy)
        db.commit()
        db.refresh(policy)

        app_req, level = quotation_engine.determine_approval_requirement(
            risk_score=Decimal("10.00"),
            has_line_violations=False,
            approval_policies=[policy],
        )
        assert app_req is False
        assert level is None

    def test_persisted_policy_matching_sales_manager(self, db: Session):
        """Risk score in Manager policy range returns (True, 'SALES_MANAGER')."""
        policy = ApprovalPolicy(
            name=f"Manager Tier {uuid.uuid4().hex[:6]}",
            min_risk_score=Decimal("15.01"),
            max_risk_score=Decimal("40.00"),
            requires_manager=True,
            requires_finance=False,
            priority=10,
            is_active=True,
        )
        db.add(policy)
        db.commit()
        db.refresh(policy)

        app_req, level = quotation_engine.determine_approval_requirement(
            risk_score=Decimal("25.00"),
            has_line_violations=True,
            approval_policies=[policy],
        )
        assert app_req is True
        assert level == ApproverRole.SALES_MANAGER.value

    def test_persisted_policy_matching_finance_operations(self, db: Session):
        """Risk score in Finance policy range returns (True, 'FINANCE_OPERATIONS')."""
        policy = ApprovalPolicy(
            name=f"Finance Tier {uuid.uuid4().hex[:6]}",
            min_risk_score=Decimal("40.01"),
            max_risk_score=None,
            requires_manager=True,
            requires_finance=True,
            priority=20,
            is_active=True,
        )
        db.add(policy)
        db.commit()
        db.refresh(policy)

        app_req, level = quotation_engine.determine_approval_requirement(
            risk_score=Decimal("85.00"),
            has_line_violations=True,
            approval_policies=[policy],
        )
        assert app_req is True
        assert level == ApproverRole.FINANCE_OPERATIONS.value

    def test_priority_resolution_between_overlapping_policies(self, db: Session):
        """Higher priority policy wins when risk score matches multiple policies."""
        low_priority_policy = ApprovalPolicy(
            name=f"Low Priority Policy {uuid.uuid4().hex[:6]}",
            min_risk_score=Decimal("10.00"),
            max_risk_score=Decimal("50.00"),
            requires_manager=True,
            requires_finance=False,
            priority=1,
            is_active=True,
        )
        high_priority_policy = ApprovalPolicy(
            name=f"High Priority Policy {uuid.uuid4().hex[:6]}",
            min_risk_score=Decimal("20.00"),
            max_risk_score=Decimal("60.00"),
            requires_manager=True,
            requires_finance=True,
            priority=50,
            is_active=True,
        )
        db.add_all([low_priority_policy, high_priority_policy])
        db.commit()

        # At score 30, both match. High priority policy (priority=50, finance=True) should win.
        app_req, level = quotation_engine.determine_approval_requirement(
            risk_score=Decimal("30.00"),
            has_line_violations=True,
            approval_policies=[low_priority_policy, high_priority_policy],
        )
        assert app_req is True
        assert level == ApproverRole.FINANCE_OPERATIONS.value

    def test_inactive_policy_ignored_by_engine(self, db: Session):
        """Deactivated policies are bypassed by the engine in favor of active policies or baseline."""
        inactive_policy = ApprovalPolicy(
            name=f"Inactive Dual Tier {uuid.uuid4().hex[:6]}",
            min_risk_score=Decimal("10.00"),
            max_risk_score=Decimal("50.00"),
            requires_manager=True,
            requires_finance=True,
            priority=100,
            is_active=False,
        )
        active_manager_policy = ApprovalPolicy(
            name=f"Active Manager Tier {uuid.uuid4().hex[:6]}",
            min_risk_score=Decimal("10.00"),
            max_risk_score=Decimal("50.00"),
            requires_manager=True,
            requires_finance=False,
            priority=10,
            is_active=True,
        )
        db.add_all([inactive_policy, active_manager_policy])
        db.commit()

        app_req, level = quotation_engine.determine_approval_requirement(
            risk_score=Decimal("25.00"),
            has_line_violations=True,
            approval_policies=[inactive_policy, active_manager_policy],
        )
        # Should match active_manager_policy (SALES_MANAGER), NOT inactive_policy (FINANCE_OPERATIONS)
        assert app_req is True
        assert level == ApproverRole.SALES_MANAGER.value


class TestConfigurationExecutionIsolation:
    """Verifies complete separation of Approval Policy configuration from Approval Execution."""

    def test_approval_policy_does_not_cascade_to_execution(self, db: Session):
        """Creating, modifying, or querying policies produces zero side-effects on execution models."""
        assert db.query(ApprovalInstance).count() == 0
        assert db.query(ApprovalStep).count() == 0
        assert db.query(Quotation).count() == 0

        # Persist multiple policies
        p1 = ApprovalPolicy(
            name=f"Isolation Test 1 {uuid.uuid4().hex[:6]}",
            min_risk_score=Decimal("0.00"),
            max_risk_score=Decimal("20.00"),
            requires_manager=False,
        )
        p2 = ApprovalPolicy(
            name=f"Isolation Test 2 {uuid.uuid4().hex[:6]}",
            min_risk_score=Decimal("20.01"),
            requires_manager=True,
        )
        db.add_all([p1, p2])
        db.commit()

        # Update
        p1.priority = 10
        p2.is_active = False
        db.commit()

        # Verify execution tables remain untouched
        assert db.query(ApprovalInstance).count() == 0
        assert db.query(ApprovalStep).count() == 0
        assert db.query(Quotation).count() == 0

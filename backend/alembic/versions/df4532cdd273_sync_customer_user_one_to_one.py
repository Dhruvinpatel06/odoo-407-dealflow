"""sync_customer_user_one_to_one

Revision ID: df4532cdd273
Revises: e5f9fbc62d10
Create Date: 2026-09-06 08:15:22.063934

"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision: str = 'df4532cdd273'
down_revision: Union[str, None] = 'e5f9fbc62d10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Reconcile existing data safely before adding unique constraint:
    # 1a. Reset customer_id for non-CUSTOMER users (non-customer users should not link to customers)
    conn.execute(text("UPDATE users SET customer_id = NULL WHERE role != 'CUSTOMER'"))

    # 1b. For CUSTOMER users, link to existing unlinked customer with matching email if available
    conn.execute(
        text(
            """
            UPDATE users u
            SET customer_id = c.id
            FROM customers c
            WHERE u.role = 'CUSTOMER'
              AND LOWER(u.email) = LOWER(c.email)
              AND (u.customer_id IS NULL OR u.customer_id != c.id)
              AND NOT EXISTS (
                  SELECT 1 FROM users other
                  WHERE other.customer_id = c.id AND other.id != u.id
              )
            """
        )
    )

    # 1c. For CUSTOMER users that still have no customer_id, create a new customer record
    # Find default active tier
    tier_result = conn.execute(
        text("SELECT id FROM customer_tiers WHERE is_active = true ORDER BY default_discount_limit ASC LIMIT 1")
    ).fetchone()

    default_tier_id = None
    if tier_result:
        default_tier_id = tier_result[0]
    else:
        # If no active tier exists, create a default standard tier
        default_tier_id = uuid.uuid4()
        conn.execute(
            text(
                """
                INSERT INTO customer_tiers (id, name, description, default_discount_limit, is_active, created_at, updated_at)
                VALUES (:id, 'STANDARD', 'Default Customer Tier', 0.00, true, NOW(), NOW())
                """
            ),
            {"id": default_tier_id},
        )

    # Fetch any CUSTOMER users without customer_id
    orphan_users = conn.execute(
        text("SELECT id, name, email, is_active FROM users WHERE role = 'CUSTOMER' AND customer_id IS NULL")
    ).fetchall()

    for user_row in orphan_users:
        u_id, u_name, u_email, u_is_active = user_row[0], user_row[1], user_row[2], user_row[3]
        new_cust_id = uuid.uuid4()
        conn.execute(
            text(
                """
                INSERT INTO customers (id, name, email, customer_tier_id, is_active, created_at, updated_at)
                VALUES (:id, :name, :email, :tier_id, :is_active, NOW(), NOW())
                """
            ),
            {
                "id": new_cust_id,
                "name": u_name,
                "email": u_email,
                "tier_id": default_tier_id,
                "is_active": u_is_active,
            },
        )
        conn.execute(
            text("UPDATE users SET customer_id = :cust_id WHERE id = :user_id"),
            {"cust_id": new_cust_id, "user_id": u_id},
        )

    # 2. Schema changes: replace non-unique index on users.customer_id with unique index
    op.drop_index('ix_users_customer_id', table_name='users')
    op.create_index(op.f('ix_users_customer_id'), 'users', ['customer_id'], unique=True)


def downgrade() -> None:
    # Revert unique index back to non-unique index
    op.drop_index(op.f('ix_users_customer_id'), table_name='users')
    op.create_index(op.f('ix_users_customer_id'), 'users', ['customer_id'], unique=False)

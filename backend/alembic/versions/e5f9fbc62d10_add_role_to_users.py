"""add_role_to_users

Revision ID: e5f9fbc62d10
Revises: ce58f26a68b0
Create Date: 2026-09-05 21:03:34.301465

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e5f9fbc62d10'
down_revision: Union[str, None] = 'ce58f26a68b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Enum definition containing exactly the 5 required application roles
user_role_enum = postgresql.ENUM(
    'CUSTOMER',
    'SALES_REP',
    'SALES_MANAGER',
    'FINANCE_OPERATIONS',
    'ADMIN',
    name='user_role',
    create_type=False,
)


def upgrade() -> None:
    # 1. Create the user_role enum type in PostgreSQL
    sa_enum = sa.Enum(
        'CUSTOMER',
        'SALES_REP',
        'SALES_MANAGER',
        'FINANCE_OPERATIONS',
        'ADMIN',
        name='user_role',
    )
    sa_enum.create(op.get_bind(), checkfirst=True)

    # 2. Add non-nullable role column to users table
    op.add_column(
        'users',
        sa.Column('role', user_role_enum, nullable=False),
    )


def downgrade() -> None:
    # 1. Drop role column from users table
    op.drop_column('users', 'role')

    # 2. Drop user_role enum type
    sa_enum = sa.Enum(
        'CUSTOMER',
        'SALES_REP',
        'SALES_MANAGER',
        'FINANCE_OPERATIONS',
        'ADMIN',
        name='user_role',
    )
    sa_enum.drop(op.get_bind(), checkfirst=True)

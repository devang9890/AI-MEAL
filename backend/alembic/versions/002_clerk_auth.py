"""Add clerk_user_id; make password_hash nullable

Revision ID: 002_clerk_auth
Revises: 001_initial_tables
Create Date: 2026-09-08

Changes
-------
* users.clerk_user_id  — new VARCHAR(255) UNIQUE nullable column with index
* users.password_hash  — relaxed from NOT NULL → nullable (Clerk owns identity)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '002_clerk_auth'
down_revision: Union[str, None] = '001_initial_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add clerk_user_id column
    op.add_column(
        'users',
        sa.Column('clerk_user_id', sa.String(length=255), nullable=True),
    )
    op.create_index(
        op.f('ix_users_clerk_user_id'),
        'users',
        ['clerk_user_id'],
        unique=True,
    )

    # Make password_hash nullable (Clerk owns auth; no local password needed)
    op.alter_column(
        'users',
        'password_hash',
        existing_type=sa.String(length=255),
        nullable=True,
    )


def downgrade() -> None:
    # Restore password_hash to NOT NULL (will fail if any rows are NULL; handle manually)
    op.alter_column(
        'users',
        'password_hash',
        existing_type=sa.String(length=255),
        nullable=False,
    )

    op.drop_index(op.f('ix_users_clerk_user_id'), table_name='users')
    op.drop_column('users', 'clerk_user_id')

"""add diseases to members

Revision ID: 005_member_diseases
Revises: 004_household_members_nutrition
"""
from alembic import op
import sqlalchemy as sa

revision = "005_member_diseases"
down_revision = "004_household_members_nutrition"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("members", sa.Column("diseases", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("members", "diseases")

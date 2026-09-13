"""Household, members and nutrition engine schema updates

Revision ID: 004_household_members_nutrition
Revises: 003_food_and_recipe_db
Create Date: 2026-09-13

Changes
-------
* households:
    - Add updated_at (TIMESTAMP WITH TIME ZONE)
* members:
    - Add height_cm (FLOAT)
    - Add weight_kg (FLOAT)
    - Add dietary_preference (VARCHAR(50), default 'vegetarian')
    - Add updated_at (TIMESTAMP WITH TIME ZONE)
* nutrition_targets:
    - Add daily_calories (FLOAT)
    - Add daily_protein_g (FLOAT)
    - Add daily_carbs_g (FLOAT)
    - Add daily_fat_g (FLOAT)
    - Add daily_fiber_g (FLOAT, default 0.0)
    - Add updated_at (TIMESTAMP WITH TIME ZONE)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '004_household_members_nutrition'
down_revision: Union[str, None] = '003_food_and_recipe_db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update households
    op.add_column(
        'households',
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )

    # 2. Update members
    op.add_column(
        'members',
        sa.Column('height_cm', sa.Float(), nullable=True)
    )
    op.add_column(
        'members',
        sa.Column('weight_kg', sa.Float(), nullable=True)
    )
    op.add_column(
        'members',
        sa.Column('dietary_preference', sa.String(length=50), server_default='vegetarian', nullable=False)
    )
    op.add_column(
        'members',
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )

    # Migrate any existing values from legacy columns
    op.execute("UPDATE members SET height_cm = height WHERE height_cm IS NULL AND height IS NOT NULL")
    op.execute("UPDATE members SET weight_kg = weight WHERE weight_kg IS NULL AND weight IS NOT NULL")
    op.execute("UPDATE members SET dietary_preference = diet_type WHERE dietary_preference IS NULL AND diet_type IS NOT NULL")

    # 3. Update nutrition_targets
    op.add_column(
        'nutrition_targets',
        sa.Column('daily_calories', sa.Float(), nullable=True)
    )
    op.add_column(
        'nutrition_targets',
        sa.Column('daily_protein_g', sa.Float(), nullable=True)
    )
    op.add_column(
        'nutrition_targets',
        sa.Column('daily_carbs_g', sa.Float(), nullable=True)
    )
    op.add_column(
        'nutrition_targets',
        sa.Column('daily_fat_g', sa.Float(), nullable=True)
    )
    op.add_column(
        'nutrition_targets',
        sa.Column('daily_fiber_g', sa.Float(), server_default='0.0', nullable=False)
    )
    op.add_column(
        'nutrition_targets',
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )

    # Migrate any existing values from legacy columns
    op.execute("UPDATE nutrition_targets SET daily_calories = calories WHERE daily_calories IS NULL AND calories IS NOT NULL")
    op.execute("UPDATE nutrition_targets SET daily_protein_g = protein WHERE daily_protein_g IS NULL AND protein IS NOT NULL")
    op.execute("UPDATE nutrition_targets SET daily_carbs_g = carbohydrates WHERE daily_carbs_g IS NULL AND carbohydrates IS NOT NULL")
    op.execute("UPDATE nutrition_targets SET daily_fat_g = fat WHERE daily_fat_g IS NULL AND fat IS NOT NULL")


def downgrade() -> None:
    # Revert nutrition_targets
    op.drop_column('nutrition_targets', 'updated_at')
    op.drop_column('nutrition_targets', 'daily_fiber_g')
    op.drop_column('nutrition_targets', 'daily_fat_g')
    op.drop_column('nutrition_targets', 'daily_carbs_g')
    op.drop_column('nutrition_targets', 'daily_protein_g')
    op.drop_column('nutrition_targets', 'daily_calories')

    # Revert members
    op.drop_column('members', 'updated_at')
    op.drop_column('members', 'dietary_preference')
    op.drop_column('members', 'weight_kg')
    op.drop_column('members', 'height_cm')

    # Revert households
    op.drop_column('households', 'updated_at')

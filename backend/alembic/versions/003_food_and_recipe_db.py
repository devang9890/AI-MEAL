"""Food and recipe database schema enhancements

Revision ID: 003_food_and_recipe_db
Revises: 002_clerk_auth
Create Date: 2026-09-13

Changes
-------
* ingredients:
    - Add category (VARCHAR(100), indexed)
    - Add fiber (FLOAT)
    - Make name UNIQUE (drop non-unique index, create unique index)
* recipes:
    - Add preparation_time (INTEGER)
    - Add cooking_time (INTEGER)
    - Add dietary_tags (JSON)
    - Add index on meal_type and cuisine
    - Make name UNIQUE (drop non-unique index, create unique index)
* recipe_ingredients:
    - Add unit (VARCHAR(50), default 'g')
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '003_food_and_recipe_db'
down_revision: Union[str, None] = '002_clerk_auth'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update ingredients table
    op.add_column(
        'ingredients',
        sa.Column('category', sa.String(length=100), nullable=False, server_default='General')
    )
    op.create_index(
        op.f('ix_ingredients_category'),
        'ingredients',
        ['category'],
        unique=False
    )
    op.add_column(
        'ingredients',
        sa.Column('fiber', sa.Float(), nullable=True, server_default='0.0')
    )
    op.drop_index('ix_ingredients_name', table_name='ingredients')
    op.create_index(
        op.f('ix_ingredients_name'),
        'ingredients',
        ['name'],
        unique=True
    )

    # 2. Update recipes table
    op.add_column(
        'recipes',
        sa.Column('preparation_time', sa.Integer(), nullable=True, server_default='15')
    )
    op.add_column(
        'recipes',
        sa.Column('cooking_time', sa.Integer(), nullable=True, server_default='20')
    )
    op.add_column(
        'recipes',
        sa.Column('dietary_tags', sa.JSON(), nullable=True)
    )
    op.create_index(
        op.f('ix_recipes_meal_type'),
        'recipes',
        ['meal_type'],
        unique=False
    )
    op.create_index(
        op.f('ix_recipes_cuisine'),
        'recipes',
        ['cuisine'],
        unique=False
    )
    op.drop_index('ix_recipes_name', table_name='recipes')
    op.create_index(
        op.f('ix_recipes_name'),
        'recipes',
        ['name'],
        unique=True
    )

    # 3. Update recipe_ingredients table
    op.add_column(
        'recipe_ingredients',
        sa.Column('unit', sa.String(length=50), nullable=False, server_default='g')
    )


def downgrade() -> None:
    # 3. Revert recipe_ingredients
    op.drop_column('recipe_ingredients', 'unit')

    # 2. Revert recipes
    op.drop_index(op.f('ix_recipes_name'), table_name='recipes')
    op.create_index('ix_recipes_name', 'recipes', ['name'], unique=False)
    op.drop_index(op.f('ix_recipes_cuisine'), table_name='recipes')
    op.drop_index(op.f('ix_recipes_meal_type'), table_name='recipes')
    op.drop_column('recipes', 'dietary_tags')
    op.drop_column('recipes', 'cooking_time')
    op.drop_column('recipes', 'preparation_time')

    # 1. Revert ingredients
    op.drop_index(op.f('ix_ingredients_name'), table_name='ingredients')
    op.create_index('ix_ingredients_name', 'ingredients', ['name'], unique=False)
    op.drop_column('ingredients', 'fiber')
    op.drop_index(op.f('ix_ingredients_category'), table_name='ingredients')
    op.drop_column('ingredients', 'category')

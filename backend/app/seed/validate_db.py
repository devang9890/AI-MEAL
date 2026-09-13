"""Database Integrity and Validation Checker for Food & Recipe Database.

Usage:
    python -m app.seed.validate_db
"""
import sys
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import SessionLocal
from app.models.ingredient import Ingredient
from app.models.recipe import Recipe, RecipeIngredient


def validate_database() -> bool:
    db: Session = SessionLocal()
    is_valid = True
    errors: list[str] = []

    try:
        # 1. Total counts
        ing_count = db.query(Ingredient).count()
        recipe_count = db.query(Recipe).count()
        ri_count = db.query(RecipeIngredient).count()

        print("=" * 60)
        print("FOOD & RECIPE DATABASE VALIDATION REPORT")
        print("=" * 60)
        print(f"Ingredients count:                  {ing_count}")
        print(f"Recipes count:                      {recipe_count}")
        print(f"Recipe-Ingredient associations:     {ri_count}")
        print("-" * 60)

        # Minimum thresholds
        if ing_count < 50:
            errors.append(f"FAILED: Ingredient count ({ing_count}) is less than required 50.")
            is_valid = False
        else:
            print("[OK] PASS: Ingredient count >= 50")

        if recipe_count < 100:
            errors.append(f"FAILED: Recipe count ({recipe_count}) is less than required 100.")
            is_valid = False
        else:
            print("[OK] PASS: Recipe count >= 100")

        if ri_count == 0:
            errors.append("FAILED: No Recipe-Ingredient associations found.")
            is_valid = False
        else:
            print("[OK] PASS: Recipe-Ingredient associations exist")

        # 2. Duplicate ingredient names
        duplicate_ings = (
            db.query(Ingredient.name, func.count(Ingredient.id))
            .group_by(Ingredient.name)
            .having(func.count(Ingredient.id) > 1)
            .all()
        )
        if duplicate_ings:
            errors.append(f"FAILED: Found duplicate ingredients: {duplicate_ings}")
            is_valid = False
        else:
            print("[OK] PASS: No duplicate ingredient names")

        # 3. Duplicate recipe names
        duplicate_recipes = (
            db.query(Recipe.name, func.count(Recipe.id))
            .group_by(Recipe.name)
            .having(func.count(Recipe.id) > 1)
            .all()
        )
        if duplicate_recipes:
            errors.append(f"FAILED: Found duplicate recipes: {duplicate_recipes}")
            is_valid = False
        else:
            print("[OK] PASS: No duplicate recipe names")

        # 4. Ingredient data quality (no negative prices, valid nutrition)
        invalid_nutrition_ings = (
            db.query(Ingredient)
            .filter(
                (Ingredient.calories < 0)
                | (Ingredient.protein < 0)
                | (Ingredient.carbohydrates < 0)
                | (Ingredient.fat < 0)
                | (Ingredient.fiber < 0)
                | (Ingredient.price_per_unit < 0)
                | (Ingredient.calories.is_(None))
                | (Ingredient.price_per_unit.is_(None))
            )
            .all()
        )
        if invalid_nutrition_ings:
            names = [i.name for i in invalid_nutrition_ings]
            errors.append(f"FAILED: Ingredients with invalid/negative nutrition or price: {names}")
            is_valid = False
        else:
            print("[OK] PASS: All ingredients have positive/non-negative nutrition and prices")

        # 5. Every recipe must have at least one ingredient
        recipes_without_ings = []
        recipes = db.query(Recipe).all()
        for r in recipes:
            if len(r.recipe_ingredients) == 0:
                recipes_without_ings.append(r.name)

        if recipes_without_ings:
            errors.append(f"FAILED: Recipes with 0 ingredients: {recipes_without_ings}")
            is_valid = False
        else:
            print("[OK] PASS: Every recipe has at least one ingredient")

        # 6. RecipeIngredient data quality (positive quantity, valid FK)
        all_ing_ids = {i.id for i in db.query(Ingredient.id).all()}
        invalid_ri = []
        for ri in db.query(RecipeIngredient).all():
            if ri.quantity <= 0:
                invalid_ri.append(f"ID {ri.id}: quantity <= 0 ({ri.quantity})")
            if ri.ingredient_id not in all_ing_ids:
                invalid_ri.append(f"ID {ri.id}: invalid ingredient_id {ri.ingredient_id}")

        if invalid_ri:
            errors.append(f"FAILED: Invalid recipe_ingredients found: {invalid_ri[:10]}")
            is_valid = False
        else:
            print("[OK] PASS: All recipe quantities are positive and link to valid ingredients")

        # 7. Summary
        print("=" * 60)
        if is_valid:
            print("ALL VALIDATION CHECKS PASSED SUCCESSFULLY! [OK]")

            print("=" * 60)
            return True
        else:
            print("VALIDATION FAILED WITH ERRORS:")
            for err in errors:
                print(f"  - {err}")
            print("=" * 60)
            return False

    finally:
        db.close()


if __name__ == "__main__":
    success = validate_database()
    sys.exit(0 if success else 1)

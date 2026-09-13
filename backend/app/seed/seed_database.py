"""Idempotent Database Seeding Pipeline for Food and Recipes.

Usage:
    python -m app.seed.seed_database
"""
import sys
from decimal import Decimal
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.ingredient import Ingredient
from app.models.recipe import Recipe, RecipeIngredient
from app.seed.ingredients import INGREDIENTS_DATA
from app.seed.recipes import RECIPES_DATA


def seed_ingredients(db: Session) -> dict[str, Ingredient]:
    """Seed or update ingredients idempotently. Returns a dict mapping name -> Ingredient."""
    ingredient_map: dict[str, Ingredient] = {}
    created_count = 0
    updated_count = 0

    for item in INGREDIENTS_DATA:
        name = item["name"].strip()
        existing = db.query(Ingredient).filter(Ingredient.name == name).first()
        if existing:
            # Update fields to ensure latest values
            existing.category = item["category"]
            existing.unit = item["unit"]
            existing.price_per_unit = Decimal(str(item["price_per_unit"]))
            existing.calories = item["calories"]
            existing.protein = item["protein"]
            existing.carbohydrates = item["carbohydrates"]
            existing.fat = item["fat"]
            existing.fiber = item.get("fiber", 0.0)
            ingredient_map[name] = existing
            updated_count += 1
        else:
            new_ing = Ingredient(
                name=name,
                category=item["category"],
                unit=item["unit"],
                price_per_unit=Decimal(str(item["price_per_unit"])),
                calories=item["calories"],
                protein=item["protein"],
                carbohydrates=item["carbohydrates"],
                fat=item["fat"],
                fiber=item.get("fiber", 0.0),
            )
            db.add(new_ing)
            db.flush()
            ingredient_map[name] = new_ing
            created_count += 1

    db.commit()
    print(f"Ingredients: {created_count} inserted, {updated_count} updated (Total: {len(ingredient_map)})")
    return ingredient_map


def seed_recipes(db: Session, ingredient_map: dict[str, Ingredient]) -> None:
    """Seed or update recipes and recipe_ingredients idempotently."""
    created_recipes = 0
    updated_recipes = 0
    total_associations = 0

    for r_data in RECIPES_DATA:
        name = r_data["name"].strip()

        # Compute accurate estimated cost based on ingredient prices
        # formula: sum( (quantity / 100.0) * ingredient.price_per_unit )
        computed_cost = Decimal("0.00")
        for ing_entry in r_data["ingredients"]:
            ing_obj = ingredient_map.get(ing_entry["name"])
            if ing_obj and ing_obj.price_per_unit is not None:
                qty_factor = Decimal(str(ing_entry["quantity"])) / Decimal("100.0")
                computed_cost += qty_factor * Decimal(str(ing_obj.price_per_unit))

        computed_cost = round(computed_cost, 2)

        existing_recipe = db.query(Recipe).filter(Recipe.name == name).first()
        if existing_recipe:
            existing_recipe.description = r_data.get("description")
            existing_recipe.meal_type = r_data.get("meal_type")
            existing_recipe.cuisine = r_data.get("cuisine")
            existing_recipe.servings = r_data.get("servings", 2)
            existing_recipe.preparation_time = r_data.get("preparation_time", 15)
            existing_recipe.cooking_time = r_data.get("cooking_time", 20)
            existing_recipe.dietary_tags = r_data.get("dietary_tags", [])
            existing_recipe.instructions = r_data.get("instructions")
            existing_recipe.estimated_cost = computed_cost
            recipe = existing_recipe
            updated_recipes += 1

            # Clear existing recipe_ingredients to ensure a fresh, clean association set
            db.query(RecipeIngredient).filter(RecipeIngredient.recipe_id == recipe.id).delete()
            db.flush()
        else:
            recipe = Recipe(
                name=name,
                description=r_data.get("description"),
                meal_type=r_data.get("meal_type"),
                cuisine=r_data.get("cuisine"),
                servings=r_data.get("servings", 2),
                preparation_time=r_data.get("preparation_time", 15),
                cooking_time=r_data.get("cooking_time", 20),
                dietary_tags=r_data.get("dietary_tags", []),
                instructions=r_data.get("instructions"),
                estimated_cost=computed_cost,
            )
            db.add(recipe)
            db.flush()
            created_recipes += 1

        # Add recipe-ingredient associations
        for ing_entry in r_data["ingredients"]:
            ing_obj = ingredient_map.get(ing_entry["name"])
            if not ing_obj:
                print(f"Warning: Ingredient '{ing_entry['name']}' not found in database for recipe '{name}'!")
                continue

            ri = RecipeIngredient(
                recipe_id=recipe.id,
                ingredient_id=ing_obj.id,
                quantity=float(ing_entry["quantity"]),
                unit=ing_entry.get("unit", "g"),
            )
            db.add(ri)
            total_associations += 1

    db.commit()
    print(f"Recipes: {created_recipes} inserted, {updated_recipes} updated (Total: {created_recipes + updated_recipes})")
    print(f"Recipe-Ingredient associations created: {total_associations}")


def main():
    """Run seeding pipeline."""
    print("=" * 60)
    print("Starting Food & Recipe Database Seeding Pipeline")
    print("=" * 60)

    db: Session = SessionLocal()
    try:
        print("[1/2] Seeding Ingredients...")
        ingredient_map = seed_ingredients(db)

        print("[2/2] Seeding Recipes & Recipe Ingredients...")
        seed_recipes(db, ingredient_map)

        print("\nSeeding completed successfully!")
    except Exception as e:
        db.rollback()
        print(f"\nERROR during seeding: {e}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

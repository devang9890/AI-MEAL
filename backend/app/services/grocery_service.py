"""Grocery List Consolidation Service.

Aggregates recipe ingredients across all meals in a generated plan,
merges duplicate ingredients, and estimates total weekly shopping cost.

DISCLAIMER: Cost estimates are project-level approximations for
demonstration purposes.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List

from sqlalchemy.orm import Session, joinedload

from app.models.recipe import Recipe, RecipeIngredient
from app.models.ingredient import Ingredient


def build_grocery_list(meals: List[Dict[str, Any]], db: Session) -> Dict[str, Any]:
    """
    Build a consolidated grocery list from a list of meal dicts.

    Each meal dict must have: recipe_id, servings.
    Returns dict with: items (sorted by category), total_cost, item_count.
    """
    recipe_ids = list({m.get("recipe_id") for m in meals if m.get("recipe_id")})
    recipes_by_id: Dict[int, Recipe] = {}
    if recipe_ids:
        loaded_recipes = (
            db.query(Recipe)
            .options(
                joinedload(Recipe.recipe_ingredients).joinedload(RecipeIngredient.ingredient)
            )
            .filter(Recipe.id.in_(recipe_ids))
            .all()
        )
        recipes_by_id = {r.id: r for r in loaded_recipes}

    # Aggregate: ingredient_id -> {name, category, unit, total_qty_g, price_per_100g}
    aggregated: Dict[int, Dict[str, Any]] = defaultdict(lambda: {
        "ingredient_id": None,
        "name": "",
        "category": "",
        "unit": "g",
        "total_quantity_g": 0.0,
        "price_per_100g": 0.0,
    })

    for meal in meals:
        recipe_id = meal.get("recipe_id")
        servings_factor = (meal.get("servings") or 2) / 2.0  # normalise to per-2-servings base

        recipe = recipes_by_id.get(recipe_id)
        if not recipe:
            continue

        for ri in recipe.recipe_ingredients:
            ing: Ingredient = ri.ingredient
            iid = ing.id
            qty_g = ri.quantity * servings_factor

            entry = aggregated[iid]
            entry["ingredient_id"] = iid
            entry["name"] = ing.name
            entry["category"] = ing.category or "General"
            entry["unit"] = ing.unit or "g"
            entry["total_quantity_g"] += qty_g
            entry["price_per_100g"] = float(ing.price_per_unit or 0.0)

    # Compute cost and build sorted list
    items: List[Dict[str, Any]] = []
    total_cost = 0.0

    for entry in aggregated.values():
        qty_g = entry["total_quantity_g"]
        price_per_100g = entry["price_per_100g"]
        item_cost = (qty_g / 100.0) * price_per_100g

        items.append({
            "ingredient_id": entry["ingredient_id"],
            "name": entry["name"],
            "category": entry["category"],
            "quantity_g": round(qty_g, 1),
            "display_quantity": _format_quantity(qty_g, entry["unit"]),
            "estimated_cost": round(item_cost, 2),
        })
        total_cost += item_cost

    # Sort by category then name
    items.sort(key=lambda x: (x["category"], x["name"]))

    # Group by category
    by_category: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for item in items:
        by_category[item["category"]].append(item)

    return {
        "items": items,
        "by_category": dict(by_category),
        "total_cost": round(total_cost, 2),
        "item_count": len(items),
    }


def _format_quantity(qty_g: float, unit: str) -> str:
    """Format quantity into a human-readable string."""
    unit_lower = (unit or "g").lower()
    if unit_lower in ("ml", "milliliter", "millilitre"):
        if qty_g >= 1000:
            return f"{qty_g/1000:.2f} L"
        return f"{qty_g:.0f} ml"
    elif unit_lower in ("piece", "pieces", "pcs", "no.", "number"):
        return f"{round(qty_g):.0f} pcs"
    else:
        # treat as grams
        if qty_g >= 1000:
            return f"{qty_g/1000:.2f} kg"
        return f"{qty_g:.0f} g"


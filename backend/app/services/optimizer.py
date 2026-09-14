"""Meal Plan Optimizer — ILP-based weekly meal planner.

Uses PuLP to solve an Integer Linear Program that:
  - Selects one recipe per (day, meal_type) slot over 7 days
  - Minimises total estimated weekly cost
  - Satisfies per-slot calorie / macro floors summed across household members
  - Respects household weekly budget ceiling
  - Excludes recipes that conflict with member dietary preferences or allergies
  - Falls back through a 3-tier constraint relaxation ladder if infeasible

DISCLAIMER: Nutritional and cost values are project-level estimates for
demonstration purposes and do not constitute medical or dietary advice.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session, joinedload

from app.models.household import Household
from app.models.member import Member
from app.models.nutrition import NutritionTarget
from app.models.recipe import Recipe, RecipeIngredient
from app.models.ingredient import Ingredient

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DAYS: List[str] = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MEAL_TYPES: List[str] = ["breakfast", "lunch", "dinner"]

PREFERENCE_ALLOWED_TAGS: Dict[str, List[str]] = {
    "vegetarian": ["vegetarian", "vegan"],
    "vegan": ["vegan"],
    "eggitarian": ["vegetarian", "vegan", "eggitarian", "eggetarian"],
    "non_vegetarian": ["vegetarian", "vegan", "eggitarian", "eggetarian", "non_vegetarian"],
}

# Target fraction of daily nutrition provided by the 3 main dishes (breakfast, lunch, dinner)
# Note: In Indian family diets, rotis/chapatis, rice, yogurt/curd, salads, and snacks provide the remainder.
MAIN_MEAL_SHARE = 0.50

RELAXATION_TIERS: List[Tuple[float, float, Optional[str]]] = [
    (1.00, 1.00, None),
    (0.85, 0.85, "variety"),
    (0.70, 0.70, "micronutrients"),
    (0.55, 0.55, "macros"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_recipe_data(db: Session) -> Dict[int, Dict[str, Any]]:
    """Pre-compute per-recipe aggregated nutrition and cost."""
    recipes = (
        db.query(Recipe)
        .options(
            joinedload(Recipe.recipe_ingredients).joinedload(RecipeIngredient.ingredient)
        )
        .all()
    )
    recipe_data: Dict[int, Dict[str, Any]] = {}

    for recipe in recipes:
        total_calories = 0.0
        total_protein = 0.0
        total_carbs = 0.0
        total_fat = 0.0
        total_fiber = 0.0
        total_cost = float(recipe.estimated_cost or 0.0)

        for ri in recipe.recipe_ingredients:
            ing: Ingredient = ri.ingredient
            factor = ri.quantity / 100.0
            total_calories += (ing.calories or 0.0) * factor
            total_protein += (ing.protein or 0.0) * factor
            total_carbs += (ing.carbohydrates or 0.0) * factor
            total_fat += (ing.fat or 0.0) * factor
            total_fiber += (ing.fiber or 0.0) * factor

        recipe_data[recipe.id] = {
            "id": recipe.id,
            "name": recipe.name,
            "meal_type": (recipe.meal_type or "").lower(),
            "dietary_tags": [t.lower() for t in (recipe.dietary_tags or [])],
            "estimated_cost": total_cost,
            "calories": round(total_calories, 1),
            "protein": round(total_protein, 1),
            "carbs": round(total_carbs, 1),
            "fat": round(total_fat, 1),
            "fiber": round(total_fiber, 1),
            "servings": recipe.servings or 2,
        }

    return recipe_data


def _household_daily_targets(members: List[Member], db: Session) -> Dict[str, float]:
    """Sum member daily targets and scale by MAIN_MEAL_SHARE."""
    totals = {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0, "fiber": 0.0}
    for member in members:
        target: Optional[NutritionTarget] = (
            db.query(NutritionTarget)
            .filter(NutritionTarget.member_id == member.id)
            .order_by(NutritionTarget.updated_at.desc())
            .first()
        )
        if target:
            totals["calories"] += target.daily_calories
            totals["protein"] += target.daily_protein_g
            totals["carbs"] += target.daily_carbs_g
            totals["fat"] += target.daily_fat_g
            totals["fiber"] += target.daily_fiber_g
    return {k: round(v * MAIN_MEAL_SHARE, 1) for k, v in totals.items()}


def _eligible_recipes(
    recipe_data: Dict[int, Dict[str, Any]],
    members: List[Member],
    meal_type: str,
) -> List[Dict[str, Any]]:
    """Filter recipes by meal_type, dietary preference, and allergens."""
    allergens: List[str] = []
    for m in members:
        if m.allergies:
            for a in m.allergies.split(","):
                clean = a.strip().lower()
                if clean:
                    allergens.append(clean)
    allergens = list(set(allergens))

    # Most restrictive dietary preference wins
    pref_order = ["vegan", "vegetarian", "eggitarian", "non_vegetarian"]
    effective_pref = "non_vegetarian"
    for pref in pref_order:
        if any(m.dietary_preference == pref for m in members):
            effective_pref = pref
            break
    allowed_tags = PREFERENCE_ALLOWED_TAGS.get(effective_pref, [])

    eligible = []
    for recipe in recipe_data.values():
        r_type = recipe["meal_type"]
        if r_type and r_type != meal_type.lower():
            continue
        tags = recipe["dietary_tags"]
        if tags and allowed_tags:
            if not any(t in allowed_tags for t in tags):
                continue
        if allergens:
            name_lower = recipe["name"].lower()
            tag_str = " ".join(tags)
            if any(a in name_lower or a in tag_str for a in allergens):
                continue
        eligible.append(recipe)
    return eligible


def _solve_ilp(
    eligible_by_slot: Dict[str, List[Dict[str, Any]]],
    daily_targets: Dict[str, float],
    weekly_budget: Optional[float],
    calorie_factor: float,
    macro_factor: float,
    member_count: int = 2,
) -> Optional[Dict[Tuple[str, str], Dict[str, Any]]]:
    """Run ILP. Returns {(day, meal_type): recipe} or None if infeasible."""
    import pulp

    prob = pulp.LpProblem("MealPlan", pulp.LpMinimize)

    x: Dict[Tuple[str, str, int], Any] = {}
    for day in DAYS:
        for mtype in MEAL_TYPES:
            for recipe in eligible_by_slot.get(mtype, []):
                key = (day, mtype, recipe["id"])
                x[key] = pulp.LpVariable(f"x_{day}_{mtype}_{recipe['id']}", cat="Binary")

    if not x:
        return None

    # Helper for scaling by member count vs recipe servings
    def scale(r: Dict[str, Any]) -> float:
        return member_count / max(1, r.get("servings", 2))

    # Objective: min cost
    prob += pulp.lpSum(
        x[(day, mtype, r["id"])] * (r["estimated_cost"] * scale(r))
        for day in DAYS
        for mtype in MEAL_TYPES
        for r in eligible_by_slot.get(mtype, [])
        if (day, mtype, r["id"]) in x
    )

    # C1: exactly one recipe per slot
    for day in DAYS:
        for mtype in MEAL_TYPES:
            slot_vars = [
                x[(day, mtype, r["id"])]
                for r in eligible_by_slot.get(mtype, [])
                if (day, mtype, r["id"]) in x
            ]
            if slot_vars:
                prob += pulp.lpSum(slot_vars) == 1, f"one_{day}_{mtype}"

    # C2: daily nutrition floors (summed across breakfast, lunch, dinner for each day)
    for day in DAYS:
        for nutrient in ["calories", "protein", "carbs", "fat"]:
            floor = daily_targets.get(nutrient, 0.0)
            if floor <= 0:
                continue
            f = calorie_factor if nutrient == "calories" else macro_factor
            expr = pulp.lpSum(
                x[(day, mtype, r["id"])] * (r[nutrient] * scale(r))
                for mtype in MEAL_TYPES
                for r in eligible_by_slot.get(mtype, [])
                if (day, mtype, r["id"]) in x
            )
            prob += expr >= floor * f, f"{nutrient}_floor_{day}"

    # C3: budget ceiling
    if weekly_budget and weekly_budget > 0:
        cost_expr = pulp.lpSum(
            x[(day, mtype, r["id"])] * (r["estimated_cost"] * scale(r))
            for day in DAYS
            for mtype in MEAL_TYPES
            for r in eligible_by_slot.get(mtype, [])
            if (day, mtype, r["id"]) in x
        )
        prob += cost_expr <= weekly_budget, "budget_ceiling"

    # C4: Strict Variety Constraints
    # C4.1: Maximum 1 appearance per week for Breakfast and Lunch (guaranteeing 7 unique breakfasts and 7 unique lunches); max 2 for Dinner
    for mtype in MEAL_TYPES:
        max_limit = 1 if mtype in ["Breakfast", "Lunch"] else 2
        for r in eligible_by_slot.get(mtype, []):
            rid = r["id"]
            uses = [x[(day, mtype, rid)] for day in DAYS if (day, mtype, rid) in x]
            if uses:
                prob += pulp.lpSum(uses) <= max_limit, f"var_limit_{mtype}_{rid}"

    # C4.2: No consecutive-day repeats (never schedule the same meal two days in a row)
    for mtype in MEAL_TYPES:
        for i in range(len(DAYS) - 1):
            d1, d2 = DAYS[i], DAYS[i + 1]
            for r in eligible_by_slot.get(mtype, []):
                rid = r["id"]
                if (d1, mtype, rid) in x and (d2, mtype, rid) in x:
                    prob += (
                        x[(d1, mtype, rid)] + x[(d2, mtype, rid)] <= 1,
                        f"no_repeat_{d1}_{d2}_{mtype}_{rid}",
                    )

    solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=6, gapRel=0.08)
    prob.solve(solver)

    selected: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for (day, mtype, rid), var in x.items():
        val = pulp.value(var)
        if val is not None and val > 0.5:
            for r in eligible_by_slot.get(mtype, []):
                if r["id"] == rid:
                    selected[(day, mtype)] = r
                    break

    # Feasible only if all 21 meal slots (7 days x 3 meals) are scheduled
    if len(selected) == len(DAYS) * len(MEAL_TYPES):
        return selected

    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_meal_plan(household: Household, db: Session) -> Dict[str, Any]:
    """
    Generate a 7-day, 3-meal-per-day plan for a household using ILP.
    Returns structured dict. Raises ValueError / RuntimeError on failure.
    """
    members: List[Member] = household.members
    if not members:
        raise ValueError("Household has no members. Add at least one member with a nutrition target.")

    recipe_data = _build_recipe_data(db)
    daily_targets = _household_daily_targets(members, db)
    weekly_budget = float(household.weekly_budget) if household.weekly_budget else None

    eligible_by_slot: Dict[str, List[Dict[str, Any]]] = {}
    for mtype in MEAL_TYPES:
        eligible_by_slot[mtype] = _eligible_recipes(recipe_data, members, mtype)
        logger.info(f"Eligible for {mtype}: {len(eligible_by_slot[mtype])} recipes")

    member_count = len(members)
    relaxations_applied: List[str] = []
    selected = None

    for calorie_factor, macro_factor, tier_label in RELAXATION_TIERS:
        selected = _solve_ilp(
            eligible_by_slot, daily_targets, weekly_budget, calorie_factor, macro_factor, member_count
        )
        if selected is not None:
            if tier_label:
                relaxations_applied.append(tier_label)
            break

    if selected is None:
        # Last resort: no budget, 40% floors
        selected = _solve_ilp(eligible_by_slot, daily_targets, None, 0.4, 0.4, member_count)
        if selected:
            relaxations_applied.append("budget")

    if selected is None:
        raise RuntimeError(
            "Could not generate a feasible meal plan even after full relaxation. "
            "Add more recipes or broaden dietary preferences."
        )

    meals_out: List[Dict[str, Any]] = []
    total_cost = 0.0
    nutrition_sum = {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0, "fiber": 0.0}

    for day in DAYS:
        for mtype in MEAL_TYPES:
            recipe = selected.get((day, mtype))
            if not recipe:
                continue
            scale = member_count / max(1, recipe["servings"])
            scaled_cost = round(recipe["estimated_cost"] * scale, 2)
            meals_out.append({
                "day": day,
                "meal_type": mtype,
                "recipe_id": recipe["id"],
                "recipe_name": recipe["name"],
                "servings": member_count,
                "cost": scaled_cost,
                "calories": round(recipe["calories"] * scale, 1),
                "protein": round(recipe["protein"] * scale, 1),
                "carbs": round(recipe["carbs"] * scale, 1),
                "fat": round(recipe["fat"] * scale, 1),
                "fiber": round(recipe["fiber"] * scale, 1),
                "dietary_tags": recipe["dietary_tags"],
            })
            total_cost += scaled_cost
            nutrition_sum["calories"] += recipe["calories"] * scale
            nutrition_sum["protein"] += recipe["protein"] * scale
            nutrition_sum["carbs"] += recipe["carbs"] * scale
            nutrition_sum["fat"] += recipe["fat"] * scale
            nutrition_sum["fiber"] += recipe["fiber"] * scale

    return {
        "meals": meals_out,
        "total_cost": round(total_cost, 2),
        "weekly_budget": weekly_budget,
        "budget_utilisation_pct": (
            round(total_cost / weekly_budget * 100, 1) if weekly_budget else None
        ),
        "relaxations_applied": relaxations_applied,
        "daily_targets": daily_targets,
        "weekly_nutrition_summary": {k: round(v, 1) for k, v in nutrition_sum.items()},
        "member_count": len(members),
    }


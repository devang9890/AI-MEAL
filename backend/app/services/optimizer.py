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
from app.services.health_catalog import ALLERGY_INGREDIENT_TERMS, CLINICIAN_REVIEW_CONDITIONS, CONDITION_RULES
from app.services.compatibility_service import assess_recipe, member_reason

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DAYS: List[str] = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MEAL_TYPES: List[str] = ["breakfast", "lunch", "dinner", "snack"]

PREFERENCE_ALLOWED_TAGS: Dict[str, List[str]] = {
    "vegetarian": ["vegetarian", "vegan"],
    "vegan": ["vegan"],
    "eggitarian": ["vegetarian", "vegan", "eggitarian", "eggetarian"],
    "non_vegetarian": ["vegetarian", "vegan", "eggitarian", "eggetarian", "non_vegetarian"],
}

# Target fraction of daily nutrition provided by the 3 main dishes (breakfast, lunch, dinner)
# Note: In Indian family diets, rotis/chapatis, rice, yogurt/curd, salads, and snacks provide the remainder.
MAIN_MEAL_SHARE = 0.65

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
            "ingredient_names": [ri.ingredient.name.lower() for ri in recipe.recipe_ingredients],
            "added_salt_g": sum(ri.quantity for ri in recipe.recipe_ingredients if "salt" in ri.ingredient.name.lower()),
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
    diseases: List[str] = []
    for m in members:
        if m.allergies:
            for a in m.allergies.split(","):
                clean = a.strip().lower()
                if clean:
                    allergens.append(clean)
        if m.diseases:
            diseases.extend(d.strip() for d in m.diseases.split(",") if d.strip())
    allergens = list(set(allergens))

    # Most restrictive dietary preference wins
    pref_order = ["vegan", "vegetarian", "eggitarian", "non_vegetarian"]
    effective_pref = "non_vegetarian"
    for pref in pref_order:
        if any(m.dietary_preference == pref for m in members):
            effective_pref = pref
            break
    allowed_tags = PREFERENCE_ALLOWED_TAGS.get(effective_pref, [])

    avoid_terms: List[str] = []
    max_salt_g: Optional[float] = None
    for allergy in allergens:
        known_terms = next(
            (terms for label, terms in ALLERGY_INGREDIENT_TERMS.items() if label.lower() == allergy),
            [allergy],
        )
        avoid_terms.extend(known_terms)
    for disease in set(diseases):
        rule = CONDITION_RULES.get(disease)
        if not rule:
            continue
        avoid_terms.extend(rule.get("avoid_terms", []))
        if rule.get("max_salt_g") is not None:
            max_salt_g = min(max_salt_g, rule["max_salt_g"]) if max_salt_g is not None else rule["max_salt_g"]

    eligible = []
    for recipe in recipe_data.values():
        r_type = recipe["meal_type"]
        if r_type and r_type != meal_type.lower():
            continue
        tags = recipe["dietary_tags"]
        if tags and allowed_tags:
            if not any(t in allowed_tags for t in tags):
                continue
        ingredient_text = " ".join(recipe.get("ingredient_names", []))
        if any(term.lower() in ingredient_text for term in avoid_terms if term):
            continue
        if max_salt_g is not None and recipe.get("added_salt_g", 0.0) > max_salt_g:
            continue
        eligible.append(recipe)
    return eligible


def is_recipe_eligible_for_household(recipe_id: int, household: Household, meal_type: str, db: Session) -> bool:
    """Use the same safety and preference filter for manual swaps as planning."""
    eligible = _eligible_recipes(_build_recipe_data(db), household.members, meal_type)
    return any(recipe["id"] == recipe_id for recipe in eligible)


def personalized_options_for_recipe(
    base_recipe: Dict[str, Any], members: List[Member], recipe_data: Dict[int, Dict[str, Any]], db: Session
) -> List[Dict[str, Any]]:
    """Choose a safe per-member option while retaining a coordinated base meal.

    Allergy/condition blockers are absolute. Nutrition is used only to rank
    already-safe alternatives, never to override a blocker.
    """
    options: List[Dict[str, Any]] = []
    for member in members:
        base_assessment = assess_recipe(member, base_recipe)
        chosen = base_recipe
        assessment = base_assessment
        if not assessment["safe"]:
            candidates = [
                recipe for recipe in recipe_data.values()
                if recipe.get("meal_type") == base_recipe.get("meal_type")
                and assess_recipe(member, recipe)["safe"]
            ]
            if not candidates:
                options.append({
                    "member_id": member.id, "member_name": member.name,
                    "recipe_id": None, "recipe_name": None, "safe": False,
                    "reason": "No verified safe alternative is available for this meal slot.",
                    "blockers": assessment["blockers"], "unresolved": True,
                })
                continue
            target = db.query(NutritionTarget).filter(NutritionTarget.member_id == member.id).first()
            # Prefer protein/fibre-dense alternatives without pretending to meet a full-day target.
            protein_goal = float(target.daily_protein_g) / 4 if target else 15.0
            chosen = min(candidates, key=lambda r: (
                abs(r["protein"] / max(1, r["servings"]) - protein_goal) - r["fiber"] / max(1, r["servings"]) * .15,
                r["estimated_cost"],
            ))
            assessment = assess_recipe(member, chosen)
        servings = max(1, chosen.get("servings", 1))
        options.append({
            "member_id": member.id, "member_name": member.name,
            "recipe_id": chosen["id"], "recipe_name": chosen["name"], "safe": assessment["safe"],
            "personalized": chosen["id"] != base_recipe["id"],
            "reason": member_reason(member, base_recipe, chosen, base_assessment),
            "blockers": base_assessment["blockers"],
            "ingredients": chosen.get("ingredient_names", []),
            "calories": round(chosen["calories"] / servings, 1),
            "protein": round(chosen["protein"] / servings, 1),
            "carbs": round(chosen["carbs"] / servings, 1),
            "fat": round(chosen["fat"] / servings, 1),
            "fiber": round(chosen["fiber"] / servings, 1),
            "cost": round(chosen["estimated_cost"] / servings, 2),
        })
    return options


def personalized_options_for_recipe_id(recipe_id: int, members: List[Member], db: Session) -> List[Dict[str, Any]]:
    """Public rehydration helper for persisted plan cards."""
    recipes = _build_recipe_data(db)
    recipe = recipes.get(recipe_id)
    return personalized_options_for_recipe(recipe, members, recipes, db) if recipe else []


def nutrition_dashboard(meals: List[Dict[str, Any]], members: List[Member], db: Session) -> List[Dict[str, Any]]:
    """Aggregate the selected individual options across one representative day."""
    dashboard: List[Dict[str, Any]] = []
    nutrients = ("calories", "protein", "carbs", "fat", "fiber")
    for member in members:
        target = db.query(NutritionTarget).filter(NutritionTarget.member_id == member.id).first()
        planned = {key: 0.0 for key in nutrients}
        unresolved: List[str] = []
        # Monday is representative; every day has the same four meal categories.
        for meal in meals:
            if meal["day"] != DAYS[0]:
                continue
            option = next((o for o in meal.get("personalized_options", []) if o["member_id"] == member.id), None)
            if not option or option.get("unresolved"):
                unresolved.append(f"{meal['meal_type'].capitalize()}: no verified safe option")
                continue
            for key in nutrients:
                planned[key] += float(option.get(key) or 0)
        targets = {
            "calories": float(target.daily_calories) if target else 0,
            "protein": float(target.daily_protein_g) if target else 0,
            "carbs": float(target.daily_carbs_g) if target else 0,
            "fat": float(target.daily_fat_g) if target else 0,
            "fiber": float(target.daily_fiber_g) if target else 0,
        }
        dashboard.append({
            "member_id": member.id, "member_name": member.name,
            "targets": {k: round(v, 1) for k, v in targets.items()},
            "planned": {k: round(v, 1) for k, v in planned.items()},
            "gaps": {k: round(max(0, targets[k] - planned[k]), 1) for k in nutrients},
            "unresolved": unresolved,
        })
    return dashboard


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
        for nutrient in ["calories", "protein", "carbs", "fat", "fiber"]:
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
        max_limit = 1 if mtype in ["breakfast", "lunch"] else 2
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
    selected_conditions = {
        disease.strip() for member in members if member.diseases
        for disease in member.diseases.split(",") if disease.strip()
    }
    safety_notes: List[str] = []
    for condition in sorted(selected_conditions):
        rule = CONDITION_RULES.get(condition)
        if rule and rule.get("carbs_factor"):
            daily_targets["carbs"] = round(daily_targets["carbs"] * rule["carbs_factor"], 1)
        if rule and rule.get("fat_factor"):
            daily_targets["fat"] = round(daily_targets["fat"] * rule["fat_factor"], 1)
        if rule and rule.get("note"):
            safety_notes.append(f"{condition}: {rule['note']}")
        if condition in CLINICIAN_REVIEW_CONDITIONS:
            safety_notes.append(
                f"{condition}: this planner is not a clinical diet; confirm targets, medicines, and portions with the treating clinician or dietitian."
            )
    weekly_budget = float(household.weekly_budget) if household.weekly_budget else None

    eligible_by_slot: Dict[str, List[Dict[str, Any]]] = {}
    for mtype in MEAL_TYPES:
        # Build an economical household base first. Each member is then
        # deterministically assigned that base or a verified safe alternative.
        # This avoids incorrectly excluding a safe shared meal for everyone
        # because one person needs an individual substitute.
        eligible_by_slot[mtype] = _eligible_recipes(recipe_data, [], mtype)
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
                "personalized_options": personalized_options_for_recipe(recipe, members, recipe_data, db),
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
        "safety_notes": safety_notes,
        "member_nutrition_dashboard": nutrition_dashboard(meals_out, members, db),
    }


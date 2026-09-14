"""Rule-based Meal Explainability Service.

Generates plain-language explanations for why a specific recipe was selected
in a given meal slot. All logic is deterministic / template-based (no LLM),
ensuring reproducible, auditable explanations grounded in real optimizer data.

DISCLAIMER: Explanations are algorithmic approximations for demonstration
purposes and do not represent clinical dietary recommendations.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


def explain_meal(
    meal: Dict[str, Any],
    per_slot_targets: Dict[str, float],
    weekly_budget: Optional[float],
    total_weekly_cost: float,
    relaxations_applied: Optional[List[str]] = None,
) -> str:
    """
    Generate a plain-language explanation for a meal selection.

    Args:
        meal: meal dict with keys: recipe_name, calories, protein, carbs, fat,
              fiber, cost, dietary_tags, meal_type, day, servings
        per_slot_targets: per-slot calorie/macro targets for the household
        weekly_budget: household weekly budget in INR
        total_weekly_cost: actual total cost of the generated plan
        relaxations_applied: list of relaxation tier labels applied

    Returns:
        A 1-3 sentence explanation string.
    """
    recipe_name = meal.get("recipe_name", "This recipe")
    meal_type = (meal.get("meal_type") or "meal").capitalize()
    cost = meal.get("cost", 0.0)
    calories = meal.get("calories", 0.0)
    protein = meal.get("protein", 0.0)
    tags = meal.get("dietary_tags", [])

    target_cal = per_slot_targets.get("calories", 0.0)
    target_protein = per_slot_targets.get("protein", 0.0)

    sentences: List[str] = []

    # --- Cost rationale ---
    if weekly_budget and weekly_budget > 0:
        slot_budget = weekly_budget / (7 * 3)
        if cost <= slot_budget * 0.8:
            sentences.append(
                f"**{recipe_name}** was selected because it is budget-friendly "
                f"at ₹{cost:.0f} per serving — well within the allocated slot budget of ₹{slot_budget:.0f}."
            )
        elif cost <= slot_budget * 1.1:
            sentences.append(
                f"**{recipe_name}** fits comfortably within the per-meal budget "
                f"at ₹{cost:.0f} (slot target: ₹{slot_budget:.0f})."
            )
        else:
            sentences.append(
                f"**{recipe_name}** at ₹{cost:.0f} was chosen as the best nutritional "
                f"match for this {meal_type.lower()} slot despite being slightly over the per-meal budget."
            )
    else:
        sentences.append(f"**{recipe_name}** was selected for this {meal_type.lower()} slot.")

    # --- Nutrition rationale ---
    if target_cal > 0:
        cal_pct = (calories / target_cal * 100) if target_cal else 0
        if cal_pct >= 90:
            sentences.append(
                f"It provides {calories:.0f} kcal — meeting {cal_pct:.0f}% of the household's "
                f"per-slot calorie target."
            )
        elif cal_pct >= 70:
            sentences.append(
                f"It contributes {calories:.0f} kcal ({cal_pct:.0f}% of per-slot target), "
                f"complementing the day's other meals."
            )
        else:
            sentences.append(
                f"It provides {calories:.0f} kcal; lighter options were needed to stay within budget."
            )

    # --- Protein highlight ---
    if target_protein > 0 and protein >= target_protein * 0.8:
        sentences.append(
            f"With {protein:.1f}g of protein, it supports the household's daily protein requirement."
        )

    # --- Dietary tag highlight ---
    friendly_tags = [t for t in tags if t in ("vegetarian", "vegan", "high_protein", "low_fat", "gluten_free")]
    if friendly_tags:
        tag_str = ", ".join(t.replace("_", " ") for t in friendly_tags[:2])
        sentences.append(f"It is tagged as *{tag_str}*, matching household dietary preferences.")

    # --- Relaxation note ---
    if relaxations_applied:
        relaxation_str = " and ".join(relaxations_applied)
        sentences.append(
            f"⚠️ Note: To generate a feasible plan within your constraints, "
            f"{relaxation_str} targets were slightly relaxed."
        )

    return " ".join(sentences)


def explain_plan(plan_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate explanations for all meals in a plan result dict.

    plan_result is the dict returned by optimizer.generate_meal_plan().
    Returns the list of meals enriched with an 'explanation' key.
    """
    meals = plan_result.get("meals", [])
    per_slot_targets = plan_result.get("per_slot_targets", {})
    weekly_budget = plan_result.get("weekly_budget")
    total_cost = plan_result.get("total_cost", 0.0)
    relaxations = plan_result.get("relaxations_applied", [])

    enriched = []
    for meal in meals:
        explanation = explain_meal(
            meal=meal,
            per_slot_targets=per_slot_targets,
            weekly_budget=weekly_budget,
            total_weekly_cost=total_cost,
            relaxations_applied=relaxations if relaxations else None,
        )
        enriched.append({**meal, "explanation": explanation})

    return enriched


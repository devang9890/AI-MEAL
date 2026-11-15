"""Deterministic member-to-recipe safety and suitability checks.

The planner intentionally keeps health rules as catalog data.  This module is
the single enforcement point used for recommendations and swaps; it never
infers that a recipe with no ingredient record is safe.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List

from app.models.member import Member
from app.services.health_catalog import ALLERGY_INGREDIENT_TERMS, CONDITION_RULES


def _labels(value: str | None) -> List[str]:
    return [item.strip() for item in (value or "").split(",") if item.strip()]


def _terms_for(label: str) -> List[str]:
    """Resolve aliases from structured catalog data, with a safe label fallback."""
    lower = label.lower()
    for catalog_label, terms in ALLERGY_INGREDIENT_TERMS.items():
        if catalog_label.lower() == lower:
            return [term.lower() for term in terms]
    # Unknown selected allergen must not silently pass a named ingredient.
    return [lower.replace(" allergy", "").replace(" intolerance", "").strip()]


def assess_recipe(member: Member, recipe: Dict[str, Any]) -> Dict[str, Any]:
    """Return an auditable compatibility decision for one member and recipe."""
    ingredients = [str(name).lower() for name in recipe.get("ingredient_names", [])]
    ingredient_text = " | ".join(ingredients)
    blockers: List[str] = []
    cautions: List[str] = []
    matches: List[str] = []

    if not ingredients:
        blockers.append("Ingredient composition is incomplete, so safety cannot be verified")

    for allergy in _labels(member.allergies):
        found = [term for term in _terms_for(allergy) if term and term in ingredient_text]
        if found:
            blockers.append(f"Contains {allergy} ({', '.join(sorted(set(found)))})")
            matches.extend(found)

    tags = {str(tag).lower() for tag in recipe.get("dietary_tags", [])}
    preference = (member.dietary_preference or "").lower()
    allowed = {
        "vegan": {"vegan"},
        "vegetarian": {"vegetarian", "vegan"},
        "eggitarian": {"vegetarian", "vegan", "eggitarian", "eggetarian"},
        "non_vegetarian": {"vegetarian", "vegan", "eggitarian", "eggetarian", "non_vegetarian"},
    }.get(preference, set())
    if tags and allowed and not tags.intersection(allowed):
        blockers.append(f"Does not match {preference.replace('_', ' ')} preference")

    for condition in _labels(member.diseases):
        rule = CONDITION_RULES.get(condition, {})
        found = [term for term in rule.get("avoid_terms", []) if term.lower() in ingredient_text]
        if found:
            blockers.append(f"Conflicts with {condition} safeguard ({', '.join(found)})")
        if rule.get("max_salt_g") is not None and recipe.get("added_salt_g", 0) > rule["max_salt_g"]:
            blockers.append(f"Exceeds {condition} added-salt safeguard")
        if rule.get("note"):
            cautions.append(f"{condition}: {rule['note']}")

    return {
        "safe": not blockers,
        "blockers": blockers,
        "cautions": cautions,
        "matched_terms": sorted(set(matches)),
    }


def member_reason(member: Member, base_recipe: Dict[str, Any], selected_recipe: Dict[str, Any], assessment: Dict[str, Any]) -> str:
    if selected_recipe["id"] == base_recipe["id"]:
        return "Shared meal: its verified ingredients passed this member's recorded allergy, preference, and condition safeguards."
    reasons = assessment.get("blockers", [])
    health = "; ".join(reasons[:2]) or "individual nutrition and dietary requirements"
    return f"Personalized alternative selected because the shared meal is not suitable: {health}."

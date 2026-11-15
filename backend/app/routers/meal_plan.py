"""Meal Plan API Routes.

Endpoints for generating, retrieving, and managing weekly meal plans.
"""
from __future__ import annotations

import json
from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.household import Household
from app.models.meal_plan import MealPlan
from app.models.meal import Meal
from app.models.recipe import Recipe
from app.services.optimizer import generate_meal_plan, is_recipe_eligible_for_household, personalized_options_for_recipe_id, DAYS, MEAL_TYPES
from app.services.grocery_service import build_grocery_list
from app.services.explainability_service import explain_plan

router = APIRouter(prefix="/api", tags=["Meal Plans"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class MealOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    recipe_id: int
    recipe_name: str
    day: str
    meal_type: str
    servings: int
    cost: Optional[float] = None
    calories: Optional[float] = None
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fat: Optional[float] = None
    fiber: Optional[float] = None
    dietary_tags: Optional[List[str]] = None
    explanation: Optional[str] = None
    personalized_options: Optional[List[Dict[str, Any]]] = None


class MealPlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    household_id: int
    week_start_date: date
    total_cost: Optional[float] = None
    weekly_budget: Optional[float] = None
    budget_utilisation_pct: Optional[float] = None
    status: str
    relaxations_applied: Optional[List[str]] = None
    weekly_nutrition_summary: Optional[Dict[str, float]] = None
    member_count: Optional[int] = None
    safety_notes: Optional[List[str]] = None
    member_nutrition_dashboard: Optional[List[Dict[str, Any]]] = None
    meals: List[MealOut] = []


class SwapMealRequest(BaseModel):
    day: str
    meal_type: str
    new_recipe_id: int


class GroceryItemOut(BaseModel):
    ingredient_id: int
    name: str
    category: str
    quantity_g: float
    display_quantity: str
    estimated_cost: float


class GroceryListOut(BaseModel):
    plan_id: int
    items: List[GroceryItemOut]
    total_cost: float
    item_count: int


# ---------------------------------------------------------------------------
# Authorization helpers
# ---------------------------------------------------------------------------

def _get_owned_household(household_id: int, user: User, db: Session) -> Household:
    h = db.query(Household).filter(Household.id == household_id, Household.owner_id == user.id).first()
    if not h:
        raise HTTPException(status_code=404, detail=f"Household {household_id} not found.")
    return h


def _get_plan(plan_id: int, household_id: int, db: Session) -> MealPlan:
    plan = db.query(MealPlan).filter(MealPlan.id == plan_id, MealPlan.household_id == household_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail=f"Meal plan {plan_id} not found.")
    return plan


def _meal_to_out(m: Meal, metadata: Optional[Dict] = None, household: Optional[Household] = None, db: Optional[Session] = None) -> MealOut:
    """Convert a Meal ORM object to MealOut schema."""
    meta = metadata or {}
    options = meta.get("personalized_options")
    if options is None and household is not None and db is not None:
        options = personalized_options_for_recipe_id(m.recipe_id, household.members, db)
    return MealOut(
        id=m.id,
        recipe_id=m.recipe_id,
        recipe_name=m.recipe.name if m.recipe else "",
        day=m.day,
        meal_type=m.meal_type,
        servings=m.servings,
        cost=float(m.cost) if m.cost is not None else None,
        calories=meta.get("calories"),
        protein=meta.get("protein"),
        carbs=meta.get("carbs"),
        fat=meta.get("fat"),
        fiber=meta.get("fiber"),
        dietary_tags=meta.get("dietary_tags"),
        explanation=meta.get("explanation"),
        personalized_options=options,
    )


# ---------------------------------------------------------------------------
# Generate Plan
# ---------------------------------------------------------------------------

@router.post(
    "/households/{household_id}/generate-plan",
    response_model=MealPlanOut,
    status_code=status.HTTP_201_CREATED,
)
def generate_plan(
    household_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Run the ILP optimizer to generate a 7-day meal plan for the household.
    Stores the result in the database and returns the full plan with explanations.
    """
    household = _get_owned_household(household_id, current_user, db)

    try:
        plan_result = generate_meal_plan(household, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Add explanations
    plan_result["meals"] = explain_plan(plan_result)

    # Persist plan
    today = date.today()
    # Preserve prior plans as history; one household has one current plan.
    db.query(MealPlan).filter(
        MealPlan.household_id == household.id,
        MealPlan.status.in_(["active", "needs_regeneration"]),
    ).update({MealPlan.status: "superseded"}, synchronize_session=False)
    meal_plan = MealPlan(
        household_id=household.id,
        week_start_date=today,
        total_cost=plan_result["total_cost"],
        status="active",
    )
    db.add(meal_plan)
    db.flush()  # get meal_plan.id

    # Persist meals
    meal_objs: List[Meal] = []
    for m in plan_result["meals"]:
        meal_obj = Meal(
            meal_plan_id=meal_plan.id,
            recipe_id=m["recipe_id"],
            day=m["day"],
            meal_type=m["meal_type"],
            servings=m["servings"],
            cost=m["cost"],
        )
        db.add(meal_obj)
        meal_objs.append(meal_obj)

    db.commit()
    db.refresh(meal_plan)
    for mo in meal_objs:
        db.refresh(mo)

    # Build rich meal output with metadata
    meal_meta_by_key = {
        (m["day"], m["meal_type"]): m for m in plan_result["meals"]
    }

    meals_out = []
    for mo in meal_plan.meals:
        meta = meal_meta_by_key.get((mo.day, mo.meal_type), {})
        meals_out.append(_meal_to_out(mo, meta))

    return MealPlanOut(
        id=meal_plan.id,
        household_id=meal_plan.household_id,
        week_start_date=meal_plan.week_start_date,
        total_cost=float(meal_plan.total_cost) if meal_plan.total_cost else None,
        weekly_budget=plan_result.get("weekly_budget"),
        budget_utilisation_pct=plan_result.get("budget_utilisation_pct"),
        status=meal_plan.status,
        relaxations_applied=plan_result.get("relaxations_applied", []),
        weekly_nutrition_summary=plan_result.get("weekly_nutrition_summary"),
        member_count=plan_result.get("member_count"),
        safety_notes=plan_result.get("safety_notes", []),
        member_nutrition_dashboard=plan_result.get("member_nutrition_dashboard", []),
        meals=meals_out,
    )


# ---------------------------------------------------------------------------
# List Plans
# ---------------------------------------------------------------------------

@router.get("/households/{household_id}/plans", response_model=List[MealPlanOut])
def list_plans(
    household_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all meal plans for a household (newest first)."""
    _get_owned_household(household_id, current_user, db)
    plans = (
        db.query(MealPlan)
        .filter(MealPlan.household_id == household_id)
        .order_by(MealPlan.created_at.desc())
        .all()
    )
    return [
        MealPlanOut(
            id=p.id,
            household_id=p.household_id,
            week_start_date=p.week_start_date,
            total_cost=float(p.total_cost) if p.total_cost else None,
            status=p.status,
            meals=[_meal_to_out(m, household=_get_owned_household(household_id, current_user, db), db=db) for m in p.meals],
        )
        for p in plans
    ]


# ---------------------------------------------------------------------------
# Get Plan Detail
# ---------------------------------------------------------------------------

@router.get("/households/{household_id}/plans/{plan_id}", response_model=MealPlanOut)
def get_plan(
    household_id: int,
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get full detail for a specific meal plan."""
    _get_owned_household(household_id, current_user, db)
    plan = _get_plan(plan_id, household_id, db)
    return MealPlanOut(
        id=plan.id,
        household_id=plan.household_id,
        week_start_date=plan.week_start_date,
        total_cost=float(plan.total_cost) if plan.total_cost else None,
        status=plan.status,
        meals=[_meal_to_out(m, household=_get_owned_household(household_id, current_user, db), db=db) for m in plan.meals],
    )


# ---------------------------------------------------------------------------
# Grocery List
# ---------------------------------------------------------------------------

@router.get("/households/{household_id}/plans/{plan_id}/grocery-list", response_model=GroceryListOut)
def get_grocery_list(
    household_id: int,
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate consolidated grocery list for a meal plan."""
    _get_owned_household(household_id, current_user, db)
    plan = _get_plan(plan_id, household_id, db)

    meals_data = [
        {"recipe_id": m.recipe_id, "servings": m.servings}
        for m in plan.meals
    ]
    grocery = build_grocery_list(meals_data, db)

    return GroceryListOut(
        plan_id=plan_id,
        items=[GroceryItemOut(**item) for item in grocery["items"]],
        total_cost=grocery["total_cost"],
        item_count=grocery["item_count"],
    )


# ---------------------------------------------------------------------------
# Swap Meal
# ---------------------------------------------------------------------------

@router.post("/households/{household_id}/plans/{plan_id}/swap-meal", response_model=MealOut)
def swap_meal(
    household_id: int,
    plan_id: int,
    payload: SwapMealRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Swap one meal slot to a different recipe.
    Validates the new recipe exists and is not the same as the current one.
    """
    _get_owned_household(household_id, current_user, db)
    plan = _get_plan(plan_id, household_id, db)

    # Validate day and meal_type
    if payload.day not in DAYS:
        raise HTTPException(status_code=400, detail=f"Invalid day: {payload.day}.")
    if payload.meal_type not in MEAL_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid meal_type: {payload.meal_type}.")

    # Find existing meal slot
    meal_obj = (
        db.query(Meal)
        .filter(
            Meal.meal_plan_id == plan.id,
            Meal.day == payload.day,
            Meal.meal_type == payload.meal_type,
        )
        .first()
    )
    if not meal_obj:
        raise HTTPException(status_code=404, detail="Meal slot not found in this plan.")

    # Validate new recipe
    new_recipe: Optional[Recipe] = db.query(Recipe).filter(Recipe.id == payload.new_recipe_id).first()
    if not new_recipe:
        raise HTTPException(status_code=404, detail=f"Recipe {payload.new_recipe_id} not found.")

    if meal_obj.recipe_id == payload.new_recipe_id:
        raise HTTPException(status_code=400, detail="New recipe is the same as the current one.")
    if new_recipe.meal_type.lower() != payload.meal_type:
        raise HTTPException(status_code=400, detail="Choose a recipe from the same meal slot.")
    household = _get_owned_household(household_id, current_user, db)
    if not is_recipe_eligible_for_household(new_recipe.id, household, payload.meal_type, db):
        raise HTTPException(
            status_code=400,
            detail="This recipe conflicts with the household's dietary, allergy, or health-profile safeguards.",
        )

    # Update
    old_cost = float(meal_obj.cost or 0.0)
    new_cost = round(float(new_recipe.estimated_cost or 0.0) * meal_obj.servings / max(1, new_recipe.servings or 2), 2)

    meal_obj.recipe_id = new_recipe.id
    meal_obj.cost = new_cost

    # Update plan total cost
    if plan.total_cost is not None:
        plan.total_cost = float(plan.total_cost) - old_cost + new_cost

    db.commit()
    db.refresh(meal_obj)

    return _meal_to_out(meal_obj)


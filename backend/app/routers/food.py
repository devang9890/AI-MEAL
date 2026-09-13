"""Food and Recipe Read-Only API Endpoints."""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.models.ingredient import Ingredient
from app.models.recipe import Recipe, RecipeIngredient

router = APIRouter(prefix="/api", tags=["Food & Recipes"])


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------

class IngredientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str
    unit: str
    price_per_unit: Optional[float] = None
    calories: Optional[float] = None
    protein: Optional[float] = None
    carbohydrates: Optional[float] = None
    fat: Optional[float] = None
    fiber: Optional[float] = None


class IngredientListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    items: List[IngredientOut]


class RecipeIngredientDetail(BaseModel):
    id: int
    ingredient_id: int
    name: str
    category: str
    quantity: float
    unit: str
    price_contribution: float
    calories_contribution: float
    protein_contribution: float
    carbs_contribution: float
    fat_contribution: float
    fiber_contribution: float


class RecipeSummaryOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    meal_type: Optional[str] = None
    cuisine: Optional[str] = None
    servings: int
    preparation_time: Optional[int] = None
    cooking_time: Optional[int] = None
    dietary_tags: List[str] = []
    estimated_cost: Optional[float] = None
    instructions: Optional[str] = None
    ingredient_count: int


class RecipeListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    items: List[RecipeSummaryOut]


class NutritionSummary(BaseModel):
    calories: float
    protein: float
    carbohydrates: float
    fat: float
    fiber: float


class RecipeDetailOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    meal_type: Optional[str] = None
    cuisine: Optional[str] = None
    servings: int
    preparation_time: Optional[int] = None
    cooking_time: Optional[int] = None
    dietary_tags: List[str] = []
    estimated_cost: Optional[float] = None
    instructions: Optional[str] = None
    ingredients: List[RecipeIngredientDetail]
    nutrition_total: NutritionSummary
    nutrition_per_serving: NutritionSummary


class RecipeIngredientsResponse(BaseModel):
    recipe_id: int
    recipe_name: str
    ingredients: List[RecipeIngredientDetail]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_recipe_ingredient_detail(ri: RecipeIngredient) -> RecipeIngredientDetail:
    ing = ri.ingredient
    qty = ri.quantity
    factor = qty / 100.0 if qty else 0.0

    price_contrib = round(float(ing.price_per_unit or 0.0) * factor, 2)
    cal_contrib = round(float(ing.calories or 0.0) * factor, 1)
    pro_contrib = round(float(ing.protein or 0.0) * factor, 1)
    carb_contrib = round(float(ing.carbohydrates or 0.0) * factor, 1)
    fat_contrib = round(float(ing.fat or 0.0) * factor, 1)
    fib_contrib = round(float(ing.fiber or 0.0) * factor, 1)

    return RecipeIngredientDetail(
        id=ri.id,
        ingredient_id=ri.ingredient_id,
        name=ing.name,
        category=ing.category,
        quantity=ri.quantity,
        unit=ri.unit,
        price_contribution=price_contrib,
        calories_contribution=cal_contrib,
        protein_contribution=pro_contrib,
        carbs_contribution=carb_contrib,
        fat_contribution=fat_contrib,
        fiber_contribution=fib_contrib,
    )


# ---------------------------------------------------------------------------
# Ingredients Endpoints
# ---------------------------------------------------------------------------

@router.get("/ingredients", response_model=IngredientListResponse)
def list_ingredients(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=200, description="Page size"),
    category: Optional[str] = Query(None, description="Filter by ingredient category"),
    search: Optional[str] = Query(None, description="Search ingredient name"),
    db: Session = Depends(get_db),
):
    """Retrieve paginated list of ingredients with optional category and search filters."""
    query = db.query(Ingredient)

    if category:
        query = query.filter(Ingredient.category.ilike(f"%{category.strip()}%"))
    if search:
        query = query.filter(Ingredient.name.ilike(f"%{search.strip()}%"))

    total = query.count()
    items = query.order_by(Ingredient.name.asc()).offset(skip).limit(limit).all()

    return IngredientListResponse(
        total=total,
        skip=skip,
        limit=limit,
        items=[
            IngredientOut(
                id=i.id,
                name=i.name,
                category=i.category,
                unit=i.unit,
                price_per_unit=float(i.price_per_unit) if i.price_per_unit is not None else None,
                calories=i.calories,
                protein=i.protein,
                carbohydrates=i.carbohydrates,
                fat=i.fat,
                fiber=i.fiber,
            )
            for i in items
        ],
    )


@router.get("/ingredients/{ingredient_id}", response_model=IngredientOut)
def get_ingredient(
    ingredient_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve details of a single ingredient by ID."""
    ing = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not ing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingredient with ID {ingredient_id} not found",
        )

    return IngredientOut(
        id=ing.id,
        name=ing.name,
        category=ing.category,
        unit=ing.unit,
        price_per_unit=float(ing.price_per_unit) if ing.price_per_unit is not None else None,
        calories=ing.calories,
        protein=ing.protein,
        carbohydrates=ing.carbohydrates,
        fat=ing.fat,
        fiber=ing.fiber,
    )


# ---------------------------------------------------------------------------
# Recipes Endpoints
# ---------------------------------------------------------------------------

@router.get("/recipes", response_model=RecipeListResponse)
def list_recipes(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(20, ge=1, le=250, description="Page size"),
    meal_type: Optional[str] = Query(None, description="Filter by meal_type (breakfast, lunch, dinner, snack)"),
    cuisine: Optional[str] = Query(None, description="Filter by cuisine (North Indian, South Indian, etc.)"),
    dietary_tag: Optional[str] = Query(None, description="Filter by dietary tag (vegetarian, vegan, high_protein, etc.)"),
    search: Optional[str] = Query(None, description="Search recipe name or description"),
    db: Session = Depends(get_db),
):
    """Retrieve paginated list of recipes with filtering and search."""
    query = db.query(Recipe)

    if meal_type:
        query = query.filter(Recipe.meal_type.ilike(f"%{meal_type.strip()}%"))
    if cuisine:
        query = query.filter(Recipe.cuisine.ilike(f"%{cuisine.strip()}%"))
    if search:
        search_str = f"%{search.strip()}%"
        query = query.filter(or_(Recipe.name.ilike(search_str), Recipe.description.ilike(search_str)))

    all_matches = query.order_by(Recipe.name.asc()).all()

    # In-memory filter for dietary_tag JSON list if specified
    if dietary_tag:
        tag_lower = dietary_tag.strip().lower()
        all_matches = [
            r for r in all_matches
            if r.dietary_tags and any(tag_lower == str(t).lower() for t in r.dietary_tags)
        ]

    total = len(all_matches)
    paged = all_matches[skip : skip + limit]

    items = [
        RecipeSummaryOut(
            id=r.id,
            name=r.name,
            description=r.description,
            meal_type=r.meal_type,
            cuisine=r.cuisine,
            servings=r.servings or 2,
            preparation_time=r.preparation_time,
            cooking_time=r.cooking_time,
            dietary_tags=r.dietary_tags or [],
            estimated_cost=float(r.estimated_cost) if r.estimated_cost is not None else None,
            instructions=r.instructions,
            ingredient_count=len(r.recipe_ingredients),
        )
        for r in paged
    ]

    return RecipeListResponse(
        total=total,
        skip=skip,
        limit=limit,
        items=items,
    )


@router.get("/recipes/{recipe_id}", response_model=RecipeDetailOut)
def get_recipe(
    recipe_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve complete recipe details including its ingredients and nutritional totals."""
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipe with ID {recipe_id} not found",
        )

    ing_details = [_build_recipe_ingredient_detail(ri) for ri in recipe.recipe_ingredients]

    total_cal = round(sum(d.calories_contribution for d in ing_details), 1)
    total_pro = round(sum(d.protein_contribution for d in ing_details), 1)
    total_carb = round(sum(d.carbs_contribution for d in ing_details), 1)
    total_fat = round(sum(d.fat_contribution for d in ing_details), 1)
    total_fib = round(sum(d.fiber_contribution for d in ing_details), 1)

    servings = max(recipe.servings or 1, 1)

    return RecipeDetailOut(
        id=recipe.id,
        name=recipe.name,
        description=recipe.description,
        meal_type=recipe.meal_type,
        cuisine=recipe.cuisine,
        servings=servings,
        preparation_time=recipe.preparation_time,
        cooking_time=recipe.cooking_time,
        dietary_tags=recipe.dietary_tags or [],
        estimated_cost=float(recipe.estimated_cost) if recipe.estimated_cost is not None else None,
        instructions=recipe.instructions,
        ingredients=ing_details,
        nutrition_total=NutritionSummary(
            calories=total_cal,
            protein=total_pro,
            carbohydrates=total_carb,
            fat=total_fat,
            fiber=total_fib,
        ),
        nutrition_per_serving=NutritionSummary(
            calories=round(total_cal / servings, 1),
            protein=round(total_pro / servings, 1),
            carbohydrates=round(total_carb / servings, 1),
            fat=round(total_fat / servings, 1),
            fiber=round(total_fib / servings, 1),
        ),
    )


@router.get("/recipes/{recipe_id}/ingredients", response_model=RecipeIngredientsResponse)
def get_recipe_ingredients(
    recipe_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve list of ingredients and their portion contributions for a specific recipe."""
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipe with ID {recipe_id} not found",
        )

    ing_details = [_build_recipe_ingredient_detail(ri) for ri in recipe.recipe_ingredients]

    return RecipeIngredientsResponse(
        recipe_id=recipe.id,
        recipe_name=recipe.name,
        ingredients=ing_details,
    )

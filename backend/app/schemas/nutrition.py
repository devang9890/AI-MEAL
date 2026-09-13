"""Pydantic schemas for Nutrition Engine results and persisted targets."""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class NutritionCalculationResult(BaseModel):
    member_id: int
    member_name: str
    gender: str
    age: int
    height_cm: float
    weight_kg: float
    bmr: float = Field(..., description="Basal Metabolic Rate in kcal (Mifflin-St Jeor equation)")
    activity_level: str
    activity_multiplier: float
    tdee: float = Field(..., description="Total Daily Energy Expenditure in kcal (BMR * multiplier)")
    daily_calories: float = Field(..., description="Target daily calorie intake in kcal")
    daily_protein_g: float = Field(..., description="Daily protein target in grams (20% of calories, 4 kcal/g)")
    daily_carbs_g: float = Field(..., description="Daily carbohydrates target in grams (50% of calories, 4 kcal/g)")
    daily_fat_g: float = Field(..., description="Daily fat target in grams (30% of calories, 9 kcal/g)")
    daily_fiber_g: float = Field(..., description="Daily dietary fiber target in grams (14g per 1,000 kcal)")
    formula: str = "Mifflin-St Jeor (1990)"
    disclaimer: str = (
        "These nutritional figures are project-level engineering estimates for educational and "
        "decision-support demonstrations. They do not constitute medical or clinical dietary advice."
    )


class NutritionTargetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    member_id: int
    daily_calories: float
    daily_protein_g: float
    daily_carbs_g: float
    daily_fat_g: float
    daily_fiber_g: float
    created_at: datetime
    updated_at: datetime

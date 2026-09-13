"""Nutrition Calculation Engine Service.

Implements the Mifflin-St Jeor equation for Basal Metabolic Rate (BMR),
activity multipliers for Total Daily Energy Expenditure (TDEE),
percentage-based macronutrient distribution, and dietary fiber targets.

DISCLAIMER:
All nutrition formulas and macro ratios in this service represent project-level
engineering baseline assumptions for demonstration purposes. They do not constitute
clinical or medical dietary advice.
"""

from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models.member import Member
from app.models.nutrition import NutritionTarget


# Centralized activity multipliers based on standard physical activity levels
ACTIVITY_MULTIPLIERS: Dict[str, float] = {
    "sedentary": 1.2,        # Little or no exercise, desk job
    "light": 1.375,          # Light exercise or sports 1-3 days/week
    "moderate": 1.55,        # Moderate exercise or sports 3-5 days/week
    "active": 1.725,         # Hard exercise or sports 6-7 days/week
    "very_active": 1.9,      # Hard daily exercise and physical job / training twice a day
}

# Initial baseline macronutrient distribution percentages
# (Sum must equal 100%)
MACRO_RATIOS: Dict[str, float] = {
    "protein_pct": 0.20,     # 20% of daily calories
    "carbs_pct": 0.50,       # 50% of daily calories
    "fat_pct": 0.30,         # 30% of daily calories
}

# Energy densities (kcal per gram)
KCAL_PER_GRAM_PROTEIN = 4.0
KCAL_PER_GRAM_CARBS = 4.0
KCAL_PER_GRAM_FAT = 9.0

# Fiber recommendation: 14g per 1,000 kcal
FIBER_GRAMS_PER_1000_KCAL = 14.0


def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
    """Calculate Basal Metabolic Rate (BMR) using the Mifflin-St Jeor equation.

    Male:
        BMR = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    Female:
        BMR = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    """
    if weight_kg <= 0:
        raise ValueError("weight_kg must be positive")
    if height_cm <= 0:
        raise ValueError("height_cm must be positive")
    if age <= 0:
        raise ValueError("age must be positive")

    normalized_gender = gender.strip().lower()

    base = 10.0 * weight_kg + 6.25 * height_cm - 5.0 * age

    if normalized_gender == "male":
        return round(base + 5.0, 2)
    elif normalized_gender == "female":
        return round(base - 161.0, 2)
    else:
        raise ValueError(f"Invalid gender '{gender}'. Expected 'male' or 'female'.")


def get_activity_multiplier(activity_level: str) -> float:
    """Return the physical activity multiplier for a given activity level."""
    normalized_level = activity_level.strip().lower()
    if normalized_level not in ACTIVITY_MULTIPLIERS:
        valid_options = ", ".join(ACTIVITY_MULTIPLIERS.keys())
        raise ValueError(
            f"Invalid activity_level '{activity_level}'. Expected one of: {valid_options}."
        )
    return ACTIVITY_MULTIPLIERS[normalized_level]


def calculate_tdee(bmr: float, activity_level: str) -> float:
    """Calculate Total Daily Energy Expenditure (TDEE = BMR * Activity Multiplier)."""
    multiplier = get_activity_multiplier(activity_level)
    return round(bmr * multiplier, 2)


def calculate_macros(daily_calories: float) -> Dict[str, float]:
    """Calculate daily macronutrient targets in grams from daily calories.

    - Protein: 20% of calories (4 kcal/g)
    - Carbohydrates: 50% of calories (4 kcal/g)
    - Fat: 30% of calories (9 kcal/g)
    """
    if daily_calories <= 0:
        raise ValueError("daily_calories must be positive")

    protein_calories = daily_calories * MACRO_RATIOS["protein_pct"]
    carbs_calories = daily_calories * MACRO_RATIOS["carbs_pct"]
    fat_calories = daily_calories * MACRO_RATIOS["fat_pct"]

    protein_g = protein_calories / KCAL_PER_GRAM_PROTEIN
    carbs_g = carbs_calories / KCAL_PER_GRAM_CARBS
    fat_g = fat_calories / KCAL_PER_GRAM_FAT

    return {
        "protein_g": round(protein_g, 1),
        "carbs_g": round(carbs_g, 1),
        "fat_g": round(fat_g, 1),
    }


def calculate_fiber(daily_calories: float) -> float:
    """Calculate daily dietary fiber target based on 14g per 1,000 kcal."""
    if daily_calories <= 0:
        raise ValueError("daily_calories must be positive")
    fiber_g = (daily_calories / 1000.0) * FIBER_GRAMS_PER_1000_KCAL
    return round(fiber_g, 1)


def calculate_nutrition_for_member(member: Member) -> Dict[str, Any]:
    """Run full nutrition calculation pipeline for a Member instance."""
    bmr = calculate_bmr(
        weight_kg=member.weight_kg,
        height_cm=member.height_cm,
        age=member.age,
        gender=member.gender,
    )
    multiplier = get_activity_multiplier(member.activity_level)
    tdee = calculate_tdee(bmr, member.activity_level)

    # In maintenance mode, daily calorie target equals TDEE
    daily_calories = round(tdee, 1)
    macros = calculate_macros(daily_calories)
    fiber_g = calculate_fiber(daily_calories)

    return {
        "bmr": bmr,
        "activity_level": member.activity_level.strip().lower(),
        "activity_multiplier": multiplier,
        "tdee": round(tdee, 1),
        "daily_calories": daily_calories,
        "daily_protein_g": macros["protein_g"],
        "daily_carbs_g": macros["carbs_g"],
        "daily_fat_g": macros["fat_g"],
        "daily_fiber_g": fiber_g,
    }


def save_or_update_nutrition_target(
    db: Session, member: Member, calculated: Dict[str, Any]
) -> NutritionTarget:
    """Upsert NutritionTarget row for the specified member."""
    target = (
        db.query(NutritionTarget)
        .filter(NutritionTarget.member_id == member.id)
        .first()
    )

    if target is None:
        target = NutritionTarget(
            member_id=member.id,
            daily_calories=calculated["daily_calories"],
            daily_protein_g=calculated["daily_protein_g"],
            daily_carbs_g=calculated["daily_carbs_g"],
            daily_fat_g=calculated["daily_fat_g"],
            daily_fiber_g=calculated["daily_fiber_g"],
        )
        db.add(target)
    else:
        target.daily_calories = calculated["daily_calories"]
        target.daily_protein_g = calculated["daily_protein_g"]
        target.daily_carbs_g = calculated["daily_carbs_g"]
        target.daily_fat_g = calculated["daily_fat_g"]
        target.daily_fiber_g = calculated["daily_fiber_g"]

    db.commit()
    db.refresh(target)
    return target

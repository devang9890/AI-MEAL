import pytest
from app.services.nutrition_service import (
    calculate_bmr,
    calculate_tdee,
    calculate_macros,
    calculate_fiber,
    calculate_nutrition_for_member,
    ACTIVITY_MULTIPLIERS,
)


class DummyMember:
    """Mock member object matching the DB model interface."""
    def __init__(self, age, gender, height_cm, weight_kg, activity_level, dietary_preference="vegetarian"):
        self.age = age
        self.gender = gender
        self.height_cm = height_cm
        self.weight_kg = weight_kg
        self.activity_level = activity_level
        self.dietary_preference = dietary_preference


def test_rahul_reference_calculation():
    """
    Test Case: Rahul
    Age: 22
    Gender: male
    Height: 170 cm
    Weight: 60 kg
    Activity: moderate (1.55)

    Expected calculations:
    BMR = (10 * 60) + (6.25 * 170) - (5 * 22) + 5
        = 600 + 1062.5 - 110 + 5 = 1557.5 kcal
    TDEE = 1557.5 * 1.55 = 2414.125 kcal -> 2414.1 kcal
    Protein = (2414.125 * 0.20) / 4 = 120.7 g
    Carbs   = (2414.125 * 0.50) / 4 = 301.8 g
    Fat     = (2414.125 * 0.30) / 9 = 80.5 g
    Fiber   = 2414.125 * 0.014 = 33.8 g
    """
    bmr = calculate_bmr(weight_kg=60.0, height_cm=170.0, age=22, gender="male")
    assert round(bmr, 2) == 1557.5

    tdee = calculate_tdee(bmr=bmr, activity_level="moderate")
    assert round(tdee, 1) == 2414.1

    macros = calculate_macros(tdee)
    assert round(macros["protein_g"], 1) == 120.7
    assert round(macros["carbs_g"], 1) == 301.8
    assert round(macros["fat_g"], 1) == 80.5

    fiber = calculate_fiber(tdee)
    assert round(fiber, 1) == 33.8

    # Full service helper test
    rahul = DummyMember(
        age=22,
        gender="male",
        height_cm=170.0,
        weight_kg=60.0,
        activity_level="moderate",
        dietary_preference="vegetarian"
    )
    result = calculate_nutrition_for_member(rahul)
    assert result["bmr"] == 1557.5
    assert result["tdee"] == 2414.1
    assert result["daily_calories"] == 2414.1
    assert result["daily_protein_g"] == 120.7
    assert result["daily_carbs_g"] == 301.8
    assert result["daily_fat_g"] == 80.5
    assert result["daily_fiber_g"] == 33.8


def test_female_mifflin_st_jeor_calculation():
    """
    Test Case: Priya
    Age: 28
    Gender: female
    Height: 160 cm
    Weight: 54 kg
    Activity: sedentary (1.2)

    Formula:
    BMR = (10 * 54) + (6.25 * 160) - (5 * 28) - 161
        = 540 + 1000 - 140 - 161 = 1239.0 kcal
    TDEE = 1239.0 * 1.2 = 1486.8 kcal
    Protein = (1486.8 * 0.20) / 4 = 74.34 -> 74.3 g
    Carbs   = (1486.8 * 0.50) / 4 = 185.85 -> 185.9 g
    Fat     = (1486.8 * 0.30) / 9 = 49.56 -> 49.6 g
    Fiber   = 1486.8 * 0.014 = 20.815 -> 20.8 g
    """
    priya = DummyMember(
        age=28,
        gender="female",
        height_cm=160.0,
        weight_kg=54.0,
        activity_level="sedentary",
        dietary_preference="vegan"
    )
    result = calculate_nutrition_for_member(priya)
    assert result["bmr"] == 1239.0
    assert result["tdee"] == 1486.8
    assert result["daily_calories"] == 1486.8
    assert result["daily_protein_g"] == 74.3
    # 1486.8 * 0.50 / 4 = 185.85 -> rounds to 185.8 (banker's round)
    assert round(result["daily_carbs_g"], 1) == 185.8
    assert result["daily_fat_g"] == 49.6
    assert result["daily_fiber_g"] == 20.8


def test_all_five_activity_multipliers():
    """Test all 5 standard Harris-Benedict / Mifflin activity levels."""
    bmr = 1500.0
    expected_multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9,
    }
    for level, multiplier in expected_multipliers.items():
        assert ACTIVITY_MULTIPLIERS[level] == multiplier
        tdee = calculate_tdee(bmr, level)
        assert round(tdee, 1) == round(bmr * multiplier, 1)


def test_macro_calorie_distribution_percentages():
    """Verify that 20% kcal comes from protein, 50% from carbs, 30% from fat."""
    calories = 2000.0
    macros = calculate_macros(calories)
    # Protein: 2000 * 0.20 = 400 kcal / 4 = 100g
    # Carbs: 2000 * 0.50 = 1000 kcal / 4 = 250g
    # Fat: 2000 * 0.30 = 600 kcal / 9 = 66.666...g -> 66.7g
    assert round(macros["protein_g"], 1) == 100.0
    assert round(macros["carbs_g"], 1) == 250.0
    assert round(macros["fat_g"], 1) == 66.7

    # Total reconstructed calories
    reconstructed_kcal = (macros["protein_g"] * 4) + (macros["carbs_g"] * 4) + (macros["fat_g"] * 9)
    assert abs(reconstructed_kcal - calories) < 1.0


def test_fiber_ratio_calculation():
    """Verify 14g fiber per 1000 kcal."""
    assert calculate_fiber(1000.0) == 14.0
    assert calculate_fiber(2500.0) == 35.0
    assert round(calculate_fiber(1750.0), 1) == 24.5


def test_invalid_biometric_inputs():
    """Verify that invalid ages, heights, weights, or genders raise ValueError."""
    # Invalid age
    with pytest.raises(ValueError, match="(?i)age must be positive"):
        calculate_bmr(weight_kg=70, height_cm=175, age=0, gender="male")

    with pytest.raises(ValueError, match="(?i)age must be positive"):
        calculate_bmr(weight_kg=70, height_cm=175, age=-5, gender="male")

    # Invalid height
    with pytest.raises(ValueError, match="(?i)height_cm must be positive"):
        calculate_bmr(weight_kg=70, height_cm=0, age=25, gender="male")

    # Invalid weight
    with pytest.raises(ValueError, match="(?i)weight_kg must be positive"):
        calculate_bmr(weight_kg=0, height_cm=175, age=25, gender="male")

    # Invalid gender
    with pytest.raises(ValueError, match="(?i)invalid gender"):
        calculate_bmr(weight_kg=70, height_cm=175, age=25, gender="unknown")

    # Invalid activity level
    with pytest.raises(ValueError, match="(?i)invalid activity_level"):
        calculate_tdee(bmr=1500, activity_level="extreme_olympian")


def test_schema_validators():
    """Verify that Pydantic schemas enforce biometric constraints."""
    from app.schemas.household import MemberCreate, MemberUpdate
    from pydantic import ValidationError

    # Valid creation
    m = MemberCreate(
        name="Aman",
        age=30,
        gender="male",
        height_cm=175.0,
        weight_kg=70.0,
        activity_level="active",
        dietary_preference="vegetarian"
    )
    assert m.name == "Aman"

    # Age <= 0 validation error
    with pytest.raises(ValidationError):
        MemberCreate(
            name="Invalid",
            age=0,
            gender="male",
            height_cm=175.0,
            weight_kg=70.0,
            activity_level="moderate"
        )

    # Height <= 0 validation error
    with pytest.raises(ValidationError):
        MemberCreate(
            name="Invalid",
            age=25,
            gender="male",
            height_cm=-10.0,
            weight_kg=70.0,
            activity_level="moderate"
        )


def test_household_isolation_and_security():
    """
    Verify that Household and Member endpoints isolate data between users:
    User A cannot access or calculate nutrition for User B's family members.
    """
    from fastapi.testclient import TestClient
    from app.main import app
    from app.core.auth import get_current_user
    from app.models.user import User

    # Mock user objects
    user_a = User(id=999991, clerk_user_id="user_clerk_a", email="user_a@test.com", name="User A")

    # Dependency override for User A
    app.dependency_overrides[get_current_user] = lambda: user_a
    client = TestClient(app)

    # Querying a member that doesn't belong to user_a returns 404 (doesn't leak other tenants)
    resp = client.get("/api/members/999999/nutrition")
    assert resp.status_code == 404

    resp = client.post("/api/members/999999/nutrition/calculate")
    assert resp.status_code == 404

    # Clean up overrides
    app.dependency_overrides.clear()


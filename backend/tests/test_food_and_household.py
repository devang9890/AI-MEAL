"""Tests for optimized Food and Household endpoints."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.household import Household
from app.models.member import Member
from app.models.nutrition import NutritionTarget
from app.models.ingredient import Ingredient
from app.models.recipe import Recipe, RecipeIngredient
from app.main import app


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_food_and_household_fast_endpoints(db_session):
    user = User(clerk_user_id="clerk_fast_user", email="fast@example.com", name="Fast User")
    db_session.add(user)
    db_session.commit()

    # Create household & member with nutrition target
    h = Household(name="Speed Family", weekly_budget=2000.0, owner_id=user.id)
    db_session.add(h)
    db_session.commit()

    m = Member(
        household_id=h.id,
        name="Aarav",
        age=28,
        gender="male",
        height_cm=180.0,
        weight_kg=75.0,
        activity_level="moderate",
        dietary_preference="vegetarian",
    )
    db_session.add(m)
    db_session.commit()

    nt = NutritionTarget(
        member_id=m.id,
        daily_calories=2200.0,
        daily_protein_g=110.0,
        daily_carbs_g=275.0,
        daily_fat_g=73.0,
        daily_fiber_g=30.0,
    )
    db_session.add(nt)
    db_session.commit()

    # Create ingredient & recipe
    ing = Ingredient(
        name="Paneer",
        category="Dairy",
        unit="g",
        price_per_unit=0.45,
        calories=265.0,
        protein=18.3,
        carbohydrates=1.2,
        fat=20.8,
        fiber=0.0,
    )
    db_session.add(ing)
    db_session.commit()

    rec = Recipe(
        name="Paneer Bhurji",
        meal_type="breakfast",
        cuisine="North Indian",
        servings=2,
        dietary_tags=["vegetarian", "high_protein"],
        estimated_cost=90.0,
    )
    db_session.add(rec)
    db_session.commit()

    ri = RecipeIngredient(
        recipe_id=rec.id,
        ingredient_id=ing.id,
        quantity=150.0,
        unit="g",
    )
    db_session.add(ri)
    db_session.commit()

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        client = TestClient(app)

        # 1. Test GET /api/ingredients
        res_ing = client.get("/api/ingredients?limit=50")
        assert res_ing.status_code == 200
        data_ing = res_ing.json()
        assert data_ing["total"] >= 1
        assert any(item["name"] == "Paneer" for item in data_ing["items"])

        # 2. Test GET /api/recipes
        res_rec = client.get("/api/recipes?limit=50&meal_type=breakfast")
        assert res_rec.status_code == 200
        data_rec = res_rec.json()
        assert data_rec["total"] >= 1
        assert any(item["name"] == "Paneer Bhurji" for item in data_rec["items"])

        # 3. Test GET /api/recipes/{id}
        res_detail = client.get(f"/api/recipes/{rec.id}")
        assert res_detail.status_code == 200
        detail = res_detail.json()
        assert detail["id"] == rec.id
        assert len(detail["ingredients"]) == 1
        assert detail["nutrition_total"]["calories"] > 0

        # 4. Test GET /api/households/{id}/members with inlined nutrition_target
        res_mem = client.get(f"/api/households/{h.id}/members")
        assert res_mem.status_code == 200
        members = res_mem.json()
        assert len(members) == 1
        assert members[0]["has_nutrition_target"] is True
        assert members[0]["nutrition_target"] is not None
        assert members[0]["nutrition_target"]["daily_calories"] == 2200.0

    finally:
        app.dependency_overrides.clear()


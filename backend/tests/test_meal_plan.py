"""Tests for Meal Plan routes and performance optimization."""
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.household import Household
from app.models.member import Member
from app.models.recipe import Recipe
from app.models.meal_plan import MealPlan
from app.models.meal import Meal
from app.main import app


@pytest.fixture
def db_session():
    """Provides an isolated in-memory SQLite database session for tests."""
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


def test_list_plans_and_get_plan_fast(db_session):
    user = User(clerk_user_id="clerk_user_mp", email="user_mp@example.com", name="User MP")
    db_session.add(user)
    db_session.commit()

    household = Household(name="Test Family", weekly_budget=1000.0, owner_id=user.id)
    db_session.add(household)
    db_session.commit()

    member = Member(
        household_id=household.id,
        name="Member 1",
        age=30,
        gender="male",
        height_cm=175.0,
        weight_kg=70.0,
        activity_level="moderate",
        dietary_preference="vegetarian",
    )
    db_session.add(member)
    db_session.commit()

    recipe = Recipe(
        name="Test Dal Tadka",
        meal_type="dinner",
        dietary_tags=["vegetarian"],
        servings=2,
        estimated_cost=80.0,
    )
    db_session.add(recipe)
    db_session.commit()

    plan = MealPlan(
        household_id=household.id,
        week_start_date=date.today(),
        total_cost=80.0,
        status="active",
    )
    db_session.add(plan)
    db_session.commit()

    meal = Meal(
        meal_plan_id=plan.id,
        recipe_id=recipe.id,
        day="Monday",
        meal_type="dinner",
        servings=2,
        cost=80.0,
    )
    db_session.add(meal)
    db_session.commit()

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        client = TestClient(app)
        # Test GET /api/households/{id}/plans
        res_list = client.get(f"/api/households/{household.id}/plans")
        assert res_list.status_code == 200
        data_list = res_list.json()
        assert len(data_list) == 1
        assert data_list[0]["id"] == plan.id
        assert len(data_list[0]["meals"]) == 1
        assert data_list[0]["meals"][0]["recipe_name"] == "Test Dal Tadka"
        assert data_list[0]["weekly_budget"] == 1000.0

        # Test GET /api/households/{id}/plans/{plan_id}
        res_detail = client.get(f"/api/households/{household.id}/plans/{plan.id}")
        assert res_detail.status_code == 200
        data_detail = res_detail.json()
        assert data_detail["id"] == plan.id
        assert len(data_detail["meals"]) == 1
        assert data_detail["meals"][0]["recipe_name"] == "Test Dal Tadka"
    finally:
        app.dependency_overrides.clear()


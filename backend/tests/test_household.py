"""Tests for Household CRUD routes."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.household import Household
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


def test_update_household_budget_and_name(db_session):
    """Test PUT /api/households/{id} successfully updates budget and name."""
    user = User(clerk_user_id="clerk_user_1", email="user1@example.com", name="User 1")
    db_session.add(user)
    db_session.commit()

    household = Household(name="Initial Family", weekly_budget=500.0, owner_id=user.id)
    db_session.add(household)
    db_session.commit()

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        client = TestClient(app)
        response = client.put(
            f"/api/households/{household.id}",
            json={"name": "DHRUV FAMILY", "weekly_budget": 1000.0},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == household.id
        assert data["name"] == "DHRUV FAMILY"
        assert data["weekly_budget"] == 1000.0

        # Verify in database
        db_session.refresh(household)
        assert household.name == "DHRUV FAMILY"
        assert float(household.weekly_budget) == 1000.0
    finally:
        app.dependency_overrides.clear()


def test_update_household_unauthorized(db_session):
    """Test User A cannot update User B's household."""
    user_a = User(clerk_user_id="clerk_a", email="a@example.com", name="User A")
    user_b = User(clerk_user_id="clerk_b", email="b@example.com", name="User B")
    db_session.add_all([user_a, user_b])
    db_session.commit()

    household_b = Household(name="Family B", weekly_budget=2000.0, owner_id=user_b.id)
    db_session.add(household_b)
    db_session.commit()

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: user_a

    try:
        client = TestClient(app)
        response = client.put(
            f"/api/households/{household_b.id}",
            json={"name": "Hacked Family", "weekly_budget": 10.0},
        )
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()

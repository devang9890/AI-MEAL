"""Tests for AI Chat Service and API."""
from unittest.mock import MagicMock
import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.user import User
from app.models.household import Household
from app.models.member import Member
from app.models.nutrition import NutritionTarget
from app.models.recipe import Recipe
from app.models.ingredient import Ingredient
from app.schemas.chat import ChatRequest, ChatMessageItem
from app.services.chat_service import (
    generate_chat_reply,
    get_household_context,
    build_system_prompt,
    get_food_knowledge_context
)


@pytest.fixture
def db_session():
    """Provides an isolated in-memory SQLite database session for tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_1_valid_message():
    """Test 1: Valid message creates a valid ChatRequest."""
    req = ChatRequest(message="How many calories do I need?", conversation=[])
    assert req.message == "How many calories do I need?"
    assert len(req.conversation) == 0


def test_2_empty_message_rejection():
    """Test 2: Empty message and whitespace-only messages are rejected."""
    with pytest.raises(ValidationError):
        ChatRequest(message="", conversation=[])

    with pytest.raises(ValidationError):
        ChatRequest(message="   \n\t  ", conversation=[])

    with pytest.raises(ValidationError):
        ChatMessageItem(role="user", content="   ")


def test_3_message_length_validation():
    """Test 3: Messages exceeding 2000 characters are rejected."""
    long_message = "A" * 2001
    with pytest.raises(ValidationError):
        ChatRequest(message=long_message, conversation=[])

    # 2000 characters should be valid
    valid_long = "A" * 2000
    req = ChatRequest(message=valid_long, conversation=[])
    assert len(req.message) == 2000


def test_4_groq_success_response(db_session):
    """Test 4: Groq success response returns expected reply and success=True."""
    mock_groq = MagicMock()
    mock_completion = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Your household daily target is 2221 kcal/day."
    mock_completion.choices = [mock_choice]
    mock_groq.chat.completions.create.return_value = mock_completion

    result = generate_chat_reply(
        message="What is my calorie target?",
        conversation=[],
        db=db_session,
        current_user=None,
        groq_client=mock_groq
    )

    assert result["success"] is True
    assert "2221 kcal/day" in result["reply"]
    assert result["error"] is None
    assert mock_groq.chat.completions.create.called


def test_5_groq_failure_handling(db_session):
    """Test 5: Groq failure is handled gracefully with friendly message and no crash."""
    mock_groq = MagicMock()
    mock_groq.chat.completions.create.side_effect = RuntimeError("Groq API Timeout or Network issue")

    result = generate_chat_reply(
        message="Hello",
        conversation=[],
        db=db_session,
        current_user=None,
        groq_client=mock_groq
    )

    assert result["success"] is False
    assert "Sorry, I couldn't process that right now." in result["reply"]
    assert result["error"] == "GROQ_PROCESSING_ERROR"


def test_6_conversation_history(db_session):
    """Test 6: Conversation history is passed to the Groq completion messages."""
    mock_groq = MagicMock()
    mock_completion = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Because you have 3 active family members."
    mock_completion.choices = [mock_choice]
    mock_groq.chat.completions.create.return_value = mock_completion

    history = [
        ChatMessageItem(role="user", content="How many calories do we need?"),
        ChatMessageItem(role="assistant", content="Your household needs 2400 kcal/day.")
    ]

    result = generate_chat_reply(
        message="Why?",
        conversation=history,
        db=db_session,
        current_user=None,
        groq_client=mock_groq
    )

    assert result["success"] is True
    call_kwargs = mock_groq.chat.completions.create.call_args[1]
    messages_sent = call_kwargs["messages"]

    # System prompt + 2 history items + 1 current message = 4
    assert len(messages_sent) == 4
    assert messages_sent[0]["role"] == "system"
    assert messages_sent[1]["role"] == "user"
    assert messages_sent[1]["content"] == "How many calories do we need?"
    assert messages_sent[2]["role"] == "assistant"
    assert messages_sent[2]["content"] == "Your household needs 2400 kcal/day."
    assert messages_sent[3]["role"] == "user"
    assert messages_sent[3]["content"] == "Why?"


def test_7_authenticated_household_context(db_session):
    """Test 7: Authenticated user's household, member biometrics, and nutrition targets are included."""
    user = User(clerk_user_id="clerk_user_1", email="user1@example.com", name="Devang")
    db_session.add(user)
    db_session.commit()

    household = Household(name="Sharma Household", weekly_budget=3500.0, owner_id=user.id)
    db_session.add(household)
    db_session.commit()

    member = Member(
        household_id=household.id,
        name="Devang",
        age=28,
        gender="male",
        height_cm=175.0,
        weight_kg=72.0,
        activity_level="moderate",
        dietary_preference="vegetarian"
    )
    db_session.add(member)
    db_session.commit()

    target = NutritionTarget(
        member_id=member.id,
        daily_calories=2221.0,
        daily_protein_g=111.0,
        daily_carbs_g=277.0,
        daily_fat_g=74.0,
        daily_fiber_g=31.0
    )
    db_session.add(target)
    db_session.commit()

    ctx = get_household_context(db_session, current_user=user)
    assert ctx["has_household"] is True
    assert ctx["household_name"] == "Sharma Household"
    assert ctx["member_count"] == 1
    assert ctx["aggregate_targets"]["daily_calories"] == 2221.0
    assert ctx["aggregate_targets"]["daily_protein_g"] == 111.0

    system_prompt = build_system_prompt(ctx, {"sample_recipes": [], "affordable_ingredients": []})
    assert "Sharma Household" in system_prompt
    assert "2221.0 kcal/day" in system_prompt
    assert "111.0 g/day" in system_prompt
    assert "Devang" in system_prompt
    assert "vegetarian" in system_prompt


def test_8_no_cross_user_household_data_access(db_session):
    """Test 8: User A cannot access User B's household, even if specifying B's household_id."""
    user_a = User(clerk_user_id="clerk_a", email="a@example.com", name="User A")
    user_b = User(clerk_user_id="clerk_b", email="b@example.com", name="User B")
    db_session.add_all([user_a, user_b])
    db_session.commit()

    household_b = Household(name="Private B Household", weekly_budget=5000.0, owner_id=user_b.id)
    db_session.add(household_b)
    db_session.commit()

    # User A tries to query B's household by ID
    ctx_a = get_household_context(db_session, current_user=user_a, household_id=household_b.id)

    # Must NOT return household_b
    assert ctx_a["has_household"] is False
    assert "No household profiles found" in ctx_a["reason"]


def test_9_api_endpoint_integration(monkeypatch, db_session):
    """Test 9: POST /api/chat responds via FastAPI TestClient."""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.core.database import get_db

    # Override get_db dependency to use db_session
    app.dependency_overrides[get_db] = lambda: db_session

    try:
        # Mock generate_chat_reply
        with monkeypatch.context() as m:
            m.setattr(
                "app.routers.chat.generate_chat_reply",
                lambda **kwargs: {
                    "reply": "Your family needs balanced macros.",
                    "success": True,
                    "error": None
                }
            )
            client = TestClient(app)
            response = client.post("/api/chat", json={"message": "What should we eat?"})
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["reply"] == "Your family needs balanced macros."
    finally:
        app.dependency_overrides.clear()

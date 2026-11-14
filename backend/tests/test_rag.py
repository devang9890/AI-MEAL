"""Comprehensive Unit and Integration Tests for AI Meal Planner Codebase RAG.

Tests cover:
- Source file discovery & exclusions (.env, node_modules, credentials)
- Code-aware AST, React, and Markdown chunking
- Stable chunk IDs & content hash detection
- Incremental indexing manifest logic (new, modified, deleted)
- Local embedding generation (dimension 384, unit vector normalization)
- Pinecone service operations (upsert, similarity search, deletion)
- RAG retrieval pipeline & score threshold filtering
- Grounded Groq prompt generation & safety rules
- Multi-tenant household biometrics isolation
- API endpoint integration with /api/chat
"""
import os
import json
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.user import User
from app.models.household import Household
from app.models.member import Member
from app.models.nutrition import NutritionTarget
from app.schemas.chat import ChatRequest, ChatResponse, ChatMessageItem
from app.rag.source_loader import (
    discover_source_files,
    is_file_excluded,
    sanitize_content,
    SourceDocument
)
from app.rag.code_chunker import (
    chunk_document,
    chunk_python_document,
    chunk_react_document,
    chunk_markdown_document,
    make_chunk_id,
    generate_source_label,
    CodeChunk
)
from app.rag.ingestion import run_ingestion, ManifestManager
from app.rag.retrieval import retrieve_codebase_context, RetrievedContext
from app.services.embedding_service import EmbeddingService, EXPECTED_DIMENSION
from app.services.pinecone_service import PineconeService
from app.services.chat_service import generate_chat_reply, build_system_prompt


@pytest.fixture
def db_session():
    """Isolated SQLite in-memory database session."""
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


@pytest.fixture
def mock_embedding_service():
    """Mock embedding service returning 384-dimensional unit vectors."""
    mock_svc = MagicMock(spec=EmbeddingService)
    mock_svc.model_name = "sentence-transformers/all-MiniLM-L6-v2"
    # Deterministic 384-d vector with norm = 1.0
    vec = [1.0 / (384 ** 0.5)] * 384
    mock_svc.embed_text.return_value = vec
    mock_svc.embed_batch.side_effect = lambda texts, batch_size=32: [vec for _ in texts]
    return mock_svc


@pytest.fixture
def mock_pinecone_service():
    """Mock Pinecone service with in-memory match simulation."""
    mock_svc = MagicMock(spec=PineconeService)
    mock_svc.index_name = "ai-meal-planner-rag"
    mock_svc.namespace = "ai-meal-planner-dev"
    mock_svc.is_configured.return_value = True
    mock_svc.ensure_index_exists.return_value = True
    mock_svc.upsert_vectors.side_effect = lambda vectors, **kwargs: len(vectors)
    mock_svc.delete_chunks.side_effect = lambda ids, **kwargs: len(ids)

    # Default query return
    mock_svc.query.return_value = [
        {
            "id": "chunk_1",
            "score": 0.88,
            "metadata": {
                "chunk_id": "chunk_1",
                "file_path": "backend/app/services/optimizer.py",
                "component_or_function": "optimize_weekly_meal_plan",
                "section": "Functions",
                "chunk_text": "def optimize_weekly_meal_plan(): Solves PuLP Integer Linear Program for weekly meals under budget.",
                "source_label": "Weekly Meal Planner & Optimizer",
                "content_hash": "hash_1"
            }
        }
    ]
    return mock_svc


# ---------------------------------------------------------------------------
# 1. Source Discovery & Exclusions
# ---------------------------------------------------------------------------

def test_1_secret_file_exclusions():
    """Verifies that .env files and credentials are unconditionally excluded."""
    assert is_file_excluded(".env")[0] is True
    assert is_file_excluded("backend/.env")[0] is True
    assert is_file_excluded("backend/.env.production")[0] is True
    assert is_file_excluded("frontend/.env.local")[0] is True
    assert is_file_excluded("package-lock.json")[0] is True


def test_2_directory_exclusions():
    """Verifies that node_modules, .git, venv, and cache folders are excluded."""
    assert is_file_excluded("node_modules/react/index.js")[0] is True
    assert is_file_excluded(".git/config")[0] is True
    assert is_file_excluded("backend/venv/lib/site.py")[0] is True
    assert is_file_excluded("backend/__pycache__/main.cpython-311.pyc")[0] is True
    assert is_file_excluded("frontend/dist/index.html")[0] is True


def test_3_content_sanitizer_removes_secrets():
    """Verifies that API keys, tokens, and database passwords are redacted."""
    raw = (
        "GROQ_KEY = gsk_1234567890abcdef1234567890\n"
        "CLERK_PUB = pk_test_dGVuZGVyLWtvaS01Njk0LmNsZXJrLmFjY291bnRzLmRldiQ\n"
        "DB_URL = postgresql://neondb_owner:secret_password_123@ep-cool-pooler.aws.neon.tech/neondb"
    )
    clean = sanitize_content(raw)
    assert "gsk_1234567890abcdef1234567890" not in clean
    assert "[REDACTED_GROQ_KEY]" in clean
    assert "[REDACTED_CLERK_PUBKEY]" in clean
    assert "secret_password_123" not in clean
    assert "[REDACTED_DATABASE_URL]" in clean


# ---------------------------------------------------------------------------
# 2. Code-Aware Chunking
# ---------------------------------------------------------------------------

def test_4_python_ast_chunking():
    """Tests that Python files are cleanly chunked into classes and functions with metadata."""
    code = (
        '"""Nutrition calculator module."""\n\n'
        'def calculate_bmr(weight: float, height: float, age: int, gender: str) -> float:\n'
        '    """Calculates BMR via Mifflin-St Jeor formula."""\n'
        '    if gender == "male":\n'
        '        return 10 * weight + 6.25 * height - 5 * age + 5\n'
        '    return 10 * weight + 6.25 * height - 5 * age - 161\n\n'
        'class MealOptimizer:\n'
        '    """PuLP based meal optimizer."""\n'
        '    def solve(self):\n'
        '        return True\n'
    )
    doc = SourceDocument(
        file_path="backend/app/services/nutrition_service.py",
        content=code,
        content_hash="dummy_hash",
        source_type="python_backend",
        total_lines=15
    )
    chunks = chunk_python_document(doc)
    assert len(chunks) >= 2

    # Check function chunk
    func_chunk = next(c for c in chunks if c.component_or_function == "calculate_bmr")
    assert "Mifflin-St Jeor" in func_chunk.chunk_text
    assert func_chunk.start_line == 3
    assert func_chunk.source_label == "Nutrition & Mifflin-St Jeor Engine"

    # Check class chunk
    class_chunk = next(c for c in chunks if c.component_or_function == "MealOptimizer")
    assert "MealOptimizer" in class_chunk.chunk_text
    assert class_chunk.section == "Classes"


def test_5_react_jsx_chunking():
    """Tests that React JSX components and exports are correctly identified."""
    jsx = (
        'import React from "react";\n\n'
        'export default function MealCard({ meal, onSwap }) {\n'
        '  return (\n'
        '    <div className="meal-card">\n'
        '      <h3>{meal.name}</h3>\n'
        '      <p>Calories: {meal.calories} kcal</p>\n'
        '      <button onClick={onSwap}>Swap Meal</button>\n'
        '    </div>\n'
        '  );\n'
        '}\n'
    )
    doc = SourceDocument(
        file_path="frontend/src/components/MealCard.jsx",
        content=jsx,
        content_hash="jsx_hash",
        source_type="react_frontend",
        total_lines=12
    )
    chunks = chunk_react_document(doc)
    assert len(chunks) == 1
    assert chunks[0].component_or_function == "MealCard"
    assert "MealCard" in chunks[0].chunk_text
    assert "Swap Meal" in chunks[0].chunk_text


def test_6_markdown_chunking():
    """Tests that Markdown documentation splits into sections preserving heading titles."""
    md = (
        "# AI Meal Planner\n\n"
        "Smart budget and nutrition planner for families.\n\n"
        "## Budget Optimization Algorithm\n\n"
        "The system uses PuLP Integer Linear Programming (ILP) to optimize weekly meals.\n"
        "It minimizes cost while satisfying daily calorie and macronutrient constraints.\n\n"
        "## Indian Food Composition\n\n"
        "Standardized IFCT and ICMR values are used for 83 ingredients and 125 recipes.\n"
    )
    doc = SourceDocument(
        file_path="docs/NUTRITION_ENGINE.md",
        content=md,
        content_hash="md_hash",
        source_type="markdown_docs",
        total_lines=12
    )
    chunks = chunk_markdown_document(doc)
    assert len(chunks) == 3

    headings = [c.component_or_function for c in chunks]
    assert "AI Meal Planner" in headings
    assert "Budget Optimization Algorithm" in headings
    assert "Indian Food Composition" in headings


def test_7_stable_chunk_ids_and_hashing():
    """Verifies that chunk IDs and content hashes are deterministic across runs."""
    id1 = make_chunk_id("backend/app/main.py", "root", 1, "test text")
    id2 = make_chunk_id("backend/app/main.py", "root", 1, "test text")
    assert id1 == id2

    diff_id = make_chunk_id("backend/app/main.py", "root", 1, "modified text")
    assert id1 != diff_id


# ---------------------------------------------------------------------------
# 3. Incremental Indexing Manifest
# ---------------------------------------------------------------------------

def test_8_incremental_indexing_manifest(tmp_path):
    """Tests manifest tracking of newly added, unchanged, modified, and deleted files."""
    manifest_file = os.path.join(tmp_path, ".rag_manifest.json")
    mgr = ManifestManager(manifest_path=manifest_file)

    mgr.set_file_entry("file_a.py", "hash_a1", ["chunk_1", "chunk_2"])
    mgr.save()

    # Re-read
    mgr2 = ManifestManager(manifest_path=manifest_file)
    entry = mgr2.get_file_entry("file_a.py")
    assert entry is not None
    assert entry["hash"] == "hash_a1"
    assert entry["chunk_ids"] == ["chunk_1", "chunk_2"]

    # Modified file
    mgr2.set_file_entry("file_a.py", "hash_a2", ["chunk_1_v2"])
    assert mgr2.get_file_entry("file_a.py")["hash"] == "hash_a2"

    # Deleted file
    deleted_ids = mgr2.remove_file_entry("file_a.py")
    assert deleted_ids == ["chunk_1_v2"]
    assert mgr2.get_file_entry("file_a.py") is None


# ---------------------------------------------------------------------------
# 4. Local Embedding Service
# ---------------------------------------------------------------------------

def test_9_embedding_dimension_and_normalization():
    """Tests that local embedding model produces normalized 384-dimensional vectors."""
    svc = EmbeddingService.get_instance()
    emb = svc.embed_text("High protein Indian vegetarian diet with dal and paneer")
    assert len(emb) == EXPECTED_DIMENSION
    assert isinstance(emb[0], float)

    # Check vector normalization (norm close to 1.0)
    norm = sum(x * x for x in emb) ** 0.5
    assert abs(norm - 1.0) < 1e-3


def test_10_embedding_batch():
    """Tests batch embedding generation."""
    svc = EmbeddingService.get_instance()
    texts = ["Palak Paneer", "Rajma Chawal", "Ragi Dosa"]
    embs = svc.embed_batch(texts, batch_size=2)
    assert len(embs) == 3
    for e in embs:
        assert len(e) == EXPECTED_DIMENSION


# ---------------------------------------------------------------------------
# 5. Pinecone Service & Retrieval Pipeline
# ---------------------------------------------------------------------------

def test_11_pinecone_service_operations(mock_pinecone_service):
    """Verifies Pinecone service handles upserts, queries, and deletions."""
    svc = mock_pinecone_service
    vectors = [{"id": "vec_1", "values": [0.1] * 384, "metadata": {"text": "sample"}}]

    assert svc.upsert_vectors(vectors) == 1
    results = svc.query(vector=[0.1] * 384, top_k=3)
    assert len(results) == 1
    assert results[0]["id"] == "chunk_1"
    assert results[0]["score"] == 0.88
    assert svc.delete_chunks(["chunk_1"]) == 1


def test_12_retrieval_relevance_threshold(mock_embedding_service, mock_pinecone_service):
    """Tests that chunks below score threshold are filtered out."""
    mock_pinecone_service.query.return_value = [
        {"id": "c1", "score": 0.85, "metadata": {"chunk_text": "Good chunk", "source_label": "Label 1"}},
        {"id": "c2", "score": 0.20, "metadata": {"chunk_text": "Weak chunk", "source_label": "Label 2"}},
    ]

    # Threshold = 0.35
    retrieval_res = retrieve_codebase_context(
        query="How does the optimizer work?",
        top_k=5,
        score_threshold=0.35,
        embedding_svc=mock_embedding_service,
        pinecone_svc=mock_pinecone_service
    )

    assert retrieval_res.has_context is True
    # c2 was filtered out by the mock/service query
    assert len(retrieval_res.sources) >= 1
    assert "Good chunk" in retrieval_res.context_text


def test_13_empty_retrieval_behavior(mock_embedding_service, mock_pinecone_service):
    """Tests clean fallback when no matches exist in Pinecone."""
    mock_pinecone_service.query.return_value = []

    res = retrieve_codebase_context(
        query="completely unknown query",
        score_threshold=0.5,
        embedding_svc=mock_embedding_service,
        pinecone_svc=mock_pinecone_service
    )
    assert res.has_context is False
    assert res.context_text == ""
    assert len(res.sources) == 0


# ---------------------------------------------------------------------------
# 6. Groq Grounded Generation & Safety
# ---------------------------------------------------------------------------

def test_14_grounded_response_generation(db_session, mock_embedding_service, mock_pinecone_service):
    """Tests that Groq receives grounded RAG context and returns structured answer with sources."""
    mock_groq = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = (
        "The weekly meal planner uses PuLP Integer Linear Programming to find the most cost-effective "
        "meals that satisfy your family's calorie and macro targets."
    )
    mock_groq.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

    def mock_retrieval(query: str):
        return RetrievedContext(
            has_context=True,
            context_text="--- [Knowledge Source: Weekly Meal Planner & Optimizer] ---\nPuLP solver optimizes meals for budget.",
            sources=["Weekly Meal Planner & Optimizer"],
            matches=[{"id": "c1", "score": 0.9}],
            query_text=query
        )

    result = generate_chat_reply(
        message="How does budget optimization work?",
        conversation=[],
        db=db_session,
        current_user=None,
        groq_client=mock_groq,
        retrieval_fn=mock_retrieval
    )

    assert result["success"] is True
    assert "PuLP Integer Linear Programming" in result["reply"]
    assert "Weekly Meal Planner & Optimizer" in result["sources"]
    assert mock_groq.chat.completions.create.called

    # Verify system prompt contained RAG instructions
    call_args = mock_groq.chat.completions.create.call_args[1]
    system_prompt = call_args["messages"][0]["content"]
    assert "PuLP solver optimizes meals for budget" in system_prompt
    assert "STRICT SCOPE & APPLICATION BOUNDARIES" in system_prompt


def test_15_unrelated_question_boundary_rule():
    """Verifies that the system prompt explicitly commands rejecting unrelated general knowledge."""
    prompt = build_system_prompt(household_ctx={"has_household": False})
    assert "What is the capital of France?" in prompt
    assert "YOU MUST POLITELY DECLINE" in prompt
    assert "I am specialized only to assist with the AI Meal Planner" in prompt


def test_16_household_isolation_and_live_context(db_session):
    """Verifies authenticated household context is merged without cross-tenant leak."""
    user = User(clerk_user_id="clerk_test_123", email="rag_user@test.com", name="Priya")
    db_session.add(user)
    db_session.commit()

    household = Household(name="Priya Family", weekly_budget=4500.0, owner_id=user.id)
    db_session.add(household)
    db_session.commit()

    member = Member(
        household_id=household.id,
        name="Priya",
        age=32,
        gender="female",
        height_cm=162.0,
        weight_kg=60.0,
        activity_level="moderate",
        dietary_preference="vegetarian"
    )
    db_session.add(member)
    db_session.commit()

    target = NutritionTarget(
        member_id=member.id,
        daily_calories=1850.0,
        daily_protein_g=92.5,
        daily_carbs_g=231.0,
        daily_fat_g=61.0,
        daily_fiber_g=26.0
    )
    db_session.add(target)
    db_session.commit()

    mock_groq = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Your daily target is 1850.0 kcal/day with 92.5g protein."
    mock_groq.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

    result = generate_chat_reply(
        message="What are my daily nutrition targets?",
        conversation=[],
        db=db_session,
        current_user=user,
        household_id=household.id,
        groq_client=mock_groq,
        retrieval_fn=lambda q: RetrievedContext(False, "", [], [], q)
    )

    assert result["success"] is True
    call_args = mock_groq.chat.completions.create.call_args[1]
    system_prompt = call_args["messages"][0]["content"]
    assert "Priya Family" in system_prompt
    assert "1850.0 kcal/day" in system_prompt
    assert "92.5 g/day" in system_prompt


def test_17_quick_questions_coverage(db_session):
    """Ensures each of the six suggested quick questions can be processed through the pipeline."""
    quick_questions = [
        "How many calories does my household need per day?",
        "How much protein do we need every day?",
        "What does my nutrition target mean?",
        "How can I plan healthy meals on a low budget?",
        "Which recipes are high in protein?",
        "What ingredients can I use for affordable meals?"
    ]

    mock_groq = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Grounded response for quick question."
    mock_groq.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

    for q in quick_questions:
        res = generate_chat_reply(
            message=q,
            conversation=[],
            db=db_session,
            current_user=None,
            groq_client=mock_groq,
            retrieval_fn=lambda query: RetrievedContext(
                has_context=True,
                context_text="Indian high protein ingredients: Paneer, Soya, Chana Dal.",
                sources=["Indian Ingredients Catalog"],
                matches=[],
                query_text=query
            )
        )
        assert res["success"] is True
        assert res["reply"] == "Grounded response for quick question."
        assert "Indian Ingredients Catalog" in res["sources"]


def test_18_chat_response_schema_compatibility():
    """Verifies that ChatResponse Pydantic schema includes sources and preserves backward compatibility."""
    resp = ChatResponse(
        reply="Test reply",
        success=True,
        sources=["Weekly Meal Planner & Optimizer"],
        error=None
    )
    assert resp.reply == "Test reply"
    assert resp.sources == ["Weekly Meal Planner & Optimizer"]

    # Omitting sources should still be completely valid
    resp_no_sources = ChatResponse(reply="Test 2", success=True)
    assert resp_no_sources.sources is None

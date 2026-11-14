"""Verification Script for Groq-Powered RAG Answer Generation.

Tests:
Phase 2: 6 In-Scope Domain Queries
Phase 3: 3 Out-of-Scope Queries
Inspects similarity scores, retrieved sources, Groq generation, and grounding against Pinecone context.
"""
import os
import sys
import dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Load environment
dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from app.core.database import Base
from app.services.chat_service import generate_chat_reply
from app.rag.retrieval import retrieve_codebase_context
from app.services.embedding_service import EmbeddingService
from app.services.pinecone_service import PineconeService

IN_SCOPE_QUERIES = [
    "What is AI Meal Planner and who is it designed for?",
    "How does the household meal planning system work?",
    "How does the application optimize meals according to a weekly budget?",
    "What nutritional information does the application consider?",
    "How does the meal swap feature work?",
    "Which technologies are used in this project?"
]

OUT_OF_SCOPE_QUERIES = [
    "Who won yesterday's cricket match?",
    "Write me a Java program to reverse a string.",
    "What is the capital of France?"
]


def setup_in_memory_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    return Session()


def test_rag_generation():
    db = setup_in_memory_db()
    emb_svc = EmbeddingService.get_instance()
    pc_svc = PineconeService()

    print("=" * 80)
    print("      GROQ-POWERED RAG ANSWER GENERATION AUDIT & BENCHMARK")
    print("=" * 80)
    print(f"Pinecone Index:     {pc_svc.index_name}")
    print(f"Target Namespace:   {pc_svc.namespace}")
    print(f"Embedding Model:    {emb_svc.model_name}")
    print(f"Groq Model:         {os.getenv('GROQ_MODEL')}")
    print("=" * 80 + "\n")

    # -------------------------------------------------------------
    # PHASE 2: In-Scope Domain Queries
    # -------------------------------------------------------------
    print("=" * 80)
    print("PHASE 2: TESTING 6 IN-SCOPE DOMAIN QUERIES")
    print("=" * 80)

    for idx, q in enumerate(IN_SCOPE_QUERIES, 1):
        print("\n" + "*" * 75)
        print(f"[IN-SCOPE {idx}] Query: \"{q}\"")
        print("*" * 75)

        # 1. Inspect retrieval directly
        retrieval = retrieve_codebase_context(q, top_k=5, score_threshold=0.0)
        top_matches = retrieval.matches[:5]
        print(f"Top 5 Retrieval Scores: {[round(m['score'], 4) for m in top_matches]}")
        print("Retrieved Sources:")
        for m in top_matches:
            meta = m.get("metadata", {})
            print(f"  - [{m['score']:.4f}] {meta.get('file_path')} (L{meta.get('start_line')}-L{meta.get('end_line')}): {meta.get('component_or_function')}")

        # 2. Generate answer via full chat_service pipeline
        reply_res = generate_chat_reply(
            message=q,
            conversation=[],
            db=db,
            current_user=None
        )

        print("\nGenerated Groq Answer:")
        print(reply_res.get("reply"))
        print("\nSource Badges:", reply_res.get("sources"))
        print("-" * 75)

    # -------------------------------------------------------------
    # PHASE 3: Out-of-Scope Queries
    # -------------------------------------------------------------
    print("\n\n" + "=" * 80)
    print("PHASE 3: TESTING 3 OUT-OF-SCOPE / UNRELATED QUERIES")
    print("=" * 80)

    for idx, q in enumerate(OUT_OF_SCOPE_QUERIES, 1):
        print("\n" + "*" * 75)
        print(f"[OUT-OF-SCOPE {idx}] Query: \"{q}\"")
        print("*" * 75)

        # 1. Inspect retrieval scores
        retrieval = retrieve_codebase_context(q, top_k=5, score_threshold=0.0)
        top_matches = retrieval.matches[:5]
        print(f"Top 5 Retrieval Scores: {[round(m['score'], 4) for m in top_matches]}")
        print("Retrieved Sources (Notice the weak similarity scores):")
        for m in top_matches:
            meta = m.get("metadata", {})
            print(f"  - [{m['score']:.4f}] {meta.get('file_path')}: {meta.get('component_or_function')}")

        # 2. Generate answer via full chat_service pipeline
        reply_res = generate_chat_reply(
            message=q,
            conversation=[],
            db=db,
            current_user=None
        )

        print("\nGenerated Groq Answer:")
        print(reply_res.get("reply"))
        print("\nSource Badges:", reply_res.get("sources"))
        print("-" * 75)


if __name__ == "__main__":
    test_rag_generation()

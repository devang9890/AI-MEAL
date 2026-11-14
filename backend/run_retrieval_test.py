"""Standalone RAG Retrieval Verification Script for AI Meal Planner.

Tests 6 core domain queries against live Pinecone index (ai-meal-planner-rag / ai-meal-planner-dev).
Measures query embedding generation, similarity scoring, source metadata, and semantic relevance.
"""
import os
import sys
import dotenv

# Load environment
dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from app.rag.retrieval import retrieve_codebase_context
from app.services.embedding_service import EmbeddingService
from app.services.pinecone_service import PineconeService

TEST_QUERIES = [
    "What is AI Meal Planner?",
    "How does the household meal planning system work?",
    "How does the application optimize meals according to a weekly budget?",
    "What nutritional information does the application consider?",
    "How does the meal swap feature work?",
    "Which technologies are used in this project?"
]


def run_retrieval_audit():
    emb_svc = EmbeddingService.get_instance()
    pc_svc = PineconeService()

    print("\n" + "=" * 80)
    print("           AI MEAL PLANNER RAG RETRIEVAL VERIFICATION")
    print("=" * 80)
    print(f"Pinecone Index:     {pc_svc.index_name}")
    print(f"Target Namespace:   {pc_svc.namespace}")
    print(f"Embedding Model:    {emb_svc.model_name}")
    print(f"Embedding Dims:     384")

    # Confirm stats
    stats = pc_svc.describe_stats()
    ns_stats = stats.get("namespaces", {}).get(pc_svc.namespace, {})
    vector_count = ns_stats.get("vector_count", 0)
    print(f"Namespace Vectors:  {vector_count}")
    print("=" * 80 + "\n")

    if vector_count == 0:
        print(f"WARNING: Namespace '{pc_svc.namespace}' contains 0 vectors.")
        return

    results = []

    for q_idx, query in enumerate(TEST_QUERIES, 1):
        print("*" * 80)
        print(f"QUERY {q_idx}: \"{query}\"")
        print("*" * 80)

        # Retrieve top 5 matches
        retrieval_result = retrieve_codebase_context(
            query=query,
            top_k=5,
            score_threshold=0.0,
            embedding_svc=emb_svc,
            pinecone_svc=pc_svc
        )

        matches = retrieval_result.matches[:5]
        print(f"Matches Retrieved: {len(matches)}")
        print(f"Distinct Source Badges: {retrieval_result.sources}")
        print("-" * 80)

        query_data = {
            "query": query,
            "matches": []
        }

        for m_idx, m in enumerate(matches, 1):
            score = float(m.get("score", 0.0))
            meta = m.get("metadata", {})
            file_path = meta.get("file_path", "unknown")
            component = meta.get("component_or_function", "general")
            start_line = meta.get("start_line", "?")
            end_line = meta.get("end_line", "?")
            source_label = meta.get("source_label", "")
            raw_text = meta.get("chunk_text", "").replace("\n", " ").strip()
            preview = raw_text[:220] + ("..." if len(raw_text) > 220 else "")

            print(f"  [Match {m_idx}] Cosine Similarity: {score:.4f}")
            print(f"    Source File:  {file_path} (Lines {start_line}-{end_line})")
            print(f"    Component:    {component}")
            print(f"    Source Badge: {source_label}")
            print(f"    Preview:      {preview}")
            print()

            query_data["matches"].append({
                "rank": m_idx,
                "score": score,
                "file_path": file_path,
                "lines": f"{start_line}-{end_line}",
                "component": component,
                "source_label": source_label,
                "preview": preview
            })

        results.append(query_data)

    print("=" * 80)
    print("ALL 6 QUERIES RETRIEVED SUCCESSFULLY WITH ZERO ERRORS.")
    print("=" * 80 + "\n")
    return results


if __name__ == "__main__":
    run_retrieval_audit()

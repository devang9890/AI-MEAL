"""Retrieval Pipeline for AI Meal Planner Codebase RAG.

Embeds user queries with the local MiniLM model, queries Pinecone vector database,
applies relevance thresholds and deduplication, and formats grounded context for Groq.
"""
import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from app.services.embedding_service import EmbeddingService
from app.services.pinecone_service import PineconeService

logger = logging.getLogger(__name__)

DEFAULT_TOP_K = 5
DEFAULT_SCORE_THRESHOLD = 0.28


@dataclass
class RetrievedContext:
    """Holds formatted retrieved context for LLM grounding."""
    has_context: bool
    context_text: str
    sources: List[str]
    matches: List[Dict[str, Any]]
    query_text: str


def retrieve_codebase_context(
    query: str,
    top_k: Optional[int] = None,
    score_threshold: Optional[float] = None,
    embedding_svc: Optional[EmbeddingService] = None,
    pinecone_svc: Optional[PineconeService] = None
) -> RetrievedContext:
    """
    Retrieves grounded codebase knowledge from Pinecone for a given user query.
    """
    clean_query = query.strip() if query else ""
    if not clean_query:
        return RetrievedContext(
            has_context=False,
            context_text="",
            sources=[],
            matches=[],
            query_text=query
        )

    # Resolve settings from environment
    k = top_k if top_k is not None else int(os.getenv("RAG_TOP_K", str(DEFAULT_TOP_K)))
    threshold = score_threshold if score_threshold is not None else float(
        os.getenv("RAG_SCORE_THRESHOLD", str(DEFAULT_SCORE_THRESHOLD))
    )

    pc_service = pinecone_svc or PineconeService()
    if not pc_service.is_configured():
        logger.warning("Pinecone is not configured. Proceeding without vector retrieval.")
        return RetrievedContext(
            has_context=False,
            context_text="",
            sources=[],
            matches=[],
            query_text=clean_query
        )

    # 1. Generate local query embedding
    emb_service = embedding_svc or EmbeddingService.get_instance()
    try:
        query_vector = emb_service.embed_text(clean_query)
    except Exception as exc:
        logger.error(f"Failed to generate query embedding: {exc}")
        return RetrievedContext(
            has_context=False,
            context_text="",
            sources=[],
            matches=[],
            query_text=clean_query
        )

    # 2. Query Pinecone
    try:
        matches = pc_service.query(
            vector=query_vector,
            top_k=k,
            score_threshold=threshold
        )
    except Exception as exc:
        logger.warning(f"Pinecone retrieval failed or index offline: {exc}")
        return RetrievedContext(
            has_context=False,
            context_text="",
            sources=[],
            matches=[],
            query_text=clean_query
        )

    if not matches:
        return RetrievedContext(
            has_context=False,
            context_text="",
            sources=[],
            matches=[],
            query_text=clean_query
        )

    # 3. Deduplicate and format context
    seen_hashes = set()
    context_blocks = []
    source_labels = []

    for match in matches:
        meta = match.get("metadata", {})
        c_hash = meta.get("content_hash") or match.get("id")
        if c_hash in seen_hashes:
            continue
        seen_hashes.add(c_hash)

        chunk_text = meta.get("chunk_text", "").strip()
        if not chunk_text:
            continue

        label = meta.get("source_label", "AI Meal Planner Documentation")
        if label not in source_labels:
            source_labels.append(label)

        score = match.get("score", 0.0)
        component = meta.get("component_or_function", "General")
        section = meta.get("section", "Module")

        block = (
            f"--- [Knowledge Source: {label} | Relevance: {score:.2f} | Topic: {component}] ---\n"
            f"{chunk_text}\n"
        )
        context_blocks.append(block)

    formatted_context = "\n".join(context_blocks).strip()

    return RetrievedContext(
        has_context=bool(context_blocks),
        context_text=formatted_context,
        sources=source_labels,
        matches=matches,
        query_text=clean_query
    )

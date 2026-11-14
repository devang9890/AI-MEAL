"""Pinecone Vector Database Service for AI Meal Planner RAG.

Handles index verification, creation with ServerlessSpec (384 dimensions, cosine metric),
batched upserting, similarity search, and stale chunk deletion.
"""
import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

DEFAULT_INDEX_NAME = "ai-meal-planner-rag"
DEFAULT_NAMESPACE = "ai-meal-planner-dev"
DEFAULT_CLOUD = "aws"
DEFAULT_REGION = "us-east-1"
INDEX_DIMENSION = 384
INDEX_METRIC = "cosine"


class PineconeService:
    """
    Manages connections and operations with the Pinecone Vector Database.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        index_name: Optional[str] = None,
        namespace: Optional[str] = None,
        cloud: Optional[str] = None,
        region: Optional[str] = None,
        client_instance: Optional[Any] = None,
        index_instance: Optional[Any] = None
    ):
        self.api_key = api_key or os.getenv("PINECONE_API_KEY", "").strip()
        self.index_name = index_name or os.getenv("PINECONE_INDEX_NAME", DEFAULT_INDEX_NAME).strip() or DEFAULT_INDEX_NAME
        self.namespace = namespace or os.getenv("PINECONE_NAMESPACE", DEFAULT_NAMESPACE).strip() or DEFAULT_NAMESPACE
        self.cloud = cloud or os.getenv("PINECONE_CLOUD", DEFAULT_CLOUD).strip() or DEFAULT_CLOUD
        self.region = region or os.getenv("PINECONE_REGION", DEFAULT_REGION).strip() or DEFAULT_REGION

        self._client = client_instance
        self._index = index_instance

    def is_configured(self) -> bool:
        """Returns True if Pinecone API key is provided or a mock client is injected."""
        return bool(self.api_key or self._client is not None or self._index is not None)

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client

        if not self.api_key:
            raise ValueError(
                "PINECONE_API_KEY is not configured in environment or backend/.env."
            )

        from pinecone import Pinecone
        self._client = Pinecone(api_key=self.api_key)
        return self._client

    def ensure_index_exists(self) -> bool:
        """
        Verifies that the target Pinecone index exists with 384 dims and cosine metric.
        If it does not exist, attempts to create it as a Serverless index.
        Returns True if index is ready, False otherwise.
        """
        if self._index is not None:
            return True

        try:
            client = self._get_client()

            # Check if index exists
            if hasattr(client, "has_index"):
                exists = client.has_index(self.index_name)
            else:
                existing_names = [i.name for i in client.list_indexes()]
                exists = self.index_name in existing_names

            if not exists:
                logger.info(
                    f"Creating Pinecone index '{self.index_name}' "
                    f"(dim={INDEX_DIMENSION}, metric={INDEX_METRIC}, cloud={self.cloud}, region={self.region})..."
                )
                from pinecone import ServerlessSpec
                client.create_index(
                    name=self.index_name,
                    dimension=INDEX_DIMENSION,
                    metric=INDEX_METRIC,
                    spec=ServerlessSpec(cloud=self.cloud, region=self.region)
                )
                logger.info(f"Pinecone index '{self.index_name}' created successfully.")

            return True
        except Exception as exc:
            logger.error(f"Error checking or creating Pinecone index '{self.index_name}': {exc}")
            return False

    def get_index(self) -> Any:
        """Returns the connected Pinecone Index instance."""
        if self._index is not None:
            return self._index

        client = self._get_client()
        self._index = client.Index(self.index_name)
        return self._index

    def upsert_vectors(
        self,
        vectors: List[Dict[str, Any]],
        namespace: Optional[str] = None,
        batch_size: int = 100
    ) -> int:
        """
        Upserts vectors into Pinecone in batches.
        Each vector item must have:
          - id: str
          - values: List[float] (384-dimensional)
          - metadata: Dict[str, Any]
        Returns count of successfully upserted vectors.
        """
        if not vectors:
            return 0

        target_namespace = namespace or self.namespace
        index = self.get_index()
        total_upserted = 0

        for i in range(0, len(vectors), batch_size):
            batch = vectors[i : i + batch_size]
            try:
                index.upsert(vectors=batch, namespace=target_namespace)
                total_upserted += len(batch)
            except Exception as exc:
                logger.error(f"Failed to upsert batch {i // batch_size + 1} to Pinecone: {exc}")
                raise

        return total_upserted

    def query(
        self,
        vector: List[float],
        top_k: int = 5,
        namespace: Optional[str] = None,
        score_threshold: Optional[float] = None,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Performs cosine similarity search against the Pinecone index.
        Returns a list of match dicts with keys: id, score, metadata.
        """
        target_namespace = namespace or self.namespace
        index = self.get_index()

        query_kwargs: Dict[str, Any] = {
            "vector": vector,
            "top_k": top_k,
            "include_metadata": True,
            "namespace": target_namespace
        }
        if filter_dict:
            query_kwargs["filter"] = filter_dict

        try:
            response = index.query(**query_kwargs)
        except Exception as exc:
            logger.error(f"Pinecone query error: {exc}")
            raise

        matches = []
        raw_matches = getattr(response, "matches", []) or response.get("matches", [])
        for match in raw_matches:
            # Handle object vs dictionary
            m_id = getattr(match, "id", None) or (match.get("id") if isinstance(match, dict) else "")
            m_score = getattr(match, "score", None) or (match.get("score") if isinstance(match, dict) else 0.0)
            m_meta = getattr(match, "metadata", None) or (match.get("metadata") if isinstance(match, dict) else {})

            if score_threshold is not None and m_score < score_threshold:
                continue

            matches.append({
                "id": m_id,
                "score": float(m_score),
                "metadata": dict(m_meta) if m_meta else {}
            })

        return matches

    def delete_chunks(self, chunk_ids: List[str], namespace: Optional[str] = None) -> int:
        """Deletes vectors by ID from Pinecone."""
        if not chunk_ids:
            return 0

        target_namespace = namespace or self.namespace
        index = self.get_index()

        try:
            index.delete(ids=chunk_ids, namespace=target_namespace)
            return len(chunk_ids)
        except Exception as exc:
            logger.error(f"Failed to delete {len(chunk_ids)} chunks from Pinecone: {exc}")
            raise

    def delete_all_in_namespace(self, namespace: Optional[str] = None) -> bool:
        """Deletes all vectors in the configured namespace (for full rebuilds)."""
        target_namespace = namespace or self.namespace
        index = self.get_index()

        try:
            index.delete(delete_all=True, namespace=target_namespace)
            return True
        except Exception as exc:
            logger.error(f"Failed to clear namespace '{target_namespace}' in Pinecone: {exc}")
            return False

    def describe_stats(self) -> Dict[str, Any]:
        """Returns statistics for the Pinecone index."""
        try:
            index = self.get_index()
            stats = index.describe_index_stats()
            if hasattr(stats, "to_dict"):
                return stats.to_dict()
            return dict(stats) if isinstance(stats, dict) else {"raw": str(stats)}
        except Exception as exc:
            logger.warning(f"Could not retrieve Pinecone index stats: {exc}")
            return {"error": str(exc)}

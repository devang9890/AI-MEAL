"""Local Embedding Service for AI Meal Planner RAG.

Uses sentence-transformers/all-MiniLM-L6-v2 running locally on CPU.
Produces 384-dimensional normalized vector embeddings for both
codebase document chunks and runtime user queries.
"""
import os
import logging
import threading
from typing import List, Optional, Any
import numpy as np

logger = logging.getLogger(__name__)

DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EXPECTED_DIMENSION = 384


class EmbeddingService:
    """
    Thread-safe Singleton Embedding Service.
    Caches the SentenceTransformer model locally so it is only loaded once per process.
    """
    _instance: Optional["EmbeddingService"] = None
    _lock = threading.Lock()

    def __init__(self, model_name: Optional[str] = None, model_instance: Optional[Any] = None):
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL_NAME", DEFAULT_MODEL_NAME).strip() or DEFAULT_MODEL_NAME
        self._model = model_instance
        self._init_lock = threading.Lock()

    @classmethod
    def get_instance(cls, model_name: Optional[str] = None, model_instance: Optional[Any] = None) -> "EmbeddingService":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(model_name=model_name, model_instance=model_instance)
        elif model_instance is not None:
            # Allow injecting a mock instance (useful in unit testing)
            cls._instance._model = model_instance
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Resets the singleton (primarily for testing)."""
        with cls._lock:
            cls._instance = None

    def _load_model(self) -> Any:
        if self._model is not None:
            return self._model

        with self._init_lock:
            if self._model is not None:
                return self._model

            logger.info(f"Loading local embedding model: {self.model_name} on CPU...")
            try:
                # Prefer offline cache to prevent unnecessary network polling
                cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
                cached_model_path = os.path.join(cache_dir, f"models--{self.model_name.replace('/', '--')}")
                if os.path.exists(cached_model_path):
                    os.environ.setdefault("HF_HUB_OFFLINE", "1")

                from sentence_transformers import SentenceTransformer
                model = SentenceTransformer(self.model_name, device="cpu")

                self._model = model
                logger.info("Local embedding model loaded successfully.")
                return self._model
            except Exception as exc:
                logger.error(f"Failed to load embedding model '{self.model_name}': {exc}", exc_info=True)
                raise RuntimeError(
                    f"Could not load local embedding model '{self.model_name}'. "
                    f"Ensure 'sentence-transformers' is installed and network/cache is accessible. Error: {exc}"
                ) from exc

    def embed_text(self, text: str) -> List[float]:
        """
        Generates a 384-dimensional normalized embedding vector for a single text string.
        """
        clean_text = text.strip() if text else ""
        if not clean_text:
            return [0.0] * EXPECTED_DIMENSION

        model = self._load_model()
        # normalize_embeddings=True produces unit vectors for cosine similarity
        embedding = model.encode(clean_text, normalize_embeddings=True, show_progress_bar=False)

        if isinstance(embedding, np.ndarray):
            vector = embedding.tolist()
        else:
            vector = list(embedding)

        if len(vector) != EXPECTED_DIMENSION:
            raise ValueError(
                f"Embedding dimension mismatch: expected {EXPECTED_DIMENSION}, got {len(vector)}"
            )

        return vector

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generates normalized embedding vectors for a batch of text strings.
        """
        if not texts:
            return []

        clean_texts = [t.strip() if t and t.strip() else " " for t in texts]
        model = self._load_model()

        embeddings = model.encode(
            clean_texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > 50
        )

        vectors: List[List[float]] = []
        for emb in embeddings:
            vec = emb.tolist() if isinstance(emb, np.ndarray) else list(emb)
            if len(vec) != EXPECTED_DIMENSION:
                raise ValueError(
                    f"Embedding dimension mismatch: expected {EXPECTED_DIMENSION}, got {len(vec)}"
                )
            vectors.append(vec)

        return vectors


# Convenience module-level functions
def get_embedding(text: str) -> List[float]:
    """Generates embedding for a single text using singleton service."""
    return EmbeddingService.get_instance().embed_text(text)


def get_embeddings(texts: List[str], batch_size: int = 32) -> List[List[float]]:
    """Generates embeddings for a batch of texts using singleton service."""
    return EmbeddingService.get_instance().embed_batch(texts, batch_size=batch_size)

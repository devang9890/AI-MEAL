"""Incremental Ingestion Pipeline for AI Meal Planner Codebase RAG.

Discovers project source files, applies exclusions, chunks code/docs semantically,
generates local MiniLM embeddings, and synchronizes with Pinecone vector database.
"""
import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import argparse
from dotenv import load_dotenv

# Ensure backend root is in sys.path when executed directly
backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
repo_root = os.path.abspath(os.path.join(backend_root, ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

# Load environment variables from backend/.env
env_path = os.path.join(backend_root, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)

from app.rag.source_loader import discover_source_files, SourceDocument
from app.rag.code_chunker import chunk_document, CodeChunk
from app.services.embedding_service import EmbeddingService, EXPECTED_DIMENSION
from app.services.pinecone_service import PineconeService

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

DEFAULT_MANIFEST_PATH = os.path.join(backend_root, ".rag_manifest.json")


class ManifestManager:
    """Manages the local JSON manifest tracking indexed file hashes and chunk IDs."""

    def __init__(self, manifest_path: str = DEFAULT_MANIFEST_PATH):
        self.manifest_path = manifest_path
        self.data: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if os.path.exists(self.manifest_path):
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as exc:
                logger.warning(f"Could not read manifest, starting fresh: {exc}")
        return {"files": {}, "last_ingested_at": None, "model": None}

    def save(self) -> None:
        try:
            with open(self.manifest_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except Exception as exc:
            logger.warning(f"Failed to write manifest: {exc}")

    def get_file_entry(self, rel_path: str) -> Optional[Dict[str, Any]]:
        return self.data.get("files", {}).get(rel_path)

    def set_file_entry(self, rel_path: str, file_hash: str, chunk_ids: List[str]) -> None:
        if "files" not in self.data:
            self.data["files"] = {}
        self.data["files"][rel_path] = {
            "hash": file_hash,
            "chunk_ids": chunk_ids,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

    def remove_file_entry(self, rel_path: str) -> Optional[List[str]]:
        if "files" in self.data and rel_path in self.data["files"]:
            old_ids = self.data["files"][rel_path].get("chunk_ids", [])
            del self.data["files"][rel_path]
            return old_ids
        return None

    def clear(self) -> None:
        self.data = {"files": {}, "last_ingested_at": None, "model": None}
        self.save()


def run_ingestion(
    rebuild: bool = False,
    dry_run: bool = False,
    target_repo_root: Optional[str] = None,
    manifest_path: Optional[str] = None,
    pinecone_svc: Optional[PineconeService] = None,
    embedding_svc: Optional[EmbeddingService] = None
) -> Dict[str, Any]:
    """
    Executes incremental or full RAG ingestion.
    """
    active_repo_root = target_repo_root or repo_root
    manifest = ManifestManager(manifest_path or DEFAULT_MANIFEST_PATH)

    if rebuild:
        logger.info("Rebuild requested: clearing local manifest and wiping namespace...")
        manifest.clear()

    # 1. Discover source files
    eligible_docs, discovery_stats = discover_source_files(active_repo_root)

    # 2. Check changes against manifest
    new_or_modified_docs: List[SourceDocument] = []
    unchanged_files = 0
    stale_chunk_ids_to_delete: List[str] = []

    current_file_paths = {doc.file_path for doc in eligible_docs}
    manifest_files = list(manifest.data.get("files", {}).keys())

    # Detect deleted files
    for old_path in manifest_files:
        if old_path not in current_file_paths:
            old_chunk_ids = manifest.remove_file_entry(old_path) or []
            stale_chunk_ids_to_delete.extend(old_chunk_ids)

    # Categorize eligible docs
    for doc in eligible_docs:
        entry = manifest.get_file_entry(doc.file_path)
        if entry is None:
            # Newly added file
            new_or_modified_docs.append(doc)
        elif entry.get("hash") != doc.content_hash:
            # Modified file: collect old chunk IDs to delete
            stale_chunk_ids_to_delete.extend(entry.get("chunk_ids", []))
            new_or_modified_docs.append(doc)
        else:
            unchanged_files += 1

    # 3. Chunk new and modified files
    new_chunks: List[CodeChunk] = []
    file_to_chunks_map: Dict[str, List[str]] = {}

    for doc in new_or_modified_docs:
        doc_chunks = chunk_document(doc)
        new_chunks.extend(doc_chunks)
        file_to_chunks_map[doc.file_path] = [c.chunk_id for c in doc_chunks]

    total_chunks_created = len(new_chunks)

    # Initialize services
    emb_service = embedding_svc or EmbeddingService.get_instance()
    pc_service = pinecone_svc or PineconeService()

    summary: Dict[str, Any] = {
        "files_discovered": discovery_stats["files_discovered"],
        "files_eligible": discovery_stats["files_eligible"],
        "files_excluded": discovery_stats["files_excluded"],
        "unchanged_files": unchanged_files,
        "new_or_modified_files": len(new_or_modified_docs),
        "chunks_created": total_chunks_created,
        "new_chunks_indexed": 0,
        "updated_chunks": 0,
        "deleted_stale_chunks": len(stale_chunk_ids_to_delete),
        "embedding_model": emb_service.model_name,
        "vector_dimension": EXPECTED_DIMENSION,
        "pinecone_index": pc_service.index_name,
        "pinecone_namespace": pc_service.namespace,
        "status": "SUCCESS"
    }

    # If dry run, return summary without modifying Pinecone
    if dry_run:
        summary["status"] = "SUCCESS (DRY RUN)"
        _print_summary(summary)
        return summary

    # Check Pinecone configuration
    if not pc_service.is_configured():
        summary["status"] = "PENDING_API_KEY (Pinecone API key not configured in backend/.env)"
        _print_summary(summary)
        return summary

    # Verify / Create Pinecone index
    index_ready = pc_service.ensure_index_exists()
    if not index_ready:
        summary["status"] = "FAILED (Could not connect to or create Pinecone index)"
        _print_summary(summary)
        return summary

    # If rebuild, clear namespace in Pinecone
    if rebuild:
        pc_service.delete_all_in_namespace()
        stale_chunk_ids_to_delete.clear()

    # Delete stale chunks from Pinecone if any
    if stale_chunk_ids_to_delete:
        try:
            pc_service.delete_chunks(stale_chunk_ids_to_delete)
        except Exception as exc:
            logger.warning(f"Could not delete some stale chunks: {exc}")

    # 4. Generate local embeddings and upsert
    if new_chunks:
        logger.info(f"Generating local embeddings for {len(new_chunks)} chunks...")
        chunk_texts = [c.chunk_text for c in new_chunks]
        embeddings = emb_service.embed_batch(chunk_texts, batch_size=32)

        vectors_to_upsert: List[Dict[str, Any]] = []
        for chunk, emb in zip(new_chunks, embeddings):
            vectors_to_upsert.append({
                "id": chunk.chunk_id,
                "values": emb,
                "metadata": chunk.to_pinecone_metadata()
            })

        logger.info(f"Upserting {len(vectors_to_upsert)} vectors to Pinecone index '{pc_service.index_name}'...")
        upserted_count = pc_service.upsert_vectors(vectors_to_upsert, batch_size=100)
        summary["new_chunks_indexed"] = upserted_count

        # Update manifest for processed docs
        for doc in new_or_modified_docs:
            c_ids = file_to_chunks_map.get(doc.file_path, [])
            manifest.set_file_entry(doc.file_path, doc.content_hash, c_ids)

        manifest.data["last_ingested_at"] = datetime.now(timezone.utc).isoformat()
        manifest.data["model"] = emb_service.model_name
        manifest.save()
    else:
        logger.info("All eligible files are up-to-date in manifest. No new embeddings required.")
        summary["status"] = "SUCCESS (UP TO DATE)"

    _print_summary(summary)
    return summary


def _print_summary(summary: Dict[str, Any]) -> None:
    """Prints a clear, structured summary block matching user specification."""
    print("\n" + "=" * 55)
    print("      AI MEAL PLANNER CODEBASE RAG INGESTION")
    print("=" * 55)
    print(f"Files discovered:     {summary.get('files_discovered', 0)}")
    print(f"Files eligible:       {summary.get('files_eligible', 0)}")
    print(f"Files excluded:       {summary.get('files_excluded', 0)}")
    print(f"Chunks created:       {summary.get('chunks_created', 0)}")
    print(f"New chunks indexed:   {summary.get('new_chunks_indexed', 0)}")
    print(f"Updated chunks:       {summary.get('updated_chunks', 0)}")
    print(f"Deleted stale chunks: {summary.get('deleted_stale_chunks', 0)}")
    print(f"Embedding model:      {summary.get('embedding_model', '')}")
    print(f"Vector dimension:     {summary.get('vector_dimension', 384)}")
    print(f"Pinecone index:       {summary.get('pinecone_index', '')}")
    print(f"Pinecone namespace:   {summary.get('pinecone_namespace', '')}")
    print(f"Status:               {summary.get('status', 'SUCCESS')}")
    print("=" * 55 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Ingest AI Meal Planner codebase into Pinecone RAG.")
    parser.add_argument("--rebuild", action="store_true", help="Wipe manifest and rebuild entire vector index.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate discovery and chunking without calling Pinecone.")
    args = parser.parse_args()

    run_ingestion(rebuild=args.rebuild, dry_run=args.dry_run)


if __name__ == "__main__":
    main()

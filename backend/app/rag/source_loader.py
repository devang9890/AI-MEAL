"""Source File Discovery and Extraction for AI Meal Planner Codebase RAG.

Scans frontend, backend, and documentation files while enforcing strict
exclusion of secrets, environments, build artifacts, and binaries.
"""
import os
import re
import hashlib
import logging
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Excluded directories
EXCLUDED_DIRS: Set[str] = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "__pycache__",
    "dist",
    "build",
    "coverage",
    ".coverage",
    ".pytest_cache",
    ".vite",
    ".vscode",
    ".idea",
    "SCREENSHOTS",
    "htmlcov",
    ".tox",
    ".nox"
}

# Excluded file names & patterns
EXCLUDED_FILE_PATTERNS: Set[str] = {
    ".env",
    ".env.example",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    ".rag_manifest.json",
    ".DS_Store",
    "Thumbs.db"
}

# Excluded extensions (binaries, media, compiled, fonts, locks)
EXCLUDED_EXTENSIONS: Set[str] = {
    ".pyc", ".pyo", ".pyd", ".png", ".jpg", ".jpeg", ".gif", ".svg",
    ".ico", ".webp", ".pdf", ".mp4", ".zip", ".tar", ".gz", ".db",
    ".sqlite3", ".log", ".woff", ".woff2", ".ttf", ".eot"
}

# Allowed extensions to inspect
ALLOWED_EXTENSIONS: Set[str] = {
    ".py", ".jsx", ".js", ".md", ".html", ".css", ".json"
}

# High-priority directories to index
INCLUDED_ROOT_PATHS = [
    "backend/app",
    "frontend/src",
    "docs",
    "README.md",
    "RUNBOOK.md",
    "frontend/index.html",
    "frontend/vite.config.js"
]

# Sensitive patterns that should NEVER be indexed (redacted on the fly)
SECRET_REGEXES = [
    (re.compile(r'gsk_[A-Za-z0-9_-]{20,}'), '[REDACTED_GROQ_KEY]'),
    (re.compile(r'sk_test_[A-Za-z0-9_-]{15,}'), '[REDACTED_CLERK_SECRET]'),
    (re.compile(r'sk_live_[A-Za-z0-9_-]{15,}'), '[REDACTED_CLERK_SECRET]'),
    (re.compile(r'pk_test_[A-Za-z0-9_\$]{20,}'), '[REDACTED_CLERK_PUBKEY]'),
    (re.compile(r'pk_live_[A-Za-z0-9_\$]{20,}'), '[REDACTED_CLERK_PUBKEY]'),
    (re.compile(r'pcsk_[A-Za-z0-9_-]{20,}'), '[REDACTED_PINECONE_KEY]'),
    (re.compile(r'postgresql(?:\+[a-z0-9]+)?://[^:\s]+:[^@\s]+@[^\s]+'), '[REDACTED_DATABASE_URL]'),
]


@dataclass
class SourceDocument:
    """Represents a discovered and sanitized source document."""
    file_path: str               # Normalized relative path (e.g. backend/app/main.py)
    content: str                 # Sanitized text content
    content_hash: str            # SHA-256 hash of sanitized content
    source_type: str             # e.g. python_backend, react_frontend, markdown_docs
    total_lines: int


def sanitize_content(raw_text: str, file_path: str = "") -> str:
    """
    Sanitizes raw text to ensure no real secrets or credentials leak into RAG chunks.
    """
    sanitized = raw_text
    for pattern, replacement in SECRET_REGEXES:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


def determine_source_type(rel_path: str) -> str:
    """Categorizes the file based on path and extension."""
    norm_path = rel_path.replace("\\", "/")
    if norm_path.startswith("backend/app/"):
        return "python_backend"
    elif norm_path.startswith("frontend/src/"):
        return "react_frontend"
    elif norm_path.startswith("docs/") or norm_path.endswith(".md"):
        return "markdown_docs"
    elif norm_path.endswith(".html"):
        return "html_entry"
    elif "config" in norm_path or norm_path.endswith(".json"):
        return "config_file"
    return "general_source"


def is_file_excluded(rel_path: str) -> Tuple[bool, str]:
    """
    Checks whether a file should be excluded from indexing.
    Returns (is_excluded, reason).
    """
    norm_path = rel_path.replace("\\", "/")
    parts = norm_path.split("/")
    filename = parts[-1]
    name_lower = filename.lower()

    # Directory exclusion check
    for part in parts[:-1]:
        if part in EXCLUDED_DIRS:
            return True, f"in excluded directory '{part}'"

    # Environment and secret files check (CRITICAL)
    if name_lower.startswith(".env") or name_lower == ".env":
        return True, "environment secret file"

    # Specific file patterns
    if filename in EXCLUDED_FILE_PATTERNS:
        return True, "excluded filename pattern"

    # Extension check
    _, ext = os.path.splitext(filename)
    ext_lower = ext.lower()

    if ext_lower in EXCLUDED_EXTENSIONS:
        return True, f"excluded extension '{ext_lower}'"

    if ext_lower not in ALLOWED_EXTENSIONS:
        return True, f"extension '{ext_lower}' not in allowed set"

    # Alembic migrations are auto-generated boilerplate, exclude them to focus on application logic
    if "alembic/versions" in norm_path:
        return True, "auto-generated database migration file"

    return False, ""


def discover_source_files(repo_root: str) -> Tuple[List[SourceDocument], Dict[str, int]]:
    """
    Scans the repository root and loads eligible source documents.
    Returns:
        (eligible_documents, stats_dict)
    """
    stats = {
        "files_discovered": 0,
        "files_eligible": 0,
        "files_excluded": 0
    }
    eligible_docs: List[SourceDocument] = []

    for dirpath, dirnames, filenames in os.walk(repo_root):
        # Prune excluded directories in-place so os.walk skips descending into them
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]

        for fname in filenames:
            stats["files_discovered"] += 1
            full_path = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(full_path, repo_root).replace("\\", "/")

            excluded, reason = is_file_excluded(rel_path)
            if excluded:
                stats["files_excluded"] += 1
                continue

            # Must be within included paths
            is_relevant = any(
                rel_path == p or rel_path.startswith(p.rstrip("/") + "/")
                for p in INCLUDED_ROOT_PATHS
            )
            if not is_relevant:
                stats["files_excluded"] += 1
                continue

            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()

                # Basic content length filter (ignore completely empty files)
                if not content.strip():
                    stats["files_excluded"] += 1
                    continue

                sanitized = sanitize_content(content, rel_path)
                content_hash = hashlib.sha256(sanitized.encode("utf-8")).hexdigest()
                source_type = determine_source_type(rel_path)
                line_count = len(sanitized.splitlines())

                eligible_docs.append(SourceDocument(
                    file_path=rel_path,
                    content=sanitized,
                    content_hash=content_hash,
                    source_type=source_type,
                    total_lines=line_count
                ))
                stats["files_eligible"] += 1

            except Exception as exc:
                logger.warning(f"Could not read source file '{rel_path}': {exc}")
                stats["files_excluded"] += 1

    return eligible_docs, stats

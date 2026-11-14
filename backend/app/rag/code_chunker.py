"""Code-aware and Markdown-aware Chunking for AI Meal Planner Codebase RAG.

Extracts syntactically coherent chunks from Python ASTs, React JSX components,
and Markdown documentation sections with stable chunk IDs and metadata.
"""
import ast
import re
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from app.rag.source_loader import SourceDocument

MAX_CHUNK_CHARS = 1600
MIN_CHUNK_CHARS = 20


@dataclass
class CodeChunk:
    """Represents a chunk extracted from a source document."""
    chunk_id: str
    file_path: str
    source_type: str
    component_or_function: str
    section: str
    start_line: int
    end_line: int
    content_hash: str
    indexed_at: str
    chunk_text: str
    source_label: str

    def to_pinecone_metadata(self) -> Dict[str, Any]:
        """Converts chunk into Pinecone metadata dictionary."""
        return {
            "chunk_id": self.chunk_id,
            "file_path": self.file_path,
            "source_type": self.source_type,
            "component_or_function": self.component_or_function,
            "section": self.section,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "content_hash": self.content_hash,
            "indexed_at": self.indexed_at,
            "chunk_text": self.chunk_text,
            "source_label": self.source_label
        }


def generate_source_label(file_path: str, component_or_func: str) -> str:
    """
    Generates a clean, user-friendly source label that hides internal file systems.
    E.g.: 'Weekly Meal Plan Optimizer' or 'Indian Food Database'.
    """
    path_lower = file_path.lower()
    if "optimizer.py" in path_lower or "meal_plan" in path_lower:
        return "Weekly Meal Planner & Optimizer"
    elif "nutrition_service.py" in path_lower or "metabolic" in path_lower or "nutrition" in path_lower:
        return "Nutrition & Mifflin-St Jeor Engine"
    elif "recipe" in path_lower or "ingredient" in path_lower:
        return "Indian Recipes & Ingredients Catalog"
    elif "grocery" in path_lower:
        return "Automated Grocery Shopping Engine"
    elif "household" in path_lower or "member" in path_lower:
        return "Family & Household Hub"
    elif "auth" in path_lower or "clerk" in path_lower:
        return "Clerk Authentication & User Management"
    elif "chat" in path_lower:
        return "AI Assistant System"
    elif "docs/" in path_lower or path_lower.endswith(".md"):
        return "Application Documentation"
    elif "frontend/" in path_lower:
        return f"UI Interface: {component_or_func or 'React Component'}"
    return "AI Meal Planner Core"


def make_chunk_id(file_path: str, comp_name: str, index: int, text: str) -> str:
    """
    Creates a deterministic, stable chunk ID.
    """
    clean_path = file_path.replace("/", "_").replace("\\", "_").replace(".", "_")
    clean_comp = re.sub(r'[^a-zA-Z0-9_]', '_', comp_name)[:30]
    text_digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]
    return f"{clean_path}_{clean_comp}_{index}_{text_digest}"


# ---------------------------------------------------------------------------
# Python AST Chunking
# ---------------------------------------------------------------------------

def chunk_python_document(doc: SourceDocument) -> List[CodeChunk]:
    """
    Uses Python AST to extract classes, functions, and module docstrings.
    Falls back to line chunking if AST parsing fails.
    """
    lines = doc.content.splitlines()
    now_iso = datetime.now(timezone.utc).isoformat()
    chunks: List[CodeChunk] = []

    # Handle specialized seed files (recipes & ingredients data)
    if "seed/recipes.py" in doc.file_path:
        return chunk_recipes_seed(doc)
    if "seed/ingredients.py" in doc.file_path:
        return chunk_ingredients_seed(doc)

    try:
        tree = ast.parse(doc.content, filename=doc.file_path)
    except Exception:
        # Fall back to sliding window if AST fails
        return chunk_lines_fallback(doc)

    # 1. Module-level docstring and header
    module_doc = ast.get_docstring(tree)
    if module_doc:
        doc_text = f"File: {doc.file_path}\nModule Overview:\n{module_doc.strip()}"
        chunk_id = make_chunk_id(doc.file_path, "module_doc", 0, doc_text)
        chunks.append(CodeChunk(
            chunk_id=chunk_id,
            file_path=doc.file_path,
            source_type=doc.source_type,
            component_or_function="module_overview",
            section="Module Overview",
            start_line=1,
            end_line=len(module_doc.splitlines()) + 2,
            content_hash=hashlib.sha256(doc_text.encode("utf-8")).hexdigest(),
            indexed_at=now_iso,
            chunk_text=doc_text,
            source_label=generate_source_label(doc.file_path, "Module Overview")
        ))

    chunk_idx = 1
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start_l = node.lineno
            end_l = getattr(node, "end_lineno", start_l + 10)
            func_code = "\n".join(lines[start_l - 1 : end_l])
            func_name = node.name

            header = f"File: {doc.file_path} (lines {start_l}-{end_l})\nFunction: {func_name}\n"
            text_body = header + func_code

            # If function is too huge, truncate or split
            if len(text_body) > MAX_CHUNK_CHARS:
                # Include docstring + signature + first portion
                func_doc = ast.get_docstring(node) or ""
                text_body = f"{header}Docstring: {func_doc}\nCode snippet:\n{func_code[:MAX_CHUNK_CHARS - 200]}..."

            chunk_id = make_chunk_id(doc.file_path, func_name, chunk_idx, text_body)
            chunks.append(CodeChunk(
                chunk_id=chunk_id,
                file_path=doc.file_path,
                source_type=doc.source_type,
                component_or_function=func_name,
                section="Functions",
                start_line=start_l,
                end_line=end_l,
                content_hash=hashlib.sha256(text_body.encode("utf-8")).hexdigest(),
                indexed_at=now_iso,
                chunk_text=text_body,
                source_label=generate_source_label(doc.file_path, func_name)
            ))
            chunk_idx += 1

        elif isinstance(node, ast.ClassDef):
            start_l = node.lineno
            end_l = getattr(node, "end_lineno", start_l + 20)
            class_code = "\n".join(lines[start_l - 1 : end_l])
            class_name = node.name

            header = f"File: {doc.file_path} (lines {start_l}-{end_l})\nClass: {class_name}\n"
            text_body = header + class_code

            if len(text_body) > MAX_CHUNK_CHARS:
                class_doc = ast.get_docstring(node) or ""
                text_body = f"{header}Docstring: {class_doc}\nClass definitions:\n{class_code[:MAX_CHUNK_CHARS - 200]}..."

            chunk_id = make_chunk_id(doc.file_path, class_name, chunk_idx, text_body)
            chunks.append(CodeChunk(
                chunk_id=chunk_id,
                file_path=doc.file_path,
                source_type=doc.source_type,
                component_or_function=class_name,
                section="Classes",
                start_line=start_l,
                end_line=end_l,
                content_hash=hashlib.sha256(text_body.encode("utf-8")).hexdigest(),
                indexed_at=now_iso,
                chunk_text=text_body,
                source_label=generate_source_label(doc.file_path, class_name)
            ))
            chunk_idx += 1

    # If no functions or classes extracted (e.g. config or simple script), extract overall file content
    if not chunks:
        return chunk_lines_fallback(doc)

    return chunks


def chunk_recipes_seed(doc: SourceDocument) -> List[CodeChunk]:
    """Specialized semantic chunker for 125 Indian recipes in recipes.py."""
    from app.seed.recipes import RECIPES_DATA
    now_iso = datetime.now(timezone.utc).isoformat()
    chunks: List[CodeChunk] = []

    for idx, r in enumerate(RECIPES_DATA):
        name = r.get("name", f"Recipe {idx+1}")
        cuisine = r.get("cuisine", "Indian")
        meal_type = r.get("meal_type", "Meal")
        dietary_tags = ", ".join(r.get("dietary_tags", []))
        prep_m = r.get("prep_time_minutes", 0)
        cook_m = r.get("cook_time_minutes", 0)
        desc = r.get("description", "")
        cost = r.get("estimated_cost", "N/A")
        instructions = r.get("instructions", "")

        # Format ingredients list
        ings = []
        for ing in r.get("ingredients", []):
            ings.append(f"{ing.get('name')} ({ing.get('quantity')} {ing.get('unit')})")
        ings_str = ", ".join(ings)

        chunk_text = (
            f"Recipe: {name}\n"
            f"Cuisine: {cuisine} | Meal Type: {meal_type}\n"
            f"Dietary Tags: {dietary_tags} | Est. Cost: ₹{cost}\n"
            f"Time: {prep_m}m prep, {cook_m}m cook\n"
            f"Description: {desc}\n"
            f"Ingredients: {ings_str}\n"
            f"Instructions: {instructions[:300]}..."
        )

        chunk_id = make_chunk_id(doc.file_path, name, idx, chunk_text)
        chunks.append(CodeChunk(
            chunk_id=chunk_id,
            file_path=doc.file_path,
            source_type=doc.source_type,
            component_or_function=name,
            section="Indian Recipes",
            start_line=1,
            end_line=50,
            content_hash=hashlib.sha256(chunk_text.encode("utf-8")).hexdigest(),
            indexed_at=now_iso,
            chunk_text=chunk_text,
            source_label="Indian Recipes Catalog"
        ))

    return chunks


def chunk_ingredients_seed(doc: SourceDocument) -> List[CodeChunk]:
    """Specialized chunker for 83 Indian ingredients in ingredients.py, grouped by category."""
    from app.seed.ingredients import INGREDIENTS_DATA
    now_iso = datetime.now(timezone.utc).isoformat()
    chunks: List[CodeChunk] = []

    # Group ingredients by category
    by_category: Dict[str, List[Dict[str, Any]]] = {}
    for ing in INGREDIENTS_DATA:
        cat = ing.get("category", "General")
        by_category.setdefault(cat, []).append(ing)

    chunk_idx = 0
    for cat, items in by_category.items():
        # Sub-batch 6 items per chunk for clean readability
        for i in range(0, len(items), 6):
            group = items[i : i + 6]
            lines = [f"Ingredients Category: {cat} (IFCT / ICMR Standardized Nutrition & Pricing)"]
            for item in group:
                p_unit = f"₹{item.get('price_per_unit')}/{item.get('unit')}" if item.get('price_per_unit') else "Benchmark price"
                lines.append(
                    f"- {item.get('name')}: {p_unit} | "
                    f"Calories: {item.get('calories')} kcal, Protein: {item.get('protein')}g, "
                    f"Carbs: {item.get('carbs')}g, Fat: {item.get('fat')}g, Fiber: {item.get('fiber')}g"
                )

            chunk_text = "\n".join(lines)
            chunk_id = make_chunk_id(doc.file_path, f"{cat}_{chunk_idx}", chunk_idx, chunk_text)
            chunks.append(CodeChunk(
                chunk_id=chunk_id,
                file_path=doc.file_path,
                source_type=doc.source_type,
                component_or_function=f"{cat} Ingredients",
                section="Ingredients Catalog",
                start_line=1,
                end_line=50,
                content_hash=hashlib.sha256(chunk_text.encode("utf-8")).hexdigest(),
                indexed_at=now_iso,
                chunk_text=chunk_text,
                source_label="Indian Ingredients Catalog"
            ))
            chunk_idx += 1

    return chunks


# ---------------------------------------------------------------------------
# React / JSX Chunking
# ---------------------------------------------------------------------------

def chunk_react_document(doc: SourceDocument) -> List[CodeChunk]:
    """
    Extracts React components, export statements, and functions.
    """
    lines = doc.content.splitlines()
    now_iso = datetime.now(timezone.utc).isoformat()
    chunks: List[CodeChunk] = []

    # Pattern for functions / components
    comp_regex = re.compile(
        r'^(?:export\s+default\s+function|export\s+function|function|const)\s+([A-Za-z0-9_]+)',
        re.MULTILINE
    )

    matches = list(comp_regex.finditer(doc.content))
    if not matches:
        return chunk_lines_fallback(doc)

    for i, m in enumerate(matches):
        comp_name = m.group(1)
        start_char = m.start()
        end_char = matches[i + 1].start() if i + 1 < len(matches) else len(doc.content)

        comp_content = doc.content[start_char:end_char].strip()
        if len(comp_content) < MIN_CHUNK_CHARS:
            continue

        start_line = doc.content[:start_char].count("\n") + 1
        end_line = start_line + comp_content.count("\n")

        # Truncate if exceeds Pinecone size
        if len(comp_content) > MAX_CHUNK_CHARS:
            comp_content = comp_content[:MAX_CHUNK_CHARS - 100] + "\n... [component truncated for length]"

        chunk_text = f"File: {doc.file_path} (lines {start_line}-{end_line})\nComponent/Function: {comp_name}\n\n{comp_content}"
        chunk_id = make_chunk_id(doc.file_path, comp_name, i, chunk_text)

        chunks.append(CodeChunk(
            chunk_id=chunk_id,
            file_path=doc.file_path,
            source_type=doc.source_type,
            component_or_function=comp_name,
            section="React Components",
            start_line=start_line,
            end_line=end_line,
            content_hash=hashlib.sha256(chunk_text.encode("utf-8")).hexdigest(),
            indexed_at=now_iso,
            chunk_text=chunk_text,
            source_label=generate_source_label(doc.file_path, comp_name)
        ))

    if not chunks:
        return chunk_lines_fallback(doc)

    return chunks


# ---------------------------------------------------------------------------
# Markdown Chunking
# ---------------------------------------------------------------------------

def chunk_markdown_document(doc: SourceDocument) -> List[CodeChunk]:
    """
    Chunks Markdown documentation based on heading structure (# or ## or ###).
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    chunks: List[CodeChunk] = []

    # Split by headings
    heading_pattern = re.compile(r'^(#{1,3}\s+.+)$', re.MULTILINE)
    splits = list(heading_pattern.finditer(doc.content))

    if not splits:
        return chunk_lines_fallback(doc)

    for i, match in enumerate(splits):
        heading = match.group(1).strip()
        start_char = match.start()
        end_char = splits[i + 1].start() if i + 1 < len(splits) else len(doc.content)

        section_body = doc.content[start_char:end_char].strip()
        if len(section_body) < MIN_CHUNK_CHARS:
            continue

        start_line = doc.content[:start_char].count("\n") + 1
        end_line = start_line + section_body.count("\n")

        # Clean heading label
        clean_heading = re.sub(r'^#+\s*', '', heading)

        # If section is very large, split into sub-chunks
        if len(section_body) > MAX_CHUNK_CHARS:
            paragraphs = section_body.split("\n\n")
            curr_text = f"Doc: {doc.file_path}\nSection: {heading}\n\n"
            sub_idx = 0
            for p in paragraphs:
                if len(curr_text) + len(p) > MAX_CHUNK_CHARS and len(curr_text) > MIN_CHUNK_CHARS:
                    c_id = make_chunk_id(doc.file_path, clean_heading, sub_idx, curr_text)
                    chunks.append(CodeChunk(
                        chunk_id=c_id,
                        file_path=doc.file_path,
                        source_type=doc.source_type,
                        component_or_function=clean_heading,
                        section="Documentation",
                        start_line=start_line,
                        end_line=end_line,
                        content_hash=hashlib.sha256(curr_text.encode("utf-8")).hexdigest(),
                        indexed_at=now_iso,
                        chunk_text=curr_text.strip(),
                        source_label=generate_source_label(doc.file_path, clean_heading)
                    ))
                    sub_idx += 1
                    curr_text = f"Doc: {doc.file_path}\nSection: {heading} (cont.)\n\n{p}\n\n"
                else:
                    curr_text += p + "\n\n"

            if len(curr_text.strip()) > MIN_CHUNK_CHARS:
                c_id = make_chunk_id(doc.file_path, clean_heading, sub_idx, curr_text)
                chunks.append(CodeChunk(
                    chunk_id=c_id,
                    file_path=doc.file_path,
                    source_type=doc.source_type,
                    component_or_function=clean_heading,
                    section="Documentation",
                    start_line=start_line,
                    end_line=end_line,
                    content_hash=hashlib.sha256(curr_text.encode("utf-8")).hexdigest(),
                    indexed_at=now_iso,
                    chunk_text=curr_text.strip(),
                    source_label=generate_source_label(doc.file_path, clean_heading)
                ))
        else:
            chunk_text = f"Doc: {doc.file_path}\n{section_body}"
            c_id = make_chunk_id(doc.file_path, clean_heading, i, chunk_text)
            chunks.append(CodeChunk(
                chunk_id=c_id,
                file_path=doc.file_path,
                source_type=doc.source_type,
                component_or_function=clean_heading,
                section="Documentation",
                start_line=start_line,
                end_line=end_line,
                content_hash=hashlib.sha256(chunk_text.encode("utf-8")).hexdigest(),
                indexed_at=now_iso,
                chunk_text=chunk_text,
                source_label=generate_source_label(doc.file_path, clean_heading)
            ))

    return chunks


# ---------------------------------------------------------------------------
# Fallback Chunking (Line sliding window)
# ---------------------------------------------------------------------------

def chunk_lines_fallback(doc: SourceDocument, window_lines: int = 50, overlap_lines: int = 10) -> List[CodeChunk]:
    """
    Splits arbitrary text files using a sliding window of lines.
    """
    lines = doc.content.splitlines()
    now_iso = datetime.now(timezone.utc).isoformat()
    chunks: List[CodeChunk] = []

    if not lines:
        return []

    step = max(1, window_lines - overlap_lines)
    chunk_idx = 0

    for start_i in range(0, len(lines), step):
        end_i = min(len(lines), start_i + window_lines)
        window = lines[start_i:end_i]
        text_body = f"File: {doc.file_path} (lines {start_i + 1}-{end_i})\n" + "\n".join(window)

        if len(text_body.strip()) < MIN_CHUNK_CHARS:
            continue

        c_id = make_chunk_id(doc.file_path, f"part_{chunk_idx}", chunk_idx, text_body)
        chunks.append(CodeChunk(
            chunk_id=c_id,
            file_path=doc.file_path,
            source_type=doc.source_type,
            component_or_function=f"Lines {start_i + 1}-{end_i}",
            section="General Source",
            start_line=start_i + 1,
            end_line=end_i,
            content_hash=hashlib.sha256(text_body.encode("utf-8")).hexdigest(),
            indexed_at=now_iso,
            chunk_text=text_body[:MAX_CHUNK_CHARS],
            source_label=generate_source_label(doc.file_path, f"Lines {start_i + 1}-{end_i}")
        ))
        chunk_idx += 1

    return chunks


def chunk_document(doc: SourceDocument) -> List[CodeChunk]:
    """
    Routes document to appropriate domain-aware chunker based on source type.
    """
    if doc.source_type == "python_backend":
        return chunk_python_document(doc)
    elif doc.source_type == "react_frontend":
        return chunk_react_document(doc)
    elif doc.source_type == "markdown_docs":
        return chunk_markdown_document(doc)
    else:
        return chunk_lines_fallback(doc)

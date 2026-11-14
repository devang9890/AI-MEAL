# 🧠 AI Meal Planner: Codebase RAG Architecture

## 1. What is RAG (Retrieval-Augmented Generation)?

Traditional Large Language Models (LLMs) like GPT-4 or Llama 3 are trained on vast amounts of public internet data. However, they:
1. **Know nothing about private applications**: They do not know your custom algorithms, database schemas, React components, or business rules.
2. **Hallucinate when guessing**: When asked about specific system features, they often invent functions or numbers.
3. **Cannot fit entire codebases into prompts**: Stuffing hundreds of code files into every prompt exceeds context window limits and is slow and expensive.

**Retrieval-Augmented Generation (RAG)** solves this by:
1. Converting your project files into small, searchable knowledge blocks (**chunks**).
2. Storing numerical representations (**vector embeddings**) of these blocks in a vector database.
3. When a user asks a question, finding only the **top few relevant blocks** through similarity search.
4. Supplying these relevant blocks to the LLM as verified ground truth before it generates an answer.

---

## 2. What is Codebase RAG and Why Index Source Files?

Standard RAG systems index plain PDFs, Word documents, or text articles. 

**Codebase RAG** indexes the **actual project implementation**:
- **Backend**: FastAPI routes, SQLAlchemy data models, Pydantic schemas, PuLP Integer Linear Programming (ILP) optimizer, and Mifflin–St Jeor BMR/TDEE calculation formulas.
- **Frontend**: React components, UI pages, user workflows, form validations, and navigation paths.
- **Data Catalog**: 125 Indian recipes and 83 standardized IFCT/ICMR ingredients.
- **Documentation**: Architecture specifications and operational runbooks.

### Why index the code?
When a user asks:
- *"How does the weekly budget optimization work?"*
- *"Why did the planner pick Palak Paneer?"*
- *"How are daily calories calculated?"*

The chatbot retrieves the **real PuLP mathematical formulation** from `optimizer.py`, the **real Mifflin–St Jeor equation** from `nutrition_service.py`, and the **exact recipe details** from `recipes.py`. The assistant explains the actual application without guessing.

---

## 3. The Extraction & Chunking Pipeline

Raw code cannot be cut blindly in the middle of a line or loop. Our system employs **syntax-aware chunking**:

```
Project Files (Frontend, Backend, Docs)
          │
          ▼
   [Source Loader]
   - Filters out .git, node_modules, .env, secrets
   - Sanitizes credentials
          │
          ▼
   [Syntax-Aware Chunker]
   ├── Python AST: Splits by class, function, and module docstring
   ├── Seed Catalogs: Splits by individual recipe and ingredient category
   ├── React JSX: Splits by component and export function
   └── Markdown: Splits by heading hierarchy (#, ##, ###)
          │
          ▼
   [Normalized Chunks with Stable IDs]
   - chunk_id, file_path, start_line, end_line, source_label, content_hash
```

### Exclusions & Security Rules
The source loader strictly ignores:
- Virtual environments (`venv/`, `.venv/`)
- Package caches (`node_modules/`, `__pycache__/`)
- Build outputs (`dist/`, `build/`, `.vite/`)
- All environment secret files (`.env`, `.env.*`)
- Binary files and images (`.png`, `.svg`, `.ico`, `.pdf`)
- Auto-generated migrations (`alembic/versions/`)

Any accidental secrets matching API key patterns (`gsk_`, `pk_`, `sk_`, database passwords) are automatically scrubbed by regex sanitizers before chunk creation.

---

## 4. Local Embeddings: `sentence-transformers/all-MiniLM-L6-v2`

### What is an Embedding?
An embedding converts a piece of text into a vector: a list of floating-point numbers that capture its **semantic meaning**. Texts with similar meanings end up close together in vector space.

### Why `all-MiniLM-L6-v2`?
- **Speed & Efficiency**: Compact model (22M parameters) designed for high-performance semantic search.
- **Local & Private**: Runs directly on your CPU using PyTorch/SentenceTransformers. No queries or code snippets are sent to third-party embedding APIs.
- **One-time Download**: Automatically cached in `~/.cache/huggingface/hub/`. Subsequent loads take seconds with zero network calls.
- **Identical Model for Both Ingestion & Retrieval**: Using the exact same model ensures query vectors and document vectors share the exact same geometric space.

### What Does 384 Dimensions Mean?
The embedding model represents text in a 384-dimensional coordinate space. Each vector is an array of 384 floating-point numbers:
```
[0.0381, -0.0124, 0.0892, ..., -0.0451]
```
The vectors are unit-normalized ($\|v\| = 1.0$), ensuring consistent distance comparisons.

---

## 5. Vector Database: Pinecone

### What Pinecone Does
Pinecone is a managed, serverless vector database designed for real-time similarity search. While relational databases like PostgreSQL find exact matches (e.g. `WHERE id = 5`), Pinecone finds **conceptual matches** using high-dimensional geometry.

### Cosine Similarity
Our index uses the **cosine similarity metric**:
$$\text{Cosine Similarity} = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\| \|\mathbf{v}\|}$$
For unit-normalized vectors, this is simply the dot product $\mathbf{u} \cdot \mathbf{v}$. A score near `1.0` means nearly identical meaning, while scores near `0.0` or below mean unrelated topics.

### Index & Namespaces
- **Index Name**: `ai-meal-planner-rag` (384 dimensions, cosine metric).
- **Namespace**: `ai-meal-planner-dev`. Namespaces isolate different environments (e.g., dev, staging, prod) within a single Pinecone index.

---

## 6. Two-Tier Context: Live Database vs. Pinecone Knowledge

The assistant combines **two distinct sources of ground truth**:

```
                       User Asks Question
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
[Tier 1: Live PostgreSQL]            [Tier 2: Pinecone Vector RAG]
- Active User Household              - Codebase Architecture
- Member Biometrics (Age, Wt, Ht)    - PuLP Optimizer Math
- Mifflin–St Jeor Daily Targets      - 125 Indian Recipes
- Weekly Budget Status               - 83 Ingredients & Prices
            │                                     │
            └──────────────────┬──────────────────┘
                               ▼
                   [Grounded System Prompt]
                               │
                               ▼
                        [Groq LLM API]
                               │
                               ▼
               Answer with Clean Source Badges
```

- **Live Database**: Answers *"What are MY calories?"* or *"What is MY family's protein goal?"*.
- **Pinecone RAG**: Answers *"HOW does the budget optimizer work?"* or *"What high-protein vegetarian meals are available?"*.

---

## 7. Complete Request-Response Flow

```
1. User types message in existing React floating chat widget.
2. React app sends POST /api/chat with message, conversation history, and Clerk JWT.
3. FastAPI endpoint verifies Clerk JWT and retrieves user's household from PostgreSQL.
4. Local EmbeddingService converts the query into a 384-d normalized vector.
5. Pinecone queries namespace 'ai-meal-planner-dev' (top_k=5, threshold=0.35).
6. Relevant code/doc excerpts and human-friendly source labels are assembled.
7. System prompt is constructed with strict safety boundaries and grounded context.
8. Groq LLM (openai/gpt-oss-120b) generates the final answer.
9. FastAPI returns ChatResponse with reply, success status, and clean source badges.
10. React Chatbot displays the grounded answer and subtle '📚 Based on' attribution.
```

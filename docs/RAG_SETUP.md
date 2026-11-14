# 🛠️ AI Meal Planner: RAG Setup & Verification Guide

This guide walks you through setting up and running the Codebase RAG system using local embeddings, Pinecone serverless vector database, and Groq LLM.

---

## 1. Prerequisites

- Python 3.10+
- Node.js 18+ and npm
- Free Pinecone Account ([app.pinecone.io](https://app.pinecone.io/))
- Free Groq Account ([console.groq.com](https://console.groq.com/))

---

## 2. Obtain Your Pinecone API Key

1. Log in to [app.pinecone.io](https://app.pinecone.io/).
2. In the left navigation, click **API Keys**.
3. Click **Create API Key**, name it `ai-meal-planner`, and copy the generated key (`pcsk_...`).
4. *(Optional)* You can pre-create the index in the console or let the automated ingestion script create it for you:
   - **Index Name**: `ai-meal-planner-rag`
   - **Dimensions**: `384`
   - **Metric**: `cosine`
   - **Type**: `Serverless` (AWS `us-east-1`)

---

## 3. Configure `backend/.env`

Open your existing `backend/.env` file and add the Pinecone configuration:

```env
# Groq API (already configured)
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b

# Pinecone Vector Database
PINECONE_API_KEY=pcsk_your_actual_pinecone_api_key_here
PINECONE_INDEX_NAME=ai-meal-planner-rag
PINECONE_NAMESPACE=ai-meal-planner-dev
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1

# Local Embedding Model
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2

# RAG Search Settings
RAG_TOP_K=5
RAG_SCORE_THRESHOLD=0.35
```

> [!IMPORTANT]
> Never commit `backend/.env` to Git. It is automatically ignored in `.gitignore`.

---

## 4. Install Dependencies

In the `backend` directory, install the required packages:

```bash
cd backend
pip install -r requirements.txt
```

This installs `sentence-transformers` and `pinecone`.

---

## 5. Local Embedding Model Caching

The embedding model `sentence-transformers/all-MiniLM-L6-v2` runs locally on your CPU:
- It downloads automatically on first run and is cached in your user profile:  
  `C:\Users\<USER>\.cache\huggingface\hub\models--sentence-transformers--all-MiniLM-L6-v2`
- Total disk footprint is approximately **80 MB**.
- Once cached, no external network calls are made for embedding generation; it loads instantly.

---

## 6. Run Source Code Ingestion

To extract code/docs, generate local embeddings, and synchronize with Pinecone, run:

```bash
cd backend
python -m app.rag.ingestion
```

### Expected Output

```
=======================================================
      AI MEAL PLANNER CODEBASE RAG INGESTION
=======================================================
Files discovered:     101
Files eligible:       73
Files excluded:       28
Chunks created:       405
New chunks indexed:   405
Updated chunks:       0
Deleted stale chunks: 0
Embedding model:      sentence-transformers/all-MiniLM-L6-v2
Vector dimension:     384
Pinecone index:       ai-meal-planner-rag
Pinecone namespace:   ai-meal-planner-dev
Status:               SUCCESS
=======================================================
```

---

## 7. Incremental Updates & Rebuilding

### A. Incremental Ingestion (Fast)
When you modify or add source files, simply re-run:
```bash
python -m app.rag.ingestion
```
The ingestion engine checks file SHA-256 hashes against `.rag_manifest.json`. Only modified or new files are re-embedded. Unchanged files are skipped (0 extra embedding calls). Stale vectors from deleted or modified files are automatically purged from Pinecone.

### B. Dry Run (Simulation)
To preview file discovery and chunking without making network calls to Pinecone:
```bash
python -m app.rag.ingestion --dry-run
```

### C. Full Index Rebuild
If you want to clear the namespace and re-embed everything from scratch:
```bash
python -m app.rag.ingestion --rebuild
```

---

## 8. Starting the Application

### Start the Backend (FastAPI)
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### Start the Frontend (React + Vite)
```bash
cd frontend
npm run dev
```

Open your browser at `http://localhost:5173`.

---

## 9. Troubleshooting & FAQ

### 1. `Status: PENDING_API_KEY`
**Cause**: `PINECONE_API_KEY` is not set or empty in `backend/.env`.  
**Fix**: Add your Pinecone key to `backend/.env` and re-run `python -m app.rag.ingestion`.

### 2. `Embedding dimension mismatch`
**Cause**: An index was created with dimensions other than 384.  
**Fix**: Ensure the index is created with `dimension=384` and `metric=cosine`.

### 3. `HF_HUB_OFFLINE` / HuggingFace Network Warnings
**Cause**: HuggingFace occasionally checks for remote model commits.  
**Fix**: The `EmbeddingService` automatically sets `HF_HUB_OFFLINE=1` when cached models exist, avoiding unnecessary network polling.

### 4. Running Backend Tests
To run all 29 automated tests (including mock RAG, chat, and household tests):
```bash
cd backend
python -m pytest tests -v
```

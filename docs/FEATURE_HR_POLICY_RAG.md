# HR Policy RAG Feature

A professional, self‑contained guide to the HR Policy Retrieval‑Augmented Generation (RAG) feature.

## Executive Summary

The HR Policy RAG feature answers employee questions using your company policy documents. It retrieves the most relevant policy excerpts from a vector database and generates grounded answers with citations via OpenAI or Gemini. If no provider is configured or available, it returns a concise, retrieval‑only answer based on the sources.

Highlights:

- Grounded answers with explicit citations
- Multi‑provider support: OpenAI, Gemini, or Auto (prefer → fallback)
- Low‑latency mode for faster responses (shorter outputs, faster models)
- Conversation summary caching (Redis or in‑memory) to shrink prompts
- Minimalist Streamlit UI with sticky input and streaming

## Components & Responsibilities

- `tools/policy_rag/document_processor.py`
  - Ingests PDFs/text, splits into overlapping chunks, extracts metadata (filename, page)
- `tools/policy_rag/vector_database.py`
  - Stores chunk embeddings (Chroma DB), provides semantic search and basic stats
- `tools/policy_rag/mcp_tool.py` (PolicySearchTool)
  - Exposes `search_policies(query, top_k)` and `get_database_stats()`
- `tools/policy_rag/rag_engine.py` (RAGEngine & ConversationManager)
  - Provider selection (`openai`, `gemini`, `auto`) with fallback
  - Prompt creation with retrieved chunks + optional conversation summary + recent turns
  - Response generation with LLM or retrieval‑only fallback
  - Low‑latency mode (fast models, lower tokens/temperature)
  - Conversation summaries (no‑LLM heuristic) with Redis/in‑memory caching
- `tools/cache/redis_cache.py`
  - Unified cache interface with Redis client or in‑memory fallback
- `ui/streamlit_app.py`
  - Chat UI, status badges, settings (Top‑K, Low‑latency, Fast responses), commands
  - Streams assistant output for better perceived latency
- `scripts/warmup.py`
  - Pre‑initializes vector search and the LLM provider to reduce first‑response latency

## Data Flow (Query Lifecycle)

1. User submits a question in the UI
2. UI records the user turn in `ConversationManager`
3. UI retrieves Top‑K chunks via `PolicySearchTool.search_policies()`
4. UI fetches a cached conversation summary (or generates a quick heuristic summary)
5. UI calls `RAGEngine.generate_response()` with: question, chunks, summary, recent turns, low‑latency flag
6. RAGEngine chooses the active provider (or Basic fallback) and returns an answer + metadata
7. UI streams the answer text, displays source citations, and persists the assistant turn

## Configuration (Environment)

Required (for AI responses; if omitted, Basic mode works):

- `OPENAI_API_KEY` or `GEMINI_API_KEY`

Vector DB & Documents:

- `VECTOR_DB_PATH=./data/vector_db`
- `VECTOR_DB_COLLECTION_NAME=hr_policies`
- `HR_DOCUMENTS_PATH=./data/hr_documents`
- `EMBEDDING_MODEL=all-MiniLM-L6-v2`

Caching (optional):

- `REDIS_URL=redis://localhost:6379/0`
  - or `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`

Low‑latency tuning (optional):

- `FAST_OPENAI_MODEL=gpt-3.5-turbo`
- `FAST_GEMINI_MODEL=gemini-1.5-flash`
- `LOW_LATENCY_MAX_TOKENS=350`
- `LOW_LATENCY_TEMPERATURE=0.0`

## Setup & Ingest

```powershell
# Windows PowerShell
python -m venv .venv; .\.venv\Scripts\activate
pip install -r requirements.txt

# Place PDFs/text into data/hr_documents/
python setup.py   # builds/updates vector DB; skips redundant re‑processing when possible
```

## Running the Feature

```powershell
# Optional warm‑up to reduce the first response latency
python scripts/warmup.py

# Start the UI
streamlit run ui/streamlit_app.py
```

In the UI sidebar → Settings:

- Search results (Top‑K)
- Low‑latency mode (prefer faster models / Basic)
- Fast responses (smaller context for speed)

Commands in the input box:

- `/clear` — reset chat
- `/help` — list commands
- `/provider openai|gemini|auto` — switch provider at runtime

## Caching & Low‑Latency

- Conversation summaries are cached per session at `conv:summary:<user_id>` (≈30 minutes)
- Redis is preferred; if unavailable, an in‑memory fallback is used (per process)
- Low‑latency mode temporarily caps tokens, lowers temperature, and can switch to fast models
- If no provider keys are set, the feature operates in fast, retrieval‑only Basic mode

## Extending & Customization

- Providers: adjust defaults or add adapters to support additional LLMs
- Vector DB: swap Chroma with Pinecone/Milvus by adapting `vector_database.py`
- Summaries: replace the heuristic summarizer with a compact LLM‑based variant (still cached)
- UI: add export (JSON/MD), persistent conversations, inline [1][2] citations with copy/open

## Troubleshooting

- No AI responses: set `OPENAI_API_KEY` or `GEMINI_API_KEY`; otherwise Basic mode answers are used
- No documents found: confirm files in `data/hr_documents/` and re‑run `python setup.py`
- Slow first response: run `python scripts/warmup.py` and enable Low‑latency mode
- Cache unavailable: ensure `REDIS_URL` is reachable; otherwise in‑memory fallback is active

## File Map

```
tools/policy_rag/
├── document_processor.py    # PDF/text to chunks
├── vector_database.py       # Chroma DB wrapper
├── mcp_tool.py              # PolicySearchTool (search/stats)
└── rag_engine.py            # RAGEngine + ConversationManager

tools/cache/redis_cache.py   # Redis/in‑memory JSON cache interface
ui/streamlit_app.py          # Chat UI
scripts/warmup.py            # Warm‑up script
```

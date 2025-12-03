# Interview Pitch: MCP-powered HR Assistant

1. Problem Statement

- Manual HR workflows are slow, inconsistent, and hard to audit (policy Q&A, resume screening, onboarding).
- Goal: Build a resilient, auditable AI assistant that accelerates these workflows without compromising clarity or control.

2. What This Project Delivers

- Policy Q&A with citations (RAG) for trustworthy answers.
- Resume screening via semantic relevance and skill matching.
- Role-based onboarding checklist backed by JSON, safe and atomic.
- Streamlit UI for demos; MCP server exposes tools with clean contracts.

3. Architecture Overview

- UI: `ui/streamlit_app.py` (tabs: Policies, Resume Screening, Onboarding).
- Server: `mcp_server/server.py` (router, lazy tool registration, health/manifest).
- Tools:
  - Policy RAG: `tools/policy_rag/` (ChromaDB, sentence-transformers, LLM fallback).
  - Resume Screening: `tools/resume_screening/mcp_tool.py` (chunking, embeddings, cosine similarity, skill bonus).
  - Onboarding: `tools/onboarding/mcp_tool.py` (JSON persistence; actions: get tasks, mark complete, get status).
- Data: `data/hr_documents/*` for policies; `data/vector_db/` for Chroma; `data/onboarding_tasks.json` for onboarding.
- Cache: `tools/cache/redis_cache.py` with Redis (TTL) or in-memory fallback.
- Warmup: `scripts/warmup.py` to reduce cold-start latency.

4. Why It’s Robust

- Lazy tool registration prevents hard failure when optional dependencies are missing.
- Predictable JSON schemas across tools simplify integration and testing.
- Citations in policy answers improve trust and auditability.
- Thread-safe, atomic writes in onboarding avoid data races and corruption.

5. Key Features (Demo-Ready)

- Policy answers with cited sources from `data/hr_documents/`.
- Resume ranking output: score, top snippets (from most relevant chunks), matched skills.
- Onboarding dashboard: role pick, task checklist, completion status.
- Health and manifest endpoints via MCP server for introspection.

6. Technical Highlights

- Vector search: Chroma + normalized sentence-transformers embeddings.
- LLM providers: OpenAI/Gemini fallback in RAG; configurable.
- Cache: `REDIS_URL` autodetect with `PING` health check; safe in-memory fallback if Redis is absent.
- Warmup script: pre-initializes vector DB and LLM to cut first-response latency.

7. Design Choices

- No LangChain to keep the stack lean, transparent, and controllable.
- Professional README with monochrome architecture diagram and clear sections.
- Error hygiene in UI: logs to stderr instead of surfacing raw exceptions.

8. How Resume Screening Works

- Extract: `pdfplumber` for PDFs or UTF-8 decode for text.
- Chunk: 700-word chunks with 100-word overlap for local relevance.
- Embed: `SentenceTransformer` (default `all-MiniLM-L6-v2`, configurable via `RESUME_EMBEDDING_MODEL`).
- Score: Average of top-5 chunk cosine similarities + skill bonus (`0.1 * matched/total`).
- Output: Sorted candidates with `filename`, `score`, `top_snippets`, `matched_skills`.

9. Demo Script (2–3 minutes)

- Open the app; point out the three tabs.
- Policies: ask “What’s our PTO policy?” → show answer with citations.
- Resume Screening: upload 2–3 resumes → run ranking → discuss top snippets and skills.
- Onboarding: choose “Engineering” → tick tasks → show status updates.
- Close: emphasize auditability, resilience, and extensibility.

10. Security and Reliability

- No silent failures: health checks and fallbacks.
- Data handling: resumes processed in memory; PDFs parsed via `pdfplumber`.
- Citations and JSON actions ensure traceability and reduce hallucination risk.

11. Run and Try It (Windows PowerShell)

```powershell
# 1) Create and activate a virtual environment
python -m venv .venv; .\.venv\Scripts\Activate.ps1

# 2) Install dependencies
pip install -r requirements.txt

# 3) (Optional) Set cache env vars for Redis
$env:REDIS_URL = "redis://localhost:6379/0"

# 4) Warm up vector DB and LLM provider
python scripts/warmup.py

# 5) Launch the Streamlit UI
autoflake -q --in-place --remove-unused-variables ui\streamlit_app.py 2>$null
streamlit run ui\streamlit_app.py
```

12. FAQs (Concise)

- “What happens if Redis isn’t available?” → In-memory fallback; TTL ignored.
- “Can we swap the embedding model?” → Yes, set `RESUME_EMBEDDING_MODEL`.
- “How do you add a new tool?” → Implement tool with a clear JSON schema and register lazily in `mcp_server/server.py`.
- “Why not LangChain?” → Prefer minimal, transparent control; add later if needed.

13. Roadmap

- Role management UI, bulk actions, export (CSV/JSON).
- Screening evaluator metrics (precision/recall, calibration).
- Fine-tuned or domain-specific embeddings.
- Optional LangChain integration for teams preferring that ecosystem.

14. One-Liner Summary

- A resilient, auditable HR assistant that delivers cited policy answers, intelligent resume ranking, and streamlined onboarding — built with a clean MCP architecture and production-aware design.

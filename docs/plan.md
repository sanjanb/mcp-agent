## HR Agent - Project Plan (First‑Person)

This document captures my plan for the HR Agent built on MCP. It lays out scope, architecture, specs, and delivery for three features, with the HR Policy RAG Agent as the first milestone. The tone and branch strategy reflect how I intend to execute the work.

---

### Goals

- Provide accurate, citation‑backed HR answers from our policy docs
- Keep the UX simple, fast, and reliable (works with or without LLM APIs)
- Structure the codebase as MCP tools for easy extension (RAG first, then add‑ons)

### Deliverables

- Feature 1: HR Policy RAG Agent (core, MVP)
- Feature 2: Resume Screening Agent (optional extension)
- Feature 3: Onboarding Agent (lightweight workflows)

Each feature is specified so a teammate can implement it independently.

---

# Feature 1 — HR Policy RAG Agent

#### Overview

My first milestone is a grounded Q&A assistant for HR policies. It retrieves relevant chunks from policy documents and generates answers with explicit citations. It must degrade gracefully to retrieval‑only answers if no LLM is available.

#### Scope

1. Ingest and index PDFs/text
2. Chunk + embed; store in local vector DB (Chroma)
3. Expose MCP tool `policy_search` for retrieval
4. RAG prompt template enforcing citation‑only answers
5. Simple UI (Streamlit) with sources panel

#### Architecture

```
Employee → Chat UI → LLM
↓ (MCP Tool Call)
MCP Server
↓
policy_search Tool
↓
Vector Database
↓
HR Documents Storage
```

#### Components

- Ingestion: pdfplumber → text → clean → chunk (~500 tokens) + metadata (filename, page)
- Embeddings + storage: sentence‑transformers or OpenAI embeddings → Chroma (chunk text, embedding, metadata)
- MCP `policy_search`: input (`query`, `top_k`) → search → return JSON with `text`, `score`, `doc_id`, `page`
- RAG prompt: include user query + top chunks; answer only from evidence; include citations
- UI: Streamlit chat; answer + citations below

#### MCP Tool Spec (policy_search)

Input:

```json
{ "query": "string", "top_k": 5 }
```

Output:

```json
{
  "query": "string",
  "chunks": [
    {
      "doc_id": "string",
      "text": "string",
      "score": "float",
      "page": "integer"
    }
  ]
}
```

#### Build Workflow

1. Ingestion → chunks → embeddings → Chroma
2. Tool `policy_search` → query embedding → similarity search → JSON
3. RAG prompt → enforce citations
4. Chat UI → ask → tool → LLM → render answer + sources
5. Test with leave/PTO/benefits/attendance queries

#### Success Criteria

- Answers include correct citations; no hallucinations
- Tool calls visible in logs; search returns relevant chunks
- Works with and without LLM keys (retrieval‑only fallback)

#### Future Extensions

- HR FAQ dataset, multilingual support, document versioning, admin uploader

---

# Feature 2 — Resume Screening Agent (Optional)

#### Objective

Rank resumes against a job description using embeddings and simple scoring; present ranking, top snippets, and a skills breakdown.

#### Architecture

```
Recruiter → Web UI → MCP Server → resume_screening Tool
↓
Vector DB
↓
Resume Storage
```

#### Components

- Ingest resumes (PDF→text), optionally extract sections; chunk by paragraph/bullets
- Store embeddings in vector DB under `resumes` namespace (metadata: resume_id, chunk_index, candidate_name)
- MCP `resume_screening` inputs: `job_description`, `resume_ids`
- Output:

```json
{
  "results": [
    {
      "resume_id": "string",
      "score": "float",
      "breakdown": { "semantic": 0.82, "skills": 0.61 },
      "top_snippets": ["...", "...", "..."]
    }
  ]
}
```

- Ranking (simple): `semantic_score = avg top‑5 similarities`; `final_score = 0.7*semantic + 0.3*skill_match`
- Skills: simple keyword counts (e.g., Python, AWS)

#### UI Integration

- Table: Rank | Resume | Score | Fit Summary; optional LLM‑generated summaries (fit/risks/next actions)

#### Success Criteria

- Human‑plausible ranking, top 3 snippets per resume, stable tool calls

---

# Feature 3 — Onboarding Agent (Simple Workflows)

#### Objective

Guide new hires through a JSON‑backed checklist. No RAG/embeddings, just structured steps and MCP actions.

#### Architecture

```
Employee → Chat UI → LLM
↓ (MCP call)
onboarding Tool
↓
JSON Database
```

#### Components

- Checklist JSON (e.g., `onboarding_checklist.json`):

```json
{
  "engineering": [
    { "id": 1, "task": "Set up email", "completed": false },
    { "id": 2, "task": "Read engineering handbook", "completed": false },
    { "id": 3, "task": "Join Slack channels", "completed": false }
  ]
}
```

- MCP `onboarding` actions: `get_tasks`, `mark_completed`, `get_status`
- Input/Output: small JSON payloads
- LLM prompt: “Always use tool results; never invent tasks.”

#### Success Criteria

- Users can view pending tasks, mark completion, and see updated status via the tool

---

## Branch Strategy

### Branch 1: `feature/hr-policy-rag`

- Build ingestion + vector indexing
- Implement `policy_search` tool
- Add RAG prompt + Streamlit chat
- Test end‑to‑end thoroughly
- Merge to `main`

### Branch 2: `feature/resume-screening`

- Resume ingestion + embeddings
- Scoring + MCP tool + minimal UI
- Test with 5–10 resumes
- Merge to `main`

### Branch 3: `feature/onboarding-agent`

- Checklist JSON + MCP actions
- Conversational workflow + UI connection
- Merge when stable

---

## Execution Notes

- Keep scope tight per branch and ship incrementally
- Prioritize reliability, then speed (warm‑up, low‑latency, caching)
- Maintain clear logs and JSON schemas for all tools

## Definition of Done (Feature 1)

- Search returns relevant chunks with metadata
- Answers are grounded with citations (or retrieval‑only fallback)
- UI streams responses and shows sources
- Passing ad‑hoc tests for common HR questions

## Risks & Mitigations

- Poor retrieval quality → adjust chunking, embedding model, or top‑K
- Latency → enable warm‑up, use low‑latency mode, cache summaries
- LLM outages → Basic retrieval‑only fallback always available

## Timeline (Indicative)

- Week 1: Feature 1 MVP (ingest, search, RAG, UI)
- Week 2: Perf passes (warm‑up, low‑latency, caching), docs and polish
- Week 3+: Optional Feature 2 and 3 in parallel branches

---

This plan reflects how I intend to build and phase the work. It is concrete enough for teammates to pick up tasks independently while staying aligned with my priorities and architecture.

---

Got it — here are **three separate Markdown files**, one for each feature.
Each file is written so that **a coding agent or teammate can directly start building the feature from it**, with architecture, workflow, data handling, tool design, and MCP integration.

If you want these delivered as **physical repo files** (in a canvas or zipped structure), tell me and I’ll generate them.

---

# **📄 Feature 1 — HR Policy RAG Agent (Markdown File)**

**Filename: `HR_Policy_RAG_Agent.md`**

```md
# HR Policy RAG Agent (MCP Tool)

## 1. Overview

The HR Policy RAG Agent is the first and core feature of the system.  
It answers employee HR questions by retrieving policy documents, extracting the most relevant sections, and generating grounded, citation-backed responses.

This feature demonstrates:

- Document ingestion
- Embedding + vector search
- MCP tool usage
- RAG prompting
- Chat UI integration

A coding agent can build this independently using the details here.

---

## 2. Scope

The agent must:

1. Ingest & index company HR documents (PDFs or text).
2. Chunk + embed content.
3. Store embeddings in a local vector DB.
4. Provide an MCP tool (`policy_search`) that:
   - Accepts a query
   - Returns top matching chunks with metadata
5. Provide a prompt template for LLM to answer grounded questions.
6. Run in a simple UI (Streamlit or chat widget).

No external HRIS integration is required.

---

## 3. High-Level Architecture
```

Employee → Chat UI → LLM
↓ (MCP Tool Call)
MCP Server
↓
policy_search Tool
↓
Vector Database
↓
HR Documents Storage

````

---

## 4. Components to Build

### A) Document Ingestion
- Input: folder containing PDFs or text files.
- Convert PDF → text (pdfplumber).
- Clean & normalize text.
- Split into chunks (~500 tokens).
- Attach metadata:
  - filename
  - page number
  - section header (optional)

### B) Embeddings + Vector Storage
- Use a simple model (OpenAI embedding or sentence-transformers).
- Store:
  - chunk text
  - embedding
  - metadata
- Vector DB: **Chroma** (local, simple).

### C) MCP Tool: `policy_search`
Functionality:
- Input: `query: string`, `top_k: int`
- Embed query
- Search vector DB for top chunks
- Return JSON with fields:
  - text
  - score
  - doc_id
  - page number

### D) LLM RAG Prompt Template
Provide the LLM with:
- user query
- retrieved chunks
- instructions to answer only using evidence
- instructions for citations

### E) UI Layer
A simple Streamlit page:
- Text box for employee question
- Display the answer
- Display citations under answer

---

## 5. MCP Tool Specification

### Tool Name
`policy_search`

### Input Schema
```json
{
  "query": "string",
  "top_k": 5
}
````

### Output Schema

```json
{
  "query": "string",
  "chunks": [
    {
      "doc_id": "string",
      "text": "string",
      "score": "float",
      "page": "integer"
    }
  ]
}
```

### Expected Behavior

- Retrieve `top_k` relevant chunks.
- Sort by similarity.
- Return JSON response only.

---

## 6. End-to-end Workflow for Coding Agent

1. Build ingestion function:

   - Convert PDF to text
   - Chunk text
   - Embed chunks
   - Save to vector DB

2. Build `policy_search` tool:

   - Accept JSON input
   - Embed query
   - run `.search()`
   - Return structured chunks

3. Build RAG prompt:

   - Feed chunks into LLM
   - Ensure citation style

4. Build simple chat UI:

   - Ask → MCP tool → LLM → show answer

5. Test queries:

   - Leave policies
   - PTO rules
   - Benefits
   - Attendance rules

---

## 7. Success Indicators

- The agent answers HR queries with correct citations.
- No hallucinations.
- MCP tool call is visible in logs.
- Vector search returns relevant chunks.

---

## 8. Future Extensions

- Add HR FAQ dataset
- Add multilingual support
- Add document versioning
- Add admin upload dashboard

````

---

# **📄 Feature 2 — Resume Screening Agent (Markdown File)**
**Filename: `Resume_Screening_Agent.md`**

```md
# Resume Screening Agent (MCP Tool)

## 1. Overview
The Resume Screening Agent ranks candidate resumes based on a job description using embeddings and simple scoring rules.

This feature is optional for MVP, but recommended if time permits.

---

## 2. Objectives
The system must:
1. Accept a job description (JD).
2. Accept multiple resumes (PDF or text).
3. Extract resume text.
4. Chunk + embed resume content.
5. Embed the JD.
6. Compute similarity scores.
7. Produce:
   - ranking
   - top snippets
   - skill match breakdown

---

## 3. Architecture

````

Recruiter → Web UI → MCP Server → resume_screening Tool
↓
Vector DB
↓
Resume Storage

````

---

## 4. Components to Build

### A) Resume Ingestion
- Convert PDFs → text
- Extract sections (optional)
- Chunk by paragraphs or bullets

### B) Embeddings & Storage
- Insert chunks into vector DB in a new namespace: `resumes`.
- Metadata:
  - resume_id
  - chunk_index
  - candidate_name (optional)

### C) MCP Tool: `resume_screening`

### Inputs:
- `job_description: string`
- `resume_ids: [ids]`

### Output:
```json
{
  "results": [
    {
      "resume_id": "string",
      "score": "float",
      "breakdown": {"semantic":0.82,"skills":0.61},
      "top_snippets": ["...", "...", "..."]
    }
  ]
}
````

### Ranking Logic (simple)

- Embed JD
- Fetch chunks for each resume
- Compute similarity:

  ```
  semantic_score = average top 5 similarities
  final_score = semantic_score * 0.7 + skill_match * 0.3
  ```

- Extract top chunks as snippets

### Skill Matching (lightweight)

- Hardcode a list of tech skills (e.g., Python, AWS)
- Count matches in text

---

## 5. Integration with LLM UI

For each candidate:

- LLM summarizes:

  - why they fit
  - risks
  - next actions

Show ranking table:
| Rank | Resume | Score | Fit Summary |


## 6. Steps for Coding Agent

1. Build resume → text extraction.
2. Chunk resumes.
3. Embed and store in vector DB.
4. Build MCP tool `resume_screening`.
5. Implement scoring formula.
6. Build recruiter UI section:

   - upload JD
   - upload resumes
   - view ranking



## 7. Success Indicators

- Ranks resumes in human-plausible order.
- Shows top 3 supporting snippets.
- Stable MCP tool call.



## 8. Future Extensions

- Title normalization
- Employment gap detection
- Bias mitigation
- ATS integration



---

# **Feature 3 — Onboarding Agent (Markdown File)**
**Filename: `Onboarding_Agent.md`**

```md
# Onboarding Agent (MCP Tool)

## 1. Overview
The Onboarding Agent acts as a conversational assistant that guides new hires through their first-week tasks.

This is the simplest feature:
- No RAG
- No embeddings
- Only JSON workflows



## 2. Objectives
The system must:
1. Provide a checklist of onboarding tasks.
2. Allow employees to ask:
   - “What should I do next?”
   - “What tasks are pending?”
3. Allow marking tasks as completed via MCP tool.
4. Show next tasks in the UI.



## 3. Architecture

````

Employee → Chat UI → LLM
↓ (MCP call)
onboarding Tool
↓
JSON Database

````

---

## 4. Components

### A) Onboarding Checklist Structure
Save as `onboarding_checklist.json`:

```json
{
  "engineering": [
    {"id": 1, "task": "Set up email", "completed": false},
    {"id": 2, "task": "Read engineering handbook", "completed": false},
    {"id": 3, "task": "Join Slack channels", "completed": false}
  ]
}
````

### B) MCP Tool: `onboarding`

Supported actions:

- `get_tasks`
- `mark_completed`
- `get_status`

### Input:

```json
{
  "employee_id": "E001",
  "action": "get_tasks",
  "payload": {}
}
```

### Output:

```json
{
  "tasks": [{ "id": 1, "task": "Set up email", "completed": false }]
}
```

---

## 5. LLM Prompt Integration

Instructions:

- Show tasks
- Provide guidance
- Never invent tasks

Example:

```
System: You are an onboarding assistant. Always use the task list returned by the tool.
```

---

## 6. Steps for Coding Agent

1. Load checklist JSON.
2. Build MCP tool handler with 3 actions.
3. Add simple state file (local JSON DB).
4. Connect UI to the tool.
5. Test flow with 2–3 questions.

---

## 7. Success Indicators

- Employee can see pending tasks.
- Employee can mark tasks completed.
- LLM responds based on MCP tool data.

---

## 8. Future Extensions

- HRIS integration
- Automated IT ticket creation
- Email reminders

```

Branch-by-branch checklist

### **Branch 1: `feature/hr-policy-rag`**

* Build ingestion
* Build vector DB indexing
* Build `policy_search` MCP tool
* Build RAG prompt
* Build Chat UI
* Test everything thoroughly
* Merge into `main`

This gives you a working end-to-end MCP agent.
Even if you stop here, the project is strong.

---

### **Branch 2: `feature/resume-screening`**

* Build resume ingestion
* Build resume embeddings
* Build score function
* Build MCP tool
* Build small recruiter UI or reuse chat
* Test with 5–10 resumes
* Merge into `main`

Even if this is not perfect, it’s an impressive second module.

---

### **Branch 3: `feature/onboarding-agent`**

* Create onboarding JSON checklist
* Build MCP tool with actions
* Add conversational workflow
* Add simple UI connections
* Merge when stable

This feature is easy and clean.

---
Things to keep in mind
---

# ✔ All three features are now documented in detailed Markdown files.

If you want:
- a **repo folder structure** containing these files,
- a **48-hour sprint plan**,
- or **actual full code implementations** for each feature + MCP server,

just say **“Create the full repo”** or **“Start with Feature 1 code.”**
```

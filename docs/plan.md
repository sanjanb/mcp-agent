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

---

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

---

## 7. Success Indicators

- Ranks resumes in human-plausible order.
- Shows top 3 supporting snippets.
- Stable MCP tool call.

---

## 8. Future Extensions

- Title normalization
- Employment gap detection
- Bias mitigation
- ATS integration

````

---

# **📄 Feature 3 — Onboarding Agent (Markdown File)**
**Filename: `Onboarding_Agent.md`**

```md
# Onboarding Agent (MCP Tool)

## 1. Overview
The Onboarding Agent acts as a conversational assistant that guides new hires through their first-week tasks.

This is the simplest feature:
- No RAG
- No embeddings
- Only JSON workflows

---

## 2. Objectives
The system must:
1. Provide a checklist of onboarding tasks.
2. Allow employees to ask:
   - “What should I do next?”
   - “What tasks are pending?”
3. Allow marking tasks as completed via MCP tool.
4. Show next tasks in the UI.

---

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

---

# ✔ All three features are now documented in detailed Markdown files.

If you want:
- a **repo folder structure** containing these files,
- a **48-hour sprint plan**,
- or **actual full code implementations** for each feature + MCP server,

just say **“Create the full repo”** or **“Start with Feature 1 code.”**
```

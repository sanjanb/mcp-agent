# Resume Screening Agent — Project Description**

The Resume Screening Agent helps recruiters quickly evaluate large numbers of resumes by comparing them with a given job description. It uses embeddings, structured analysis, and lightweight scoring logic to rank candidates based on relevance, skills, and experience. The goal is to reduce manual screening time and present recruiters with clear, evidence-based insights.

The agent reads resumes, extracts meaningful text, identifies key skills, and measures how closely each resume matches the job description. It surfaces the top candidates along with matched snippets and a short summary of fit. The system is designed to be simple, explainable, and reliable so recruiters understand why a candidate was ranked higher or lower.

The project supports:

* Uploading multiple resumes in PDF or text format
* Uploading a job description
* Automatic text extraction and cleaning
* Embedding-based similarity scoring
* Skill keyword detection
* Ranking resumes with transparent scoring
* Returning top snippets as evidence
* Optional LLM summaries for recruiter insight

The Resume Screening Agent is built to be easy to integrate into existing hiring workflows. It keeps the process consistent and helps avoid human fatigue during early-stage screening. Instead of replacing a recruiter, it gives them a fast, structured starting point for shortlisting candidates.

---
Here’s a **clear, realistic, industry-ready tech stack** for the **Resume Screening Agent**.
I’m keeping it practical, not bloated, and aligned with what you’ll actually build.

---

# **Tech Stack for Resume Screening Agent**

## **1. Backend / Core Processing**

### **Python**

The main language for:

* resume parsing
* text cleaning
* embedding generation
* scoring logic
* MCP integration

### **Key Python Libraries**

* **pdfplumber** → extract text from PDFs
* **spaCy / regex** → cleaning + preprocessing
* **sentence-transformers** → embedding generation (e.g., `all-MiniLM-L6-v2`)
* **numpy / sklearn** → similarity scoring
* **pydantic** → MCP tool input validation
* **fastapi** (optional) → if you need a local API wrapper

---

## **2. MCP (Model Context Protocol)**

You need MCP for:

* exposing resume screening as a tool
* structured input/output
* safe LLM interaction
* modular architecture

### **MCP Components**

* MCP server (`Python`)
* MCP tool: `resume_screening`
* JSON I/O schemas

---

## **3. Vector Database**

Used for storing resume embeddings.

Choose **one** depending on simplicity vs performance:

### **Recommended for your 48-hr build:**

* **ChromaDB (local)** → Zero setup, fast, perfect for hackathons

### Alternatives:

* Pinecone
* Weaviate
* Qdrant

But keep it simple unless you're integrating at production scale.

---

## **4. LLM Layer**

Used for:

* explanation summaries
* interpretation of match results
* answering recruiter questions

### Options:

* **OpenAI / GPT models**
* **Ollama local models**
* **GPT-4o mini (cheap + effective)**

Choose one depending on constraints.

---

## **5. Frontend / UI**

Have to add this feature to the main branch's frontend, I donno how, you have to figure it out

### **Recommended:**

* **Streamlit**
  Why?
* very fast to build
* easy file uploads
* perfect for interactive demo

---

## **6. Storage**

Only basic storage is needed.

### **Local storage:**

* `/resumes/` → uploaded resume PDFs
* `/embeddings/` → vector DB data
* `/logs/` → MCP tool logs


## **7. Data Formats**

* PDF or plain text resumes
* Job description as plain text
* JSON for tool communication
* Markdown for summaries

---

## **8. Version Control / Workflow**

* **GitHub**
* Branches:

  * `main`
  * `feature/resume-screening`

---

# **Short Version**

**Tech Stack:**

* Python, MCP, Sentence-Transformers
* ChromaDB for vector search
* pdfplumber for parsing resumes
* Streamlit for UI
* GPT-4o mini for summarization
* GitHub for version control

---


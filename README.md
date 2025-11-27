Okay, this is an incredibly detailed and well-thought-out platform design\! It's clear you've put a lot of effort into outlining the components and pipelines.

Based on your comprehensive description, here's an architecture image that visualizes your proposed AI Agent Platform. I've focused on clarity, modularity, and highlighting the shared infrastructure as well as the distinct feature pipelines.

```mermaid
graph TD
    subgraph Core Infrastructure
        A[Data Ingestion / ETL] --- B[Object Storage (Raw Docs)]
        A --- C[SQL DB (Metadata)]
        C --- D[Embedding Service (Cached, Versioned)]
        D --- E[Vector DB (Chroma/Pinecone/Milvus)]
        E --- F[LLM Provider (OpenAI/Private LLMs)]
        F --- G[Auth & Permissions (SSO/RBAC)]
        G --- H[Audit & Logging]
    end

    subgraph HR Assistant Agent (RAG)
        HRA_UI[Employee Chat UI (Slack/Teams/Web)] --- HRA_Ret[Retriever / RAG Orchestrator]
        B -- Policy Docs --> A
        A -- Chunked & Indexed --> E
        HRA_Ret -- Embed Query --> D
        HRA_Ret -- Retrieve Chunks --> E
        HRA_Ret -- Prompt LLM --> F
        F -- Answer + Citations + Confidence --> HRA_Logic[HR Assistant Business Logic]
        HRA_Logic -- Human-in-Loop / Escalation --> HRA_Admin[HR Admin Portal]
        HRA_Logic -- PII/Medical Flagging --> HRA_Safety[Safety & Legal Filters]
        HRA_Logic --- HRA_UI
        HRA_Safety --- H
    end

    subgraph Resume Screening Agent
        RS_UI[Recruiter Dashboard] --- RS_Score[Resume Scoring Logic]
        B -- Resumes / JDs --> A
        A -- Parsed & Chunked --> E
        RS_Score -- Embed JD/Chunks --> D
        RS_Score -- Similarity & Rule Engine --> E
        RS_Score -- Summarize Fit (LLM) --> F
        RS_Score -- Bias Mitigation --> RS_Bias[Bias Checks]
        RS_Score -- Human Feedback Loop --> RS_Admin[HR Admin Portal]
        RS_Score --- RS_UI
        RS_Bias --- H
    end

    subgraph Employee Onboarding Agent
        EO_UI[New Hire Chat UI (Web/Email)] --- EO_Workflow[Workflow Engine]
        EO_Workflow -- Conversational Flow (LLM) --> F
        EO_Workflow -- RAG for Q&A --> HRA_Ret
        EO_Workflow -- Task Assignment & State Tracking --> C
        EO_Workflow -- Escalation / Ticketing --> EO_Integrations[IT/HR Integrations]
        EO_Integrations --- EO_Admin[HR Admin Portal]
        EO_Workflow --- EO_UI
        EO_Workflow --- H
    end

    HRA_Admin --- G
    RS_Admin --- G
    EO_Admin --- G

    style A fill:#D6EAF8,stroke:#2E86C1,stroke-width:2px
    style B fill:#F5EEF8,stroke:#9B59B6,stroke-width:2px
    style C fill:#E8F8F5,stroke:#28B463,stroke-width:2px
    style D fill:#FCF3CF,stroke:#F4D03F,stroke-width:2px
    style E fill:#D5F5E3,stroke:#2ECC71,stroke-width:2px
    style F fill:#FADBD8,stroke:#E74C3C,stroke-width:2px
    style G fill:#EBDEF0,stroke:#AF7AC5,stroke-width:2px
    style H fill:#EAF2F8,stroke:#5D6D7E,stroke-width:2px

    style HRA_UI fill:#A9DFBF,stroke:#27AE60,stroke-width:2px
    style HRA_Ret fill:#D4EFDF,stroke:#2ECC71,stroke-width:2px
    style HRA_Logic fill:#E8F6F3,stroke:#1ABC9C,stroke-width:2px
    style HRA_Admin fill:#FADBD8,stroke:#C0392B,stroke-width:2px
    style HRA_Safety fill:#F5B7B1,stroke:#E74C3C,stroke-width:2px

    style RS_UI fill:#F9E79F,stroke:#F4D03F,stroke-width:2px
    style RS_Score fill:#FCF3CF,stroke:#F1C40F,stroke-width:2px
    style RS_Bias fill:#FAD7A0,stroke:#E67E22,stroke-width:2px
    style RS_Admin fill:#FADBD8,stroke:#C0392B,stroke-width:2px

    style EO_UI fill:#D6DBDF,stroke:#7F8C8D,stroke-width:2px
    style EO_Workflow fill:#EBF5FB,stroke:#3498DB,stroke-width:2px
    style EO_Integrations fill:#DDEBF1,stroke:#5DADE2,stroke-width:2px
    style EO_Admin fill:#FADBD8,stroke:#C0392B,stroke-width:2px

```

**Explanation of the Architecture:**

1.  **Core Infrastructure (Top):** This central block shows the shared services that all three agents leverage.

    - **Data Ingestion/ETL** feeds into **Object Storage** (for raw files) and **SQL DB** (for metadata).
    - **Embedding Service** (cached, versioned) and **Vector DB** (for search) are core for RAG and similarity-based tasks.
    - **LLM Provider** is the gateway to your chosen LLMs.
    - **Auth & Permissions** and **Audit & Logging** are cross-cutting concerns.

2.  **HR Assistant Agent (Left):**

    - Highlights the flow from `Employee Chat UI` to the `Retriever / RAG Orchestrator`, which uses `Embedding Service` and `Vector DB`.
    - The `LLM Provider` generates answers.
    - A dedicated `HR Assistant Business Logic` handles citations, confidence, PII filtering (`Safety & Legal Filters`), and `Human-in-Loop / Escalation` via the `HR Admin Portal`.

3.  **Resume Screening Agent (Middle):**

    - Starts with `Recruiter Dashboard`.
    - `Resume Scoring Logic` uses embeddings (`Embedding Service`, `Vector DB`) and a `Rule Engine` (implicitly part of the scoring logic).
    - `LLM Provider` is used for summarization/explainability.
    - `Bias Checks` are called out as a specific component of the scoring.
    - `Human Feedback Loop` goes to the `HR Admin Portal`.

4.  **Employee Onboarding Agent (Right):**

    - Driven by the `New Hire Chat UI`.
    - A `Workflow Engine` manages tasks and state, interacting with `SQL DB` for state.
    - `LLM Provider` is used for conversational flow and Q\&A (which might also tap into the RAG retriever from the HR Assistant for specific docs).
    - `IT/HR Integrations` handle external system interactions.
    - `HR Admin Portal` for workflow configuration.

5.  **Arrows and Connections:** Show the data and control flow, emphasizing how agent-specific components interact with the shared infrastructure. `HR Admin Portal` acts as a central control point for all three agents for configuration, human-in-loop, and feedback.

This architecture clearly visualizes the modularity and shared components you've described, making it easy to understand the platform's structure at a glance.

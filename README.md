Okay, this is an incredibly detailed and well-thought-out platform design\! It's clear you've put a lot of effort into outlining the components and pipelines.

Based on your comprehensive description, here's an architecture image that visualizes your proposed AI Agent Platform. I've focused on clarity, modularity, and highlighting the shared infrastructure as well as the distinct feature pipelines.

```mermaid
graph TD
    subgraph CI["Core Infrastructure"]
        A[Data Ingestion / ETL] --- B[Object Storage - Raw Docs]
        A --- C[SQL DB - Metadata]
        C --- D[Embedding Service - Cached, Versioned]
        D --- E[Vector DB - Chroma/Pinecone/Milvus]
        E --- F[LLM Provider - OpenAI/Private LLMs]
        F --- G[Auth & Permissions - SSO/RBAC]
        G --- H[Audit & Logging]
    end

    subgraph HRA["HR Assistant Agent (RAG)"]
        HRA_UI[Employee Chat UI - Slack/Teams/Web]
        HRA_Ret[Retriever / RAG Orchestrator]
        HRA_Logic[HR Assistant Business Logic]
        HRA_Admin[HR Admin Portal]
        HRA_Safety[Safety & Legal Filters]

        HRA_UI --- HRA_Ret
        HRA_Ret --- HRA_Logic
        HRA_Logic --- HRA_UI
        HRA_Logic --- HRA_Admin
        HRA_Logic --- HRA_Safety
    end

    subgraph RSA["Resume Screening Agent"]
        RS_UI[Recruiter Dashboard]
        RS_Score[Resume Scoring Logic]
        RS_Bias[Bias Checks]
        RS_Admin[HR Admin Portal]

        RS_UI --- RS_Score
        RS_Score --- RS_Bias
        RS_Score --- RS_Admin
    end

    subgraph EOA["Employee Onboarding Agent"]
        EO_UI[New Hire Chat UI - Web/Email]
        EO_Workflow[Workflow Engine]
        EO_Integrations[IT/HR Integrations]
        EO_Admin[HR Admin Portal]

        EO_UI --- EO_Workflow
        EO_Workflow --- EO_Integrations
        EO_Integrations --- EO_Admin
    end

    %% Core Infrastructure Connections
    B -.-> A

    %% HR Assistant Agent Connections
    HRA_Ret -.-> D
    HRA_Ret -.-> E
    HRA_Ret -.-> F
    HRA_Safety -.-> H
    HRA_Admin -.-> G

    %% Resume Screening Agent Connections
    B -.-> RS_Score
    RS_Score -.-> D
    RS_Score -.-> E
    RS_Score -.-> F
    RS_Bias -.-> H
    RS_Admin -.-> G

    %% Employee Onboarding Agent Connections
    EO_Workflow -.-> F
    EO_Workflow -.-> HRA_Ret
    EO_Workflow -.-> C
    EO_Workflow -.-> H
    EO_Admin -.-> G

    %% Styling
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

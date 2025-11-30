# **📘Onboarding Agent — Project Description (For Copilot / Coding Agent)**

The Onboarding Agent is a simple workflow automation tool that helps new employees track and complete their onboarding tasks. It exposes a small set of actions through an MCP tool so an LLM-powered UI can guide users through the onboarding process.

The system works on a JSON-based checklist instead of a database. Each employee or role has a list of tasks, each with an ID, description, and completion status. The MCP tool provides functions to read tasks, update tasks, and return the current onboarding status. The goal is to keep the implementation simple, predictable, and safe.

### **Core Features**

1. Load onboarding tasks from a JSON file.
2. Return all tasks for a given employee or role.
3. Mark a task as completed using its task ID.
4. Return the onboarding progress (percentage completed).
5. Expose all functionality through an MCP tool called `onboarding`.
6. Ensure all tool responses are structured, predictable JSON.

### **MCP Tool Actions**

The tool should support these actions:

- **get_tasks** → return the task list
- **mark_completed** → update a task’s completed status
- **get_status** → return progress stats

Each action receives a JSON payload and returns a JSON response.

### **Checklist Example (JSON File)**

The checklist file should follow this structure:

```json
{
  "engineering": [
    { "id": 1, "task": "Set up email", "completed": false },
    { "id": 2, "task": "Read engineering handbook", "completed": false },
    { "id": 3, "task": "Join Slack channels", "completed": false }
  ]
}
```

### **Expected MCP Tool Input Example**

```json
{
  "action": "get_tasks",
  "role": "engineering"
}
```

### **Expected MCP Tool Output Example**

```json
{
  "tasks": [
    { "id": 1, "task": "Set up email", "completed": false },
    { "id": 2, "task": "Read engineering handbook", "completed": false },
    { "id": 3, "task": "Join Slack channels", "completed": false }
  ]
}
```

### **Tech Requirements**

- Python (for implementation)
- Local JSON file for storage
- MCP server + MCP tool definition
- No database or RAG required
- No embedding models needed

### **Constraints**

- Keep code simple and readable
- Every action must validate inputs
- Return errors in clear JSON format
- Avoid side effects or global state
- Update the JSON file safely on write

### **What the LLM/UI will do**

The UI or chat agent will call the MCP tool to:

- Display tasks
- Show pending vs completed items
- Provide next-step guidance using LLM

So the MCP tool must return structured data that the LLM can convert into helpful answers.

---

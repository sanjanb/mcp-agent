# **Project Rules & Guidelines (Keep This Always in Mind)**

## **1. One Feature at a Time**

- Work on **only one feature branch** at any moment.
- Finish it fully before touching anything else.
- Merge only when the feature is stable and tested.

**Reason:** prevents broken pipelines and confusing bug chains.

---

## **2. Keep `main` / `master` Always Clean**

- Never push unfinished code to `main`.
- `main` must always run without errors.
- Treat `main` as demo-ready at all times.

---

## **3. Start Small, Don’t Overbuild**

- Build the **smallest version** of the feature first.
- Make it work.
- Only then add small improvements.

Avoid:

- Fancy UI early
- Full backend abstraction
- Overthinking architecture
- Integrating multiple systems at once

---

## **4. Make To-do Lists for Everything**

Before starting a feature, we’ll always create:

- A clear list of tasks
- A clear order to execute them
- A clear definition of “done”

This keeps the work predictable.

---

## **5. Test Code Immediately After Writing It**

After every small part:

- run it
- check logs
- check outputs
- catch bugs early

**Don’t jump ahead without testing.**

---

## **6. If Something Breaks, Stop Immediately**

Don’t continue writing more code.

Steps:

1. Stop.
2. Tell me exactly what broke.
3. Share the output or traceback.
4. We fix only that part.
5. Test again after fixing.

No rushing.

---

## **7. Keep All Features Independent**

HR RAG
Resume Screener
Onboarding

These should not rely on each other’s code to work.

This prevents cross-feature bugs.

---

## **8. Use Clear and Simple File Structure**

Don’t create too many folders early.

Start with:

```
/project
  /mcp_server
  /tools
     /policy_rag
     /resume_screening
     /onboarding
  /data
  /ui
```

We add structure **only when needed**.

---

## **9. Avoid Doing Everything in One File**

But also avoid splitting files too early.

Rule:

- If a file is >200 lines or has >2 responsibilities, split it.

---

## **10. Keep Code Readable**

Avoid overly complex patterns early.

Prefer:

- simple if/else
- simple classes
- clear names
- short functions

---

## **11. Always Log What Tools Are Doing**

Every MCP tool should log:

- when it starts
- the input it received
- what it returns

This makes debugging easy.

---

## **12. Never Touch Vector DB Unless Needed**

Build ingestion → test
Build search → test

Don’t rebuild embeddings unless something is broken.

---

## **13. Each Feature Must Have Its Own “Definition of Done”**

For example:

### HR Policy RAG Done When:

- documents ingested
- embeddings stored
- MCP tool returns chunks
- UI can ask questions
- LLM responds with citations

Only then merge.

### Resume Screener Done When:

- resume ingestion works
- embeddings stored
- scoring works
- MCP tool returns rankings
- UI displays ranking

### Onboarding Done When:

- checklist loads
- MCP tool returns tasks
- tasks can be marked done
- chat assistant responds using tool data

---

## **14. No Guessing. If unsure, stop and ask.**

Before writing code:

- clarify
- verify
- confirm steps

No assumptions.

---

## **15. Make Safe Commits**

After something works:

- commit
- push to feature branch
- tag the commit (optional)

So if something breaks later, we can go back.

---

## **16. Manual Review Before Merge**

Checklist before merging into main:

- Does it run?
- Did we test basic scenarios?
- Does the UI behave correctly?
- Is the MCP tool answering consistently?
- No leftover debug prints?
- README updated?

Only then merge.

---

## **17. Keep All Instructions in 프로젝트 root**

You can create a simple file:

`WORKFLOW_RULES.md`

Add all rules there so you never forget them.

---

## **18. No Complex Refactors During Feature Dev**

If you feel like “cleaning up everything,” don’t.
Finish the feature → test → merge → then consider refactor.

---

# 💡 Summary (Short Version)

To keep everything safe and stable:

- One feature → one branch → one merge
- Small steps → test each step → fix fast
- Don’t start new code if something is broken
- No heavy architecture early
- Keep main stable
- Keep communication clear and simple

This guarantees:

- no surprises
- no broken pipelines
- no lost progress
- predictable development
- clean demo-ready code at every stage

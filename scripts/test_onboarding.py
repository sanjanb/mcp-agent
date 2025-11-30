"""Simple validation script for onboarding MCP tool.
Run: python scripts/test_onboarding.py
"""
from tools.onboarding.mcp_tool import (
    onboarding_get_tasks,
    onboarding_mark_completed,
    onboarding_get_status,
)
import json
import os
from pathlib import Path

ROLE = "engineering"

def show(title, obj):
    print(f"\n== {title} ==")
    print(json.dumps(obj, indent=2)[:1000])


def main():
    # 1. Get tasks
    tasks_resp = onboarding_get_tasks(ROLE)
    show("Initial Tasks", tasks_resp)
    assert tasks_resp.get("success"), "Failed to load tasks"
    tasks = tasks_resp.get("tasks", [])
    assert tasks, "No tasks returned"

    # 2. Get status
    status_resp = onboarding_get_status(ROLE)
    show("Initial Status", status_resp)
    assert status_resp.get("success"), "Failed to get status"

    # 3. Mark first incomplete task
    target_task = next((t for t in tasks if not t.get("completed")), None)
    if target_task:
        mark_resp = onboarding_mark_completed(ROLE, target_task["id"])
        show("Mark Completed", mark_resp)
        assert mark_resp.get("success"), "Failed to mark completed"
    else:
        print("All tasks already completed; skipping mark test.")

    # 4. Status after update
    status_after = onboarding_get_status(ROLE)
    show("Status After Update", status_after)
    assert status_after.get("success"), "Failed to get status after update"

    print("\nAll onboarding tool checks passed.")

if __name__ == "__main__":
    main()

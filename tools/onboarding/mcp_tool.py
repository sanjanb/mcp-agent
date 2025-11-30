"""Onboarding MCP Tool

Provides structured access to onboarding task checklists stored in a JSON file.
Actions:
- onboarding_get_tasks(role)
- onboarding_mark_completed(role, task_id)
- onboarding_get_status(role)

All responses are JSON-serializable dicts with predictable keys.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List
import threading
import os

_LOCK = threading.Lock()

DEFAULT_TASKS_PATH = Path(os.getenv("ONBOARDING_TASKS_PATH", Path(__file__).parent.parent.parent / "data" / "onboarding_tasks.json"))

def _load_tasks(path: Path = DEFAULT_TASKS_PATH) -> Dict[str, List[Dict[str, Any]]]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        return {"__error__": f"Failed to read tasks file: {exc}"}

def _write_tasks(data: Dict[str, List[Dict[str, Any]]], path: Path = DEFAULT_TASKS_PATH) -> bool:
    tmp_path = path.with_suffix(".tmp")
    try:
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        tmp_path.replace(path)
        return True
    except Exception:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass
        return False

def onboarding_get_tasks(role: str) -> Dict[str, Any]:
    tasks_data = _load_tasks()
    if "__error__" in tasks_data:
        return {"success": False, "error": tasks_data["__error__"], "role": role}
    if role not in tasks_data:
        return {"success": False, "error": f"Role '{role}' not found", "available_roles": list(tasks_data.keys())}
    return {"success": True, "role": role, "tasks": tasks_data[role]}

def onboarding_mark_completed(role: str, task_id: int) -> Dict[str, Any]:
    with _LOCK:
        tasks_data = _load_tasks()
        if "__error__" in tasks_data:
            return {"success": False, "error": tasks_data["__error__"], "role": role}
        if role not in tasks_data:
            return {"success": False, "error": f"Role '{role}' not found", "available_roles": list(tasks_data.keys())}
        tasks = tasks_data[role]
        target = None
        for t in tasks:
            if t.get("id") == task_id:
                target = t
                break
        if not target:
            return {"success": False, "error": f"Task id {task_id} not found for role '{role}'", "role": role}
        if target.get("completed") is True:
            return {"success": True, "role": role, "task_id": task_id, "updated": target, "note": "Already completed"}
        target["completed"] = True
        if not _write_tasks(tasks_data):
            target["completed"] = False  # rollback
            return {"success": False, "error": "Failed to persist task update", "role": role, "task_id": task_id}
        return {"success": True, "role": role, "task_id": task_id, "updated": target}

def onboarding_get_status(role: str) -> Dict[str, Any]:
    tasks_data = _load_tasks()
    if "__error__" in tasks_data:
        return {"success": False, "error": tasks_data["__error__"], "role": role}
    if role not in tasks_data:
        return {"success": False, "error": f"Role '{role}' not found", "available_roles": list(tasks_data.keys())}
    tasks = tasks_data[role]
    total = len(tasks)
    completed = sum(1 for t in tasks if t.get("completed"))
    pct = (completed / total * 100.0) if total else 0.0
    return {
        "success": True,
        "role": role,
        "total_tasks": total,
        "completed_tasks": completed,
        "percent_complete": round(pct, 2),
        "remaining_tasks": [t for t in tasks if not t.get("completed")]
    }

MCP_TOOLS = {
    "onboarding_get_tasks": {
        "description": "Return all onboarding tasks for a given role.",
        "parameters": {
            "role": {"type": "string", "description": "Role identifier (e.g., engineering, hr)"}
        },
        "function": onboarding_get_tasks,
    },
    "onboarding_mark_completed": {
        "description": "Mark an onboarding task as completed by id for a role.",
        "parameters": {
            "role": {"type": "string", "description": "Role identifier"},
            "task_id": {"type": "number", "description": "Numeric task id"}
        },
        "function": onboarding_mark_completed,
    },
    "onboarding_get_status": {
        "description": "Get progress statistics for a role's onboarding tasks.",
        "parameters": {
            "role": {"type": "string", "description": "Role identifier"}
        },
        "function": onboarding_get_status,
    }
}

__all__ = ["MCP_TOOLS"]

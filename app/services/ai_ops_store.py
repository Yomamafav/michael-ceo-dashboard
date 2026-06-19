from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
AI_OPS_PATH = DATA_DIR / "ai_ops.json"

AGENT_STATUSES = ("idle", "running", "error", "scheduled", "disabled")
INBOX_TYPES = ("report", "alert", "recommendation", "info")
INBOX_STATUSES = ("unread", "read", "actioned", "dismissed")


def _default_data() -> dict[str, Any]:
    return {
        "agents": [
            {
                "id": "agent-1",
                "name": "Chief of Staff",
                "agent_type": "chief_of_staff",
                "description": "Reviews all agent reports, detects blockers, surfaces questions, and keeps COMMAND_CENTER.md current.",
                "status": "idle",
                "last_run": "",
                "next_run": "",
                "last_result": "Not yet run.",
                "error_message": "",
                "registered_at": datetime.now().isoformat(timespec="seconds"),
            },
        ],
        "inbox": [],
        "activity": [],
    }


def ensure_ai_ops_storage() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not AI_OPS_PATH.exists():
        AI_OPS_PATH.write_text(json.dumps(_default_data(), indent=2), encoding="utf-8")


def _load() -> dict[str, Any]:
    ensure_ai_ops_storage()
    try:
        with AI_OPS_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            defaults = _default_data()
            for key in defaults:
                data.setdefault(key, defaults[key])
            return data
    except json.JSONDecodeError:
        pass
    return _default_data()


def _save(data: dict[str, Any]) -> None:
    AI_OPS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _next_id(collection: list[dict[str, Any]], prefix: str) -> str:
    existing = {item["id"] for item in collection}
    index = len(collection) + 1
    new_id = f"{prefix}{index}"
    while new_id in existing:
        index += 1
        new_id = f"{prefix}{index}"
    return new_id


# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------

def get_agents() -> list[dict[str, Any]]:
    return _load()["agents"]


def register_agent(fields: dict[str, Any]) -> dict[str, Any]:
    data = _load()
    new_id = _next_id(data["agents"], "agent-")
    agent: dict[str, Any] = {
        "id": new_id,
        "name": str(fields.get("name", "")).strip(),
        "agent_type": str(fields.get("agent_type", "")).strip(),
        "description": str(fields.get("description", "")).strip(),
        "status": "idle",
        "last_run": "",
        "next_run": str(fields.get("next_run", "")).strip(),
        "last_result": "",
        "error_message": "",
        "registered_at": _now_iso(),
    }
    data["agents"].append(agent)
    _save(data)
    return agent


def update_agent_status(agent_id: str, fields: dict[str, Any]) -> dict[str, Any]:
    data = _load()
    agent = next((a for a in data["agents"] if a["id"] == agent_id), None)
    if agent is None:
        raise KeyError(f"Agent {agent_id} not found")
    if fields.get("status") in AGENT_STATUSES:
        agent["status"] = fields["status"]
    if fields.get("last_run"):
        agent["last_run"] = str(fields["last_run"]).strip()
    if fields.get("next_run") is not None:
        agent["next_run"] = str(fields["next_run"]).strip()
    if fields.get("last_result") is not None:
        agent["last_result"] = str(fields["last_result"]).strip()
    if fields.get("error_message") is not None:
        agent["error_message"] = str(fields["error_message"]).strip()
    _save(data)
    # AUTOMATION HOOK: if status == "error", alert Michael
    # future: if agent["status"] == "error": push_notification(to="michael", subject=f"Agent error: {agent['name']}", body=agent["error_message"])
    return agent


# ---------------------------------------------------------------------------
# Inbox
# ---------------------------------------------------------------------------

def get_inbox(status: str | None = None) -> list[dict[str, Any]]:
    items = _load()["inbox"]
    if status:
        items = [i for i in items if i.get("status") == status]
    return items


def create_inbox_item(fields: dict[str, Any]) -> dict[str, Any]:
    data = _load()
    new_id = _next_id(data["inbox"], "inbox-")
    item: dict[str, Any] = {
        "id": new_id,
        "agent_name": str(fields.get("agent_name", "Agent")).strip(),
        "agent_type": str(fields.get("agent_type", "")).strip(),
        "subject": str(fields.get("subject", "")).strip(),
        "summary": str(fields.get("summary", "")).strip(),
        "body": str(fields.get("body", "")).strip(),
        "type": str(fields.get("type", "info")).strip() if fields.get("type") in INBOX_TYPES else "info",
        "status": "unread",
        "action_required": str(fields.get("action_required", "false")).lower() in ("true", "1", "yes"),
        "created_at": _now_iso(),
    }
    data["inbox"].insert(0, item)
    _save(data)
    # AUTOMATION HOOK: if action_required, surface in Michael's attention queue
    # future: if item["action_required"]: push_notification(to="michael", subject=item["subject"], body=item["summary"])
    return item


def update_inbox_item(item_id: str, fields: dict[str, Any]) -> dict[str, Any]:
    data = _load()
    item = next((i for i in data["inbox"] if i["id"] == item_id), None)
    if item is None:
        raise KeyError(f"Inbox item {item_id} not found")
    if fields.get("status") in INBOX_STATUSES:
        item["status"] = fields["status"]
    _save(data)
    return item


# ---------------------------------------------------------------------------
# Activity Feed
# ---------------------------------------------------------------------------

def get_activity(limit: int = 50) -> list[dict[str, Any]]:
    return _load()["activity"][:limit]


def add_activity(fields: dict[str, Any]) -> dict[str, Any]:
    data = _load()
    new_id = _next_id(data["activity"], "act-")
    entry: dict[str, Any] = {
        "id": new_id,
        "timestamp": _now_iso(),
        "agent_name": str(fields.get("agent_name", "")).strip(),
        "action": str(fields.get("action", "")).strip(),
        "detail": str(fields.get("detail", "")).strip(),
        "type": str(fields.get("type", "info")).strip(),
    }
    data["activity"].insert(0, entry)
    if len(data["activity"]) > 200:
        data["activity"] = data["activity"][:200]
    _save(data)
    return entry

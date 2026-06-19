from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
CC_PATH = DATA_DIR / "command_center.json"

TASK_STATUSES = ("New", "In Progress", "Blocked", "Waiting for Michael", "Complete")
TASK_PRIORITIES = ("High", "Medium", "Low")
APPROVAL_DECISIONS = ("approved", "rejected", "needs_changes")
QUESTION_STATUSES = ("pending", "answered")


def _default_data() -> dict[str, Any]:
    return {
        "tasks": [
            {
                "id": "task-1",
                "title": "Connect Google Sheets as live data source",
                "description": "Replace mock briefing data with real Google Sheets data. GOOGLE_SHEETS_ENABLED flag already exists in .env.example — just needs a live test.",
                "assigned_to": "Claude Code",
                "priority": "High",
                "status": "New",
                "due": "",
                "created_at": "2026-06-19T10:00:00",
                "updated_at": "2026-06-19T10:00:00",
                "notes": "",
                "notes_history": [],
            },
            {
                "id": "task-2",
                "title": "Overdue follow-up notifications",
                "description": "Alert Michael when a follow-up is due 'Today' and it's past 5 PM without being marked complete.",
                "assigned_to": "Claude Code",
                "priority": "Medium",
                "status": "New",
                "due": "",
                "created_at": "2026-06-19T10:00:00",
                "updated_at": "2026-06-19T10:00:00",
                "notes": "",
                "notes_history": [],
            },
            {
                "id": "task-3",
                "title": "Mobile update photo attachments",
                "description": "Allow attaching a photo (job site, receipt) when submitting a mobile update.",
                "assigned_to": "Claude Code",
                "priority": "Low",
                "status": "New",
                "due": "",
                "created_at": "2026-06-19T10:00:00",
                "updated_at": "2026-06-19T10:00:00",
                "notes": "",
                "notes_history": [],
            },
        ],
        "questions": [
            {
                "id": "q-1",
                "question": "Should the dashboard auto-refresh every few minutes when open on a laptop?",
                "context": "If the crew submits a mobile update, Michael won't see it without manually refreshing. Auto-refresh fixes this but adds background polling.",
                "asked_at": "2026-06-19T09:00:00",
                "asked_by": "Claude Code",
                "task_id": None,
                "status": "pending",
                "answer": "",
                "answered_at": None,
            },
            {
                "id": "q-2",
                "question": "Do you want to track revenue totals per month, or just the current day targets?",
                "context": "The construction and printing revenue cards currently show only daily targets. Monthly tracking would require a more permanent data store.",
                "asked_at": "2026-06-19T09:30:00",
                "asked_by": "Claude Code",
                "task_id": None,
                "status": "pending",
                "answer": "",
                "answered_at": None,
            },
        ],
        "project_status": {
            "mission": "Build a local-first, mobile-friendly CEO dashboard for Michael to manage 4 My4 Construction and POG Printing daily operations — accessible from the shop laptop and the phone in the field.",
            "active_task_ids": ["task-1", "task-2"],
            "blockers": [],
            "completed_work": [
                {
                    "date": "2026-06-19",
                    "description": "Agent Command Center: new /command-center tab with Command Inbox, Agent Questions, Project Status, Change Log, and Approval Queue. All data stored locally in app/data/command_center.json.",
                },
                {
                    "date": "2026-06-18",
                    "description": "Phase 1 interactivity: clickable cards, detail modals, action buttons (complete, note, deposit-paid, payment-received), add-item forms for all 6 categories.",
                },
                {
                    "date": "2026-06-17",
                    "description": "Initial dashboard: FastAPI server, Jinja2 templates, Google Sheets integration with mock fallback, mobile update form, updates log.",
                },
            ],
            "next_recommended_action": "Enable GOOGLE_SHEETS_ENABLED=true in .env and run a live test against the real spreadsheet. The integration code already exists — just needs a connected service account.",
        },
        "change_log": [
            {
                "id": "cl-1",
                "timestamp": "2026-06-19T10:00:00",
                "feature": "Agent Command Center",
                "files_changed": [
                    "app/main.py",
                    "app/services/command_center_store.py",
                    "app/templates/command_center.html",
                    "app/static/command_center.js",
                    "app/static/styles.css",
                    "app/data/command_center.json",
                    "app/templates/base.html",
                ],
                "description": "Added /command-center page with 5 sections: Command Inbox (create/assign tasks), Agent Questions (answer and mark resolved), Project Status (mission/blockers/next action), Change Log (file-level audit trail), Approval Queue (approve/reject/needs-changes).",
                "agent_notes": "All data is local JSON. Automation hook stubs are in place at every action that will eventually trigger agent calls or external API writes.",
            },
            {
                "id": "cl-2",
                "timestamp": "2026-06-18T18:00:00",
                "feature": "Phase 1 interactivity",
                "files_changed": [
                    "app/main.py",
                    "app/services/items_store.py",
                    "app/templates/base.html",
                    "app/static/app.js",
                    "app/static/styles.css",
                    "app/data/dashboard_items.json",
                ],
                "description": "Added clickable item cards with detail modals, action buttons (complete, note, deposit-paid, payment-received), and add-item forms for all 6 dashboard categories.",
                "agent_notes": "Item actions write to local JSON only. Google Sheets write-back explicitly deferred. Modal reloads page when dirty (modalDirty flag).",
            },
            {
                "id": "cl-3",
                "timestamp": "2026-06-17T14:00:00",
                "feature": "Initial dashboard build",
                "files_changed": [
                    "app/main.py",
                    "app/services/data_store.py",
                    "app/services/google_sheets.py",
                    "app/templates/dashboard.html",
                    "app/templates/mobile.html",
                    "app/templates/base.html",
                    "app/static/styles.css",
                    "app/data/mobile_updates.json",
                ],
                "description": "Initial FastAPI server with dashboard, mobile update form, and updates log. Google Sheets integration gated by GOOGLE_SHEETS_ENABLED env flag.",
                "agent_notes": "Mock data lives in app/data/mobile_updates.json. Real Sheets connection requires a service-account JSON and credentials configured in .env.",
            },
        ],
        "approvals": [
            {
                "id": "ap-1",
                "title": "Agent Command Center tab",
                "description": "New /command-center page with 5 sections: Command Inbox, Agent Questions, Project Status, Change Log, and Approval Queue. Data stored locally in app/data/command_center.json. Structure is compatible with Google Sheets, Firebase, Supabase, or a local SQL database for future migration.",
                "requested_at": "2026-06-19T10:00:00",
                "status": "pending",
                "feedback": "",
                "decided_at": None,
                "files_affected": [
                    "app/main.py",
                    "app/services/command_center_store.py",
                    "app/templates/command_center.html",
                    "app/static/command_center.js",
                    "app/static/styles.css",
                    "app/data/command_center.json",
                ],
            }
        ],
    }


def ensure_cc_storage() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not CC_PATH.exists():
        CC_PATH.write_text(json.dumps(_default_data(), indent=2), encoding="utf-8")


def load_cc() -> dict[str, Any]:
    ensure_cc_storage()
    try:
        with CC_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            for key, default_val in _default_data().items():
                data.setdefault(key, default_val)
            _migrate(data)
            return data
    except json.JSONDecodeError:
        pass
    return _default_data()


def _migrate(data: dict[str, Any]) -> None:
    """Backfill new fields onto records written before the schema was extended."""
    changed = False
    for task in data.get("tasks", []):
        if "due" not in task:
            task["due"] = ""
            changed = True
        if "notes_history" not in task:
            task["notes_history"] = [{"timestamp": task.get("updated_at", ""), "text": task["notes"]}] if task.get("notes") else []
            changed = True
    for q in data.get("questions", []):
        if "task_id" not in q:
            q["task_id"] = None
            changed = True
        if "asked_by" not in q:
            q["asked_by"] = "Claude Code"
            changed = True
    for ap in data.get("approvals", []):
        if "requested_by" not in ap:
            ap["requested_by"] = "Claude Code"
            changed = True
    if changed:
        save_cc(data)


def save_cc(data: dict[str, Any]) -> None:
    CC_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

def get_tasks() -> list[dict[str, Any]]:
    return load_cc()["tasks"]


def create_task(fields: dict[str, Any]) -> dict[str, Any]:
    data = load_cc()
    existing_ids = {t["id"] for t in data["tasks"]}
    index = len(data["tasks"]) + 1
    new_id = f"task-{index}"
    while new_id in existing_ids:
        index += 1
        new_id = f"task-{index}"

    now = _now_iso()
    task: dict[str, Any] = {
        "id": new_id,
        "title": str(fields.get("title", "")).strip(),
        "description": str(fields.get("description", "")).strip(),
        "assigned_to": str(fields.get("assigned_to", "Claude Code")).strip() or "Claude Code",
        "priority": str(fields.get("priority", "Medium")).strip() if fields.get("priority") in TASK_PRIORITIES else "Medium",
        "status": "New",
        "due": str(fields.get("due", "")).strip(),
        "created_at": now,
        "updated_at": now,
        "notes": str(fields.get("notes", "")).strip(),
        "notes_history": [],
    }
    if task["notes"]:
        task["notes_history"] = [{"timestamp": now, "text": task["notes"]}]
    data["tasks"].insert(0, task)
    save_cc(data)
    # AUTOMATION HOOK: notify assigned agent that a new task was created
    # future: trigger_agent_notification(task["assigned_to"], "new_task", task)
    return task


def update_task(task_id: str, fields: dict[str, Any]) -> dict[str, Any]:
    data = load_cc()
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        raise KeyError(f"Task {task_id} not found")
    if fields.get("status") in TASK_STATUSES:
        task["status"] = fields["status"]
    if fields.get("priority") in TASK_PRIORITIES:
        task["priority"] = fields["priority"]
    if fields.get("due") is not None:
        task["due"] = str(fields["due"]).strip()
    if fields.get("notes"):
        note_text = str(fields["notes"]).strip()
        note_entry = {"timestamp": _now_iso(), "text": note_text}
        task["notes_history"] = [note_entry] + task.get("notes_history", [])
        task["notes"] = note_text  # keep latest for display
    task["updated_at"] = _now_iso()
    save_cc(data)
    # AUTOMATION HOOK: if status changed to "Blocked", surface in agent's attention queue
    # future: if task["status"] == "Blocked": alert_michael(task)
    return task


# ---------------------------------------------------------------------------
# Questions
# ---------------------------------------------------------------------------

def get_questions() -> list[dict[str, Any]]:
    return load_cc()["questions"]


def create_question(fields: dict[str, Any]) -> dict[str, Any]:
    data = load_cc()
    existing_ids = {q["id"] for q in data["questions"]}
    index = len(data["questions"]) + 1
    new_id = f"q-{index}"
    while new_id in existing_ids:
        index += 1
        new_id = f"q-{index}"

    question: dict[str, Any] = {
        "id": new_id,
        "question": str(fields.get("question", "")).strip(),
        "context": str(fields.get("context", "")).strip(),
        "asked_at": _now_iso(),
        "asked_by": str(fields.get("asked_by", "Claude Code")).strip() or "Claude Code",
        "task_id": fields.get("task_id") or None,
        "status": "pending",
        "answer": "",
        "answered_at": None,
    }
    data["questions"].insert(0, question)
    save_cc(data)
    # AUTOMATION HOOK: notify Michael that a new question needs his attention
    # future: push_notification(to="michael", subject="Agent needs your answer", body=question["question"])
    return question


def answer_question(q_id: str, answer: str) -> dict[str, Any]:
    data = load_cc()
    question = next((q for q in data["questions"] if q["id"] == q_id), None)
    if question is None:
        raise KeyError(f"Question {q_id} not found")
    question["answer"] = answer.strip()
    question["status"] = "answered"
    question["answered_at"] = _now_iso()
    save_cc(data)
    # AUTOMATION HOOK: route answer back to the agent that asked the question
    # future: send_answer_to_agent(question["id"], question["answer"])
    # AUTOMATION HOOK: if question has a task_id, set that task back to "In Progress"
    # future: if question.get("task_id"): update_task(question["task_id"], {"status": "In Progress"})
    return question


# ---------------------------------------------------------------------------
# Project Status
# ---------------------------------------------------------------------------

def get_project_status() -> dict[str, Any]:
    data = load_cc()
    status = dict(data["project_status"])
    tasks_by_id = {t["id"]: t for t in data["tasks"]}
    status["active_tasks"] = [
        tasks_by_id[tid] for tid in status.pop("active_task_ids", []) if tid in tasks_by_id
    ]
    return status


# ---------------------------------------------------------------------------
# Change Log
# ---------------------------------------------------------------------------

def get_change_log() -> list[dict[str, Any]]:
    return load_cc()["change_log"]


def add_change_log_entry(entry: dict[str, Any]) -> dict[str, Any]:
    data = load_cc()
    existing_ids = {cl["id"] for cl in data["change_log"]}
    index = len(data["change_log"]) + 1
    new_id = f"cl-{index}"
    while new_id in existing_ids:
        index += 1
        new_id = f"cl-{index}"
    entry["id"] = new_id
    entry.setdefault("timestamp", _now_iso())
    data["change_log"].insert(0, entry)
    save_cc(data)
    return entry


# ---------------------------------------------------------------------------
# Approvals
# ---------------------------------------------------------------------------

def get_approvals() -> list[dict[str, Any]]:
    return load_cc()["approvals"]


def create_approval(fields: dict[str, Any]) -> dict[str, Any]:
    data = load_cc()
    existing_ids = {a["id"] for a in data["approvals"]}
    index = len(data["approvals"]) + 1
    new_id = f"ap-{index}"
    while new_id in existing_ids:
        index += 1
        new_id = f"ap-{index}"

    # files_affected may arrive as a comma-separated string or a list
    raw_files = fields.get("files_affected", "")
    if isinstance(raw_files, str):
        files_affected = [f.strip() for f in raw_files.split(",") if f.strip()]
    else:
        files_affected = list(raw_files)

    approval: dict[str, Any] = {
        "id": new_id,
        "title": str(fields.get("title", "")).strip(),
        "description": str(fields.get("description", "")).strip(),
        "requested_at": _now_iso(),
        "requested_by": str(fields.get("requested_by", "Claude Code")).strip() or "Claude Code",
        "status": "pending",
        "feedback": "",
        "decided_at": None,
        "files_affected": files_affected,
    }
    data["approvals"].insert(0, approval)
    save_cc(data)
    # AUTOMATION HOOK: notify Michael that a new approval is waiting
    # future: push_notification(to="michael", subject="Approval needed", body=approval["title"])
    return approval


def decide_approval(ap_id: str, decision: str, feedback: str = "") -> dict[str, Any]:
    if decision not in APPROVAL_DECISIONS:
        raise ValueError(f"Invalid decision: {decision}")
    data = load_cc()
    approval = next((a for a in data["approvals"] if a["id"] == ap_id), None)
    if approval is None:
        raise KeyError(f"Approval {ap_id} not found")
    approval["status"] = decision
    approval["feedback"] = feedback.strip()
    approval["decided_at"] = _now_iso()
    save_cc(data)
    # AUTOMATION HOOK: if approved, trigger the pending code change; if rejected, surface to agent
    # future: if decision == "approved": trigger_pending_change(approval)
    # future: elif decision in ("rejected", "needs_changes"): notify_agent(approval, feedback)
    return approval

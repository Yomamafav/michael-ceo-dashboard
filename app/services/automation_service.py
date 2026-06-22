from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable

from app.services.data_store import log_dashboard_action, save_mobile_update
from app.services.items_store import (
    ItemNotFoundError,
    add_item_note,
    create_follow_up,
    mark_deposit_paid,
    mark_item_complete,
    mark_payment_received,
    update_item,
)
from app.services.ai_ops_store import (
    add_activity,
    get_agents,
    get_automation_state,
    update_agent_status,
    update_automation_state,
)
from app.services.command_center_store import (
    add_change_log_entry,
    create_approval,
    create_question,
    create_task,
    get_approvals,
    mark_approval_execution,
)


AgentRunner = Callable[[dict[str, Any], str], Awaitable[dict[str, Any]]]


def automation_enabled() -> bool:
    return os.getenv("AI_AUTOMATION_ENABLED", "true").strip().lower() == "true"


def get_refresh_minutes() -> int:
    raw_value = os.getenv("AI_AUTOMATION_REFRESH_MINUTES", "15").strip()
    try:
        minutes = int(raw_value)
    except ValueError:
        minutes = 15
    return max(1, minutes)


def _now() -> datetime:
    return datetime.now()


def _now_iso() -> str:
    return _now().isoformat(timespec="seconds")


def _parse_iso(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _next_run_iso(now: datetime | None = None) -> str:
    current = now or _now()
    return (current + timedelta(minutes=get_refresh_minutes())).isoformat(timespec="seconds")


def build_automation_snapshot() -> dict[str, Any]:
    state = get_automation_state()
    state["enabled"] = automation_enabled()
    state["refresh_minutes"] = get_refresh_minutes()
    approvals = get_approvals()
    state["pending_approvals"] = sum(1 for ap in approvals if ap.get("status") == "pending")
    state["approved_pending_execution"] = sum(
        1 for ap in approvals
        if ap.get("status") == "approved" and ap.get("execution_status") == "pending"
    )
    return state


def get_due_agents(now: datetime | None = None) -> list[dict[str, Any]]:
    current = now or _now()
    due_agents: list[dict[str, Any]] = []
    for agent in get_agents():
        if agent.get("status") in ("running", "disabled"):
            continue
        next_run = _parse_iso(agent.get("next_run", ""))
        if next_run and next_run <= current:
            due_agents.append(agent)
    return due_agents


def get_executable_approvals() -> list[dict[str, Any]]:
    return [
        approval for approval in get_approvals()
        if approval.get("status") == "approved"
        and approval.get("execution_type")
        and approval.get("execution_status") == "pending"
    ]


def _stringify_result(value: Any) -> str:
    if isinstance(value, dict):
        if value.get("warning"):
            return str(value["warning"])
        if value.get("source"):
            return f"Saved using {value['source']}."
        if value.get("id"):
            return f"Created {value['id']}."
    return str(value)


def _execute_non_agent_approval(approval: dict[str, Any]) -> dict[str, Any]:
    execution_type = approval.get("execution_type", "")
    payload = approval.get("execution_payload", {}) or {}
    if not isinstance(payload, dict):
        payload = {"raw": payload}

    if execution_type == "mobile_update":
        update_type = str(payload.get("update_type", "Add Quick Note")).strip()
        subject = str(payload.get("subject", approval.get("title", "Approved update"))).strip()
        details = str(payload.get("details", approval.get("description", ""))).strip()
        if not subject or not details:
            return {"ok": False, "message": "mobile_update requires subject and details."}
        result = save_mobile_update(
            {"update_type": update_type, "subject": subject, "details": details},
            source="automation",
        )
        return {"ok": True, "message": _stringify_result(result), "detail": result}

    if execution_type == "create_follow_up":
        name = str(payload.get("name", "")).strip()
        if not name:
            return {"ok": False, "message": "create_follow_up requires a name."}
        item = create_follow_up(
            name=name,
            phone=str(payload.get("phone", "")).strip(),
            email=str(payload.get("email", "")).strip(),
            job=str(payload.get("job", payload.get("topic", ""))).strip(),
            due=str(payload.get("due", "Today")).strip() or "Today",
            channel=str(payload.get("channel", "Call")).strip() or "Call",
        )
        return {"ok": True, "message": f"Created follow-up {item.get('id', '')}.", "detail": item}

    if execution_type == "item_action":
        category = str(payload.get("category", "")).strip()
        item_id = str(payload.get("item_id", "")).strip()
        action = str(payload.get("action", "")).strip()
        if not category or not item_id or not action:
            return {"ok": False, "message": "item_action requires category, item_id, and action."}
        try:
            if action == "mark_complete":
                item = mark_item_complete(category, item_id)
            elif action == "add_note":
                note = str(payload.get("note", "")).strip()
                if not note:
                    return {"ok": False, "message": "add_note requires note text."}
                item = add_item_note(category, item_id, note)
            elif action == "deposit_paid":
                item = mark_deposit_paid(item_id)
            elif action == "payment_received":
                item = mark_payment_received(item_id)
            elif action == "update_fields":
                fields = payload.get("fields", {})
                if not isinstance(fields, dict) or not fields:
                    return {"ok": False, "message": "update_fields requires a fields object."}
                item = update_item(category, item_id, fields)
            else:
                return {"ok": False, "message": f"Unsupported item action: {action}"}
        except ItemNotFoundError as exc:
            return {"ok": False, "message": str(exc)}
        return {
            "ok": True,
            "message": f"Updated {category} item {item_id} via {action}.",
            "detail": item,
        }

    if execution_type == "cc_create":
        record_type = str(payload.get("record_type", "")).strip()
        fields = payload.get("fields", {})
        if not isinstance(fields, dict):
            return {"ok": False, "message": "cc_create requires a fields object."}
        if record_type == "task":
            created = create_task(fields)
        elif record_type == "question":
            created = create_question(fields)
        elif record_type == "approval":
            created = create_approval(fields)
        elif record_type == "change":
            created = add_change_log_entry(fields)
        else:
            return {"ok": False, "message": f"Unsupported cc_create record_type: {record_type}"}
        return {"ok": True, "message": f"Created {record_type} record.", "detail": created}

    if execution_type == "dashboard_action":
        update_type = str(payload.get("update_type", "Add Quick Note")).strip()
        subject = str(payload.get("subject", approval.get("title", "Automation action"))).strip()
        details = str(payload.get("details", approval.get("description", ""))).strip()
        result = log_dashboard_action(update_type, subject, details)
        return {"ok": True, "message": _stringify_result(result), "detail": result}

    return {"ok": False, "message": f"Unsupported execution type: {execution_type}"}


async def run_automation_cycle(agent_runner: AgentRunner) -> dict[str, Any]:
    if not automation_enabled():
        snapshot = build_automation_snapshot()
        snapshot["last_result"] = "Automation is disabled."
        return snapshot

    started_at = _now()
    update_automation_state({
        "enabled": True,
        "refresh_minutes": get_refresh_minutes(),
        "is_running": True,
        "last_error": "",
    })

    due_agents = get_due_agents(started_at)
    executable_approvals = get_executable_approvals()
    agents_dispatched = 0
    approvals_completed = 0
    approvals_failed = 0

    try:
        for agent in due_agents:
            update_agent_status(agent["id"], {
                "status": "running",
                "last_run": _now_iso(),
                "current_task": "Scheduled automation refresh",
                "error_message": "",
            })
            result = await agent_runner(agent, "Scheduled 15-minute refresh")
            agents_dispatched += 1
            if not result.get("ok"):
                add_activity({
                    "agent_name": agent.get("name", ""),
                    "action": "Scheduled run failed",
                    "detail": result.get("message", "Agent run failed."),
                    "type": "alert",
                })

        for approval in executable_approvals:
            execution_type = approval.get("execution_type", "")
            target = approval.get("execution_target", "")
            payload = approval.get("execution_payload", {})

            if execution_type != "agent_run":
                result = _execute_non_agent_approval(approval)
                if result.get("ok"):
                    mark_approval_execution(
                        approval["id"],
                        "completed",
                        result.get("message", "Execution completed."),
                    )
                    add_activity({
                        "agent_name": "Automation Loop",
                        "action": "Approved action executed",
                        "detail": approval.get("title", ""),
                        "type": "info",
                    })
                    approvals_completed += 1
                else:
                    mark_approval_execution(
                        approval["id"],
                        "failed",
                        result.get("message", "Execution failed."),
                    )
                    add_activity({
                        "agent_name": "Automation Loop",
                        "action": "Approved action failed",
                        "detail": f"{approval.get('title', '')}: {result.get('message', 'Execution failed.')}",
                        "type": "alert",
                    })
                    approvals_failed += 1
                continue

            agent = next(
                (
                    candidate for candidate in get_agents()
                    if candidate.get("id") == target or candidate.get("agent_type") == target
                ),
                None,
            )
            if agent is None:
                mark_approval_execution(
                    approval["id"],
                    "failed",
                    f"No agent matched execution target '{target}'.",
                )
                approvals_failed += 1
                continue

            update_agent_status(agent["id"], {
                "status": "running",
                "last_run": _now_iso(),
                "current_task": f"Approved action: {approval.get('title', 'Approval execution')}",
                "error_message": "",
            })
            prompt = str(payload.get("input", "")).strip() if isinstance(payload, dict) else ""
            result = await agent_runner(agent, prompt or f"Execute approved action: {approval.get('title', '')}")
            if result.get("ok"):
                mark_approval_execution(
                    approval["id"],
                    "completed",
                    result.get("message", f"Dispatched {agent.get('name', 'agent')}."),
                )
                add_activity({
                    "agent_name": agent.get("name", ""),
                    "action": "Approved action executed",
                    "detail": approval.get("title", ""),
                    "type": "info",
                })
                approvals_completed += 1
            else:
                mark_approval_execution(
                    approval["id"],
                    "failed",
                    result.get("message", "Execution failed."),
                )
                approvals_failed += 1

        summary = (
            f"Agents dispatched: {agents_dispatched}. "
            f"Approvals completed: {approvals_completed}. "
            f"Approvals failed: {approvals_failed}."
        )
        return update_automation_state({
            "enabled": True,
            "refresh_minutes": get_refresh_minutes(),
            "last_run": started_at.isoformat(timespec="seconds"),
            "last_result": "Automation cycle completed.",
            "last_summary": summary,
            "last_error": "",
            "is_running": False,
        })
    except Exception as exc:
        return update_automation_state({
            "enabled": True,
            "refresh_minutes": get_refresh_minutes(),
            "last_run": started_at.isoformat(timespec="seconds"),
            "last_result": "Automation cycle failed.",
            "last_summary": "",
            "last_error": str(exc)[:300],
            "is_running": False,
        })


def schedule_next_run_for_agent(agent_id: str) -> dict[str, Any]:
    return update_agent_status(agent_id, {"next_run": _next_run_iso()})

import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.services.data_store import (
    UPDATE_TYPES as UPDATE_TYPE_OPTIONS,
    ensure_storage,
    get_recent_updates,
    get_today_briefing,
    log_dashboard_action,
    save_mobile_update,
)
from app.services.items_store import (
    CATEGORIES as ITEM_CATEGORIES,
    CATEGORY_LABELS,
    ItemNotFoundError,
    add_item_note,
    create_follow_up,
    create_item,
    delete_item,
    get_item,
    load_items,
    mark_deposit_paid,
    mark_item_complete,
    mark_payment_received,
    update_item,
)
from app.services.command_center_store import (
    TASK_STATUSES,
    TASK_PRIORITIES,
    APPROVAL_DECISIONS,
    ensure_cc_storage,
    get_tasks,
    create_task,
    update_task,
    get_questions,
    create_question,
    answer_question,
    get_project_status,
    get_change_log,
    add_change_log_entry,
    get_approvals,
    create_approval,
    decide_approval,
)
from app.services.ai_ops_store import (
    ensure_ai_ops_storage,
    get_agents,
    register_agent,
    update_agent_status,
    get_inbox,
    create_inbox_item,
    update_inbox_item,
    get_activity,
    add_activity,
)
from app.services.automation_service import (
    automation_enabled,
    build_automation_snapshot,
    get_refresh_minutes,
    run_automation_cycle,
    schedule_next_run_for_agent,
)

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


load_dotenv()

app = FastAPI(title="Michael CEO Dashboard")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@app.on_event("startup")
def on_startup() -> None:
    ensure_storage()
    ensure_cc_storage()
    ensure_ai_ops_storage()
    app.state.automation_lock = asyncio.Lock()
    app.state.automation_task = None
    if automation_enabled():
        app.state.automation_task = asyncio.create_task(_automation_loop())


@app.on_event("shutdown")
async def on_shutdown() -> None:
    task = getattr(app.state, "automation_task", None)
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request) -> HTMLResponse:
    briefing_result = get_today_briefing()
    updates_result = get_recent_updates(limit=5)
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "briefing": briefing_result["briefing"],
            "recent_updates": updates_result["updates"],
            "briefing_warning": briefing_result["warning"],
            "updates_warning": updates_result["warning"],
            "briefing_source": briefing_result["source"],
            "updates_source": updates_result["source"],
        },
    )


@app.get("/mobile", response_class=HTMLResponse)
async def mobile_page(request: Request) -> HTMLResponse:
    updates_result = get_recent_updates(limit=10)
    return templates.TemplateResponse(
        request,
        "mobile.html",
        {
            "update_types": UPDATE_TYPE_OPTIONS,
            "recent_updates": updates_result["updates"],
            "updates_warning": updates_result["warning"],
            "updates_source": updates_result["source"],
        },
    )


@app.get("/updates", response_class=HTMLResponse)
async def updates_page(request: Request) -> HTMLResponse:
    updates_result = get_recent_updates(limit=50)
    return templates.TemplateResponse(
        request,
        "updates.html",
        {
            "recent_updates": updates_result["updates"],
            "updates_warning": updates_result["warning"],
            "updates_source": updates_result["source"],
        },
    )


@app.get("/api/briefing/today")
async def briefing_today() -> JSONResponse:
    try:
        result = get_today_briefing()
        return JSONResponse(
            {
                "status": "ok",
                "data": result["briefing"],
                "source": result["source"],
                "warning": result["warning"],
            }
        )
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail="Unable to load today's briefing") from exc


@app.post("/api/mobile/update")
async def mobile_update(
    update_type: str = Form(...),
    subject: str = Form(...),
    details: str = Form(...),
) -> JSONResponse:
    if update_type not in UPDATE_TYPE_OPTIONS:
        raise HTTPException(status_code=400, detail="Invalid update type")
    if not subject.strip() or not details.strip():
        raise HTTPException(status_code=400, detail="Subject and details are required")

    entry = {
        "update_type": update_type,
        "subject": subject.strip(),
        "details": details.strip(),
    }
    try:
        result = save_mobile_update(entry)
    except OSError as exc:
        raise HTTPException(status_code=500, detail="Unable to save update") from exc
    return JSONResponse(
        {
            "status": "saved",
            "entry": result["entry"],
            "source": result["source"],
            "warning": result["warning"],
        }
    )


@app.get("/api/mobile/updates")
async def mobile_updates() -> JSONResponse:
    result = get_recent_updates(limit=50)
    return JSONResponse(
        {
            "status": "ok",
            "updates": result["updates"],
            "source": result["source"],
            "warning": result["warning"],
        }
    )


@app.get("/api/items/{category}/{item_id}")
async def item_detail(category: str, item_id: str) -> JSONResponse:
    if category not in ITEM_CATEGORIES:
        raise HTTPException(status_code=404, detail="Unknown item category")
    try:
        item = get_item(category, item_id)
    except ItemNotFoundError:
        raise HTTPException(status_code=404, detail="Item not found")
    return JSONResponse({"status": "ok", "item": item, "category": category})


@app.post("/api/items/{category}/{item_id}/complete")
async def item_complete(category: str, item_id: str) -> JSONResponse:
    if category not in ITEM_CATEGORIES:
        raise HTTPException(status_code=404, detail="Unknown item category")
    try:
        item = mark_item_complete(category, item_id)
    except ItemNotFoundError:
        raise HTTPException(status_code=404, detail="Item not found")
    log_dashboard_action(
        "Update Job Status",
        item.get("name", ""),
        f"Marked {CATEGORY_LABELS[category].lower()} complete: {item.get('job') or item.get('name', '')}",
    )
    return JSONResponse({"status": "ok", "item": item})


@app.post("/api/items/{category}/{item_id}/note")
async def item_add_note(category: str, item_id: str, note: str = Form(...)) -> JSONResponse:
    if category not in ITEM_CATEGORIES:
        raise HTTPException(status_code=404, detail="Unknown item category")
    if not note.strip():
        raise HTTPException(status_code=400, detail="Note text is required")
    try:
        item = add_item_note(category, item_id, note.strip())
    except ItemNotFoundError:
        raise HTTPException(status_code=404, detail="Item not found")
    log_dashboard_action(
        "Add Job Note",
        item.get("name", ""),
        note.strip(),
    )
    return JSONResponse({"status": "ok", "item": item})


@app.patch("/api/items/{category}/{item_id}")
async def edit_item(category: str, item_id: str, request: Request) -> JSONResponse:
    if category not in ITEM_CATEGORIES:
        raise HTTPException(status_code=404, detail="Unknown item category")
    form = await request.form()
    fields = {key: str(value) for key, value in form.items()}
    try:
        item = update_item(category, item_id, fields)
    except ItemNotFoundError:
        raise HTTPException(status_code=404, detail="Item not found")
    log_dashboard_action(
        "Edit Item",
        item.get("name", ""),
        f"Updated {CATEGORY_LABELS[category].lower()}: {item.get('job') or item.get('name', '')}",
    )
    return JSONResponse({"status": "ok", "item": item})


@app.post("/api/items/{category}/{item_id}/delete")
async def remove_item(category: str, item_id: str) -> JSONResponse:
    if category not in ITEM_CATEGORIES:
        raise HTTPException(status_code=404, detail="Unknown item category")
    try:
        item = delete_item(category, item_id)
    except ItemNotFoundError:
        raise HTTPException(status_code=404, detail="Item not found")
    log_dashboard_action(
        "Remove Item",
        item.get("name", ""),
        f"Removed {CATEGORY_LABELS[category].lower()}: {item.get('job') or item.get('name', '')}",
    )
    return JSONResponse({"status": "ok", "item": item})


@app.post("/api/items/payments/{item_id}/deposit-paid")
async def item_deposit_paid(item_id: str) -> JSONResponse:
    try:
        item = mark_deposit_paid(item_id)
    except ItemNotFoundError:
        raise HTTPException(status_code=404, detail="Payment not found")
    log_dashboard_action("Mark Deposit Paid", item.get("name", ""), f"Deposit marked paid for {item.get('job', '')}")
    return JSONResponse({"status": "ok", "item": item})


@app.post("/api/items/payments/{item_id}/payment-received")
async def item_payment_received(item_id: str) -> JSONResponse:
    try:
        item = mark_payment_received(item_id)
    except ItemNotFoundError:
        raise HTTPException(status_code=404, detail="Payment not found")
    log_dashboard_action("Add Payment Received", item.get("name", ""), f"Payment received for {item.get('job', '')}")
    return JSONResponse({"status": "ok", "item": item})


@app.post("/api/items/{category}")
async def add_item(category: str, request: Request) -> JSONResponse:
    if category not in ITEM_CATEGORIES:
        raise HTTPException(status_code=404, detail="Unknown item category")
    form = await request.form()
    fields = {key: str(value).strip() for key, value in form.items()}
    if not fields.get("name"):
        raise HTTPException(status_code=400, detail="Name is required")
    try:
        item = create_item(category, fields)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    log_dashboard_action(
        f"Add {CATEGORY_LABELS[category]}",
        item.get("name", ""),
        item.get("job") or f"New {CATEGORY_LABELS[category].lower()} created",
    )
    return JSONResponse({"status": "ok", "item": item})


@app.post("/api/follow-ups")
async def add_follow_up(
    name: str = Form(...),
    phone: str = Form(""),
    email: str = Form(""),
    job: str = Form(""),
    due: str = Form("Today"),
    channel: str = Form("Call"),
) -> JSONResponse:
    if not name.strip():
        raise HTTPException(status_code=400, detail="Name is required")
    item = create_follow_up(name=name.strip(), phone=phone.strip(), email=email.strip(), job=job.strip(), due=due.strip() or "Today", channel=channel.strip() or "Call")
    log_dashboard_action("Add Follow-Up", item["name"], item.get("job") or "New follow-up created")
    return JSONResponse({"status": "ok", "item": item})


@app.get("/command-center", response_class=HTMLResponse)
async def command_center(request: Request) -> HTMLResponse:
    tasks = get_tasks()
    questions = get_questions()
    project_status = get_project_status()
    change_log = get_change_log()
    approvals = get_approvals()
    item_options = load_items()
    pending_q_count = sum(1 for q in questions if q["status"] == "pending")
    pending_ap_count = sum(1 for a in approvals if a["status"] == "pending")
    return templates.TemplateResponse(
        request,
        "command_center.html",
        {
            "tasks": tasks,
            "questions": questions,
            "project_status": project_status,
            "change_log": change_log,
            "approvals": approvals,
            "item_options": item_options,
            "task_statuses": TASK_STATUSES,
            "task_priorities": TASK_PRIORITIES,
            "pending_q_count": pending_q_count,
            "pending_ap_count": pending_ap_count,
        },
    )


@app.post("/api/cc/tasks")
async def cc_create_task(request: Request) -> JSONResponse:
    form = await request.form()
    fields = {key: str(value).strip() for key, value in form.items()}
    if not fields.get("title"):
        raise HTTPException(status_code=400, detail="Title is required")
    task = create_task(fields)
    return JSONResponse({"status": "ok", "task": task})


@app.post("/api/cc/tasks/{task_id}")
async def cc_update_task(task_id: str, request: Request) -> JSONResponse:
    form = await request.form()
    fields = {key: str(value).strip() for key, value in form.items()}
    try:
        task = update_task(task_id, fields)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return JSONResponse({"status": "ok", "task": task})


@app.post("/api/cc/questions/{q_id}/answer")
async def cc_answer_question(q_id: str, answer: str = Form(...)) -> JSONResponse:
    if not answer.strip():
        raise HTTPException(status_code=400, detail="Answer is required")
    try:
        question = answer_question(q_id, answer)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return JSONResponse({"status": "ok", "question": question})


@app.post("/api/cc/approvals/{ap_id}/decide")
async def cc_decide_approval(
    ap_id: str,
    decision: str = Form(...),
    feedback: str = Form(""),
) -> JSONResponse:
    if decision not in APPROVAL_DECISIONS:
        raise HTTPException(status_code=400, detail=f"Invalid decision. Must be one of: {', '.join(APPROVAL_DECISIONS)}")
    try:
        approval = decide_approval(ap_id, decision, feedback)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return JSONResponse({"status": "ok", "approval": approval})


# ---------------------------------------------------------------------------
# Missing CC write endpoints (audit gap fix)
# ---------------------------------------------------------------------------

@app.post("/api/cc/questions")
async def cc_create_question(request: Request) -> JSONResponse:
    form = await request.form()
    fields = {key: str(value).strip() for key, value in form.items()}
    if not fields.get("question"):
        raise HTTPException(status_code=400, detail="Question text is required")
    question = create_question(fields)
    return JSONResponse({"status": "ok", "question": question})


@app.post("/api/cc/approvals")
async def cc_create_approval(request: Request) -> JSONResponse:
    form = await request.form()
    fields = {key: str(value).strip() for key, value in form.items()}
    if not fields.get("title"):
        raise HTTPException(status_code=400, detail="Title is required")
    approval = create_approval(fields)
    return JSONResponse({"status": "ok", "approval": approval})


@app.post("/api/cc/changes")
async def cc_add_change(request: Request) -> JSONResponse:
    form = await request.form()
    fields = {key: str(value).strip() for key, value in form.items()}
    if not fields.get("feature"):
        raise HTTPException(status_code=400, detail="Feature name is required")
    raw_files = fields.get("files_changed", "")
    files_changed = [f.strip() for f in raw_files.split(",") if f.strip()]
    entry = {
        "feature": fields["feature"],
        "description": fields.get("description", ""),
        "files_changed": files_changed,
        "agent_notes": fields.get("agent_notes", ""),
    }
    saved = add_change_log_entry(entry)
    return JSONResponse({"status": "ok", "entry": saved})


# ---------------------------------------------------------------------------
# Agent-facing API (machine-to-machine, returns JSON optimised for agents)
# ---------------------------------------------------------------------------

@app.get("/api/agent/tasks")
async def agent_get_tasks(
    assigned_to: str | None = None,
    status: str | None = None,
) -> JSONResponse:
    tasks = get_tasks()
    if assigned_to:
        tasks = [t for t in tasks if t.get("assigned_to", "").lower() == assigned_to.lower()]
    if status:
        tasks = [t for t in tasks if t.get("status", "").lower() == status.lower()]
    return JSONResponse({"status": "ok", "tasks": tasks, "count": len(tasks)})


@app.get("/api/agent/questions")
async def agent_get_questions(status: str | None = None) -> JSONResponse:
    questions = get_questions()
    if status:
        questions = [q for q in questions if q.get("status", "").lower() == status.lower()]
    return JSONResponse({"status": "ok", "questions": questions, "count": len(questions)})


@app.post("/api/agent/questions")
async def agent_create_question(request: Request) -> JSONResponse:
    form = await request.form()
    fields = {key: str(value).strip() for key, value in form.items()}
    if not fields.get("question"):
        raise HTTPException(status_code=400, detail="Question text is required")
    question = create_question(fields)
    return JSONResponse({"status": "ok", "question": question})


@app.get("/api/agent/activity")
async def agent_get_activity(limit: int = 20) -> JSONResponse:
    entries = get_change_log()
    return JSONResponse({"status": "ok", "activity": entries[:limit], "count": len(entries[:limit])})


@app.get("/api/agent/approvals")
async def agent_get_approvals(status: str | None = None) -> JSONResponse:
    approvals = get_approvals()
    if status:
        approvals = [a for a in approvals if a.get("status", "").lower() == status.lower()]
    return JSONResponse({"status": "ok", "approvals": approvals, "count": len(approvals)})


@app.post("/api/agent/approvals")
async def agent_create_approval(request: Request) -> JSONResponse:
    form = await request.form()
    fields = {key: str(value).strip() for key, value in form.items()}
    if not fields.get("title"):
        raise HTTPException(status_code=400, detail="Title is required")
    approval = create_approval(fields)
    return JSONResponse({"status": "ok", "approval": approval})


# ---------------------------------------------------------------------------
# AI Operations page
# ---------------------------------------------------------------------------

@app.get("/ai-operations", response_class=HTMLResponse)
async def ai_operations(request: Request) -> HTMLResponse:
    agents = get_agents()
    inbox = get_inbox()
    questions = get_questions()
    activity = get_activity(limit=50)
    automation = build_automation_snapshot()
    unread_count = sum(1 for i in inbox if i["status"] == "unread")
    pending_q_count = sum(1 for q in questions if q["status"] == "pending")
    # Count pending (action_required + not resolved) inbox items per agent_type
    pending_per_agent: dict[str, int] = {}
    for item in inbox:
        if item.get("action_required") and item.get("status") not in ("actioned", "dismissed"):
            key = item.get("agent_type", "")
            pending_per_agent[key] = pending_per_agent.get(key, 0) + 1
    return templates.TemplateResponse(
        request,
        "ai_operations.html",
        {
            "agents": agents,
            "inbox": inbox,
            "questions": questions,
            "activity": activity,
            "unread_count": unread_count,
            "pending_q_count": pending_q_count,
            "pending_per_agent": pending_per_agent,
            "automation": automation,
        },
    )


# ---------------------------------------------------------------------------
# AI Operations API — agents
# ---------------------------------------------------------------------------

@app.get("/api/aiops/agents")
async def aiops_get_agents() -> JSONResponse:
    return JSONResponse({"status": "ok", "agents": get_agents()})


@app.post("/api/aiops/agents")
async def aiops_register_agent(request: Request) -> JSONResponse:
    form = await request.form()
    fields = {key: str(value).strip() for key, value in form.items()}
    if not fields.get("name"):
        raise HTTPException(status_code=400, detail="Agent name is required")
    agent = register_agent(fields)
    return JSONResponse({"status": "ok", "agent": agent})


@app.post("/api/aiops/agents/{agent_id}")
async def aiops_update_agent(agent_id: str, request: Request) -> JSONResponse:
    form = await request.form()
    fields = {key: str(value).strip() for key, value in form.items()}
    try:
        agent = update_agent_status(agent_id, fields)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return JSONResponse({"status": "ok", "agent": agent})


# ---------------------------------------------------------------------------
# AI Operations API — inbox
# ---------------------------------------------------------------------------

@app.get("/api/aiops/inbox")
async def aiops_get_inbox(status: str | None = None) -> JSONResponse:
    items = get_inbox(status=status)
    return JSONResponse({"status": "ok", "inbox": items, "count": len(items)})


@app.post("/api/aiops/inbox")
async def aiops_create_inbox_item(request: Request) -> JSONResponse:
    form = await request.form()
    fields = {key: str(value).strip() for key, value in form.items()}
    if not fields.get("subject"):
        raise HTTPException(status_code=400, detail="Subject is required")
    item = create_inbox_item(fields)
    return JSONResponse({"status": "ok", "item": item})


@app.post("/api/aiops/inbox/{item_id}")
async def aiops_update_inbox_item(item_id: str, request: Request) -> JSONResponse:
    form = await request.form()
    fields = {key: str(value).strip() for key, value in form.items()}
    try:
        item = update_inbox_item(item_id, fields)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return JSONResponse({"status": "ok", "item": item})


# ---------------------------------------------------------------------------
# AI Operations API — activity feed
# ---------------------------------------------------------------------------

@app.get("/api/aiops/feed")
async def aiops_get_feed(limit: int = 50) -> JSONResponse:
    entries = get_activity(limit=limit)
    return JSONResponse({"status": "ok", "activity": entries, "count": len(entries)})


@app.post("/api/aiops/feed")
async def aiops_add_activity(request: Request) -> JSONResponse:
    form = await request.form()
    fields = {key: str(value).strip() for key, value in form.items()}
    if not fields.get("action"):
        raise HTTPException(status_code=400, detail="Action description is required")
    entry = add_activity(fields)
    return JSONResponse({"status": "ok", "entry": entry})


@app.post("/api/aiops/agents/{agent_id}/run")
async def aiops_run_agent(agent_id: str) -> JSONResponse:
    """Trigger an agent to run now via OpenJarvis. Updates status to 'running' immediately."""
    agent = next((candidate for candidate in get_agents() if candidate.get("id") == agent_id), None)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent = update_agent_status(agent_id, {
        "status": "running",
        "last_run": _now_iso(),
        "current_task": "Running on demand...",
        "error_message": "",
    })
    asyncio.create_task(_dispatch_agent_to_openjarvis(agent, "Run your morning briefing for Michael now."))
    return JSONResponse({"status": "running", "agent": agent})


async def _dispatch_agent_to_openjarvis(agent: dict[str, Any], prompt: str) -> dict[str, Any]:
    """Dispatch an agent to OpenJarvis and persist result state for UI + automation."""
    openjarvis_url = os.environ.get("OPENJARVIS_URL", "http://localhost:8000").rstrip("/")
    agent_type = agent.get("agent_type", "")
    agent_id = agent.get("id", "")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{openjarvis_url}/v1/agents/{agent_type}/run",
                json={"input": prompt},
            )
            if resp.status_code >= 400:
                update_agent_status(agent_id, {
                    "status": "error",
                    "error_message": f"OpenJarvis returned {resp.status_code}",
                    "current_task": "",
                    "last_result": "",
                })
                return {"ok": False, "message": f"OpenJarvis returned {resp.status_code}"}
            schedule_next_run_for_agent(agent_id)
            update_agent_status(agent_id, {
                "status": "idle",
                "last_run": _now_iso(),
                "current_task": "",
                "last_result": "Run completed and next cycle scheduled.",
                "error_message": "",
            })
            add_activity({
                "agent_name": agent.get("name", agent_type),
                "action": "Agent run completed",
                "detail": prompt,
                "type": "info",
            })
            return {"ok": True, "message": f"Dispatched {agent.get('name', agent_type)} successfully."}
    except Exception as exc:
        update_agent_status(agent_id, {
            "status": "error",
            "error_message": str(exc)[:200],
            "current_task": "",
            "last_result": "",
        })
        return {"ok": False, "message": str(exc)[:200]}


async def _run_automation_cycle_locked() -> dict[str, Any]:
    async with app.state.automation_lock:
        return await run_automation_cycle(_dispatch_agent_to_openjarvis)


async def _automation_loop() -> None:
    while True:
        try:
            await _run_automation_cycle_locked()
        except Exception:
            pass
        await asyncio.sleep(get_refresh_minutes() * 60)


@app.get("/api/automation/status")
async def automation_status() -> JSONResponse:
    return JSONResponse({"status": "ok", "automation": build_automation_snapshot()})


@app.post("/api/automation/run")
async def automation_run_now() -> JSONResponse:
    state = build_automation_snapshot()
    if state.get("is_running"):
        return JSONResponse(
            {"status": "busy", "automation": state, "detail": "Automation cycle is already running."},
            status_code=409,
        )
    await _run_automation_cycle_locked()
    return JSONResponse({"status": "ok", "automation": build_automation_snapshot()})


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception) -> HTMLResponse | JSONResponse:
    if request.url.path.startswith("/api/"):
        detail = getattr(exc, "detail", "Not found")
        return JSONResponse({"status": "error", "detail": detail}, status_code=404)
    return templates.TemplateResponse(
        request,
        "error.html",
        {"status_code": 404, "message": "Page not found."},
        status_code=404,
    )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc: Exception) -> HTMLResponse | JSONResponse:
    if request.url.path.startswith("/api/"):
        return JSONResponse({"status": "error", "detail": "Internal server error"}, status_code=500)
    return templates.TemplateResponse(
        request,
        "error.html",
        {"status_code": 500, "message": "Something went wrong loading the dashboard."},
        status_code=500,
    )


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


UPDATE_TYPES = UPDATE_TYPE_OPTIONS

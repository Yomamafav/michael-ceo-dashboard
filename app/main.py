from pathlib import Path

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
    get_item,
    mark_deposit_paid,
    mark_item_complete,
    mark_payment_received,
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


UPDATE_TYPES = UPDATE_TYPE_OPTIONS

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
    save_mobile_update,
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


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "error.html",
        {"status_code": 404, "message": "Page not found."},
        status_code=404,
    )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc: Exception) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "error.html",
        {"status_code": 500, "message": "Something went wrong loading the dashboard."},
        status_code=500,
    )


UPDATE_TYPES = UPDATE_TYPE_OPTIONS

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from app.services import items_store
from app.services.google_sheets import (
    GoogleSheetsConfigError,
    get_google_sheets_service,
)


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
UPDATES_PATH = DATA_DIR / "mobile_updates.json"

UPDATE_TYPES = [
    "Add Customer",
    "Add Job Note",
    "Update Job Status",
    "Mark Deposit Paid",
    "Add Payment Received",
    "Add Follow-Up",
    "Add Material Purchase",
    "Add Transaction",
    "Add Quick Note",
]

TAB_HEADERS = {
    "MobileUpdates": [
        "update_id",
        "update_type",
        "customer_name",
        "job_name",
        "amount",
        "note",
        "followup_date",
        "status",
        "raw_text",
        "created_at",
    ],
}

LEGACY_TAB_MAP = {
    "projects": "Master Projects",
    "tasks": "Tasks",
    "pricing": "Pricing",
    "materials": "Materials",
}


def ensure_storage() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not UPDATES_PATH.exists():
        UPDATES_PATH.write_text("[]", encoding="utf-8")
    items_store.ensure_items_storage()


def is_google_sheets_enabled() -> bool:
    return os.getenv("GOOGLE_SHEETS_ENABLED", "false").strip().lower() == "true"


def load_local_updates() -> list[dict[str, Any]]:
    ensure_storage()
    try:
        with UPDATES_PATH.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass
    return []


def save_local_update(entry: dict[str, Any]) -> dict[str, Any]:
    updates = load_local_updates()
    updates.insert(0, entry)
    with UPDATES_PATH.open("w", encoding="utf-8") as handle:
        json.dump(updates[:100], handle, indent=2)
    return entry


def get_mock_briefing() -> dict[str, Any]:
    # TODO: Add Gmail follow-up enrichment once inbox integrations are enabled.
    # TODO: Add Google Calendar sync for family and business events.
    # TODO: Add live MLB / Rockies data feed integration.
    # TODO: Add softball feed integration for tournament and recruiting updates.
    return {
        "date": "Tuesday, June 16",
        "one_next_action": {
            "title": "Call Jose Ramirez about the garage slab deposit",
            "detail": "Confirm the $2,500 deposit cleared and lock Friday's concrete crew.",
            "deadline": "Before 10:30 AM",
        },
        "schedule": [
            {"time": "7:30 AM", "title": "Crew check-in", "detail": "4 My4 Construction daily kickoff"},
            {"time": "9:00 AM", "title": "School office call", "detail": "Confirm Ava softball camp forms"},
            {"time": "11:30 AM", "title": "POG print proof review", "detail": "Approve church banner revision"},
            {"time": "3:45 PM", "title": "Family pickup", "detail": "Grab Luke from summer weights"},
        ],
        "construction_revenue": {
            "today_target": "$4,800",
            "week_booked": "$18,400",
            "active_job": {
                "customer": "Jose Ramirez",
                "job": "Garage slab + driveway extension",
                "status": "Waiting on deposit confirmation",
                "next_step": "Schedule crew and order rebar",
            },
        },
        "printing_revenue": {
            "today_target": "$1,250",
            "open_orders": 3,
            "featured_task": {
                "client": "Front Range Youth Camp",
                "task": "24 yard signs and 2 sponsor banners",
                "deadline": "Tomorrow at 2:00 PM",
            },
        },
        "follow_ups": [
            {"name": "Samantha Lee", "topic": "Fence repair estimate", "due": "Today", "channel": "Text"},
            {"name": "Grace Fellowship", "topic": "Banner invoice approval", "due": "Today", "channel": "Email"},
            {"name": "Miguel Torres", "topic": "Kitchen remodel site visit", "due": "Tomorrow", "channel": "Call"},
        ],
        "payments": [
            {"name": "Jose Ramirez", "type": "Deposit", "amount": "$2,500", "status": "Pending"},
            {"name": "Front Range Youth Camp", "type": "Invoice", "amount": "$640", "status": "Received"},
        ],
        "bills_money": [
            {"name": "Concrete supplier", "amount": "$1,180", "due": "Today"},
            {"name": "Truck payment", "amount": "$622", "due": "Friday"},
            {"name": "Shop internet", "amount": "$96", "due": "Friday"},
        ],
        "family_calendar": [
            {"time": "5:30 PM", "event": "Ava softball practice", "location": "Longmont Rec Fields"},
            {"time": "6:15 PM", "event": "Family dinner with Mom", "location": "Home"},
        ],
        "rockies": {
            "headline": "Rockies start a home series tonight against the Giants.",
            "detail": "First pitch is 6:40 PM MT. Freeland is projected to start after a solid last outing.",
        },
        "softball": {
            "headline": "Colorado summer showcase registration windows are closing this week.",
            "detail": "Two strong recruiting events still have open slots for 14U and 16U teams.",
        },
        "ai_ideas": [
            {
                "title": "Auto-draft follow-up texts from job notes",
                "impact": "Saves 20 to 30 minutes each evening and reduces dropped leads.",
            },
            {
                "title": "Daily cash snapshot from Sheets into this dashboard",
                "impact": "One-screen view of deposits, bills, and overdue payments.",
            },
        ],
    }


def read_sheet(tab_name: str) -> list[dict[str, str]]:
    if not is_google_sheets_enabled():
        return []
    service = get_google_sheets_service()
    return service.read_sheet(tab_name)


def _tab_exists(tab_name: str) -> bool:
    if not is_google_sheets_enabled():
        return False
    service = get_google_sheets_service()
    return service.tab_exists(tab_name)


def append_row(tab_name: str, row_data: dict[str, Any]) -> None:
    if not is_google_sheets_enabled():
        return
    headers = TAB_HEADERS.get(tab_name)
    payload = row_data
    if headers:
        payload = {header: row_data.get(header, "") for header in headers}
    service = get_google_sheets_service()
    service.append_row(tab_name, payload)


def _pick_first(rows: list[dict[str, str]], *keys: str, default: str = "") -> str:
    if not rows:
        return default
    return _row_value(rows[0], *keys, default=default)


def _row_value(row: dict[str, str], *keys: str, default: str = "") -> str:
    lowered = {key.strip().lower(): value for key, value in row.items()}
    for key in keys:
        value = lowered.get(key.lower())
        if value:
            return value
    return default


def _normalize_mobile_updates(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for row in rows:
        customer_name = _row_value(row, "customer_name", "subject", "name")
        job_name = _row_value(row, "job_name")
        raw_text = _row_value(row, "raw_text", "details", "description")
        note = _row_value(row, "note", "details")
        subject_parts = [part for part in [customer_name, job_name] if part]
        subject = " - ".join(subject_parts) if subject_parts else _row_value(row, "subject", default="Mobile update")
        details = raw_text or note or _row_value(row, "status")
        normalized.append(
            {
                "timestamp": _row_value(row, "created_at", "timestamp"),
                "update_type": _row_value(row, "update_type", "type"),
                "subject": subject,
                "details": details,
            }
        )
    return [row for row in normalized if row["update_type"] or row["subject"] or row["details"]]


def _briefing_from_sheet_rows() -> dict[str, Any]:
    briefing = get_mock_briefing()
    use_legacy_layout = _tab_exists(LEGACY_TAB_MAP["projects"])

    jobs = read_sheet("Jobs") if _tab_exists("Jobs") else []
    customers = read_sheet("Customers") if _tab_exists("Customers") else []
    follow_ups = read_sheet("FollowUps") if _tab_exists("FollowUps") else []
    payments = read_sheet("Payments") if _tab_exists("Payments") else []
    bills = read_sheet("Bills") if _tab_exists("Bills") else []
    family_events = read_sheet("FamilyEvents") if _tab_exists("FamilyEvents") else []
    sports_notes = read_sheet("SportsNotes") if _tab_exists("SportsNotes") else []
    ideas = read_sheet("Ideas") if _tab_exists("Ideas") else []

    if use_legacy_layout:
        projects = read_sheet(LEGACY_TAB_MAP["projects"])
        tasks = read_sheet(LEGACY_TAB_MAP["tasks"]) if _tab_exists(LEGACY_TAB_MAP["tasks"]) else []
        materials = read_sheet(LEGACY_TAB_MAP["materials"]) if _tab_exists(LEGACY_TAB_MAP["materials"]) else []

        open_projects = [
            row for row in projects
            if "completed" not in _row_value(row, "project status", "status").lower()
        ]
        prioritized_projects = sorted(
            open_projects or projects,
            key=lambda row: (
                "high" not in _row_value(row, "priority").lower(),
                "follow-up" not in _row_value(row, "project status").lower(),
            ),
        )

        if prioritized_projects:
            active_project = prioritized_projects[0]
            briefing["construction_revenue"]["active_job"] = {
                "customer": _row_value(active_project, "customer name", default=briefing["construction_revenue"]["active_job"]["customer"]),
                "job": _row_value(active_project, "project name", default=briefing["construction_revenue"]["active_job"]["job"]),
                "status": _row_value(active_project, "project status", default=briefing["construction_revenue"]["active_job"]["status"]),
                "next_step": _row_value(active_project, "recommended next action", default=briefing["construction_revenue"]["active_job"]["next_step"]),
            }
            briefing["one_next_action"] = {
                "title": _row_value(active_project, "recommended next action", default=briefing["one_next_action"]["title"]),
                "detail": _row_value(active_project, "notes", default=briefing["one_next_action"]["detail"]),
                "deadline": _row_value(active_project, "scheduled date", "last updated", default=briefing["one_next_action"]["deadline"]),
            }

        def _parse_currency(value: str) -> float:
            cleaned = value.replace("$", "").replace(",", "").strip()
            try:
                return float(cleaned)
            except ValueError:
                return 0.0

        total_open = sum(_parse_currency(_row_value(row, "estimate amount")) for row in open_projects)
        total_all = sum(_parse_currency(_row_value(row, "estimate amount")) for row in projects[:10])
        if total_open:
            briefing["construction_revenue"]["today_target"] = f"${total_open:,.0f}"
        if total_all:
            briefing["construction_revenue"]["week_booked"] = f"${total_all:,.0f}"

        schedule_rows = []
        for row in prioritized_projects[:4]:
            schedule_rows.append(
                {
                    "time": _row_value(row, "scheduled date", default="Scheduled"),
                    "title": _row_value(row, "project name", default="Project"),
                    "detail": _row_value(row, "recommended next action", "customer name", default=""),
                }
            )
        if schedule_rows:
            briefing["schedule"] = schedule_rows

        open_tasks = [row for row in tasks if "closed" not in _row_value(row, "status").lower()]
        if open_tasks:
            briefing["follow_ups"] = [
                {
                    "name": _row_value(row, "project name", default="Task"),
                    "topic": _row_value(row, "task description", default=""),
                    "due": _row_value(row, "due date", default="Soon"),
                    "channel": _row_value(row, "assigned to", default="Michael"),
                }
                for row in open_tasks[:5]
            ]

        if prioritized_projects:
            briefing["payments"] = [
                {
                    "name": _row_value(row, "customer name", default="Project"),
                    "type": "Project Balance",
                    "amount": _row_value(row, "estimate amount", default="$0"),
                    "status": _row_value(row, "payment status", default="Unknown"),
                }
                for row in prioritized_projects[:5]
            ]

        if materials:
            briefing["bills_money"] = [
                {
                    "name": _row_value(row, "material", default="Material"),
                    "amount": _row_value(row, "cost", default="TBD"),
                    "due": _row_value(row, "purchased (yes/no)", default="No"),
                }
                for row in materials[:5]
            ]

        pricing = read_sheet(LEGACY_TAB_MAP["pricing"]) if _tab_exists(LEGACY_TAB_MAP["pricing"]) else []
        if pricing:
            briefing["printing_revenue"]["featured_task"] = {
                "client": "Pricing Catalog",
                "task": _row_value(pricing[0], "service", default=briefing["printing_revenue"]["featured_task"]["task"]),
                "deadline": _row_value(pricing[0], "status", default=briefing["printing_revenue"]["featured_task"]["deadline"]),
            }
            briefing["printing_revenue"]["open_orders"] = len(pricing)
        return briefing

    if jobs:
        active_job = jobs[0]
        briefing["construction_revenue"] = {
            "today_target": _pick_first(jobs, "today_target", "today revenue target", default=briefing["construction_revenue"]["today_target"]),
            "week_booked": _pick_first(jobs, "week_booked", "week booked", default=briefing["construction_revenue"]["week_booked"]),
            "active_job": {
                "customer": _row_value(active_job, "customer", "customer_name", default=briefing["construction_revenue"]["active_job"]["customer"]),
                "job": _row_value(active_job, "job", "job_name", "title", default=briefing["construction_revenue"]["active_job"]["job"]),
                "status": _row_value(active_job, "status", default=briefing["construction_revenue"]["active_job"]["status"]),
                "next_step": _row_value(active_job, "next_step", "next action", default=briefing["construction_revenue"]["active_job"]["next_step"]),
            },
        }

        schedule_rows = []
        for row in jobs[:4]:
            schedule_rows.append(
                {
                    "time": _row_value(row, "time", "start_time", default="Today"),
                    "title": _row_value(row, "title", "job", "job_name", default="Job update"),
                    "detail": _row_value(row, "detail", "notes", "customer", default=""),
                }
            )
        if schedule_rows:
            briefing["schedule"] = schedule_rows

    if customers and not jobs:
        first_customer = customers[0]
        briefing["construction_revenue"]["active_job"]["customer"] = _row_value(
            first_customer, "customer", "name", default=briefing["construction_revenue"]["active_job"]["customer"]
        )

    if follow_ups:
        briefing["follow_ups"] = [
            {
                "name": _row_value(row, "customer_name", "name", "customer", "contact", default="Follow-up"),
                "topic": _row_value(row, "message_draft", "topic", "subject", "notes", default=""),
                "due": _row_value(row, "due_date", "due", default="Soon"),
                "channel": _row_value(row, "followup_type", "channel", "method", default="Call"),
            }
            for row in follow_ups[:5]
        ]

    if payments:
        briefing["payments"] = [
            {
                "name": _row_value(row, "name", "customer", "payer", default="Payment"),
                "type": _row_value(row, "type", "payment_type", default="Payment"),
                "amount": _row_value(row, "amount", default="$0"),
                "status": _row_value(row, "status", default="Pending"),
            }
            for row in payments[:5]
        ]

        briefing["printing_revenue"]["today_target"] = _pick_first(
            payments,
            "pog_today_target",
            "printing_today_target",
            default=briefing["printing_revenue"]["today_target"],
        )

    if bills:
        briefing["bills_money"] = [
            {
                "name": _row_value(row, "payee", "name", "vendor", default="Bill"),
                "amount": _row_value(row, "amount", default="$0"),
                "due": _row_value(row, "due_date", "due", default="Soon"),
            }
            for row in bills[:5]
        ]

    if family_events:
        briefing["family_calendar"] = [
            {
                "time": _row_value(row, "time", "start_time", default="Today"),
                "event": _row_value(row, "event_title", "event", "title", default="Family event"),
                "location": _row_value(row, "location", default=""),
            }
            for row in family_events[:5]
        ]

    if sports_notes:
        rockies_rows = [row for row in sports_notes if _row_value(row, "team", "sport", "category").lower() in {"mlb", "rockies", "colorado rockies"}]
        softball_rows = [row for row in sports_notes if _row_value(row, "sport", "category").lower() == "softball"]
        if rockies_rows:
            briefing["rockies"] = {
                "headline": _row_value(rockies_rows[0], "topic", "headline", "title", default=briefing["rockies"]["headline"]),
                "detail": _row_value(rockies_rows[0], "note", "detail", "notes", default=briefing["rockies"]["detail"]),
            }
        if softball_rows:
            briefing["softball"] = {
                "headline": _row_value(softball_rows[0], "topic", "headline", "title", default=briefing["softball"]["headline"]),
                "detail": _row_value(softball_rows[0], "note", "detail", "notes", default=briefing["softball"]["detail"]),
            }

    if ideas:
        briefing["ai_ideas"] = [
            {
                "title": _row_value(row, "title", "idea", default="Idea"),
                "impact": _row_value(row, "description", "impact", "notes", default=""),
            }
            for row in ideas[:5]
        ]
        first_idea = ideas[0]
        briefing["one_next_action"] = {
            "title": _row_value(first_idea, "next_action", "title", default=briefing["one_next_action"]["title"]),
            "detail": _row_value(first_idea, "description", "detail", "impact", "notes", default=briefing["one_next_action"]["detail"]),
            "deadline": _row_value(first_idea, "deadline", "due", default=briefing["one_next_action"]["deadline"]),
        }

    return briefing


def get_recent_updates(limit: int = 10) -> dict[str, Any]:
    local_updates = load_local_updates()
    result = {
        "updates": local_updates[:limit],
        "source": "local",
        "warning": None,
    }
    if not is_google_sheets_enabled():
        return result

    try:
        if not _tab_exists("MobileUpdates"):
            return {
                "updates": result["updates"],
                "source": "local",
                "warning": "Google Sheets is enabled, but this spreadsheet has no MobileUpdates tab. Showing local updates.",
            }
        sheet_rows = read_sheet("MobileUpdates")
        updates = _normalize_mobile_updates(sheet_rows)
        if updates:
            return {
                "updates": updates[:limit],
                "source": "google_sheets",
                "warning": None,
            }
        return {
            "updates": result["updates"],
            "source": "local",
            "warning": "Google Sheets MobileUpdates tab is empty. Showing local updates.",
        }
    except (GoogleSheetsConfigError, RuntimeError) as exc:
        return {
            "updates": result["updates"],
            "source": "local",
            "warning": f"Google Sheets unavailable: {exc}",
        }


def _unified_item(category: str, idx: int, *, name: str = "", phone: str = "", email: str = "",
                   job: str = "", amount: str = "", status: str = "", due: str = "",
                   notes: str = "", next_action: str = "") -> dict[str, Any]:
    return {
        "id": f"sheet-{category}-{idx}",
        "category": category,
        "name": name,
        "phone": phone,
        "email": email,
        "job": job,
        "amount": amount,
        "status": status,
        "due": due,
        "notes": notes,
        "next_action": next_action,
        "update_history": [],
    }


def _local_briefing_with_items() -> dict[str, Any]:
    briefing = get_mock_briefing()
    items = items_store.load_items()
    briefing["schedule"] = items["schedule"]
    briefing["follow_ups"] = items["follow_ups"]
    briefing["payments"] = items["payments"]
    briefing["bills_money"] = items["bills"]
    briefing["construction_jobs"] = items["construction_jobs"]
    briefing["printing_jobs"] = items["printing_jobs"]
    return briefing


def _attach_unified_lists_from_sheets(briefing: dict[str, Any]) -> dict[str, Any]:
    active_job = briefing["construction_revenue"]["active_job"]
    briefing["construction_jobs"] = [
        _unified_item(
            "construction_job", 0,
            name=active_job.get("customer", ""),
            job=active_job.get("job", ""),
            amount=briefing["construction_revenue"].get("today_target", ""),
            status=active_job.get("status", ""),
            next_action=active_job.get("next_step", ""),
        )
    ]

    featured_task = briefing["printing_revenue"]["featured_task"]
    briefing["printing_jobs"] = [
        _unified_item(
            "printing_job", 0,
            name=featured_task.get("client", ""),
            job=featured_task.get("task", ""),
            amount=briefing["printing_revenue"].get("today_target", ""),
            due=featured_task.get("deadline", ""),
        )
    ]

    briefing["follow_ups"] = [
        _unified_item("follow_up", i, name=row.get("name", ""), job=row.get("topic", ""),
                       due=row.get("due", ""), notes=row.get("channel", ""))
        for i, row in enumerate(briefing["follow_ups"])
    ]
    briefing["payments"] = [
        _unified_item("payment", i, name=row.get("name", ""), amount=row.get("amount", ""),
                       status=row.get("status", ""), notes=row.get("type", ""))
        for i, row in enumerate(briefing["payments"])
    ]
    briefing["bills_money"] = [
        _unified_item("bill", i, name=row.get("name", ""), amount=row.get("amount", ""),
                       due=row.get("due", ""))
        for i, row in enumerate(briefing["bills_money"])
    ]
    briefing["schedule"] = [
        _unified_item("schedule", i, name=row.get("title", ""), job=row.get("detail", ""),
                       due=row.get("time", ""))
        for i, row in enumerate(briefing["schedule"])
    ]
    return briefing


def get_today_briefing() -> dict[str, Any]:
    if not is_google_sheets_enabled():
        return {
            "briefing": _local_briefing_with_items(),
            "source": "mock_local",
            "warning": None,
        }

    try:
        briefing = _attach_unified_lists_from_sheets(_briefing_from_sheet_rows())
        return {
            "briefing": briefing,
            "source": "google_sheets",
            "warning": None,
        }
    except (GoogleSheetsConfigError, RuntimeError) as exc:
        return {
            "briefing": _local_briefing_with_items(),
            "source": "mock_local",
            "warning": f"Google Sheets unavailable: {exc}",
        }


def log_dashboard_action(update_type: str, subject: str, details: str) -> dict[str, Any]:
    return save_mobile_update(
        {"update_type": update_type, "subject": subject, "details": details},
        source="dashboard",
    )


def save_mobile_update(update_data: dict[str, Any], source: str = "mobile") -> dict[str, Any]:
    timestamp = datetime.now().isoformat(timespec="seconds")
    entry = {"timestamp": timestamp, "source": source, **update_data}
    saved_local = save_local_update(entry)

    result = {
        "entry": saved_local,
        "source": "local",
        "warning": None,
    }
    if not is_google_sheets_enabled():
        return result

    try:
        if not _tab_exists("MobileUpdates"):
            result["warning"] = "Google Sheets is enabled, but this spreadsheet has no MobileUpdates tab. Local fallback used."
            return result
        append_row(
            "MobileUpdates",
            {
                "update_id": f"upd-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "update_type": update_data["update_type"],
                "customer_name": update_data["subject"],
                "job_name": "",
                "amount": "",
                "note": update_data["details"],
                "followup_date": "",
                "status": "new",
                "raw_text": f"{update_data['subject']} - {update_data['details']}",
                "created_at": timestamp,
            },
        )
        result["source"] = "google_sheets+local"
    except (GoogleSheetsConfigError, RuntimeError) as exc:
        result["warning"] = f"Google Sheets save failed. Local fallback used: {exc}"
    return result

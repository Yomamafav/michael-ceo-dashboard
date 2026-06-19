from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
ITEMS_PATH = DATA_DIR / "dashboard_items.json"

# Maps the URL-facing category slug to the list stored under it.
CATEGORIES = ("schedule", "follow_ups", "payments", "bills", "construction_jobs", "printing_jobs")

CATEGORY_LABELS = {
    "schedule": "Schedule item",
    "follow_ups": "Follow-up",
    "payments": "Payment",
    "bills": "Bill",
    "construction_jobs": "Construction job",
    "printing_jobs": "Printing job",
}

COMPLETE_STATUS = {
    "schedule": "Done",
    "follow_ups": "Done",
    "bills": "Paid",
    "construction_jobs": "Complete",
    "printing_jobs": "Complete",
}


def _default_items() -> dict[str, list[dict[str, Any]]]:
    return {
        "schedule": [
            {
                "id": "sch-1", "category": "schedule", "name": "Crew check-in",
                "phone": "", "email": "", "job": "4 My4 Construction daily kickoff",
                "amount": "", "status": "Pending", "due": "7:30 AM",
                "notes": "", "next_action": "Be on site for the kickoff.",
                "update_history": [],
            },
            {
                "id": "sch-2", "category": "schedule", "name": "School office call",
                "phone": "", "email": "", "job": "Confirm Ava softball camp forms",
                "amount": "", "status": "Pending", "due": "9:00 AM",
                "notes": "", "next_action": "Call the school office.",
                "update_history": [],
            },
            {
                "id": "sch-3", "category": "schedule", "name": "POG print proof review",
                "phone": "", "email": "", "job": "Approve church banner revision",
                "amount": "", "status": "Pending", "due": "11:30 AM",
                "notes": "", "next_action": "Review and approve the proof.",
                "update_history": [],
            },
            {
                "id": "sch-4", "category": "schedule", "name": "Family pickup",
                "phone": "", "email": "", "job": "Grab Luke from summer weights",
                "amount": "", "status": "Pending", "due": "3:45 PM",
                "notes": "", "next_action": "Leave in time for pickup.",
                "update_history": [],
            },
        ],
        "follow_ups": [
            {
                "id": "fu-1", "category": "follow_up", "name": "Samantha Lee",
                "phone": "(303) 555-0142", "email": "samantha.lee@example.com",
                "job": "Fence repair estimate", "amount": "", "status": "Open", "due": "Today",
                "notes": "", "next_action": "Send the estimate by text.",
                "update_history": [], "channel": "Text",
            },
            {
                "id": "fu-2", "category": "follow_up", "name": "Grace Fellowship",
                "phone": "(303) 555-0199", "email": "office@gracefellowship.example",
                "job": "Banner invoice approval", "amount": "", "status": "Open", "due": "Today",
                "notes": "", "next_action": "Email an invoice approval reminder.",
                "update_history": [], "channel": "Email",
            },
            {
                "id": "fu-3", "category": "follow_up", "name": "Miguel Torres",
                "phone": "(720) 555-0173", "email": "miguel.torres@example.com",
                "job": "Kitchen remodel site visit", "amount": "", "status": "Open", "due": "Tomorrow",
                "notes": "", "next_action": "Call to confirm the site visit time.",
                "update_history": [], "channel": "Call",
            },
        ],
        "payments": [
            {
                "id": "pay-1", "category": "payment", "name": "Jose Ramirez",
                "phone": "(970) 555-0118", "email": "jose.ramirez@example.com",
                "job": "Garage slab + driveway extension", "amount": "$2,500",
                "status": "Pending", "due": "Today",
                "notes": "", "next_action": "Confirm the deposit cleared before locking the crew.",
                "update_history": [], "payment_type": "Deposit",
            },
            {
                "id": "pay-2", "category": "payment", "name": "Front Range Youth Camp",
                "phone": "(303) 555-0188", "email": "billing@frontrangeyouth.example",
                "job": "24 yard signs and 2 sponsor banners", "amount": "$640",
                "status": "Received", "due": "",
                "notes": "ACH posted this morning.", "next_action": "",
                "update_history": [], "payment_type": "Invoice",
            },
        ],
        "bills": [
            {
                "id": "bill-1", "category": "bill", "name": "Concrete supplier",
                "phone": "", "email": "", "job": "", "amount": "$1,180",
                "status": "Unpaid", "due": "Today",
                "notes": "", "next_action": "Pay before end of day.",
                "update_history": [],
            },
            {
                "id": "bill-2", "category": "bill", "name": "Truck payment",
                "phone": "", "email": "", "job": "", "amount": "$622",
                "status": "Unpaid", "due": "Friday",
                "notes": "", "next_action": "",
                "update_history": [],
            },
            {
                "id": "bill-3", "category": "bill", "name": "Shop internet",
                "phone": "", "email": "", "job": "", "amount": "$96",
                "status": "Unpaid", "due": "Friday",
                "notes": "", "next_action": "",
                "update_history": [],
            },
        ],
        "construction_jobs": [
            {
                "id": "cj-1", "category": "construction_job", "name": "Jose Ramirez",
                "phone": "(970) 555-0118", "email": "jose.ramirez@example.com",
                "job": "Garage slab + driveway extension", "amount": "$4,800",
                "status": "Waiting on deposit confirmation", "due": "Friday crew",
                "notes": "", "next_action": "Schedule crew and order rebar.",
                "update_history": [],
            },
        ],
        "printing_jobs": [
            {
                "id": "pj-1", "category": "printing_job", "name": "Front Range Youth Camp",
                "phone": "(303) 555-0188", "email": "billing@frontrangeyouth.example",
                "job": "24 yard signs and 2 sponsor banners", "amount": "$640",
                "status": "In production", "due": "Tomorrow at 2:00 PM",
                "notes": "", "next_action": "Confirm proof approval.",
                "update_history": [],
            },
            {
                "id": "pj-2", "category": "printing_job", "name": "Grace Fellowship",
                "phone": "(303) 555-0199", "email": "office@gracefellowship.example",
                "job": "Church banner revision", "amount": "$310",
                "status": "Awaiting approval", "due": "11:30 AM",
                "notes": "", "next_action": "Get sign-off on the revised proof.",
                "update_history": [],
            },
        ],
    }


def ensure_items_storage() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not ITEMS_PATH.exists():
        ITEMS_PATH.write_text(json.dumps(_default_items(), indent=2), encoding="utf-8")


def load_items() -> dict[str, list[dict[str, Any]]]:
    ensure_items_storage()
    try:
        with ITEMS_PATH.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict):
            defaults = _default_items()
            for category in CATEGORIES:
                data.setdefault(category, defaults[category])
            return data
    except json.JSONDecodeError:
        pass
    return _default_items()


def save_items(items: dict[str, list[dict[str, Any]]]) -> None:
    ITEMS_PATH.write_text(json.dumps(items, indent=2), encoding="utf-8")


class ItemNotFoundError(KeyError):
    pass


def find_item(items: dict[str, list[dict[str, Any]]], category: str, item_id: str) -> dict[str, Any]:
    if category not in CATEGORIES:
        raise ItemNotFoundError(f"Unknown category: {category}")
    for item in items[category]:
        if item.get("id") == item_id:
            return item
    raise ItemNotFoundError(f"No {category} item with id {item_id}")


def get_item(category: str, item_id: str) -> dict[str, Any]:
    items = load_items()
    return find_item(items, category, item_id)


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _append_history(item: dict[str, Any], text: str) -> None:
    history = item.setdefault("update_history", [])
    history.insert(0, {"timestamp": _now_iso(), "text": text})
    item["update_history"] = history[:20]


def mark_item_complete(category: str, item_id: str) -> dict[str, Any]:
    items = load_items()
    item = find_item(items, category, item_id)
    item["status"] = COMPLETE_STATUS.get(category, "Complete")
    _append_history(item, f"Marked {item['status'].lower()}")
    save_items(items)
    return item


def add_item_note(category: str, item_id: str, note: str) -> dict[str, Any]:
    items = load_items()
    item = find_item(items, category, item_id)
    item["notes"] = note
    _append_history(item, f"Note added: {note}")
    save_items(items)
    return item


def mark_deposit_paid(item_id: str) -> dict[str, Any]:
    items = load_items()
    item = find_item(items, "payments", item_id)
    item["status"] = "Paid"
    _append_history(item, "Deposit marked paid")
    save_items(items)
    return item


def mark_payment_received(item_id: str) -> dict[str, Any]:
    items = load_items()
    item = find_item(items, "payments", item_id)
    item["status"] = "Received"
    _append_history(item, "Payment marked received")
    save_items(items)
    return item


def create_follow_up(*, name: str, phone: str = "", email: str = "", job: str = "", due: str = "Today", channel: str = "Call") -> dict[str, Any]:
    items = load_items()
    existing_ids = {item["id"] for item in items["follow_ups"]}
    index = len(items["follow_ups"]) + 1
    new_id = f"fu-{index}"
    while new_id in existing_ids:
        index += 1
        new_id = f"fu-{index}"

    entry = {
        "id": new_id, "category": "follow_up", "name": name,
        "phone": phone, "email": email, "job": job, "amount": "",
        "status": "Open", "due": due,
        "notes": "", "next_action": "", "update_history": [], "channel": channel,
    }
    _append_history(entry, "Follow-up created")
    items["follow_ups"].insert(0, entry)
    save_items(items)
    return entry

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.google_sheets import (  # noqa: E402
    GoogleSheetsAccessError,
    GoogleSheetsConfigError,
    get_google_sheets_service,
)


REQUIRED_TABS = {
    "Customers": [
        "customer_id", "name", "phone", "email", "address", "source", "notes", "status", "created_at", "updated_at",
    ],
    "Jobs": [
        "job_id", "customer_id", "customer_name", "job_type", "scope", "address", "status", "estimate_amount",
        "deposit_required", "deposit_paid", "scheduled_date", "scheduled_time", "materials_needed", "notes",
        "created_at", "updated_at",
    ],
    "FollowUps": [
        "followup_id", "customer_id", "customer_name", "related_job_id", "followup_type", "due_date", "priority",
        "status", "message_draft", "notes", "created_at", "updated_at",
    ],
    "Payments": [
        "payment_id", "customer_id", "customer_name", "job_id", "amount", "payment_type", "payment_method", "status",
        "due_date", "paid_date", "notes", "created_at", "updated_at",
    ],
    "Bills": [
        "bill_id", "payee", "category", "amount", "due_date", "autopay_status", "status", "notes", "created_at", "updated_at",
    ],
    "FamilyEvents": [
        "event_id", "person", "event_title", "event_type", "date", "time", "location", "prep_needed", "notes",
        "created_at", "updated_at",
    ],
    "SportsNotes": [
        "note_id", "sport", "league", "team", "topic", "importance", "note", "source", "date", "created_at",
    ],
    "Ideas": [
        "idea_id", "category", "title", "description", "priority", "status", "next_action", "created_at", "updated_at",
    ],
    "MobileUpdates": [
        "update_id", "update_type", "customer_name", "job_name", "amount", "note", "followup_date", "status",
        "raw_text", "created_at",
    ],
}

LEGACY_TABS = ["Master Projects", "Tasks", "Pricing", "Materials"]


def _load_env_or_fail() -> None:
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        raise GoogleSheetsConfigError(
            "Missing .env file. Copy .env.example to .env and set GOOGLE_SERVICE_ACCOUNT_FILE and GOOGLE_SHEET_ID."
        )
    load_dotenv(env_path)


def main() -> int:
    try:
        _load_env_or_fail()
        service = get_google_sheets_service()
        titles = service.get_sheet_titles()
    except GoogleSheetsConfigError as exc:
        print(f"CONFIG ERROR: {exc}")
        return 1
    except GoogleSheetsAccessError as exc:
        print(f"ACCESS ERROR: {exc}")
        print("Check that the Google Sheet is shared with the service account email and that the Sheets API is enabled.")
        return 1
    except Exception as exc:
        print(f"UNEXPECTED ERROR: {exc}")
        return 1

    if all(tab in titles for tab in LEGACY_TABS):
        print("Google Sheet access verified.")
        print("Detected existing legacy layout. No tab changes were made.")
        for tab in LEGACY_TABS:
            print(f"- Found tab: {tab}")
        return 0

    print("Google Sheet access verified.")
    for tab in titles:
        print(f"- Found tab: {tab}")
    print("No changes were made.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

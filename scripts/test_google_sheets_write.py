from __future__ import annotations

import sys
from datetime import datetime
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
        if not service.tab_exists("MobileUpdates"):
            print("SKIPPED: This spreadsheet has no MobileUpdates tab.")
            print("No write was attempted so the existing project tabs were left untouched.")
            return 0
        timestamp = datetime.now().isoformat(timespec="seconds")
        update_id = f"test-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        test_row = {
            "update_id": update_id,
            "update_type": "test_write",
            "customer_name": "Verification Only",
            "job_name": "Google Sheets setup check",
            "amount": "0",
            "note": "Safe write test from scripts/test_google_sheets_write.py",
            "followup_date": "",
            "status": "test",
            "raw_text": f"Verification write at {timestamp}",
            "created_at": timestamp,
        }
        service.append_row("MobileUpdates", test_row)
        rows = service.get_raw_values("MobileUpdates")
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

    print("Write test succeeded.")
    print(f"Appended MobileUpdates row with update_id={update_id}")

    recent_rows = rows[-5:] if len(rows) > 5 else rows
    print("Last rows in MobileUpdates:")
    for row in recent_rows:
        print(f"- {row}")

    matched = any(update_id in row for row in recent_rows)
    if not matched:
        print("VERIFY FAILED: test row was appended but not found in the last rows returned.")
        return 1

    print("Read-back verification succeeded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

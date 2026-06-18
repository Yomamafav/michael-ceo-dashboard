# michael-ceo-dashboard

Milestone 2 keeps the local-first FastAPI dashboard shell from Milestone 1 and adds optional Google Sheets read/write support. If Google Sheets is disabled or unavailable, the app falls back to mock briefing data and local JSON persistence.

## Stack

- Python
- FastAPI
- Jinja2 templates
- HTML/CSS/JavaScript

## Features

- Dashboard home page at `/`
- Mobile update page at `/mobile`
- JSON daily briefing endpoint at `/api/briefing/today`
- Mobile update POST endpoint at `/api/mobile/update`
- Health endpoint at `/health`
- Mock daily business, family, sports, and AI opportunity data
- Local JSON persistence for submitted mobile updates
- Optional Google Sheets integration for dashboard reads and mobile update writes
- Graceful fallback to local data when Google Sheets is disabled or fails

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
uvicorn app.main:app --reload
```

4. Open:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/mobile`
- `http://127.0.0.1:8000/api/briefing/today`
- `http://127.0.0.1:8000/health`

## Google Sheets Integration

Google Sheets is optional. Leave `GOOGLE_SHEETS_ENABLED=false` to keep the app fully local.

### Expected tabs

Create these tabs in the spreadsheet:

- `Customers`
- `Jobs`
- `FollowUps`
- `Payments`
- `Bills`
- `FamilyEvents`
- `SportsNotes`
- `Ideas`
- `MobileUpdates`

### Suggested headers

Use a header row in each tab. The parser is forgiving, but these columns align with the current implementation:

- `Jobs`: `time`, `job`, `customer`, `status`, `next_step`, `today_target`, `week_booked`, `notes`
- `FollowUps`: `name`, `topic`, `due`, `channel`
- `Payments`: `name`, `type`, `amount`, `status`, `pog_today_target`
- `Bills`: `name`, `amount`, `due`
- `FamilyEvents`: `time`, `event`, `location`
- `SportsNotes`: `sport`, `headline`, `detail`
- `Ideas`: `title`, `impact`, `next_action`, `deadline`, `detail`
- `MobileUpdates`: `timestamp`, `update_type`, `subject`, `details`

### Google Cloud setup

1. Create or select a Google Cloud project at `https://console.cloud.google.com/`.
2. Enable the Google Sheets API for that project.
3. Open `APIs & Services` > `Credentials`.
4. Create a service account for this app.
5. Generate a JSON key for that service account and download it.
6. Store the JSON file outside version control, for example in a local `credentials/` folder.
7. Open the target Google Sheet and share it with the service account email address from the JSON file.
8. Copy `.env.example` to `.env` and set:

```env
GOOGLE_SHEETS_ENABLED=true
GOOGLE_SERVICE_ACCOUNT_FILE=credentials/your-service-account.json
GOOGLE_SHEET_ID=your_google_sheet_id
```

### Verify sheet access before live data

Run the setup script to create or verify the required tabs and header rows:

```bash
python scripts/setup_google_sheet.py
```

Run the safe write test to append one verification row to `MobileUpdates` and read it back:

```bash
python scripts/test_google_sheets_write.py
```

If either script reports an access error:

1. Open the service account JSON file locally and copy only the `client_email` value.
2. Share the Google Sheet with that service account email as an editor.
3. Confirm the Google Sheets API is enabled in the same Google Cloud project that owns the service account.
4. Re-run the setup script first, then the write test.

### Common failure messages

- `Missing .env file`: create `.env` from `.env.example`.
- `GOOGLE_SHEET_ID is required`: set `GOOGLE_SHEET_ID` in `.env`.
- `Service account file not found`: fix `GOOGLE_SERVICE_ACCOUNT_FILE` to point to the JSON key file.
- `The service account may not be shared on the sheet`: share the sheet with the `client_email` from the service account.
- `Google Sheets API may not be enabled`: enable the API in Google Cloud and retry.

### Security notes

- Do not commit the service account JSON file.
- Do not hardcode spreadsheet IDs or credentials.
- `.gitignore` excludes common credential file patterns and `.env`.

## Project Structure

```text
app/
  main.py
  data/
  services/
    data_store.py
    google_sheets.py
  static/
    app.js
    styles.css
  templates/
    base.html
    dashboard.html
    error.html
    mobile.html
```

## Notes

- No authentication is included yet.
- `app/data/mobile_updates.json` is created automatically on first run.
- If Google Sheets is enabled and healthy, `/api/mobile/update` appends to the `MobileUpdates` tab and still saves locally.
- If Google Sheets fails, the API returns a warning and local fallback stays active where safe.

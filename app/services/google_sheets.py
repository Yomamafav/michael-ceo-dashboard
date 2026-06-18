from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


class GoogleSheetsConfigError(RuntimeError):
    """Raised when Google Sheets is enabled but not configured correctly."""


class GoogleSheetsAccessError(RuntimeError):
    """Raised when Google Sheets credentials are valid but the sheet cannot be accessed."""


class GoogleSheetsService:
    def __init__(self) -> None:
        self.sheet_id = os.getenv("GOOGLE_SHEET_ID", "").strip()
        self.service_account_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "").strip()

        if not self.sheet_id:
            raise GoogleSheetsConfigError("GOOGLE_SHEET_ID is required when Google Sheets is enabled.")
        if not self.service_account_file:
            raise GoogleSheetsConfigError(
                "GOOGLE_SERVICE_ACCOUNT_FILE is required when Google Sheets is enabled."
            )

        credential_path = Path(self.service_account_file)
        if not credential_path.exists():
            raise GoogleSheetsConfigError(
                f"Service account file not found: {credential_path}"
            )

        credentials = Credentials.from_service_account_file(str(credential_path), scopes=SCOPES)
        self.client = build("sheets", "v4", credentials=credentials, cache_discovery=False)

    def _raise_http_error(self, exc: HttpError, action: str, tab_name: str | None = None) -> None:
        status = getattr(exc.resp, "status", None)
        target = f" tab '{tab_name}'" if tab_name else ""
        detail = f"Google Sheets request failed while trying to {action}{target}."

        if status == 403:
            detail += " The service account may not be shared on the sheet, or the Google Sheets API may not be enabled."
            raise GoogleSheetsAccessError(detail) from exc
        if status == 404:
            detail += " The spreadsheet ID may be wrong, or the service account cannot see the sheet."
            raise GoogleSheetsAccessError(detail) from exc
        raise RuntimeError(detail) from exc

    def get_sheet_titles(self) -> list[str]:
        try:
            response = (
                self.client.spreadsheets()
                .get(spreadsheetId=self.sheet_id, fields="sheets.properties.title")
                .execute()
            )
        except HttpError as exc:
            self._raise_http_error(exc, "read spreadsheet metadata")

        sheets = response.get("sheets", [])
        return [sheet["properties"]["title"] for sheet in sheets if sheet.get("properties", {}).get("title")]

    def tab_exists(self, tab_name: str) -> bool:
        return tab_name in set(self.get_sheet_titles())

    def create_tab(self, tab_name: str) -> None:
        body = {"requests": [{"addSheet": {"properties": {"title": tab_name}}}]}
        try:
            self.client.spreadsheets().batchUpdate(spreadsheetId=self.sheet_id, body=body).execute()
        except HttpError as exc:
            self._raise_http_error(exc, "create", tab_name)

    def get_raw_values(self, tab_name: str) -> list[list[str]]:
        try:
            response = (
                self.client.spreadsheets()
                .values()
                .get(spreadsheetId=self.sheet_id, range=f"{tab_name}!A:Z")
                .execute()
            )
        except HttpError as exc:
            self._raise_http_error(exc, "read", tab_name)
        return response.get("values", [])

    def write_header_row(self, tab_name: str, headers: list[str]) -> None:
        body = {"values": [headers]}
        try:
            (
                self.client.spreadsheets()
                .values()
                .update(
                    spreadsheetId=self.sheet_id,
                    range=f"{tab_name}!A1",
                    valueInputOption="RAW",
                    body=body,
                )
                .execute()
            )
        except HttpError as exc:
            self._raise_http_error(exc, "write headers to", tab_name)

    def read_sheet(self, tab_name: str) -> list[dict[str, str]]:
        rows = self.get_raw_values(tab_name)
        if not rows:
            return []

        headers = [str(cell).strip() for cell in rows[0]]
        output: list[dict[str, str]] = []
        for raw_row in rows[1:]:
            row = {
                headers[index]: str(raw_row[index]).strip()
                for index in range(min(len(headers), len(raw_row)))
                if headers[index]
            }
            if any(value for value in row.values()):
                output.append(row)
        return output

    def append_row(self, tab_name: str, row_data: dict[str, Any]) -> None:
        values = ["" if value is None else str(value) for value in row_data.values()]
        body = {"values": [values]}
        try:
            (
                self.client.spreadsheets()
                .values()
                .append(
                    spreadsheetId=self.sheet_id,
                    range=f"{tab_name}!A:Z",
                    valueInputOption="USER_ENTERED",
                    insertDataOption="INSERT_ROWS",
                    body=body,
                )
                .execute()
            )
        except HttpError as exc:
            self._raise_http_error(exc, "append to", tab_name)

    def ensure_tabs_and_headers(self, tab_headers: dict[str, list[str]]) -> list[str]:
        existing_titles = set(self.get_sheet_titles())
        summary: list[str] = []
        for tab_name, headers in tab_headers.items():
            if tab_name not in existing_titles:
                self.create_tab(tab_name)
                summary.append(f"Created tab: {tab_name}")
            else:
                summary.append(f"Verified tab exists: {tab_name}")

            raw_rows = self.get_raw_values(tab_name)
            current_headers = raw_rows[0] if raw_rows else []
            if current_headers != headers:
                self.write_header_row(tab_name, headers)
                summary.append(f"Set headers on {tab_name}")
            else:
                summary.append(f"Verified headers on {tab_name}")
        return summary


@lru_cache(maxsize=1)
def get_google_sheets_service() -> GoogleSheetsService:
    return GoogleSheetsService()

# Agent Command Center

> **How to use this file**
> - This file is a persistent record of what the agent has done and what it is working on.
> - Add planned changes under **Open Tasks** before starting significant work.
> - If a decision is needed from Michael, write the exact question under **Blockers / Questions**.
> - After every work session, update Completed Work, Change Log, and Next Recommended Action.
> - The live version of this data is at `/command-center` in the running dashboard.

---

## Current Mission

Build a local-first, mobile-friendly CEO dashboard for Michael to manage **4 My4 Construction** and **POG Printing** daily operations — accessible from the shop laptop and the phone in the field.

---

## Open Tasks

| # | Task | Owner | Priority | Status |
|---|------|-------|----------|--------|
| 1 | Connect Google Sheets as live data source | Claude Code | High | New |
| 2 | Overdue follow-up notifications | Claude Code | Medium | New |
| 3 | Mobile update photo attachments | Claude Code | Low | New |

---

## Blockers / Questions for Michael

| # | Question | Context | Date raised |
|---|----------|---------|-------------|
| 1 | Should the dashboard auto-refresh every few minutes? | Crew submits mobile updates; Michael won't see them without refreshing the page | 2026-06-19 |
| 2 | Track revenue totals per month or just daily targets? | Revenue cards currently show only daily targets; monthly tracking needs more storage | 2026-06-19 |

---

## Completed Work

| Date | What was done |
|------|---------------|
| 2026-06-19 | Agent Command Center: `/command-center` tab with Command Inbox, Agent Questions, Project Status, Change Log, Approval Queue. Data stored in `app/data/command_center.json`. |
| 2026-06-18 | Phase 1 interactivity: clickable cards, detail modals, action buttons (complete, note, deposit-paid, payment-received), add-item forms for all 6 categories. |
| 2026-06-17 | Initial dashboard: FastAPI server, Jinja2 templates, Google Sheets integration with `GOOGLE_SHEETS_ENABLED` flag, mobile update form, updates log. |

---

## Change Log

| Date | Feature | Files affected |
|------|---------|----------------|
| 2026-06-19 | Agent Command Center | `app/main.py`, `app/services/command_center_store.py`, `app/templates/command_center.html`, `app/static/command_center.js`, `app/static/styles.css`, `app/data/command_center.json`, `app/templates/base.html` |
| 2026-06-18 | Phase 1 interactivity | `app/main.py`, `app/services/items_store.py`, `app/templates/base.html`, `app/static/app.js`, `app/static/styles.css`, `app/data/dashboard_items.json` |
| 2026-06-17 | Initial dashboard | `app/main.py`, `app/services/data_store.py`, `app/services/google_sheets.py`, `app/templates/dashboard.html`, `app/templates/mobile.html`, `app/static/styles.css`, `app/data/mobile_updates.json` |

---

## Pending Approvals

| # | What | Status |
|---|------|--------|
| 1 | Agent Command Center tab | Pending Michael's review at `/command-center` → Approval Queue |

---

## Next Recommended Action

**Enable live Google Sheets data.** Set `GOOGLE_SHEETS_ENABLED=true` in `.env` and run a live test against the real spreadsheet. The service account integration code already exists in `app/services/google_sheets.py` — just needs a connected service account JSON and a live test.

---

## Architecture Notes

- All Command Center data is local JSON at `app/data/command_center.json`
- Structure is compatible with Google Sheets, Firebase, Supabase, or a local SQL DB for future migration
- Every action in `app/services/command_center_store.py` has an `# AUTOMATION HOOK` comment marking where future agent calls or external API writes will go
- The live dashboard UI for this file is at `http://localhost:8014/command-center`

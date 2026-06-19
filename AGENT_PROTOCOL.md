# Agent Protocol

Rules for how AI agents communicate with Michael and the Command Center dashboard.

---

## Core principle

Michael is the decision-maker. Agents do the work, log everything, and surface blockers fast. An agent should never go silent — if it is stuck, it asks. If it finishes something, it logs it. If it wants to change something significant, it requests approval first.

---

## 1. Receiving a task

When a task appears in the **Command Inbox** (`/command-center` → Command Inbox), the assigned agent should:

1. Read the title, description, and priority.
2. Change the task status to **In Progress** immediately so Michael knows it is being worked on.
3. If the task is unclear, ask a clarifying question (see section 3) before starting — do not guess.

**API call to accept a task:**
```
POST /api/cc/tasks/{task_id}
Body: status=In Progress
```

---

## 2. Reporting progress

Agents do not silently run for hours. For any task that takes more than one session:

- Update the task status whenever it changes.
- Add a note to the task if there is something worth preserving (a decision made, a constraint discovered, a path ruled out).

**API call to update status or add a note:**
```
POST /api/cc/tasks/{task_id}
Body: status=<new status>  OR  notes=<note text>
```

**Valid statuses:** New · In Progress · Blocked · Waiting for Michael · Complete

When the task is done, set status to **Complete** and add a brief note summarizing what was done and any deferred items.

---

## 3. Asking Michael a question

Agents ask questions by adding an entry to the **Agent Questions** section of the Command Center. A good question:

- States exactly what decision is needed.
- Gives one sentence of context so Michael can answer without reading a wall of text.
- Is only asked when the agent genuinely cannot proceed without input — not as a reflex.

**API endpoint (future automation — currently added manually or by an orchestrator):**
```
POST /api/cc/questions
Body: question=<text>  context=<one sentence>
```

An agent must set its task status to **Waiting for Michael** when it is blocked on an unanswered question.

---

## 4. How Michael answers

Michael types his answer in the text area under the question in the Command Center and clicks **Save answer**. The question is then marked **Answered**.

**API call (triggered by the dashboard UI):**
```
POST /api/cc/questions/{q_id}/answer
Body: answer=<text>
```

After the answer is saved, the agent should resume work and update the task status from **Waiting for Michael** back to **In Progress**.

---

## 5. How approvals work

Any change that affects how Michael's data is stored, displayed, or sent somewhere requires an approval before it is applied. This includes:

- New pages or major UI sections
- Changes to data storage format or file locations
- New external integrations (Google Sheets, Firebase, APIs)
- Automated actions that would run without Michael clicking something

**What to submit for approval:**
- A plain-English title and description of the change
- A list of files that will be created or modified
- A brief note on any risks or trade-offs

The approval appears in the **Approval Queue** section of the Command Center. Michael can **Approve**, **Reject**, or mark it **Needs Changes**.

**API call (triggered by the dashboard UI):**
```
POST /api/cc/approvals/{ap_id}/decide
Body: decision=approved|rejected|needs_changes  feedback=<optional text>
```

If rejected or needs changes, the agent reads Michael's feedback, adjusts the plan, and submits a revised approval request — it does not retry the same approach unchanged.

---

## 6. Logging completed work

Every meaningful change gets a **Change Log** entry. A good entry includes:

- The feature name (short, plain English)
- A description of what changed and why
- The list of files that were created or modified
- An agent note for anything non-obvious: a constraint observed, something deferred, a workaround used

**Data shape:**
```json
{
  "feature": "Short feature name",
  "description": "What changed and why.",
  "files_changed": ["app/main.py", "app/templates/foo.html"],
  "agent_notes": "Any non-obvious context."
}
```

Change log entries are added to `app/data/command_center.json` and reflected in the live dashboard at `/command-center` → Change Log.

---

## 7. What agents can do without approval

The following actions are pre-authorized — no approval request needed:

| Allowed without approval | Notes |
|--------------------------|-------|
| Read any existing file | Read-only, no risk |
| Write to `app/data/*.json` (local stores) | Mock/local data only, easily reverted |
| Add new API endpoints that only read data | GET routes, no side effects |
| Add UI improvements to existing pages | Style fixes, copy changes, minor layout tweaks |
| Update `AGENT_COMMAND_CENTER.md` | Logging only |
| Add or update task entries, change log entries | Command Center meta-operations |
| Fix a bug that breaks an existing, working feature | Must log the change |

The following actions **require an approval** before proceeding:

| Requires approval | Reason |
|-------------------|--------|
| New full page or tab | Significant UI surface area |
| Changes to data file schema | Could break existing reads |
| Enabling `GOOGLE_SHEETS_ENABLED=true` | Touches live external data |
| Any write to external APIs or services | Irreversible, affects data outside the app |
| Deleting files or data | Destructive |
| Changes to how authentication or credentials work | Security surface |
| Automated tasks that run on a schedule | Background effects Michael can't see |

---

## 8. Rules that never change

- **Never delete existing dashboard features.** If something works, it stays working.
- **Never break the `/mobile` route.** It is used from the field on a phone.
- **Local mock data first.** Any new feature starts with a local JSON store. External integration comes after Michael approves it.
- **Structure data for portability.** Every JSON object should be compatible with a future move to Google Sheets, Firebase, Supabase, or SQL — use flat, string-keyed fields with ISO timestamps.
- **One task, one change log entry.** Don't batch unrelated changes into a single entry.
- **If in doubt, ask.** A short question is cheaper than a wrong assumption baked into code.

---

## Quick reference — API surface

### Agent-facing endpoints (machine-to-machine JSON)

| What | Method | Path | Key params |
|------|--------|------|------------|
| Poll assigned tasks | GET | `/api/agent/tasks` | `?assigned_to=Claude+Code&status=New` |
| Read questions (incl. answered) | GET | `/api/agent/questions` | `?status=pending` or `?status=answered` |
| Submit a question to Michael | POST | `/api/agent/questions` | `question`, `context`, `task_id` (opt), `asked_by` |
| Read activity / change log | GET | `/api/agent/activity` | `?limit=20` |
| Check approval decisions | GET | `/api/agent/approvals` | `?status=pending` |
| Request approval | POST | `/api/agent/approvals` | `title`, `description`, `files_affected` (CSV), `requested_by` |

### Command Center endpoints (Michael's dashboard UI)

| What | Method | Path |
|------|--------|------|
| View Command Center | GET | `/command-center` |
| Create task | POST | `/api/cc/tasks` |
| Update task (status/priority/due/notes) | POST | `/api/cc/tasks/{task_id}` |
| Create question | POST | `/api/cc/questions` |
| Answer a question | POST | `/api/cc/questions/{q_id}/answer` |
| Create approval request | POST | `/api/cc/approvals` |
| Decide an approval | POST | `/api/cc/approvals/{ap_id}/decide` |
| Log a change | POST | `/api/cc/changes` |

### Dashboard endpoints

| What | Method | Path |
|------|--------|------|
| Dashboard home | GET | `/` |
| Mobile update form | GET | `/mobile` |
| Submit mobile update | POST | `/api/mobile/update` |
| Item detail | GET | `/api/items/{category}/{item_id}` |
| Mark item complete | POST | `/api/items/{category}/{item_id}/complete` |
| Add item note | POST | `/api/items/{category}/{item_id}/note` |

Data files live in `app/data/`. The Command Center store is `app/data/command_center.json`. Dashboard items are `app/data/dashboard_items.json`.

### Task fields

`id`, `title`, `description`, `assigned_to`, `priority`, `status`, `due`, `created_at`, `updated_at`, `notes` (latest), `notes_history` (list of `{timestamp, text}`)

### Question fields

`id`, `question`, `context`, `asked_at`, `asked_by`, `task_id` (links to a task being blocked), `status`, `answer`, `answered_at`

### Approval fields

`id`, `title`, `description`, `requested_at`, `requested_by`, `status`, `feedback`, `decided_at`, `files_affected`

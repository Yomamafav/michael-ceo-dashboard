# CEO Dashboard — Definition

## What It Is

The CEO Dashboard is Michael's primary control center for all company operations.
It is a single web interface where Michael manages every aspect of the business
and oversees all AI agent activity.

---

## Relationship to OpenJarvis

```
Michael
  ↓
CEO Dashboard        ← primary UI / control center
  ↓
OpenJarvis (Jarvis)  ← AI agent framework
  ↓
Agents               ← individual AI workers
```

The CEO Dashboard is **not** OpenJarvis. OpenJarvis is the underlying agent
framework. The CEO Dashboard consumes OpenJarvis agent outputs and surfaces
them to Michael in a business context.

---

## Purpose

A single interface for Michael to manage:

| Domain | Description |
|--------|-------------|
| Customers | Customer records, follow-ups, contact history |
| Projects | Construction jobs, POG printing jobs, active work |
| Tasks | Action items, assignments, deadlines |
| Events | Scheduled appointments and milestones |
| Approvals | Items requiring Michael's sign-off |
| Follow-ups | Outstanding items needing a response or action |
| Financial Summaries | Payments, deposits, bills, cash position |
| Communications | Email, messages, and channel activity |

---

## Requirements

1. **The CEO Dashboard must remain business-focused.** Business operations sections
   (customers, projects, tasks, etc.) must stay clean and separate from AI tooling.

2. **Add an AI Operations section.** This is a new tab/panel alongside the existing
   business sections — not replacing them.

3. **AI Operations must contain:**
   - **Agent Status** — live status of every OpenJarvis agent (running / idle / error)
   - **Agent Inbox** — tasks and outputs delivered by agents that need Michael's review
   - **Agent Questions** — questions agents have escalated that require Michael's decision
   - **Activity Feed** — chronological log of recent agent actions

4. **Existing customer/project functions remain separate.** No existing feature is
   removed or merged into AI Operations.

5. **The CEO Dashboard becomes the command center for both:**
   - Business operations (existing)
   - AI operations (new AI Operations section)

---

## Integrations

| Integration | Purpose |
|-------------|---------|
| Google Sheets | Live business data sync (customers, jobs, financials) |
| Gmail | Communications, follow-up tracking |
| Google Calendar | Events, scheduling |
| Obsidian | Notes, project documentation |
| CRM | Customer relationship data |
| Accounting | Financial summaries, bills, deposits |

---

## AI Operations Section — Detail

The AI Operations section bridges the CEO Dashboard and OpenJarvis. It is the
surface where Michael interacts with agents without leaving the business dashboard.

### Agent Status panel
- List of all configured OpenJarvis agents
- Current state: running / idle / error / scheduled
- Last run time and next scheduled run

### Agent Inbox
- Outputs from agents that are addressed to Michael
- Each item: agent name, summary, timestamp, action buttons (Approve / Dismiss / Reply)

### Agent Questions
- Questions escalated by agents that require a business decision
- Each item: question text, context, agent that asked, date raised
- Action: Answer (free text) or Defer

### Activity Feed
- Chronological stream of all agent actions
- Filterable by agent, date, action type
- Read-only audit trail

---

## What This Is NOT

- Not a replacement for OpenJarvis configuration (use the Jarvis CLI/UI for that)
- Not a coding interface
- Not a public-facing tool — local-first, for Michael only

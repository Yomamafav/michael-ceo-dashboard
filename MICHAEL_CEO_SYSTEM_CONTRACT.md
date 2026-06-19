# Michael CEO System Contract

This document defines the operating rules for Michael Pogue's business management system.
Every component — dashboard, agents, automations, integrations — operates under these terms.

---

## Purpose

Michael runs a construction and printing business. This system exists to help him:

1. **Make money** — quote jobs, close work, collect deposits
2. **Collect money** — track payments, flag overdue balances
3. **Finish jobs** — know what's in progress and what's stuck
4. **Follow up with customers** — never let a lead or open item go cold
5. **Manage family obligations** — schedule awareness, no surprises
6. **Reduce administrative work** — less manual tracking, more doing

**Priority order when there is a conflict:** Revenue > Follow-ups > Scheduling > Reporting > Cosmetic

Do not build, propose, or run anything that does not directly serve one of the six purposes above.

---

## Sources of Truth

Every piece of business data has exactly one place where it lives. No duplicates, no guessing.

### Google Sheets (live business data)

| Sheet | What it contains |
|-------|-----------------|
| Customers | Contact records, job history, follow-up status |
| Jobs | Active and completed construction jobs, status, amounts |
| Deposits | Deposit collected, deposit due, balance owed |
| Follow-ups | Open items, who to call, what about, due date |
| Printing Orders | POG printing jobs, status, pickup/delivery |
| Daily Updates | Field notes, status changes, anything Michael logs from the phone |

### Obsidian (knowledge and documentation)

| Vault section | What it contains |
|---------------|-----------------|
| Notes | Meeting notes, customer conversation logs |
| SOPs | Standard operating procedures for recurring jobs |
| Meeting Records | Notes from contractor, supplier, and customer meetings |
| Project History | Completed job documentation, lessons learned |

---

## System Responsibilities

### CEO Dashboard (`/`)
- Display operational status for all active items
- Display the daily briefing
- Display key business KPIs (money in, money out, jobs open, follow-ups due)
- Allow Michael to take action: log updates, mark items complete, add notes

### OpenJarvis (AI agent framework)
- Read data from Google Sheets
- Read notes and SOPs from Obsidian
- Generate insights from patterns in the data
- Generate the daily briefing for the dashboard
- Run scheduled automations (follow-up reminders, overdue payment alerts, job status summaries)

### Claude Code / Build Agent
- Maintain and improve the dashboard software
- Implement integrations (Sheets, Obsidian, Gmail, Calendar)
- Build only what Michael explicitly approves

---

## Communication Flows

### Michael logs a field update (from phone)
```
Michael → /mobile (phone) → Google Sheets → OpenJarvis reads → Dashboard reflects
```

### A customer situation changes
```
Customer pays / job updates → Michael records in Google Sheets → Dashboard reflects
```

### Michael takes notes
```
Michael's notes → Obsidian → OpenJarvis reads → Daily Briefing → Dashboard
```

### Daily briefing cycle
```
Google Sheets + Obsidian → OpenJarvis generates briefing → Dashboard displays → Michael reads
```

---

## What Michael Decides

The following always require Michael's explicit approval before any system acts on them:

| Decision | Why it requires Michael |
|----------|------------------------|
| New dashboard page or major tab | Affects what Michael sees every day |
| Enabling Google Sheets write-back | Changes live business data |
| Automated actions (send email, send text, etc.) | Irreversible, customer-facing |
| New external integrations (Gmail, Calendar, CRM) | Connects to live accounts |
| Any scheduled automation | Runs without Michael present |
| Changes to data file structure | Could break existing reads |
| Deleting any data or files | Destructive and irreversible |

---

## What the System Handles Without Asking

| Action | System |
|--------|--------|
| Read data from Sheets (read-only) | OpenJarvis |
| Read notes from Obsidian (read-only) | OpenJarvis |
| Generate the daily briefing | OpenJarvis |
| Surface questions and blockers in Command Center | Agents |
| Log completed work to the Change Log | Agents |
| Update task status as work progresses | Agents |
| Minor UI improvements to existing pages | Build Agent |
| Bug fixes that restore broken existing features | Build Agent |

---

## Rules That Never Change

1. **Never delete existing dashboard features.** If it works, it stays.
2. **Never break `/mobile`.** It is used from the field on a phone.
3. **Local data first.** Every new feature starts with a local JSON store. Live integration only after Michael approves.
4. **One source of truth per data type.** Google Sheets for live business data. Obsidian for knowledge and docs. Dashboard for displaying both.
5. **Agents ask before acting on anything irreversible.** A question is cheaper than a mistake.
6. **Every meaningful change gets a Change Log entry.** What changed, which files, why.
7. **No cosmetic work while revenue items are open.** Priorities are Revenue > Follow-ups > Scheduling > Reporting > Cosmetic.
8. **Data must be portable.** Every record uses flat fields and ISO timestamps. No schema that only works in one tool.

---

## System Stack

```
Michael
  ↓  (approves, decides, logs from phone)
CEO Dashboard     ← primary control center
  ↓  (reads, displays, accepts actions)
OpenJarvis        ← AI agent framework (reads Sheets, reads Obsidian, generates briefings)
  ↓  (executes)
Agents            ← individual workers (build agent, chief of staff, etc.)
  ↓  (reads)
Google Sheets + Obsidian    ← sources of truth
```

---

*Last updated: 2026-06-19*
*This document is the master contract. When in doubt, refer here first.*

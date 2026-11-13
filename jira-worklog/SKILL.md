---
name: jira-worklog
description: Use when the user asks to log Jira time, catch up on Jira worklogs, submit time tracking, or hasn't logged time in a while and needs to reconstruct it. Drafts an 8h/day allocation for Joe & The Juice Jira (joejuice.atlassian.net, GX project) across In Progress / Code Review tickets and GitHub PR activity, then submits via the jira CLI after explicit confirmation.
---

# Jira Worklog Catch-Up

Retrospectively submit Jira worklogs for a date range. `helper.py` does the mechanical work (query Jira and GitHub, build the draft, submit). This skill drives it: build the plan, show it as a table, take conversational edits, get an explicit `y`, then submit.

**Never call `jira issue worklog add` directly.** Always use `helper.py submit`. It handles time formatting, timezone, and per-row failures.

> `$SKILL_DIR` below is the absolute path of this skill's folder. Substitute it before running.

## Joe setup

- Jira: `joejuice.atlassian.net`, mainly project **GX** (Guest Experience). Other projects (e.g. GSH) still show up through the In-Progress query.
- Tickets count as worked on a day if they were in **In Progress** or **Code Review** that day. Epics are excluded.
- GitHub: PRs in the `joeandthejuice` org whose title has a GX key, e.g. `feat(GX-775): ...` (conventional-commit style). Reviews and commits by the user on a day add that ticket to the day. PRs without a key are skipped and counted.
- Hours: 8h/day, Mon-Fri, Danish public holidays skipped, worklogs start 09:00 Europe/Copenhagen.

## Prerequisites

- `jira` CLI ([jira-cli](https://github.com/ankitpokhrel/jira-cli)) set up for joejuice.atlassian.net (`jira init`). The helper reads `server`, `login` and `api_token` from `~/.config/.jira/.config.yml`.
- `gh` CLI logged in (adds tickets from PR reviews and commits; `--no-github` skips it).
- `pip install holidays` (optional, skips public holidays).

If any is missing, say what to install; do not work around it.

## Settings

`$SKILL_DIR/config.json`: `timezone`, `country` (holidays), `hours_per_day`, `day_start`, `increment_minutes`, `project_keys` (keys recognised in PR titles; empty = any `ABC-123`), `in_progress_statuses`, `github_owner` (limits PR search to that org; empty = all).

## Workflow

### 1. Build the plan

Default, window starts the day after the user's last worklog:

```bash
python3 "$SKILL_DIR/helper.py" plan --auto-since
```

Explicit range:

```bash
python3 "$SKILL_DIR/helper.py" plan --since YYYY-MM-DD --until YYYY-MM-DD
```

Flags: `--country XX` (override holidays, `""` disables), `--no-github`. `--until` defaults to today.

The helper prints the path of a JSON plan. Read it. Handle:
- `{"error": "no_anchor"}`: no worklogs ever; ask for an explicit `--since`.
- `holidays_warning` in the plan: tell the user holidays were not skipped.
- `github.error`: tell the user the plan is Jira-only.

### 2. Present the plan

Markdown table, minutes as `Xh Ym`. Include every day, also `already_logged`, `empty` and `holiday` ones:

| Date | Weekday | Ticket | Summary | Hours | Status |
|---|---|---|---|---|---|
| 2026-04-20 | Mon | GX-123 | Refactor X | 4h | |
| 2026-04-20 | Mon | GX-456 | Add Y | 4h | |
| 2026-04-21 | Tue | — | — | — | already logged (8h) |
| 2026-04-22 | Wed | — | — | — | no In Progress tickets |
| 2026-04-06 | Mon | — | — | — | holiday (Easter Monday) |

Then ask: "Edit anything, or submit as-is?"

### 3. Edit loop

Apply natural-language edits to the plan JSON, redraw the table, ask again. Examples:
- "drop GX-456 Monday, 8h to GX-123" → remove entry, set GX-123 to 480.
- "Friday was GX-202, 8h" → add entry (fetch the summary with `jira issue view GX-202 --plain` if useful).
- "Wed I was on PTO" → set that day's `entries` to `[]`.

Days with status `already_logged` are locked. If asked to edit one, warn that adding entries double-logs and ask before doing it.

For a day to be submitted its status must be `editable`; if you add entries to an `empty` day, set its status to `editable`.

### 4. Final confirmation

On "submit", "go", "looks good" etc., do NOT submit yet. Print:

> Submitting N entries totalling Xh across 2026-04-20 → 2026-04-27. Confirm? (y/n)

Only an explicit `y` proceeds. Anything else returns to the edit loop.

### 5. Submit

Write the edited plan back to its file, then:

```bash
python3 "$SKILL_DIR/helper.py" submit --plan-file <plan path>
```

Report "Submitted M of N. Failed: …". Offer to retry failures with a minimal plan containing only those rows.

## Red flags

Stop if you are about to:
- call `jira issue worklog add` directly
- hand-write JQL instead of letting `helper.py plan` build it
- submit without the final summary and an explicit `y`
- skip the existing-worklog check
- change `already_logged` days without warning

Not for: live time tracking, editing or deleting worklogs, non-Jira systems.

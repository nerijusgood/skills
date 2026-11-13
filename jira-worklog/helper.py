"""Jira worklog catch-up helper. Settings live in config.json next to this file."""

import base64
import json
import os
import re
from datetime import date, datetime, time, timedelta
from subprocess import CompletedProcess
from typing import Callable, Dict, List, Optional, Set, Tuple
from urllib.parse import quote
from zoneinfo import ZoneInfo

HttpGet = Callable[[str, dict], dict]
Runner = Callable[[List[str]], CompletedProcess]

DEFAULT_SETTINGS = {
    "timezone": "Europe/Copenhagen",
    "country": "DK",
    "hours_per_day": 8,
    "day_start": "09:00",
    "increment_minutes": 15,
    "project_keys": [],
    "in_progress_statuses": ["In Progress"],
    "github_owner": "",
}


def load_settings(path: Optional[str] = None) -> dict:
    """config.json next to this file, over DEFAULT_SETTINGS. Missing file is fine."""
    path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    settings = dict(DEFAULT_SETTINGS)
    try:
        with open(path) as f:
            settings.update(json.load(f))
    except FileNotFoundError:
        pass
    return settings


def build_key_regex(project_keys: List[str]) -> "re.Pattern[str]":
    """Regex for issue keys. Empty project_keys means any PROJ-123 style key."""
    if project_keys:
        projects = "|".join(re.escape(k) for k in project_keys)
    else:
        projects = r"[A-Za-z][A-Za-z0-9]+"
    return re.compile(rf"\b(?:{projects})-\d+", re.IGNORECASE)


SETTINGS = load_settings()
LOCAL_TZ = ZoneInfo(SETTINGS["timezone"])
ISSUE_KEY_RE = build_key_regex(SETTINGS["project_keys"])


def extract_issue_key(text: str) -> Optional[str]:
    """First issue-key match (case-insensitive), uppercased. None if absent."""
    m = ISSUE_KEY_RE.search(text or "")
    return m.group(0).upper() if m else None


def _utc_iso_to_local_date(iso_str: str) -> date:
    """Convert a Z-suffixed UTC ISO 8601 timestamp to local-tz date."""
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    return dt.astimezone(LOCAL_TZ).date()


def workdays_in_range(since: date, until: date) -> List[date]:
    """Inclusive Mon–Fri date list. Empty if since > until."""
    if since > until:
        return []
    result = []
    cursor = since
    while cursor <= until:
        if cursor.weekday() < 5:  # 0=Mon … 4=Fri
            result.append(cursor)
        cursor += timedelta(days=1)
    return result


def _holidays_installed() -> bool:
    try:
        import holidays  # type: ignore  # noqa: F401
    except ImportError:
        return False
    return True


def holidays_in_range(since: date, until: date, country: Optional[str]) -> Dict[date, str]:
    """Map of {date: holiday_name} for the given country in the inclusive range.

    Returns empty dict if country is falsy or the `holidays` package is not
    installed — callers should treat absence of holidays as a no-op.
    """
    if not country:
        return {}
    try:
        import holidays as _holidays  # type: ignore
    except ImportError:
        return {}
    years = list(range(since.year, until.year + 1))
    cal = _holidays.country_holidays(country, years=years)
    return {d: name for d, name in cal.items() if since <= d <= until}


def _quoted_statuses() -> str:
    return ", ".join(f'"{x}"' for x in SETTINGS["in_progress_statuses"])


def parse_jql_window(day: date) -> str:
    """JQL clause for tickets in an in-progress status on the given day.

    Statuses come from config.json (in_progress_statuses). Epics are excluded:
    they typically span the whole window and would soak up time alongside
    their child tasks, double-allocating effort.
    """
    next_day = day + timedelta(days=1)
    return (
        f'assignee = currentUser() AND issuetype != Epic '
        f'AND status was in ({_quoted_statuses()}) '
        f'DURING ("{day.isoformat()}", "{next_day.isoformat()}")'
    )


INCREMENT = int(SETTINGS["increment_minutes"])  # minutes — worklog allocation granularity


def allocate_day(
    target_minutes: int,
    existing_minutes: int,
    ticket_keys: List[str],
) -> Tuple[str, List[Tuple[str, int]]]:
    """Split (target − existing) minutes across tickets in 15-min increments."""
    if existing_minutes >= target_minutes:
        return "locked", []
    if not ticket_keys:
        return "empty", []
    remaining = target_minutes - existing_minutes
    n = len(ticket_keys)
    base_share = (remaining // n) // INCREMENT * INCREMENT  # round DOWN to 15-min
    used = base_share * n
    leftover = remaining - used
    extra_chunks = leftover // INCREMENT  # number of +15-min boosts to distribute
    entries: List[Tuple[str, int]] = []
    for i, key in enumerate(ticket_keys):
        share = base_share + (INCREMENT if i < extra_chunks else 0)
        entries.append((key, share))
    return "editable", entries


REQUIRED_CONFIG_KEYS = ("installation", "server", "login", "api_token")
_CONFIG_LINE = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)$')


def load_jira_config(path: str) -> Dict[str, str]:
    """Parse top-level scalar keys from jira-cli's YAML config."""
    with open(path) as f:
        raw = f.read()
    cfg: Dict[str, str] = {}
    for line in raw.splitlines():
        # Only top-level keys (no leading whitespace).
        if line.startswith((" ", "\t")) or not line.strip() or line.lstrip().startswith("#"):
            continue
        m = _CONFIG_LINE.match(line)
        if not m:
            continue
        key, value = m.group(1), m.group(2).strip()
        if not value:
            continue  # nested mapping — skip, we don't read children here
        # Strip matched surrounding quotes.
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        cfg[key] = value
    missing = [k for k in REQUIRED_CONFIG_KEYS if k not in cfg]
    if missing:
        raise ValueError(f"Missing required keys in {path}: {', '.join(missing)}")
    return cfg


def _basic_auth_header(email: str, token: str) -> str:
    raw = f"{email}:{token}".encode()
    return "Basic " + base64.b64encode(raw).decode()


def fetch_existing_worklogs_for_issue(
    *,
    http_get: HttpGet,
    base_url: str,
    auth: Tuple[str, str],
    issue_key: str,
    day: date,
    current_account_id: str,
) -> int:
    """Total minutes logged by current user on issue_key for day."""
    url = f"{base_url.rstrip('/')}/rest/api/3/issue/{issue_key}/worklog"
    headers = {
        "Authorization": _basic_auth_header(*auth),
        "Accept": "application/json",
    }
    payload = http_get(url, headers)
    iso_day = day.isoformat()
    total_seconds = 0
    for entry in payload.get("worklogs", []):
        author = entry.get("author") or {}
        if author.get("accountId") != current_account_id:
            continue
        started = entry.get("started", "")
        if not started.startswith(iso_day):
            continue
        total_seconds += int(entry.get("timeSpentSeconds", 0))
    return total_seconds // 60


def fetch_current_user_account_id(
    *, http_get: HttpGet, base_url: str, auth: Tuple[str, str]
) -> str:
    """Returns the current user's Jira accountId via /rest/api/3/myself."""
    url = f"{base_url.rstrip('/')}/rest/api/3/myself"
    headers = {
        "Authorization": _basic_auth_header(*auth),
        "Accept": "application/json",
    }
    payload = http_get(url, headers)
    return payload["accountId"]


def fetch_last_worklog_date(
    *, http_get: HttpGet, base_url: str, auth: Tuple[str, str], account_id: str
) -> Optional[date]:
    """Date of the user's most recent worklog, or None if they've never logged."""
    headers = {
        "Authorization": _basic_auth_header(*auth),
        "Accept": "application/json",
    }
    jql = "worklogAuthor = currentUser() ORDER BY updated DESC"
    search_url = (
        f"{base_url.rstrip('/')}/rest/api/3/search/jql"
        f"?jql={quote(jql)}&fields=key&maxResults=50"
    )
    search = http_get(search_url, headers)
    latest: Optional[date] = None
    for issue in search.get("issues", []):
        wl_url = f"{base_url.rstrip('/')}/rest/api/3/issue/{issue['key']}/worklog"
        wl = http_get(wl_url, headers)
        for entry in wl.get("worklogs", []):
            if (entry.get("author") or {}).get("accountId") != account_id:
                continue
            started = entry.get("started", "")[:10]  # "YYYY-MM-DD"
            if not started:
                continue
            d = date.fromisoformat(started)
            if latest is None or d > latest:
                latest = d
    return latest


def fetch_github_login(*, runner: Runner) -> str:
    """Returns the gh-authenticated user's GitHub login (e.g. 'ragone')."""
    result = runner(["gh", "api", "user", "--jq", ".login"])
    if result.returncode != 0:
        raise RuntimeError(f"gh api user failed: {(result.stderr or '').strip()}")
    return result.stdout.strip()


def _gh_search_prs_in_window(
    *, runner: Runner, login: str, since: date, until: date
) -> List[dict]:
    """Find PRs the user touched (review/comment/author) in the window."""
    argv = [
        "gh", "search", "prs",
        f"--involves={login}",
        f"--updated=>={since.isoformat()} <={until.isoformat()}",
        "--limit", "200",
        "--json", "url,title,repository,number",
    ]
    if SETTINGS["github_owner"]:
        argv.append(f"--owner={SETTINGS['github_owner']}")
    result = runner(argv)
    if result.returncode != 0:
        # Empty results from `gh search` exit cleanly with []; a non-zero code
        # here is a real failure (auth, network). Surface it loudly.
        raise RuntimeError(f"gh search prs failed: {(result.stderr or '').strip()}")
    return json.loads(result.stdout) if result.stdout.strip() else []


def _gh_api_json(*, runner: Runner, path: str) -> list:
    """GET a paginated gh API path, returning the merged JSON array."""
    result = runner(["gh", "api", "--paginate", path])
    if result.returncode != 0:
        return []
    # `gh api --paginate` concatenates JSON arrays as `][` between pages.
    text = result.stdout.strip()
    if not text:
        return []
    text = text.replace("][", ",")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return []


def fetch_pr_activity_in_window(
    *,
    runner: Runner,
    login: str,
    since: date,
    until: date,
) -> Tuple[Dict[date, Dict[str, str]], int]:
    """Map each day in [since, until] to the {issue_key: pr_title} the user touched.

    "Touched" means the user submitted a PR review, or authored a commit, on
    that day (per the PR's per-event timestamps converted to local time).
    Returns (per-day mapping, count of PRs skipped because the title had no issue
    key).
    """
    activity: Dict[date, Dict[str, str]] = {}
    skipped_no_key = 0

    prs = _gh_search_prs_in_window(runner=runner, login=login, since=since, until=until)
    for pr in prs:
        title = pr.get("title", "")
        key = extract_issue_key(title)
        if not key:
            skipped_no_key += 1
            continue
        repo = (pr.get("repository") or {}).get("nameWithOwner")
        number = pr.get("number")
        if not repo or not number:
            continue

        # Reviews submitted by the user.
        reviews = _gh_api_json(runner=runner, path=f"repos/{repo}/pulls/{number}/reviews")
        for rev in reviews:
            if (rev.get("user") or {}).get("login") != login:
                continue
            ts = rev.get("submitted_at") or ""
            if not ts:
                continue
            d = _utc_iso_to_local_date(ts)
            if since <= d <= until:
                activity.setdefault(d, {}).setdefault(key, title)

        # Commits authored by the user. The `author` field on a commit is the
        # GitHub user; `commit.author.date` is the authored timestamp (UTC).
        commits = _gh_api_json(runner=runner, path=f"repos/{repo}/pulls/{number}/commits")
        for c in commits:
            author = (c.get("author") or {}).get("login")
            if author != login:
                continue
            ts = ((c.get("commit") or {}).get("author") or {}).get("date") or ""
            if not ts:
                continue
            d = _utc_iso_to_local_date(ts)
            if since <= d <= until:
                activity.setdefault(d, {}).setdefault(key, title)

    return activity, skipped_no_key


def fetch_in_progress_tickets(*, runner: Runner, day: date) -> List[Tuple[str, str]]:
    """Returns [(issue_key, summary), ...] for tickets In Progress on `day`."""
    jql = parse_jql_window(day)
    argv = [
        "jira", "issue", "list",
        "-q", jql,
        "--plain", "--no-headers", "--no-truncate",
        "--paginate", "0:100",
    ]
    result = runner(argv)
    if result.returncode != 0:
        # jira-cli exits non-zero on empty result sets — treat that as an
        # empty list, not an error, so days with no matching tickets become
        # an "empty" status in the plan rather than aborting the whole run.
        stderr = (result.stderr or "").strip()
        if "No result found" in stderr:
            return []
        raise RuntimeError(f"jira issue list failed: {stderr}")
    rows: List[Tuple[str, str]] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        key, summary = parts[1], parts[2]
        rows.append((key, summary))
    return rows


TARGET_MINUTES_PER_DAY = int(SETTINGS["hours_per_day"] * 60)


def build_plan(
    *,
    config: Dict[str, str],
    runner: Runner,
    http_get: HttpGet,
    until: date,
    since: Optional[date] = None,
    auto_since: bool = False,
    country: Optional[str] = SETTINGS["country"],
    include_github: bool = True,
) -> dict:
    """Assemble the worklog plan JSON for the requested window."""
    auth = (config["login"], config["api_token"])
    base_url = config["server"]
    account_id = fetch_current_user_account_id(http_get=http_get, base_url=base_url, auth=auth)

    if auto_since:
        last = fetch_last_worklog_date(
            http_get=http_get, base_url=base_url, auth=auth, account_id=account_id
        )
        if last is None:
            return {"error": "no_anchor"}
        since = last + timedelta(days=1)

    assert since is not None

    # Pull GitHub PR activity for the whole window up front. Failures here
    # are non-fatal: the plan still works with Jira-only data.
    pr_activity: Dict[date, Dict[str, str]] = {}
    pr_skipped_no_key = 0
    github_error: Optional[str] = None
    if include_github:
        try:
            login = fetch_github_login(runner=runner)
            pr_activity, pr_skipped_no_key = fetch_pr_activity_in_window(
                runner=runner, login=login, since=since, until=until,
            )
        except (RuntimeError, FileNotFoundError) as exc:
            github_error = str(exc)

    holiday_map = holidays_in_range(since, until, country)
    holidays_missing = bool(country) and not _holidays_installed()
    days_out = []
    for day in workdays_in_range(since, until):
        if day in holiday_map:
            days_out.append({
                "date": day.isoformat(),
                "weekday": day.strftime("%a"),
                "status": "holiday",
                "holiday_name": holiday_map[day],
                "existing_minutes": 0,
                "entries": [],
            })
            continue

        # Source 1: Jira In-Progress tickets (epic-filtered).
        tickets = fetch_in_progress_tickets(runner=runner, day=day)
        existing_total = 0
        ticket_summaries: Dict[str, str] = {}
        keys: List[str] = []
        seen_keys: Set[str] = set()
        for key, summary in tickets:
            if key in seen_keys:
                continue
            seen_keys.add(key)
            keys.append(key)
            ticket_summaries[key] = summary
            existing_total += fetch_existing_worklogs_for_issue(
                http_get=http_get, base_url=base_url, auth=auth,
                issue_key=key, day=day, current_account_id=account_id,
            )

        # Source 2 + 3: GitHub PR activity (reviews + commits) for the day.
        # Append to keep In-Progress tickets first; PR-only tickets get the
        # PR title as a fallback summary.
        for key, pr_title in pr_activity.get(day, {}).items():
            if key in seen_keys:
                continue
            seen_keys.add(key)
            keys.append(key)
            ticket_summaries[key] = pr_title
            existing_total += fetch_existing_worklogs_for_issue(
                http_get=http_get, base_url=base_url, auth=auth,
                issue_key=key, day=day, current_account_id=account_id,
            )

        status, allocations = allocate_day(TARGET_MINUTES_PER_DAY, existing_total, keys)
        # Translate the allocator's internal label "locked" to the plan-level
        # label "already_logged". The allocator only knows there's no remaining
        # time to allocate; the plan layer interprets that as "user already
        # logged a full day on those tickets."
        plan_status = "already_logged" if status == "locked" else status
        entries = [
            {"issue": k, "summary": ticket_summaries[k], "minutes": m}
            for (k, m) in allocations
        ]
        days_out.append({
            "date": day.isoformat(),
            "weekday": day.strftime("%a"),
            "status": plan_status,
            "existing_minutes": existing_total,
            "entries": entries,
        })

    plan: dict = {
        "window": {"since": since.isoformat(), "until": until.isoformat()},
        "current_user": {"account_id": account_id, "email": config["login"]},
        "github": {
            "enabled": include_github and github_error is None,
            "pr_skipped_no_key": pr_skipped_no_key,
        },
        "days": days_out,
    }
    if github_error:
        plan["github"]["error"] = github_error
    if holidays_missing:
        plan["holidays_warning"] = "holidays package not installed; public holidays not skipped (pip install holidays)"
    return plan


def _format_minutes(minutes: int) -> str:
    """Format minutes as 'Xh', 'Ym', or 'Xh Ym' for the jira CLI."""
    hours, mins = divmod(minutes, 60)
    if hours and mins:
        return f"{hours}h {mins}m"
    if hours:
        return f"{hours}h"
    return f"{mins}m"


DAY_START = time.fromisoformat(SETTINGS["day_start"])  # worklogs span day_start → day_start + day total


def submit_entry(
    *, runner: Runner, issue: str, day: date, minutes: int, start: time
) -> dict:
    """Run `jira issue worklog add ...` for a single entry."""
    started_at = datetime.combine(day, start).strftime("%Y-%m-%d %H:%M:%S")
    argv = [
        "jira", "issue", "worklog", "add",
        issue,
        _format_minutes(minutes),
        "--started", started_at,
        "--timezone", SETTINGS["timezone"],
        "--no-input",
    ]
    result = runner(argv)
    if result.returncode != 0:
        return {"ok": False, "error": (result.stderr or result.stdout).strip()}
    return {"ok": True}


def submit_plan(*, runner: Runner, plan: dict) -> dict:
    """Iterate editable days/entries in `plan`, calling submit_entry for each.

    Entries within a day are sequenced back-to-back starting at DAY_START so
    the worklog timestamps span the workday rather than all stacking at 9 AM.
    """
    results = []
    submitted = 0
    failed = 0
    for day in plan["days"]:
        if day["status"] != "editable":
            continue
        d = date.fromisoformat(day["date"])
        cursor = datetime.combine(d, DAY_START)
        for entry in day["entries"]:
            if entry["minutes"] <= 0:
                continue  # 0-minute entries are skipped silently — nothing to log
            outcome = submit_entry(
                runner=runner, issue=entry["issue"], day=d,
                minutes=entry["minutes"], start=cursor.time(),
            )
            cursor += timedelta(minutes=entry["minutes"])
            row = {
                "issue": entry["issue"],
                "date": day["date"],
                "minutes": entry["minutes"],
                "ok": outcome["ok"],
            }
            if not outcome["ok"]:
                row["error"] = outcome["error"]
                failed += 1
            else:
                submitted += 1
            results.append(row)
    return {"submitted": submitted, "failed": failed, "results": results}


import argparse
import os
import subprocess
import sys
import time as _time
import urllib.request

DEFAULT_CONFIG_PATH = os.path.expanduser("~/.config/.jira/.config.yml")


def _real_http_get(url: str, headers: dict) -> dict:
    """Default HTTP GET used in production — uses urllib stdlib."""
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def _real_runner(argv):
    """Default runner — captures stdout/stderr as text so callers can read them."""
    return subprocess.run(argv, capture_output=True, text=True)


def main(
    *,
    argv: List[str],
    runner: Runner = _real_runner,
    http_get: HttpGet = _real_http_get,
) -> int:
    """CLI entry point: `plan` and `submit` subcommands."""
    parser = argparse.ArgumentParser(prog="jira-worklog-helper")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("plan")
    p.add_argument("--since")
    p.add_argument("--until")
    p.add_argument("--auto-since", action="store_true")
    p.add_argument("--config", default=DEFAULT_CONFIG_PATH)
    p.add_argument(
        "--country",
        default=SETTINGS["country"],
        help="ISO country code for public-holiday skipping (default from config.json; pass empty string to disable).",
    )

    p.add_argument("--no-github", action="store_true", help="Skip GitHub PR activity as a ticket source.")

    s = sub.add_parser("submit")
    s.add_argument("--plan-file", required=True)

    args = parser.parse_args(argv)

    if args.cmd == "plan":
        config = load_jira_config(args.config)
        until = date.fromisoformat(args.until) if args.until else date.today()
        if args.auto_since:
            plan = build_plan(
                config=config, runner=runner, http_get=http_get,
                until=until, auto_since=True, country=args.country or None,
                include_github=not args.no_github,
            )
        else:
            if not args.since:
                print("error: --since is required when --auto-since not given", file=sys.stderr)
                return 2
            plan = build_plan(
                config=config, runner=runner, http_get=http_get,
                since=date.fromisoformat(args.since), until=until,
                country=args.country or None, include_github=not args.no_github,
            )
        path = f"/tmp/jira-worklog-plan-{int(_time.time())}.json"
        with open(path, "w") as f:
            json.dump(plan, f, indent=2)
        print(path)
        return 0

    if args.cmd == "submit":
        with open(args.plan_file) as f:
            plan = json.load(f)
        outcome = submit_plan(runner=runner, plan=plan)
        json.dump(outcome, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0 if outcome["failed"] == 0 else 1

    return 2


if __name__ == "__main__":
    sys.exit(main(argv=sys.argv[1:]))

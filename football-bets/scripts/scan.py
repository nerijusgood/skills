#!/usr/bin/env python3
"""Football value-bet scanner.

Pulls odds from The Odds API, uses Pinnacle (a sharp, low-margin bookmaker)
as the "true price", removes its margin, and compares every other bookmaker
against that fair price.

Outputs three lists for today + tomorrow:
  1. Value bets   - offered odds beat fair odds by >= min_edge (main stake)
  2. Longshots    - big odds that still beat fair odds (small stake)
  3. Favourites   - strong favourites with the fair odds you NEED to see
                    at your own bookmaker before betting

Standard library only. Usage:
  ODDS_API_KEY=xxx python3 scan.py              # live
  python3 scan.py --mock mock_odds.json         # offline test
  python3 scan.py --json                        # machine-readable output
"""
import argparse
import json
import os
import statistics
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
API = "https://api.the-odds-api.com/v4"

DEFAULTS = {
    "sports": {
        "soccer_epl": "Premier League",
        "soccer_spain_la_liga": "La Liga",
        "soccer_germany_bundesliga": "Bundesliga",
        "soccer_italy_serie_a": "Serie A",
        "soccer_france_ligue_one": "Ligue 1",
        "soccer_uefa_champs_league": "Champions League",
        "soccer_uefa_europa_league": "Europa League",
    },
    # Up to 10 bookmakers cost the same as 1 region. Pinnacle must stay in.
    "bookmakers": [
        "pinnacle", "unibet_se", "mrgreen_se", "leovegas_se", "betsson",
        "nordicbet", "sport888", "coolbet", "betfair_ex_eu", "williamhill",
    ],
    "sharp": "pinnacle",
    "markets": ["h2h", "totals"],
    "timezone": "Europe/Copenhagen",
    "days": 2,                    # today + tomorrow
    "min_edge": 0.03,             # 3% better than fair = value
    "longshot_min_odds": 4.0,
    "longshot_min_edge": 0.05,
    "main_odds_range": [1.30, 4.0],
    "favourite_min_prob": 0.70,
    "stake_main": 50,
    "stake_longshot": 10,
    "currency": "kr",
}

OUTCOME_LABEL = {"Draw": "Draw"}


def load_config():
    cfg = dict(DEFAULTS)
    path = HERE.parent / "config.json"
    if path.exists():
        cfg.update(json.loads(path.read_text()))
    return cfg


def find_api_key():
    key = os.environ.get("ODDS_API_KEY", "").strip()
    if key:
        return key
    for p in (Path.home() / ".config" / "odds-api" / "key", HERE.parent / ".odds_api_key"):
        if p.exists():
            return p.read_text().strip()
    return ""


def fetch_sport(sport, cfg, key, t_from, t_to):
    params = {
        "apiKey": key,
        "bookmakers": ",".join(cfg["bookmakers"]),
        "markets": ",".join(cfg["markets"]),
        "oddsFormat": "decimal",
        "commenceTimeFrom": t_from.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "commenceTimeTo": t_to.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    url = f"{API}/sports/{sport}/odds/?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "football-bets-skill/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            remaining = r.headers.get("x-requests-remaining")
            return json.loads(r.read().decode()), remaining
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:300]
        raise SystemExit(f"Odds API error {e.code} for {sport}: {body}")
    except urllib.error.URLError as e:
        raise SystemExit(
            f"Cannot reach the Odds API ({e.reason}). If this runs in a sandbox, "
            "the network may block api.the-odds-api.com - run it on your own computer."
        )


# ---------- maths ----------

def devig(prices):
    """Remove the bookmaker margin with the power method.

    Finds k so that sum((1/odds)^k) == 1. Unlike simple scaling, this takes
    more margin off longshots than favourites, which matches how bookmakers
    really price (favourite-longshot bias), so longshot 'value' is not inflated.
    prices: {outcome: decimal odds}.
    """
    inv = {name: 1 / odds for name, odds in prices.items() if odds and odds > 1}
    if len(inv) != len(prices) or len(inv) < 2:
        return None
    if sum(inv.values()) <= 1:  # no margin (or arbitrage) - just normalise
        total = sum(inv.values())
        return {name: p / total for name, p in inv.items()}
    lo, hi = 1.0, 10.0
    for _ in range(100):
        k = (lo + hi) / 2
        if sum(p ** k for p in inv.values()) > 1:
            lo = k
        else:
            hi = k
    k = (lo + hi) / 2
    probs = {name: p ** k for name, p in inv.items()}
    total = sum(probs.values())
    return {name: p / total for name, p in probs.items()}


def market_books(event, market_key):
    """Return {book_key: {line: {outcome: price}}}. line is None for h2h."""
    out = {}
    for b in event.get("bookmakers", []):
        for m in b.get("markets", []):
            if m.get("key") != market_key:
                continue
            for o in m.get("outcomes", []):
                line = o.get("point") if market_key == "totals" else None
                out.setdefault(b["key"], {}).setdefault(line, {})[o["name"]] = o["price"]
            out.setdefault(b["key"], {})
            out[b["key"]]["_title"] = b.get("title", b["key"])
    return out


def fair_probs(books, line, sharp, expected_n):
    """Fair probabilities from the sharp book, else median of all books."""
    sp = books.get(sharp, {}).get(line)
    if sp and len(sp) == expected_n:
        f = devig(sp)
        if f:
            return f, "Pinnacle"
    samples = []
    for k, lines in books.items():
        p = lines.get(line)
        if p and len(p) == expected_n:
            f = devig(p)
            if f:
                samples.append(f)
    if len(samples) >= 3:
        keys = samples[0].keys()
        med = {k: statistics.median(s[k] for s in samples) for k in keys}
        tot = sum(med.values())
        return {k: v / tot for k, v in med.items()}, "consensus"
    return None, None


def label(market_key, outcome, line, event):
    if market_key == "h2h":
        if outcome == "Draw":
            return "Draw"
        return f"{outcome} to win"
    return f"{outcome} {line} goals"


def analyse(events, cfg, league):
    tz = ZoneInfo(cfg["timezone"])
    rows = []
    for ev in events:
        kickoff = datetime.fromisoformat(ev["commence_time"].replace("Z", "+00:00")).astimezone(tz)
        match = f"{ev['home_team']} v {ev['away_team']}"
        for mk in cfg["markets"]:
            if mk not in ("h2h", "totals"):
                continue
            books = market_books(ev, mk)
            if not books:
                continue
            lines = {ln for b in books.values() for ln in b if ln != "_title"}
            for line in lines:
                n = 3 if mk == "h2h" else 2
                fair, source = fair_probs(books, line, cfg["sharp"], n)
                if not fair:
                    continue
                for outcome, p in fair.items():
                    best_price, best_book = 0, None
                    for bk, bl in books.items():
                        if bk == cfg["sharp"]:
                            continue
                        price = bl.get(line, {}).get(outcome)
                        if price and price > best_price:
                            best_price, best_book = price, bl["_title"]
                    fair_odds = 1 / p
                    rows.append({
                        "league": league,
                        "kickoff": kickoff.strftime("%a %d %b %H:%M"),
                        "kickoff_iso": kickoff.isoformat(),
                        "match": match,
                        "market": mk,
                        "bet": label(mk, outcome, line, ev),
                        "prob": round(p, 4),
                        "fair_odds": round(fair_odds, 2),
                        "need_odds": round(fair_odds * (1 + cfg["min_edge"]), 2),
                        "best_odds": best_price or None,
                        "best_book": best_book,
                        "edge": round(p * best_price - 1, 4) if best_price else None,
                        "source": source,
                    })
    return rows


def classify(rows, cfg):
    lo, hi = cfg["main_odds_range"]
    value, longshots, favourites = [], [], []
    for r in rows:
        e, o = r["edge"], r["best_odds"]
        if e is not None and o:
            if o >= cfg["longshot_min_odds"] and e >= cfg["longshot_min_edge"]:
                longshots.append(r)
            elif lo <= o < hi and e >= cfg["min_edge"]:
                value.append(r)
        if r["market"] == "h2h" and r["bet"] != "Draw" and r["prob"] >= cfg["favourite_min_prob"]:
            favourites.append(r)
    value.sort(key=lambda r: r["edge"], reverse=True)
    longshots.sort(key=lambda r: r["edge"], reverse=True)
    favourites.sort(key=lambda r: r["prob"], reverse=True)
    return value, longshots, favourites


# ---------- output ----------

def pct(x):
    return f"{x * 100:.0f}%"


def table(rows, cols):
    head = "| " + " | ".join(c[0] for c in cols) + " |"
    sep = "|" + "|".join("---" for _ in cols) + "|"
    body = ["| " + " | ".join(str(c[1](r)) for c in cols) + " |" for r in rows]
    return "\n".join([head, sep] + body)


def render(value, longshots, favourites, cfg, meta):
    cur = cfg["currency"]
    out = [f"# Football bets - {meta['window']}", ""]
    out.append(f"Scanned {meta['events']} matches in {meta['leagues']} competitions. "
               f"API credits left: {meta['remaining']}.")
    out.append("")
    base = [
        ("Kick-off", lambda r: r["kickoff"]),
        ("Match", lambda r: r["match"]),
        ("Bet", lambda r: r["bet"]),
        ("Chance", lambda r: pct(r["prob"])),
        ("Fair odds", lambda r: r["fair_odds"]),
        ("Need ≥", lambda r: r["need_odds"]),
        ("Best odds", lambda r: f"{r['best_odds']} ({r['best_book']})"),
        ("Edge", lambda r: f"+{r['edge'] * 100:.1f}%"),
    ]
    out.append(f"## 1. Value bets - stake {cfg['stake_main']} {cur} each")
    out.append(table(value[:8], base) if value else "_No value bets today. Skipping is fine._")
    out.append("")
    out.append(f"## 2. Longshots - stake {cfg['stake_longshot']} {cur} each")
    out.append(table(longshots[:3], base) if longshots else "_No fair-priced longshots today._")
    out.append("")
    fav_cols = [
        ("Kick-off", lambda r: r["kickoff"]),
        ("Match", lambda r: r["match"]),
        ("Bet", lambda r: r["bet"]),
        ("Chance", lambda r: pct(r["prob"])),
        ("Need ≥", lambda r: r["need_odds"]),
        ("Best odds", lambda r: f"{r['best_odds']} ({r['best_book']})" if r["best_odds"] else "-"),
    ]
    out.append("## 3. Strong favourites - only bet if your bookmaker beats 'Need ≥'")
    out.append(table(favourites[:8], fav_cols) if favourites else "_No strong favourites._")
    out.append("")
    out.append("_Fair odds = Pinnacle odds with the bookmaker cut removed (or the market average "
               "when Pinnacle is missing). Pinnacle odds can lag a few minutes. Check line-ups "
               "and your own bookmaker's price before betting._")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", help="read events from a JSON file instead of the API")
    ap.add_argument("--json", action="store_true", help="print JSON instead of markdown")
    ap.add_argument("--days", type=int, help="days to scan (default from config)")
    args = ap.parse_args()

    cfg = load_config()
    if args.days:
        cfg["days"] = args.days
    tz = ZoneInfo(cfg["timezone"])
    now = datetime.now(timezone.utc)
    end_local = (now.astimezone(tz) + timedelta(days=cfg["days"] - 1)).replace(
        hour=23, minute=59, second=59, microsecond=0)
    t_to = end_local.astimezone(timezone.utc)

    all_rows, n_events, leagues, remaining = [], 0, 0, "n/a"
    if args.mock:
        data = json.loads(Path(args.mock).read_text())
        for sport, events in data.items():
            name = cfg["sports"].get(sport, sport)
            leagues += 1
            n_events += len(events)
            all_rows += analyse(events, cfg, name)
    else:
        key = find_api_key()
        if not key:
            raise SystemExit("NO_API_KEY: set ODDS_API_KEY or save the key to ~/.config/odds-api/key")
        for sport, name in cfg["sports"].items():
            events, rem = fetch_sport(sport, cfg, key, now, t_to)
            remaining = rem or remaining
            if events:
                leagues += 1
                n_events += len(events)
                all_rows += analyse(events, cfg, name)

    value, longshots, favourites = classify(all_rows, cfg)
    meta = {
        "window": f"{now.astimezone(tz):%a %d %b} to {end_local:%a %d %b}",
        "events": n_events, "leagues": leagues, "remaining": remaining,
    }
    if args.json:
        print(json.dumps({"meta": meta, "value": value, "longshots": longshots,
                          "favourites": favourites}, indent=2, ensure_ascii=False))
    else:
        print(render(value, longshots, favourites, cfg, meta))


if __name__ == "__main__":
    main()

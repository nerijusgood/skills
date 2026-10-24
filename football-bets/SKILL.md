---
name: football-bets
description: Scan today's and tomorrow's football (top 5 leagues, Champions League, Europa League) for value bets, small longshots and strong favourites, using real odds from many bookmakers. Use when the user says "/football-bets", asks for today's best bets, value bets, or what football to bet on.
---

# Football bets

Find bets where a bookmaker pays MORE than the fair price.
The fair price comes from Pinnacle (a sharp bookmaker with a small cut), with its cut removed.
A bet is only "value" if the offered odds beat the fair odds by at least 3%.

Write everything for the user in simple English: short sentences, common words.

## Steps

1. **Run the scanner** (Python 3, standard library only):

   ```bash
   python3 <this-skill-folder>/scripts/scan.py
   ```

   Options: `--days 1` (today only), `--json` (raw data).
   To test without the API: `--mock <this-skill-folder>/scripts/mock_odds.json`.

2. **If it prints `NO_API_KEY`:** tell the user to get a free key at https://the-odds-api.com and save it once:

   ```bash
   mkdir -p ~/.config/odds-api && echo "THE_KEY" > ~/.config/odds-api/key
   ```

   Or set `ODDS_API_KEY`. Never print the key back or put it in a file inside the skill or repo.

3. **If it says it cannot reach the Odds API:** the sandbox blocks the site.
   Run it on the user's own computer instead (Claude Code, or the linked-computer shell),
   from `~/Projects/skills/football-bets`. Do not try other ways to fetch odds.

4. **Check team news** for the top 3 value bets only: one quick web search each
   for injuries and expected line-ups. Add a short note if a key player is out.
   If line-ups are not out yet, say "check line-ups ~1 hour before kick-off".

5. **Reply as tables in chat** (no files, no HTML):
   - **Value bets** (max 8) - stake from `config.json` (`stake_main`, default 50 kr).
   - **Longshots** (max 3) - small stake (`stake_longshot`, default 10 kr). Say clearly these lose most of the time.
   - **Strong favourites** - with the "Need ≥" odds. The user checks their own bookmaker (Mr Green etc.) and only bets if the price is at or above "Need ≥".
   - If a list is empty, say so. "No bet today" is a good result.

6. **End with 2-3 short rules**, for example:
   - Odds move. Re-check the price right before betting.
   - Same flat stake every time. Never raise stakes to win back losses.
   - Log every bet (odds taken, closing odds, result).

## How the maths works (for explaining when asked)

- Margin is removed with the power method, which takes more margin off longshots.
  This stops the tool from showing fake value on big odds.
- Fair chance = de-vigged Pinnacle price. If Pinnacle is missing, the median of all bookmakers is used (marked "consensus" in `--json`).
- Edge = fair chance × offered odds − 1. Positive edge = value.
- Totals (over/under) are only compared on the same goal line.

## Settings

Edit `config.json`: stakes, minimum edge, longshot rules, days, markets.
Each scan costs about 2 API credits per league with games (free plan: check credits at signup).
Do not add more than 10 bookmakers - more costs extra credits.

## Honesty rules

- Never call a bet "sure", "safe" or "guaranteed".
- A single win or loss proves nothing. Only hundreds of logged bets show if this works.
- Winning accounts often get limited by soft bookmakers. Mention it if the user asks why.

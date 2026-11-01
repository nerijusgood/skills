---
name: search
description: Find and compare flight prices for a trip with known dates, across Google Flights (Fli), Kiwi.com and Skiplagged. Use for "/flights:search", "find flights from X to Y on <date>", "cheapest flight to ...", or "compare flight prices".
---

# Flight search (known dates)

First read `../../rules.md` (relative to this skill folder) and follow it. It has the settings, sources, reply format and warnings.

## Steps

1. **Read the request.** Get: from, to, depart date, return date (optional), passengers, cabin, "direct only", time of day.
   - No "from": use `home_airport` from `config.json`.
   - Dates are vague ("in March", "a weekend in May"): use the `dates` skill steps instead and say so.
   - Something essential is missing (no destination): ask one short question.
2. **Resolve airports** to IATA codes.
3. **Search all three in parallel:**
   - `fli` `search_flights`: set `currency`, `sort_by: CHEAPEST`, plus any filters (`max_stops`, `departure_window`, `cabin_class`, `passengers`, `return_date`).
   - `kiwi` `search-flight`: same trip, same currency.
   - `skiplagged` `sk_flights_search`: same trip.
4. **Merge and sort** as the rules say.
5. **Reply** in the rules format.
6. **Offer one next step**, for example: "Want me to check ±3 days?" (that is the `dates` skill).

## Examples

- `/flights:search CPH LIS 12 March, back 16 March`
- `/flights:search Copenhagen to Dublin 20 Dec, direct only`
- `/flights:search to Barcelona 5-9 June, 2 people, morning flights`

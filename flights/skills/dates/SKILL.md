---
name: dates
description: Find the cheapest days to fly between two places within a date range, for one-way or return trips of a set length. Use for "/flights:dates", "when is it cheapest to fly to X", "cheapest weekend in May", or flexible-date flight searches.
---

# Cheapest dates

First read `../../rules.md` (relative to this skill folder) and follow it.

## Steps

1. **Read the request.** Get: from, to, date range, trip length (nights), one-way or return, "direct only".
   - "A weekend": trip length 2-3 nights, departing Thursday-Saturday.
   - No range: use the next 8 weeks.
   - No trip length for a return trip: ask one short question, or use 4 nights and say so.
2. **Resolve airports** to IATA codes.
3. **Search in parallel:**
   - `fli` `search_dates`: `start_date`, `end_date`, `is_round_trip`, `trip_duration` (days), `sort_by_price: true`, `currency`, filters.
   - `skiplagged` `sk_flex_departure_calendar` (and `sk_flex_return_calendar` for return trips) for the same range.
4. **Reply:**
   - One line: the cheapest date (or date pair) and price.
   - A table of the 5-8 cheapest options: Depart | Return | Price | Source. Note the weekday ("Tue 14 Jan").
   - One line on the pattern, if clear (e.g. "Tuesdays and Wednesdays are cheapest").
5. **Offer the next step:** "Want me to search the exact flights for the cheapest date?" (that is the `search` skill).

Date-search prices are the lowest fare per day. Say that the real flights may cost a little more.

## Examples

- `/flights:dates CPH to LIS in March, 4 nights`
- `/flights:dates cheapest weekend to London in December`
- `/flights:dates Dublin one-way, next 6 weeks`

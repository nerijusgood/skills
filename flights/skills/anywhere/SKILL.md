---
name: anywhere
description: Find cheap places to fly to from home (or another airport) for given dates or a month, within a budget. Use for "/flights:anywhere", "where can I fly cheap", "weekend trip ideas under X kr", or "cheapest destinations from Copenhagen".
---

# Cheap destinations ("anywhere")

First read `../../rules.md` (relative to this skill folder) and follow it.

## Steps

1. **Read the request.** Get: from (default `home_airport`), dates or month, trip length, budget, region ("Europe", "somewhere warm"), "direct only".
2. **Get ideas:** `skiplagged` `sk_destinations_anywhere` from the origin for those dates.
3. **Filter:** keep places within the budget and region. Drop hidden-city results if `show_hidden_city` is false.
4. **Check the top 3-5 with Google prices:** `fli` `search_flights` (or `search_dates` if dates are flexible) for each, in parallel, so the user sees two sources.
5. **Reply:**
   - One line: the cheapest idea and price.
   - A table: Destination | Dates | Price (Skiplagged) | Price (Google) | Stops | Link.
   - One short line per top 3 on why it fits (direct, short flight, price), only from tool data. No travel-guide text.
6. **Offer the next step:** "Want exact flights for one of these?" (that is the `search` skill).

## Examples

- `/flights:anywhere weekend in November under 1000 kr`
- `/flights:anywhere somewhere warm in February, 1 week`
- `/flights:anywhere from CPH, direct only, next month`

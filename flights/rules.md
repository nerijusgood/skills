# Shared rules for all flights skills

## Settings

Read `config.json` in the plugin folder (two levels up from each skill folder).
- `home_airport`: use it when the user gives no "from".
- `currency`: ask every server for prices in this currency.
- `passengers`, `cabin`: defaults when the user says nothing.
- `max_results`: rows per table.
- `show_hidden_city`: if false, drop Skiplagged hidden-city results.

The user's own words always win over the settings.

## The three sources

| Server | Tools | Good for |
|---|---|---|
| `fli` (Google Flights) | `find_airports`, `search_flights`, `search_dates` | Main prices, cheapest dates, filters (stops, airlines, times) |
| `kiwi` (Kiwi.com) | `search-flight` | Second price check, self-transfer combos, booking links |
| `skiplagged` (Skiplagged) | `sk_flights_search`, `sk_flex_departure_calendar`, `sk_flex_return_calendar`, `sk_destinations_anywhere`, `sk_resolve_iata` | Hidden-city deals, flexible calendars, "anywhere" ideas |

- Call the sources in parallel when you can.
- If one fails or times out, carry on with the others. Say in one short line which one failed.
- If `fli` is missing, it is a local server: it needs `uv` on the user's computer and does not run in web chat.
- Never invent a price, a flight or a link. Only show what a tool returned.

## Airports

- Turn city names into IATA codes first (`fli` `find_airports`, or `skiplagged` `sk_resolve_iata`).
- For cities with more than one airport, search them together (Fli takes comma-separated codes, e.g. `LHR,LGW,STN`).

## Merging results

- Same flight from two sources (same airline, same times) = one row. Keep the lowest price and list both sources.
- If a source gives another currency, convert roughly and mark the price with `≈`.
- Sort by price unless the user asks for something else.

## Reply format

Write in simple English: short sentences, common words.

1. One line: the cheapest price found and where.
2. A table: Price | Airline | Depart → Arrive | Time | Stops | Source | Link.
   - Show at most `max_results` rows.
   - Mark self-transfer with "self-transfer" and hidden-city with "hidden-city" in the Stops column.
3. A "Best pick" line: the best mix of price and travel time, and why, in one sentence.
4. Short warnings only when they apply (see below).
5. End with: "Prices change fast. Check the price on the booking page."

If the user asks for a visual or "infographic", use the `infographic` skill if it is installed.

## Warnings (only when they apply)

- **Hidden-city** (Skiplagged): you get off at the stopover. Carry-on only, no checked bags. Book one-way only. The airline can cancel the rest of the trip or your miles. Never use your frequent-flyer number.
- **Self-transfer** (Kiwi): separate tickets. You collect bags and check in again. If the first flight is late, the airline does not have to help.
- **Basic economy**: say if bags or seat choice cost extra, when the tool shows it.

## Never

- Never book, pay, or fill in passenger or card details. Give links only.
- Never say a price is "guaranteed".

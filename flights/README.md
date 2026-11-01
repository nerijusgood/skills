# flights

A Claude plugin that searches and compares flight prices from three sources at once.

| Source | Server | Key needed |
|---|---|---|
| Google Flights | [Fli](https://github.com/punitarani/fli) (`fli`, runs on your Mac) | No |
| Kiwi.com | Official remote server `https://mcp.kiwi.com` | No |
| Skiplagged | Official remote server `https://mcp.skiplagged.com/mcp` | No |

## Commands

| Command | What it does | Example |
|---|---|---|
| `/flights:search` | Compare prices for exact dates | `/flights:search CPH LIS 12 March, back 16 March` |
| `/flights:dates` | Find the cheapest days in a range | `/flights:dates CPH to LIS in March, 4 nights` |
| `/flights:anywhere` | Cheap destination ideas within a budget | `/flights:anywhere weekend in November under 1000 kr` |

You can also just ask, e.g. "cheapest flight to Dublin next Friday". Claude picks the right skill.

## Install (Claude Code on your Mac)

1. Install `uv` once (Fli runs through it):

   ```bash
   brew install uv
   ```

2. Add this repo as a marketplace and install the plugin:

   ```bash
   claude plugin marketplace add ~/Projects/skills
   claude plugin install flights@nerijusgood
   ```

   Using the local folder means your edits work at the next session (or after `/reload-plugins`).
   On another computer use the GitHub repo instead: `claude plugin marketplace add nerijusgood/skills`.

3. Check it: start `claude`, run `/mcp` and look for `fli`, `kiwi` and `skiplagged` as connected.

## Install (Claude app)

Go to **Customize > Plugins > Add** in the Claude app, then either:
- add the marketplace `nerijusgood/skills` (repo must be pushed), or
- **Upload plugin** with a zip of this `flights` folder.

A plugin you add in the app also shows up in Claude Code on your computers (synced at the next session start).

| | Cowork (desktop app) | Chat (web, desktop, mobile) |
|---|---|---|
| Skills / commands | Yes | Yes (Claude uses them when they fit) |
| Fli (Google Flights) | Yes, needs `uv` on the Mac | No, local servers don't run in chat |
| Kiwi, Skiplagged | Connect them on the plugin's **Connectors** tab | Same, connect on the **Connectors** tab |

On Team and Enterprise plans, an owner can limit which plugins you may install.

## Settings

Edit `config.json`:

| Key | Default | Meaning |
|---|---|---|
| `home_airport` | `CPH` | Used when you don't say "from" |
| `currency` | `DKK` | Currency asked from every source |
| `passengers` | `1` | Default adults |
| `cabin` | `ECONOMY` | `ECONOMY`, `PREMIUM_ECONOMY`, `BUSINESS`, `FIRST` |
| `max_results` | `8` | Rows per table |
| `show_hidden_city` | `true` | Show Skiplagged hidden-city deals |

Fli's fallback currency is set in `.mcp.json` (`FLI_MCP_DEFAULT_CURRENCY`).

## Optional: more sources

None are needed. If you want real airline offers and multi-city, add [Duffel](https://duffel.com) via [flights-mcp](https://github.com/ravinahp/flights-mcp). It needs a Duffel live key (account check with payment details, search only, no charges). Keep the key in your shell (`export DUFFEL_API_KEY=...`), never in this repo.

## Good to know

- Fli uses an unofficial Google Flights API. If Google changes it, Fli can break until it is updated. `uvx` pulls the newest version.
- Hidden-city and self-transfer deals come with risks. The skills warn you when they apply.
- The skills never book or pay. They give you links.

# skills

Claude skills and plugins. One folder per skill (with a `SKILL.md`) or plugin (with `.claude-plugin/plugin.json`).

| Skill | What it does |
| --- | --- |
| [`infographic`](infographic/) | Turns an answer into a calm, light, quick-scan HTML infographic with icons, doodles and avatars. Claude writes a small JSON, a script renders it. |
| [`flights`](flights/) (plugin) | Searches and compares flight prices across Google Flights (Fli), Kiwi.com and Skiplagged. Commands: `/flights:search`, `/flights:dates`, `/flights:anywhere`. No API keys. |
| [`football-bets`](football-bets/) | Scans today's and tomorrow's football (top 5 leagues, CL, EL) for value bets, small longshots and strong favourites. Uses Pinnacle as the fair price via The Odds API. Needs a free API key in `~/.config/odds-api/key`. |

## Install

### Plugins (`flights`)

This repo is also a plugin marketplace (`nerijusgood`), listed in [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json).

```bash
claude plugin marketplace add nerijusgood/skills   # or a local clone path
claude plugin install flights@nerijusgood
```

See [`flights/README.md`](flights/README.md) for setup.

### Skills

**Claude Code** (all projects): copy or link the skill folder into `~/.claude/skills/`.

```bash
ln -s "$(pwd)/infographic" ~/.claude/skills/infographic
```

**Claude app / Cowork**: zip the skill folder (`infographic/` at the top level of the zip) and upload it in Settings > Capabilities > Skills.

## Try it without Claude

```bash
cd infographic
python3 render.py examples/overview.json out.html && open out.html
```

Third-party asset licenses are listed in [`infographic/THIRD_PARTY.md`](infographic/THIRD_PARTY.md).

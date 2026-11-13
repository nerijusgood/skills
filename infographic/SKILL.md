---
name: infographic
description: Turn an answer or topic into a quick-scan infographic HTML page. Use when the user asks for an infographic, a visual summary, a "scannable" or "visual version" of a response, or says "infographic this".
---

# Infographic

Make a calm, light, one-file HTML infographic from content that is already in the chat.
Do NOT write HTML or CSS yourself. Write a small JSON file. A script builds the page.

## Steps

1. Pick the content: the last answer, or the topic the user names.
2. Cut it down. Aim for: one `tldr` line, 0-4 stats, 2-4 sections. Max ~15 words per item.
3. Write the JSON (schema below) to a temp file. Use only facts from the answer. Never invent numbers or names.
4. Run: `python3 <this-skill-folder>/render.py data.json infographic.html`
5. Deliver the file:
   - Claude Code: tell the user the path. On macOS run `open infographic.html`.
   - Claude app / Cowork: send the file to the user. Publish it as an artifact only if they want to keep or share it.
6. Reply with one short line. Do not paste the HTML or repeat the content.

## Plain-English writing (always)

Write every title, label and sentence so a first-time reader gets it in one pass.

- Short sentences, about 12 words or fewer per item. One idea each.
- Lead with the point. Active voice. Everyday words ("use", not "utilize").
- Numbers carry units ("3 min", "4,200 visits"). No unexplained jargon or acronyms.
- Titles name the thing ("Pick a plan"), not the topic ("Planning considerations").
- Same rules for diagram labels: 1-3 words per node, 2-4 words in the sublabel.
- Another language: set `"lang": "lt"` (any language code) and write the text in it. Apply the same rules.

## JSON schema

All keys are optional except `title`.

```json
{
  "title": "Short headline",
  "subtitle": "One line of context",
  "doodle": "lightbulb",
  "lang": "en",
  "palette": "moss",
  "tldr": "The answer in one sentence.",
  "stats": [{"value": "3x", "label": "what it measures", "icon": "trend-up"}],
  "sections": [
    {"title": "Options", "type": "cards", "doodle": "mug",
     "items": [{"title": "A", "text": "Short text", "icon": "palette", "tag": "Best", "tone": "good"}]},
    {"title": "Key points", "type": "points",
     "items": [{"title": "Bold lead", "text": "Detail", "icon": "target"}]},
    {"title": "How it works", "type": "steps",
     "items": [{"title": "Do this", "text": "Then this"}]},
    {"title": "Architecture", "type": "diagram", "src": "diagram.html", "caption": "Click a step to focus it.",
     "height": 560, "fallback": {"type": "flow", "items": [{"title": "A"}, {"title": "B"}]}},
    {"title": "Path", "type": "flow",
     "items": [{"title": "A", "text": "then", "tone": "good"}, {"title": "B"}]},
    {"title": "Good vs bad", "type": "compare",
     "columns": [{"title": "Pros", "tone": "good", "points": ["one", "two"]},
                 {"title": "Cons", "tone": "bad", "points": ["one"]}]},
    {"title": "Per day", "type": "chart",
     "items": [{"label": "Mon", "value": 18, "display": "1.8k"}]},
    {"title": "Ranking", "type": "bars",
     "items": [{"label": "A", "value": 10, "display": "10 MB"}]},
    {"title": "Details", "type": "table",
     "columns": ["Page", "Visits"], "rows": [["/", "4,200"], ["/menu", "3,100"]]},
    {"title": "Checklist", "type": "list", "style": "todo",
     "items": [{"text": "Done item", "done": true}, {"text": "Open item"}]},
    {"title": "Who to ask", "type": "people",
     "items": [{"name": "Real Name", "role": "Role", "text": "Optional line"}]},
    {"type": "callout", "tone": "warn", "icon": "warning", "title": "Careful", "text": "Short warning"}
  ],
  "callout": {"tone": "info", "icon": "lightbulb", "title": "Tip", "text": "Closing tip"},
  "footer": "Optional small note"
}
```

## Choosing blocks

- Summary: `tldr` + `points`. Overview: `cards` with icons. Step explanation: `flow` (2-5 boxes) + `steps` (longer). Data: `stats` + `chart` or `bars` + `table`. Checklist: `list` with `"style": "todo"`.
- `diagram`: an interactive [Archify](https://github.com/tt-a1i/archify) diagram. Use it only when the content is structure: parts and links, steps with branches, a request order, states, a data model, a timeline. Not for summaries, numbers or checklists. See "Diagrams with Archify".
- `tone` is one of: `good`, `bad`, `warn`, `info`, `neutral`.
- `flow` is for 2-5 boxes. Use `steps` for longer sequences.
- `people` only for real people the user named. Same name gives the same face. Never invent people.
- Keep illustrations light: one `doodle` at the top, at most one or two section doodles, icons where they help scanning. Do not decorate everything.
- `palette` is optional: `moss` (default, calm olive), `earthy` (warm cream, burnt orange, forest green; good for histories and timelines), `berry` (deep purple, coral and teal on near-black; good for event recaps and punchy summaries). All three have light and dark versions with high contrast. Readers can also change it with the palette button (top right). Only choose one when the topic fits or the user asks.
- `accent` (6-digit hex) is optional and only applies to the `moss` palette. Leave it out to use the default reading-first olive theme: soft paper page (light) or soft night page (dark), never pure white or black. Only set it if the user asks for another color, and pick a dark one (it must stay readable as text on white).

## Diagrams with Archify

Optional. Archify is a separate Node tool (Apache-2.0). Never install it yourself. Never block the infographic on it.

1. Find it: `ls ~/.claude/skills/archify/bin/archify.mjs ~/.agents/skills/archify/bin/archify.mjs .agents/skills/archify/bin/archify.mjs 2>/dev/null` and check `node --version` (18+).
2. Not found, or the content is not structure: use `flow` or `steps` and move on. If the user asked for a diagram, say once: install Archify by following https://raw.githubusercontent.com/tt-a1i/archify/main/llms.txt.
3. Found: pick the type from this list: `architecture`, `workflow`, `sequence`, `dataflow`, `lifecycle`, `erd`, `tree`, `class`, `timeline`, `waterfall`. Read Archify's own `SKILL.md`, its `references/authoring-defaults.md`, and the matching `examples/*.json` and `schemas/*.json` first. Write the diagram JSON with the plain-English rules above.
4. Build it next to the infographic JSON: `node <archify>/bin/archify.mjs finalize <type> diagram.archify.json diagram.html --quality showcase --json`. It must exit 0. If it fails, fix per its output, at most twice, then fall back to `flow`.
5. Add the `diagram` section with `"src": "diagram.html"` (path is relative to the infographic JSON) and a `fallback` section. `render.py` embeds the page in a sandboxed frame with an "Open full size" button. A missing or broken file only drops the diagram (and shows the `fallback`).
6. One diagram per infographic. Embedded diagrams add about 0.8 MB to the page.

Working demo: `examples/diagram.json` + `examples/diagram.archify.json`. Build `diagram.html` from the second, then render the first.

## Icons and doodles

Icon names (Phosphor, used on `cards`, `points`, `stats`, `callout`):
check-circle, lightbulb, rocket-launch, chart-bar, list-checks, warning, info, clock, users, gear, code, palette, puzzle-piece, shield-check, lightning, leaf, globe, database, package, flow-arrow, magnifying-glass, target, calendar-blank, house, star, heart, bookmark-simple, coffee, wrench, lock, bell, chat-circle, file-text, link, sparkle, trend-up, arrow-right, brain, browser, stack.

Doodle names (original drawings, used as `doodle` at the top or on a section):
plant (growth, setup), mug (routine, breaks), lightbulb (ideas, tips), rocket (launch, delivery), notebook (checklists, plans), chart (data), magnifier (research, review), sofa (home, comfort).

Unknown names are skipped with a warning, so stick to these lists.

## Files

- `render.py`: JSON to HTML. Python 3 standard library only.
- `template.html`: the design (mobile friendly). Colors are one palette written with `light-dark()` at the top of the CSS: body text 16:1 contrast in light and 13:1 in dark, muted text 8:1+, accent and tone text 7:1+ (WCAG AAA). Palette presets (`moss`, `earthy`, `berry`) are blocks under the main palette; each is one `light-dark()` set. A round button (top right) switches light/dark, a second one next to it cycles the palette, saves the choice in the browser, and also switches an embedded Archify diagram. With no saved choice it follows the system. Print is always light. Edit this to change the look for every infographic. Content width grows with the screen: 780px by default, then 880 (900px+), 1080 (1200px+), 1320 (1600px+), 1600 (2000px+), 1920 (2600px+), with the text size stepping up at 1600, 2000 and 2600. Change `--w` in the breakpoint block to tune it.
- `icons.py`, `doodles.py`, `avatars.json`: the illustration set (see `THIRD_PARTY.md` for licenses).
- `examples/`: `summary.json`, `checklist.json`, `overview.json`, `data.json`, `flow.json`, `diagram.json` (needs a built `diagram.html`).

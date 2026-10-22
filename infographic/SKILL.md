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

If the user's memory or preferences say "simple English", write the JSON text in simple English.

## JSON schema

All keys are optional except `title`.

```json
{
  "title": "Short headline",
  "subtitle": "One line of context",
  "doodle": "lightbulb",
  "tldr": "The answer in one sentence.",
  "stats": [{"value": "3x", "label": "what it measures", "icon": "trend-up"}],
  "sections": [
    {"title": "Options", "type": "cards", "doodle": "mug",
     "items": [{"title": "A", "text": "Short text", "icon": "palette", "tag": "Best", "tone": "good"}]},
    {"title": "Key points", "type": "points",
     "items": [{"title": "Bold lead", "text": "Detail", "icon": "target"}]},
    {"title": "How it works", "type": "steps",
     "items": [{"title": "Do this", "text": "Then this"}]},
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
- `tone` is one of: `good`, `bad`, `warn`, `info`, `neutral`.
- `flow` is for 2-5 boxes. Use `steps` for longer sequences.
- `people` only for real people the user named. Same name gives the same face. Never invent people.
- Keep illustrations light: one `doodle` at the top, at most one or two section doodles, icons where they help scanning. Do not decorate everything.
- `accent` (6-digit hex) is optional. Leave it out to use the default calm olive-moss theme (soft cream page, sage and terracotta details, matching dark mode). Only set it if the user asks for another color.

## Icons and doodles

Icon names (Phosphor, used on `cards`, `points`, `stats`, `callout`):
check-circle, lightbulb, rocket-launch, chart-bar, list-checks, warning, info, clock, users, gear, code, palette, puzzle-piece, shield-check, lightning, leaf, globe, database, package, flow-arrow, magnifying-glass, target, calendar-blank, house, star, heart, bookmark-simple, coffee, wrench, lock, bell, chat-circle, file-text, link, sparkle, trend-up, arrow-right, brain, browser, stack.

Doodle names (original drawings, used as `doodle` at the top or on a section):
plant (growth, setup), mug (routine, breaks), lightbulb (ideas, tips), rocket (launch, delivery), notebook (checklists, plans), chart (data), magnifier (research, review), sofa (home, comfort).

Unknown names are skipped with a warning, so stick to these lists.

## Files

- `render.py`: JSON to HTML. Python 3 standard library only.
- `template.html`: the design (light and dark theme, mobile friendly). Edit this to change the look for every infographic.
- `icons.py`, `doodles.py`, `avatars.json`: the illustration set (see `THIRD_PARTY.md` for licenses).
- `examples/`: `summary.json`, `checklist.json`, `overview.json`, `data.json`, `flow.json`.

---
name: infographic
description: Turn an answer or topic into a quick-scan infographic HTML page. Use when the user asks for an infographic, a visual summary, a "scannable" or "visual version" of a response, or says "infographic this".
---

# Infographic

Make a clean, one-file HTML infographic from content that is already in the chat.
Do NOT write HTML or CSS yourself. Write a small JSON file. A script builds the page.

## Steps

1. Pick the content: the last answer, or the topic the user names.
2. Cut it down. Aim for: one "tldr" line, 0-4 stats, 2-4 sections. Max ~15 words per item.
3. Write the JSON (schema below) to a temp file. Use only facts from the answer. Never invent numbers.
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
  "accent": "#4f46e5",
  "tldr": "The answer in one sentence.",
  "stats": [{"value": "3x", "label": "what it measures"}],
  "sections": [
    {"title": "Options", "type": "cards",
     "items": [{"title": "A", "text": "Short text", "icon": "optional emoji", "tag": "Best", "tone": "good"}]},
    {"title": "How it works", "type": "steps",
     "items": [{"title": "Do this", "text": "Then this"}]},
    {"title": "Good vs bad", "type": "compare",
     "columns": [{"title": "Pros", "tone": "good", "points": ["one", "two"]},
                 {"title": "Cons", "tone": "bad", "points": ["one"]}]},
    {"title": "Size", "type": "bars",
     "items": [{"label": "A", "value": 10, "display": "10 MB"}]},
    {"title": "Checklist", "type": "list", "items": ["one", "two"]},
    {"type": "callout", "tone": "warn", "title": "Careful", "text": "Short warning"}
  ],
  "callout": {"tone": "info", "title": "Tip", "text": "Closing tip"},
  "footer": "Optional small note"
}
```

- `tone` is one of: `good`, `bad`, `warn`, `info`, `neutral`.
- `accent` is a 6-digit hex color. Leave it out to use the default.
- Pick section types that fit the content: `cards` for options, `steps` for a process, `compare` for trade-offs, `bars` for numbers, `list` for a checklist.
- See `example.json` for a full sample.

## Files

- `render.py`: JSON to HTML. Python 3 standard library only.
- `template.html`: the design (light and dark theme, mobile friendly). Edit this to change the look for every infographic.

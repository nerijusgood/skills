# skills

My personal Claude skills. One folder per skill, each with a `SKILL.md`.

| Skill | What it does |
| --- | --- |
| [`infographic`](infographic/) | Turns an answer into a quick-scan, self-contained HTML infographic. Claude writes a small JSON, a script renders it. |

## Install

**Claude Code** (all projects): copy or link the skill folder into `~/.claude/skills/`.

```bash
ln -s "$(pwd)/infographic" ~/.claude/skills/infographic
```

**Claude app / Cowork**: zip the skill folder (`infographic/` at the top level of the zip) and upload it in Settings > Capabilities > Skills.

## Try it without Claude

```bash
cd infographic
python3 render.py example.json out.html && open out.html
```

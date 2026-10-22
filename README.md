# skills

My personal Claude skills. One folder per skill, each with a `SKILL.md`.

| Skill | What it does |
| --- | --- |
| [`infographic`](infographic/) | Turns an answer into a calm, light, quick-scan HTML infographic with icons, doodles and avatars. Claude writes a small JSON, a script renders it. |

## Install

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

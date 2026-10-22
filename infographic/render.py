#!/usr/bin/env python3
"""Render infographic JSON into one self-contained HTML page (stdlib only).

Usage:  python3 render.py data.json [out.html]     (use - to read stdin)
"""
import hashlib
import html
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from doodles import DOODLES  # noqa: E402  (original doodles)
from icons import ICONS  # noqa: E402  (Phosphor icons, MIT)

DEFAULT_ACCENT = "#4d5f2b"  # calm olive moss
DEFAULT_ACCENT_DARK = "#b7c48f"  # soft olive sage, used for the default accent in dark mode
TONES = {"good", "bad", "warn", "info", "neutral"}
NUM = re.compile(
    r"^[~<>≈$€£+\-−]?\s*\d[\d.,]*(:\d{2})?\s*(%|x|k|m|ms|s|kb|mb|gb)?$",
    re.I,
)
ARROW = (
    '<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">'
    '<path d="M5 12h14m-6-6 6 6-6 6" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
)

_AVATARS = None
_USED_AVATARS = set()


def e(value):
    """Escape any value for safe HTML output."""
    return html.escape(str(value if value is not None else ""), quote=True)


def num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def tone_of(obj, default="neutral"):
    tone = obj.get("tone", default)
    return tone if tone in TONES else default


# ---------- illustrations ----------

def icon_html(name, cls="ico"):
    """Phosphor icon in a soft rounded tile. Unknown short text (an emoji) is shown as text."""
    if not name:
        return ""
    if name in ICONS:
        return (
            '<span class="%s" aria-hidden="true"><svg viewBox="0 0 256 256" fill="currentColor">%s</svg></span>'
            % (cls, ICONS[name])
        )
    if len(str(name)) <= 3:
        return '<span class="%s" aria-hidden="true">%s</span>' % (cls, e(name))
    print("warning: unknown icon %r skipped" % name, file=sys.stderr)
    return ""


def doodle_html(name, cls):
    if not name:
        return ""
    if name not in DOODLES:
        print("warning: unknown doodle %r skipped" % name, file=sys.stderr)
        return ""
    return '<svg class="doodle %s" viewBox="0 0 160 160" aria-hidden="true">%s</svg>' % (cls, DOODLES[name])


def avatars():
    global _AVATARS
    if _AVATARS is None:
        path = HERE / "avatars.json"
        _AVATARS = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    return _AVATARS


def avatar_for(seed):
    """Same name gives the same face. Different names on one page get different faces."""
    pool = avatars()
    if not pool:
        return ""
    start = int(hashlib.md5(str(seed).strip().lower().encode("utf-8")).hexdigest(), 16) % len(pool)
    for step in range(len(pool)):
        i = (start + step) % len(pool)
        if i not in _USED_AVATARS:
            _USED_AVATARS.add(i)
            return pool[i]
    return pool[start]


# ---------- blocks ----------

def stats_html(stats):
    cells = []
    for s in stats or []:
        cells.append(
            '<div class="stat">%s<div class="stat-v">%s</div><div class="stat-l">%s</div></div>'
            % (icon_html(s.get("icon")), e(s.get("value")), e(s.get("label")))
        )
    return '<section class="stats">%s</section>' % "".join(cells) if cells else ""


def cards_html(sec):
    out = []
    for it in sec.get("items", []):
        tag = ""
        if it.get("tag"):
            tag = '<span class="tag tone-%s">%s</span>' % (tone_of(it), e(it["tag"]))
        out.append(
            '<article class="card">%s<h3>%s</h3>%s<p>%s</p></article>'
            % (icon_html(it.get("icon")), e(it.get("title")), tag, e(it.get("text")))
        )
    return '<div class="grid">%s</div>' % "".join(out)


def points_html(sec):
    out = []
    for it in sec.get("items", []):
        detail = '<span>%s</span>' % e(it["text"]) if it.get("text") else ""
        tone = (" tone-" + it["tone"]) if it.get("tone") in TONES else ""
        out.append(
            '<div class="pt%s">%s<div><b>%s</b>%s</div></div>'
            % (tone, icon_html(it.get("icon"), "ico sm"), e(it.get("title")), detail)
        )
    return '<div class="points">%s</div>' % "".join(out)


def people_html(sec):
    out = []
    for it in sec.get("items", []):
        name = it.get("name", "")
        src = avatar_for(it.get("avatar", name))
        img = '<img class="av" src="%s" alt="" width="56" height="56">' % e(src) if src else ""
        role = '<span>%s</span>' % e(it["role"]) if it.get("role") else ""
        text = '<p>%s</p>' % e(it["text"]) if it.get("text") else ""
        out.append('<div class="person">%s<div><b>%s</b>%s%s</div></div>' % (img, e(name), role, text))
    return '<div class="people">%s</div>' % "".join(out)


def steps_html(sec):
    out = []
    for it in sec.get("items", []):
        text = '<p>%s</p>' % e(it["text"]) if it.get("text") else ""
        out.append("<li><h3>%s</h3>%s</li>" % (e(it.get("title")), text))
    return '<ol class="steps">%s</ol>' % "".join(out)


def flow_html(sec):
    items = sec.get("items", [])
    parts = []
    for i, it in enumerate(items):
        text = '<p>%s</p>' % e(it["text"]) if it.get("text") else ""
        parts.append(
            '<div class="node tone-%s"><span class="n">%d</span><h3>%s</h3>%s</div>'
            % (tone_of(it), i + 1, e(it.get("title")), text)
        )
        if i < len(items) - 1:
            parts.append('<div class="arr">%s</div>' % ARROW)
    return '<div class="flow">%s</div>' % "".join(parts)


def compare_html(sec):
    cols = []
    for col in sec.get("columns", []):
        points = "".join("<li>%s</li>" % e(p) for p in col.get("points", []))
        cols.append(
            '<div class="col tone-%s"><h3>%s</h3><ul>%s</ul></div>'
            % (tone_of(col), e(col.get("title")), points)
        )
    return '<div class="compare">%s</div>' % "".join(cols)


def bars_html(sec):
    items = sec.get("items", [])
    values = [num(it.get("value")) for it in items]
    top = max(values + [1e-9])
    rows = []
    for it, val in zip(items, values):
        pct = max(0.0, min(100.0, val / top * 100.0))
        shown = it.get("display", it.get("value", ""))
        rows.append(
            '<div class="bar-row"><div class="bar-l">%s</div>'
            '<div class="bar-t"><div class="bar-f" style="width:%.1f%%"></div></div>'
            '<div class="bar-v">%s</div></div>' % (e(it.get("label")), pct, e(shown))
        )
    return '<div class="bars">%s</div>' % "".join(rows)


def chart_html(sec):
    items = sec.get("items", [])
    values = [num(it.get("value")) for it in items]
    top = max(values + [1e-9])
    cols = []
    for it, val in zip(items, values):
        ratio = max(0.0, min(1.0, val / top))
        shown = it.get("display", it.get("value", ""))
        cols.append(
            '<div class="vcol"><div class="vplot"><div class="vv">%s</div>'
            '<div class="vbar" style="--r:%.3f"></div></div><div class="vl">%s</div></div>'
            % (e(shown), ratio, e(it.get("label")))
        )
    return '<div class="chart">%s</div>' % "".join(cols)


def table_html(sec):
    cols = [str(c) for c in sec.get("columns", [])]
    rows = [[str(c) for c in r] for r in sec.get("rows", [])]
    numeric = []
    for i in range(len(cols)):
        cells = [r[i] for r in rows if i < len(r)]
        numeric.append(bool(cells) and all(NUM.match(c.strip()) for c in cells))

    def cls(i):
        return ' class="num"' if i < len(numeric) and numeric[i] else ""

    head = "".join("<th%s>%s</th>" % (cls(i), e(c)) for i, c in enumerate(cols))
    body = "".join(
        "<tr>%s</tr>" % "".join("<td%s>%s</td>" % (cls(i), e(c)) for i, c in enumerate(r))
        for r in rows
    )
    return (
        '<div class="tbl-wrap"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>'
        % (head, body)
    )


def list_html(sec):
    todo = sec.get("style") == "todo"
    out = []
    for x in sec.get("items", []):
        text, done = (x.get("text", ""), bool(x.get("done"))) if isinstance(x, dict) else (x, False)
        if todo:
            mark = '<span class="sr">%s: </span>' % ("done" if done else "to do")
            out.append('<li class="%s">%s%s</li>' % ("todo done" if done else "todo", mark, e(text)))
        else:
            out.append("<li>%s</li>" % e(text))
    return '<ul class="checks%s">%s</ul>' % (" todos" if todo else "", "".join(out))


def callout_html(c):
    title = '<strong>%s</strong>' % e(c["title"]) if c.get("title") else ""
    return '<aside class="callout tone-%s">%s<div>%s<span>%s</span></div></aside>' % (
        tone_of(c, "info"),
        icon_html(c.get("icon"), "ico sm"),
        title,
        e(c.get("text")),
    )


RENDERERS = {
    "cards": cards_html,
    "points": points_html,
    "people": people_html,
    "steps": steps_html,
    "flow": flow_html,
    "compare": compare_html,
    "bars": bars_html,
    "chart": chart_html,
    "table": table_html,
    "list": list_html,
}


def section_html(sec):
    kind = sec.get("type", "cards")
    if kind == "callout":
        return callout_html(sec)
    fn = RENDERERS.get(kind)
    if fn is None:
        print("warning: unknown section type %r skipped" % kind, file=sys.stderr)
        return ""
    heading = ""
    if sec.get("title"):
        heading = '<div class="h2row"><h2>%s</h2>%s</div>' % (
            e(sec["title"]),
            doodle_html(sec.get("doodle"), "doodle-sm"),
        )
    return '<section class="block">%s%s</section>' % (heading, fn(sec))


def build_body(data):
    sub = '<p class="sub">%s</p>' % e(data["subtitle"]) if data.get("subtitle") else ""
    parts = [
        '<header class="hero"><div class="hero-text"><h1>%s</h1>%s</div>%s</header>'
        % (e(data.get("title", "Summary")), sub, doodle_html(data.get("doodle"), "doodle-hero"))
    ]
    if data.get("tldr"):
        parts.append('<div class="tldr"><small>In short</small>%s</div>' % e(data["tldr"]))
    parts.append(stats_html(data.get("stats")))
    parts.extend(section_html(s) for s in data.get("sections", []))
    if data.get("callout"):
        parts.append(callout_html(data["callout"]))
    if data.get("footer"):
        parts.append('<footer>%s</footer>' % e(data["footer"]))
    return "\n".join(p for p in parts if p)


def render(data):
    _USED_AVATARS.clear()
    accent = str(data.get("accent", DEFAULT_ACCENT))
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", accent):
        accent = DEFAULT_ACCENT
    if accent.lower() == DEFAULT_ACCENT:
        accent_dark = DEFAULT_ACCENT_DARK
    else:
        accent_dark = "color-mix(in srgb,%s 55%%,#fff)" % accent
    body = build_body(data)
    template = (HERE / "template.html").read_text(encoding="utf-8")
    return (
        template.replace("{{TITLE}}", e(data.get("title", "Summary")))
        .replace("{{ACCENT_DARK}}", accent_dark)
        .replace("{{ACCENT}}", accent)
        .replace("{{BODY}}", body)
    )


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    raw = sys.stdin.read() if argv[1] == "-" else Path(argv[1]).read_text(encoding="utf-8")
    data = json.loads(raw)
    out = Path(argv[2] if len(argv) > 2 else "infographic.html")
    out.write_text(render(data), encoding="utf-8")
    print(out.resolve())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

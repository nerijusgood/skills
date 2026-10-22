#!/usr/bin/env python3
"""Render infographic JSON into one self-contained HTML page (stdlib only).

Usage:  python3 render.py data.json [out.html]     (use - to read stdin)
"""
import html
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_ACCENT = "#4f6b43"  # calm moss green
DEFAULT_ACCENT_DARK = "#a9b8a1"  # sage mist, used for the default accent in dark mode
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


def stats_html(stats):
    cells = []
    for s in stats or []:
        cells.append(
            '<div class="stat"><div class="stat-v">%s</div>'
            '<div class="stat-l">%s</div></div>' % (e(s.get("value")), e(s.get("label")))
        )
    return '<section class="stats">%s</section>' % "".join(cells) if cells else ""


def cards_html(sec):
    out = []
    for it in sec.get("items", []):
        icon = ""
        if it.get("icon"):
            icon = '<span class="icon" aria-hidden="true">%s</span>' % e(it["icon"])
        tag = ""
        if it.get("tag"):
            tag = '<span class="tag tone-%s">%s</span>' % (tone_of(it), e(it["tag"]))
        out.append(
            '<article class="card">%s<h3>%s</h3>%s<p>%s</p></article>'
            % (icon, e(it.get("title")), tag, e(it.get("text")))
        )
    return '<div class="grid">%s</div>' % "".join(out)


def points_html(sec):
    out = []
    for it in sec.get("items", []):
        detail = '<span>%s</span>' % e(it["text"]) if it.get("text") else ""
        tone = (" tone-" + it["tone"]) if it.get("tone") in TONES else ""
        out.append('<div class="pt%s"><b>%s</b>%s</div>' % (tone, e(it.get("title")), detail))
    return '<div class="points">%s</div>' % "".join(out)


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
    return '<aside class="callout tone-%s">%s<span>%s</span></aside>' % (
        tone_of(c, "info"),
        title,
        e(c.get("text")),
    )


RENDERERS = {
    "cards": cards_html,
    "points": points_html,
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
    heading = '<h2>%s</h2>' % e(sec["title"]) if sec.get("title") else ""
    return '<section class="block">%s%s</section>' % (heading, fn(sec))


def build_body(data):
    parts = ['<header><h1>%s</h1>' % e(data.get("title", "Summary"))]
    if data.get("subtitle"):
        parts.append('<p class="sub">%s</p>' % e(data["subtitle"]))
    parts.append("</header>")
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
    accent = str(data.get("accent", DEFAULT_ACCENT))
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", accent):
        accent = DEFAULT_ACCENT
    if accent.lower() == DEFAULT_ACCENT:
        accent_dark = DEFAULT_ACCENT_DARK
    else:
        accent_dark = "color-mix(in srgb,%s 55%%,#fff)" % accent
    template = (HERE / "template.html").read_text(encoding="utf-8")
    return (
        template.replace("{{TITLE}}", e(data.get("title", "Summary")))
        .replace("{{ACCENT_DARK}}", accent_dark)
        .replace("{{ACCENT}}", accent)
        .replace("{{BODY}}", build_body(data))
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

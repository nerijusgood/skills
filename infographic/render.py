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
DEFAULT_ACCENT = "#4f46e5"
TONES = {"good", "bad", "warn", "info", "neutral"}


def e(value):
    """Escape any value for safe HTML output."""
    return html.escape(str(value if value is not None else ""), quote=True)


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


def steps_html(sec):
    out = []
    for it in sec.get("items", []):
        text = '<p>%s</p>' % e(it["text"]) if it.get("text") else ""
        out.append("<li><h3>%s</h3>%s</li>" % (e(it.get("title")), text))
    return '<ol class="steps">%s</ol>' % "".join(out)


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
    values = []
    for it in items:
        try:
            values.append(float(it.get("value", 0)))
        except (TypeError, ValueError):
            values.append(0.0)
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


def list_html(sec):
    items = "".join("<li>%s</li>" % e(x) for x in sec.get("items", []))
    return '<ul class="checks">%s</ul>' % items


def callout_html(c):
    title = '<strong>%s</strong>' % e(c["title"]) if c.get("title") else ""
    return '<aside class="callout tone-%s">%s<span>%s</span></aside>' % (
        tone_of(c, "info"),
        title,
        e(c.get("text")),
    )


RENDERERS = {
    "cards": cards_html,
    "steps": steps_html,
    "compare": compare_html,
    "bars": bars_html,
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
    template = (HERE / "template.html").read_text(encoding="utf-8")
    return (
        template.replace("{{TITLE}}", e(data.get("title", "Summary")))
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

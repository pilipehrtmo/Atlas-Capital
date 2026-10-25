"""SVG chart builders. Charts take real series as input and never invent values.

All functions return an SVG string sized in CSS pixels, styled with the brand tokens.
Series points are (label, value) pairs; labels are usually "YYYY-MM" or "YYYY-MM-DD".
"""
from __future__ import annotations

import math
from html import escape

from atlas.brand import COLORS

MONTHS = "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split()
AX = "font:500 17px 'JetBrains Mono';fill:%s" % COLORS["muted"]
AN = "font:500 18px 'JetBrains Mono';fill:%s" % COLORS["fg"]


def color(name: str) -> str:
    return COLORS.get(name, name)


def short_label(label: str) -> str:
    """'2026-04' -> 'APR 26'; anything else is returned unchanged."""
    if len(label) >= 7 and label[4] == "-" and label[5:7].isdigit():
        return f"{MONTHS[int(label[5:7]) - 1]} {label[2:4]}"
    return label


def nice_ticks(lo: float, hi: float, n: int = 4) -> list[float]:
    span = hi - lo or abs(hi) or 1
    raw = span / n
    mag = 10 ** math.floor(math.log10(raw))
    step = min((s * mag for s in (1, 2, 2.5, 5, 10) if s * mag >= raw), default=10 * mag)
    start = math.floor(lo / step) * step
    ticks, t = [], start
    while t <= hi + step * 0.001:
        ticks.append(round(t, 10))
        t += step
    if ticks[-1] < hi:
        ticks.append(round(ticks[-1] + step, 10))
    return ticks


def fmt(v: float, unit: str = "") -> str:
    s = f"{v:,.0f}" if abs(v) >= 100 or float(v).is_integer() else f"{v:,.2f}"
    return f"{unit}{s}" if unit in ("$", "€", "£") else f"{s}{unit}"


def line_chart(series: list[dict], width: int, height: int, *, annotations: list[dict] | None = None,
               y_unit: str = "", x_ticks: list[str] | None = None) -> str:
    """series: [{"name", "points": [[label, value], ...], "color": token, "emphasis": bool}]
    annotations: [{"series": name, "at": label, "text": str}] placed at that point."""
    L, R, T, B = 70, 24, 24, 44
    labels = [p[0] for p in series[0]["points"]]
    vals = [v for s in series for _, v in s["points"]]
    ticks = nice_ticks(min(vals), max(vals))
    lo, hi = ticks[0], ticks[-1]
    x = lambda i: L + i * (width - L - R) / max(len(labels) - 1, 1)
    y = lambda v: T + (hi - v) / (hi - lo) * (height - T - B)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" style="overflow:visible">']
    for t in ticks:
        out.append(f'<line x1="{L}" x2="{width - R}" y1="{y(t):.1f}" y2="{y(t):.1f}" stroke="{COLORS["line2"]}"/>'
                   f'<text x="{L - 12}" y="{y(t) + 6:.1f}" text-anchor="end" style="{AX}">{escape(fmt(t, y_unit))}</text>')
    if x_ticks is None:
        step = max(1, len(labels) // 6)
        x_ticks = labels[::step]
    for lab in x_ticks:
        if lab in labels:
            out.append(f'<text x="{x(labels.index(lab)):.1f}" y="{height - 12}" text-anchor="middle" style="{AX}">{escape(short_label(lab))}</text>')
    for s in sorted(series, key=lambda s: s.get("emphasis", False)):
        idx = {p[0]: i for i, p in enumerate(series[0]["points"])}
        pts = " ".join(f"{x(idx[l]):.1f},{y(v):.1f}" for l, v in s["points"] if l in idx)
        w = 4 if s.get("emphasis") else 3
        out.append(f'<polyline fill="none" stroke="{color(s.get("color", "muted"))}" stroke-width="{w}" stroke-linejoin="round" points="{pts}"/>')
    for a in annotations or []:
        s = next(s for s in series if s["name"] == a["series"])
        v = dict((l, v) for l, v in s["points"])[a["at"]]
        i = labels.index(a["at"])
        cx, cy = x(i), y(v)
        c = color(s.get("color", "fg"))
        right_edge = cx > width * 0.8
        if a.get("place") == "left" or (right_edge and a.get("place") != "above"):
            anchor, tx, ty = "end", cx - 16, cy + 6
            if a.get("place") != "left":
                out.append(f'<line x1="{cx:.1f}" x2="{cx:.1f}" y1="{cy - 10:.1f}" y2="{cy - 40:.1f}" stroke="{COLORS["fg"]}" stroke-width="1.5"/>')
                anchor, tx, ty = "end", cx, cy - 48
        else:
            anchor, tx, ty = "middle", cx, cy - 20
        out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="6" fill="{c}"/>'
                   f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="{anchor}" style="{AN}">{escape(a["text"])}</text>')
    out.append("</svg>")
    return "".join(out)


def bar_chart(points: list, width: int, height: int, *, threshold: float | None = None,
              y_unit: str = "", label_every: int = 0) -> str:
    """Vertical bars from zero. Bars at or above `threshold` are drawn in the risk colour;
    negative values are drawn below the axis."""
    L, R, T, B = 70, 24, 12, 30 if label_every else 12
    vals = [v for _, v in points]
    ticks = nice_ticks(min(0, min(vals)), max(vals), 2)
    lo, hi = ticks[0], ticks[-1]
    y = lambda v: T + (hi - v) / (hi - lo) * (height - T - B)
    slot = (width - L - R) / len(points)
    bw = slot * 0.62
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">']
    if threshold is not None:
        out.append(f'<line x1="{L}" x2="{width - R}" y1="{y(threshold):.1f}" y2="{y(threshold):.1f}" stroke="{COLORS["muted"]}" stroke-dasharray="4 6"/>'
                   f'<text x="{L - 12}" y="{y(threshold) + 6:.1f}" text-anchor="end" style="{AX}">{escape(fmt(threshold, y_unit))}</text>')
    for i, (lab, v) in enumerate(points):
        cx = L + slot * (i + 0.5)
        hot = threshold is not None and v >= threshold
        fill = COLORS["risk"] if hot or v < 0 and threshold is None else COLORS["bar_neutral"]
        top, bot = (y(v), y(0)) if v >= 0 else (y(0), y(v))
        out.append(f'<rect x="{cx - bw / 2:.1f}" y="{top:.1f}" width="{bw:.1f}" height="{max(bot - top, 1):.1f}" fill="{fill}"/>')
        if label_every and i % label_every == 0:
            out.append(f'<text x="{cx:.1f}" y="{height - 6}" text-anchor="middle" style="{AX}">{escape(short_label(lab))}</text>')
    out.append(f'<line x1="{L}" x2="{width - R}" y1="{y(0):.1f}" y2="{y(0):.1f}" stroke="{COLORS["fg"]}"/>'
               f'<text x="{L - 12}" y="{y(0) + 6:.1f}" text-anchor="end" style="{AX}">0</text></svg>')
    return "".join(out)


def hbar_chart(rows: list, width: int, *, unit: str = "", row_h: int = 64, highlight: str | None = None) -> str:
    """Horizontal bars, one per (label, value), scaled from zero. Used for segments and rankings."""
    label_w, val_w = 260, 150
    vmax = max(v for _, v in rows) or 1
    h = row_h * len(rows)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{h}">']
    for i, (lab, v) in enumerate(rows):
        y0 = i * row_h
        w = (width - label_w - val_w) * v / vmax
        c = COLORS["accent"] if lab == highlight else COLORS["bar_neutral"]
        out.append(f'<text x="0" y="{y0 + row_h / 2 + 8:.1f}" style="font:500 24px Inter;fill:{COLORS["fg"]}">{escape(lab)}</text>'
                   f'<rect x="{label_w}" y="{y0 + 12}" width="{max(w, 2):.1f}" height="{row_h - 24}" fill="{c}"/>'
                   f'<text x="{label_w + w + 14:.1f}" y="{y0 + row_h / 2 + 9:.1f}" style="font:600 28px \'Barlow Condensed\';fill:{COLORS["fg"]}">{escape(fmt(v, unit))}</text>')
    out.append("</svg>")
    return "".join(out)


def sparkline(points: list, width: int, height: int, c: str = "accent", pad: int = 8) -> str:
    vals = [v for _, v in points]
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1
    pts = [(pad + i * (width - 2 * pad) / max(len(vals) - 1, 1), pad + (hi - v) / span * (height - 2 * pad)) for i, v in enumerate(vals)]
    d = " ".join(f"{px:.1f},{py:.1f}" for px, py in pts)
    lx, ly = pts[-1]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"><polyline points="{d}" fill="none" stroke="{color(c)}" '
            f'stroke-width="4" stroke-linejoin="round"/><circle cx="{lx:.1f}" cy="{ly:.1f}" r="7" fill="{color(c)}"/></svg>')


def flow_chart(flows: list[dict], width: int, height: int, *, unit: str = "") -> str:
    """Capital-flow ribbons from sources (left) to destinations (right).
    flows: [{"from": str, "to": str, "value": float, "highlight": bool}]. Ribbon width is proportional to value."""
    srcs = list(dict.fromkeys(f["from"] for f in flows))
    dsts = list(dict.fromkeys(f["to"] for f in flows))
    total = sum(f["value"] for f in flows)
    gap, node_w, lab_w = 22, 18, 230
    usable = height - gap * (max(len(srcs), len(dsts)) - 1)
    k = usable / total
    x0, x1 = lab_w, width - lab_w

    def stack(names, key):
        pos, y = {}, 0.0
        for n in names:
            tot = sum(f["value"] for f in flows if f[key] == n)
            pos[n] = [y, y + tot * k]
            y += tot * k + gap
        off = (height - (y - gap)) / 2
        return {n: [a + off, b + off] for n, (a, b) in pos.items()}

    sp, dp = stack(srcs, "from"), stack(dsts, "to")
    s_cur = {n: v[0] for n, v in sp.items()}
    d_cur = {n: v[0] for n, v in dp.items()}
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">']
    for f in sorted(flows, key=lambda f: f.get("highlight", False)):
        h = f["value"] * k
        a0, d0 = s_cur[f["from"]], d_cur[f["to"]]
        s_cur[f["from"]] += h
        d_cur[f["to"]] += h
        xa, xb = x0 + node_w, x1
        mx = (xa + xb) / 2
        c = COLORS["accent"] if f.get("highlight") else COLORS["muted"]
        op = 0.55 if f.get("highlight") else 0.18
        out.append(f'<path d="M{xa},{a0:.1f} C{mx},{a0:.1f} {mx},{d0:.1f} {xb},{d0:.1f} L{xb},{d0 + h:.1f} '
                   f'C{mx},{d0 + h:.1f} {mx},{a0 + h:.1f} {xa},{a0 + h:.1f} Z" fill="{c}" fill-opacity="{op}"/>')
    for names, pos, nx, anchor, tx in ((srcs, sp, x0, "end", x0 - 16), (dsts, dp, x1, "start", x1 + node_w + 16)):
        for n in names:
            a, b = pos[n]
            v = sum(f["value"] for f in flows if f["from" if names is srcs else "to"] == n)
            out.append(f'<rect x="{nx}" y="{a:.1f}" width="{node_w}" height="{max(b - a, 2):.1f}" fill="{COLORS["fg"]}"/>'
                       f'<text x="{tx}" y="{(a + b) / 2 - 2:.1f}" text-anchor="{anchor}" style="font:600 30px \'Barlow Condensed\';fill:{COLORS["fg"]}">{escape(n.upper())}</text>'
                       f'<text x="{tx}" y="{(a + b) / 2 + 24:.1f}" text-anchor="{anchor}" style="{AX}">{escape(fmt(v, unit))}</text>')
    out.append("</svg>")
    return "".join(out)

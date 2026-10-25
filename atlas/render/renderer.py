"""Turn a carousel spec into PNG slides and run visual QA on every slide.

A spec is JSON or YAML:

    story_id, date (YYYY-MM-DD), section, topic, handle, disclaimer
    sources: [{id, publisher, title, url, retrieved, note}]
    slides:  [{template, sources: [source ids], ...template fields}]

Templates: cover, story, data, explainer, company, flowmap, takeaway.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import date
from html import escape
from pathlib import Path

from jinja2 import ChainableUndefined, Environment, FileSystemLoader
from markupsafe import Markup
from PIL import Image

from atlas import brand
from atlas.render import charts

TEMPLATES = Path(__file__).parent / "templates"
TEMPLATE_FILES = {
    "cover": "cover.html.j2", "story": "cover.html.j2", "data": "data.html.j2",
    "explainer": "explainer.html.j2", "company": "company.html.j2",
    "flowmap": "flowmap.html.j2", "takeaway": "takeaway.html.j2",
}
REQUIRED = {
    "cover": ["headline"], "story": ["headline"], "data": ["title", "chart"],
    "explainer": ["title", "points"], "company": ["company", "title", "metrics"],
    "flowmap": ["title", "flows"], "takeaway": ["statement"],
}
MON = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


class SpecError(ValueError):
    pass


@dataclass
class SlideResult:
    index: int
    template: str
    png: str
    width: int
    height: int
    problems: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems


def highlight(text: str) -> Markup:
    """Escape copy, then turn **phrase** into the accent highlight."""
    out = re.sub(r"\*\*(.+?)\*\*", r'<span class="hl">\1</span>', escape(str(text)))
    return Markup(out.replace("\n", "<br>"))


def load_spec(path: str | Path) -> dict:
    path = Path(path)
    text = path.read_text()
    if path.suffix in (".yaml", ".yml"):
        import yaml
        spec = yaml.safe_load(text)
    else:
        spec = json.loads(text)
    spec["_dir"] = str(path.parent.resolve())
    return spec


def validate(spec: dict) -> None:
    errors = []
    src_ids = {s["id"] for s in spec.get("sources", [])}
    for s in spec.get("sources", []):
        for k in ("id", "publisher", "title", "url", "retrieved"):
            if not s.get(k):
                errors.append(f"source {s.get('id', '?')}: missing {k}")
    if not spec.get("slides"):
        errors.append("spec has no slides")
    for i, sl in enumerate(spec.get("slides", []), 1):
        t = sl.get("template")
        if t not in TEMPLATE_FILES:
            errors.append(f"slide {i}: unknown template {t!r}")
            continue
        for k in REQUIRED[t]:
            if k not in sl:
                errors.append(f"slide {i} ({t}): missing {k}")
        refs = sl.get("sources", [])
        if t not in ("takeaway",) and not refs:
            errors.append(f"slide {i} ({t}): no sources; every slide must cite at least one")
        for r in refs:
            if r not in src_ids:
                errors.append(f"slide {i}: cites unknown source {r!r}")
    if errors:
        raise SpecError("; ".join(errors))


def footnote(spec: dict, slide: dict, short: bool = False) -> str:
    by_id = {s["id"]: s for s in spec.get("sources", [])}
    parts = []
    for r in slide.get("sources", []):
        s = by_id[r]
        if short:
            parts.append(escape(s.get("short") or s["publisher"]))
        else:
            note = f" {escape(s['note'])}." if s.get("note") else ""
            parts.append(f"{escape(s['publisher'])}, {escape(s['title'])}.{note} Retrieved {escape(pretty_date(s['retrieved']))}.")
    if short:
        return "Source: " + "; ".join(parts)
    label = "Source" if len(parts) == 1 else "Sources"
    return f"<b>{label}:</b> " + " ".join(parts)


def pretty_date(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d.day} {MON[d.month - 1]} {d.year}"


def prepare(spec: dict, slide: dict, index: int, total: int) -> dict:
    s = dict(slide)
    s["_index"], s["_total"] = index, total
    s["_footnote"] = Markup(footnote(spec, slide))
    s["_footnote_short"] = Markup(footnote(spec, slide, short=True))
    t = s["template"]
    if t in ("cover", "story"):
        if s.get("photo"):
            p = (Path(spec["_dir"]) / s["photo"]["path"]).resolve()
            if not p.exists():
                raise SpecError(f"slide {index}: photo not found: {p}")
            s["photo"] = dict(s["photo"], _uri=p.as_uri())
        if s.get("spark"):
            s["_spark"] = Markup(charts.sparkline(s["spark"]["points"], s["spark"].get("width", 952), s["spark"].get("height", 150)))
    if t == "data":
        c = s["chart"]
        for ser in c["series"]:
            ser["_color"] = charts.color(ser.get("color", "muted"))
        s["_chart"] = Markup(charts.line_chart(c["series"], 936, c.get("height", 470), annotations=c.get("annotations"),
                                               y_unit=c.get("y_unit", ""), x_ticks=c.get("x_ticks")))
        if s.get("bars"):
            b = s["bars"]
            s["_bars"] = Markup(charts.bar_chart(b["points"], 936, b.get("height", 170), threshold=b.get("threshold"),
                                                 y_unit=b.get("y_unit", "")))
            s["bars"] = dict({"threshold": None}, **b)
    if t == "company" and s.get("segments"):
        g = s["segments"]
        s["_segments"] = Markup(charts.hbar_chart(g["rows"], 936, unit=g.get("unit", ""), highlight=g.get("highlight")))
    if t == "flowmap":
        s["_flows"] = Markup(charts.flow_chart(s["flows"], 936, s.get("height", 640), unit=s.get("unit", "")))
    return s


def story_context(spec: dict) -> dict:
    d = date.fromisoformat(spec["date"])
    srcs = []
    for s in spec.get("sources", []):
        u = re.sub(r"^https?://(www\.)?", "", s["url"]).rstrip("/")
        srcs.append(dict(s, url_short=u if len(u) <= 60 else u[:57] + "...", retrieved=pretty_date(s["retrieved"])))
    return dict(spec, date_label=f"{d.day:02d} {MON[d.month - 1].upper()} {d.year}", _sources=srcs,
                handle=spec.get("handle", "@atlas"),
                disclaimer=spec.get("disclaimer", "Analysis, not investment advice."))


def build_html(spec: dict) -> list[tuple[dict, str, tuple[int, int]]]:
    validate(spec)
    # Optional template fields are simply left out of a spec, so missing keys render empty.
    env = Environment(loader=FileSystemLoader(TEMPLATES), undefined=ChainableUndefined, autoescape=True)
    env.filters["hl"] = highlight
    story = story_context(spec)
    slides = spec["slides"]
    pages = []
    for i, sl in enumerate(slides, 1):
        canvas = "story" if sl["template"] == "story" else "post"
        W, H = brand.CANVAS[canvas]
        ctx = prepare(spec, sl, i, len(slides))
        html = env.get_template(TEMPLATE_FILES[sl["template"]]).render(
            slide=ctx, story=story, W=W, H=H, story_canvas=canvas == "story",
            font_faces=Markup(brand.font_face_css()), root_css=Markup(brand.root_css()))
        pages.append((ctx, html, (W, H)))
    return pages


QA_JS = """([W, H, minFont]) => {
  const problems = [];
  const slide = document.querySelector('.slide');
  for (const el of slide.querySelectorAll('*')) {
    if (el.closest('.photo') || el.classList.contains('grid')) continue;
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) continue;
    if (r.right > W + 0.5 || r.bottom > H + 0.5 || r.left < -0.5 || r.top < -0.5) {
      problems.push(`outside canvas: <${el.tagName.toLowerCase()} class="${el.className.baseVal ?? el.className}"> ${Math.round(r.right)}x${Math.round(r.bottom)}`);
    }
  }
  for (const el of slide.querySelectorAll('[data-fit]')) {
    if (el.scrollHeight > +el.dataset.fit + 1) problems.push(`text does not fit even at minimum size: "${el.textContent.trim().slice(0, 60)}"`);
  }
  const walker = document.createTreeWalker(slide, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    const n = walker.currentNode;
    if (!n.textContent.trim()) continue;
    const fs = parseFloat(getComputedStyle(n.parentElement).fontSize);
    if (fs < minFont) problems.push(`text below ${minFont}px (${fs}px): "${n.textContent.trim().slice(0, 40)}"`);
  }
  for (const img of slide.querySelectorAll('img')) if (!img.complete || !img.naturalWidth) problems.push('image failed to load');
  for (const fam of ['Barlow Condensed', 'Inter', 'JetBrains Mono']) {
    const loaded = [...document.fonts].some(f => f.family.replace(/["']/g, '') === fam && f.status === 'loaded');
    if (!loaded) problems.push(`font not loaded: ${fam}`);
  }
  const foot = slide.querySelector('.foot, .src');
  if (!foot || !foot.textContent.trim()) problems.push('missing source footnote');
  return problems;
}"""


def chromium_path() -> str | None:
    return os.environ.get("ATLAS_CHROMIUM") or None


def render(spec: dict, out_dir: str | Path) -> list[SlideResult]:
    from playwright.sync_api import sync_playwright

    out = Path(out_dir)
    (out / "html").mkdir(parents=True, exist_ok=True)
    pages = build_html(spec)
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chromium_path())
        for ctx, html, (W, H) in pages:
            name = f"{ctx['_index']:02d}-{ctx['template']}"
            hp = out / "html" / f"{name}.html"
            hp.write_text(html)
            page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
            page.goto(hp.resolve().as_uri())
            page.wait_for_selector("body[data-ready='1']", timeout=15000)
            problems = page.evaluate(QA_JS, [W, H, brand.MIN_FONT_PX])
            png = out / f"{name}.png"
            page.screenshot(path=str(png))
            page.close()
            with Image.open(png) as im:
                w, h = im.size
            if (w, h) != (W, H):
                problems.append(f"image is {w}x{h}, expected {W}x{H}")
            results.append(SlideResult(ctx["_index"], ctx["template"], str(png), w, h, problems))
        browser.close()
    (out / "manifest.json").write_text(json.dumps({
        "story_id": spec.get("story_id"),
        "slides": [r.__dict__ | {"ok": r.ok} for r in results],
        "ok": all(r.ok for r in results),
    }, indent=2))
    return results

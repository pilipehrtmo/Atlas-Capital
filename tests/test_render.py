import copy
import json
from pathlib import Path

import pytest

from atlas.render import charts
from atlas.render.renderer import SpecError, build_html, highlight, load_spec, render

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def brent():
    return load_spec(EXAMPLES / "brent-spread.json")


def gallery():
    return load_spec(EXAMPLES / "template-gallery.json")


# --- spec validation -------------------------------------------------------

def test_examples_validate():
    assert len(build_html(brent())) == 5
    assert len(build_html(gallery())) == 4


def test_slide_without_source_is_rejected():
    spec = brent()
    spec["slides"][1]["sources"] = []
    with pytest.raises(SpecError, match="no sources"):
        build_html(spec)


def test_unknown_source_and_template_are_rejected():
    spec = brent()
    spec["slides"][0]["sources"] = ["nope"]
    spec["slides"][2]["template"] = "poster"
    with pytest.raises(SpecError) as e:
        build_html(spec)
    assert "unknown source 'nope'" in str(e.value) and "unknown template 'poster'" in str(e.value)


def test_source_record_needs_url_and_retrieval_date():
    spec = brent()
    del spec["sources"][0]["url"]
    with pytest.raises(SpecError, match="missing url"):
        build_html(spec)


def test_sample_specs_are_stamped():
    html = build_html(gallery())[0][1]
    assert "NOT FOR PUBLICATION" in html
    assert "NOT FOR PUBLICATION" not in build_html(brent())[0][1]


# --- copy and charts --------------------------------------------------------

def test_highlight_escapes_html_and_marks_phrases():
    out = str(highlight("<b>x</b> costs **$17**"))
    assert "&lt;b&gt;" in out and '<span class="hl">$17</span>' in out


def test_nice_ticks_cover_range():
    t = charts.nice_ticks(57.97, 117.29)
    assert t[0] <= 57.97 and t[-1] >= 117.29 and len(t) <= 6


def test_short_label():
    assert charts.short_label("2026-04") == "APR 26"
    assert charts.short_label("Q3") == "Q3"


def test_flow_labels_show_exact_totals():
    svg = charts.flow_chart([{"from": "A", "to": "X", "value": 12}, {"from": "B", "to": "X", "value": 9}], 900, 500)
    assert ">21<" in svg and ">12<" in svg


def test_chart_values_come_from_series():
    s = [{"name": "a", "points": [["2026-01", 10], ["2026-02", 20]], "color": "accent"}]
    svg = charts.line_chart(s, 900, 400)
    assert svg.count("<polyline") == 1


# --- rendering + visual QA (needs Chromium) ---------------------------------

def _playwright_installed():
    try:
        import playwright.sync_api  # noqa: F401
    except ImportError:
        return False
    return True


needs_browser = pytest.mark.skipif(not _playwright_installed(), reason="playwright not installed")


@needs_browser
@pytest.mark.parametrize("make", [brent, gallery])
def test_examples_render_clean(make, tmp_path):
    results = render(make(), tmp_path)
    assert results and all(r.ok for r in results), [(r.index, r.problems) for r in results if not r.ok]
    for r in results:
        assert (r.width, r.height) == ((1080, 1920) if r.template == "story" else (1080, 1350))
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["ok"] is True


@needs_browser
def test_qa_catches_text_that_cannot_fit(tmp_path):
    spec = brent()
    slide = copy.deepcopy(spec["slides"][2])
    slide["points"] = ["A very long explanatory point that keeps going and going. " * 3] * 8
    spec["slides"] = [slide]
    (r,) = render(spec, tmp_path)
    assert not r.ok
    assert any("outside canvas" in p for p in r.problems)

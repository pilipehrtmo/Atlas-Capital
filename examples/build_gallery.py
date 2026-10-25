"""Build examples/template-gallery.json: one slide per template that the Brent example does not cover.

These slides use SAMPLE values to exercise layouts. The spec is flagged `sample`, which stamps every
slide "SAMPLE DATA · NOT FOR PUBLICATION"; the publisher will refuse any spec carrying that flag.
The cover photo is a generated test image, not a real photograph.
"""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).parent
ASSETS = HERE / "assets"
ASSETS.mkdir(exist_ok=True)

# A synthetic "skyline at dusk" test image so the photo-blend path is exercised without licensed media.
img = Image.new("RGB", (1080, 1350))
d = ImageDraw.Draw(img)
for y in range(1350):
    t = y / 1350
    d.line([(0, y), (1080, y)], fill=(int(40 + 120 * t), int(60 + 70 * t), int(90 + 30 * t)))
x = 0
for i, (w, h) in enumerate([(120, 420), (90, 600), (150, 520), (110, 760), (140, 480), (100, 650), (160, 560), (120, 700), (90, 450)]):
    d.rectangle([x, 1350 - h, x + w - 8, 1350], fill=(18 + i * 3, 22 + i * 2, 30))
    for wy in range(1350 - h + 30, 1350, 46):
        for wx in range(x + 14, x + w - 22, 30):
            if (wx * 7 + wy) % 5:
                d.rectangle([wx, wy, wx + 10, wy + 18], fill=(220, 200, 140))
    x += w
img.filter(ImageFilter.GaussianBlur(1.2)).save(ASSETS / "test-photo.jpg", quality=88)

SAMPLE = {"id": "sample", "publisher": "ATLAS layout sample", "short": "Sample values, not real data",
          "title": "Placeholder values for template testing", "url": "https://example.com/sample",
          "retrieved": "2026-10-25", "note": "Not for publication"}

spec = {
    "story_id": "template-gallery",
    "date": "2026-10-25",
    "section": "MARKETS",
    "topic": "TEMPLATE GALLERY",
    "sample": True,
    "sources": [SAMPLE],
    "slides": [
        {"template": "cover", "sources": ["sample"], "kicker": "Photo cover",
         "headline": "A hook headline\nwith a **highlight**", "photo": {"path": "assets/test-photo.jpg", "credit": "generated test image"},
         "cta": "SWIPE", "top": 110},
        {"template": "company", "sources": ["sample"],
         "company": {"name": "Example Corp", "ticker": "EXMP", "period": "FY SAMPLE"},
         "title": "Where the money comes from, and where it goes",
         "metrics": [
             {"label": "REVENUE", "value": "$10.0B", "delta": "▲ 12% Y/Y"},
             {"label": "OPERATING MARGIN", "value": "24%", "delta": "▼ 2 PTS", "tone": "risk"},
             {"label": "CAPEX", "value": "$3.1B", "delta": "▲ 40% Y/Y"},
             {"label": "FREE CASH FLOW", "value": "$1.2B", "delta": "▼ 18% Y/Y", "tone": "risk"},
             {"label": "NET CASH", "value": "$4.5B"},
             {"label": "BUYBACKS", "value": "$0.8B"},
         ],
         "segments": {"title": "REVENUE BY SEGMENT, $B", "unit": "", "highlight": "Data centers",
                      "rows": [["Data centers", 5.2], ["Consumer", 2.6], ["Industrial", 1.4], ["Other", 0.8]]},
         "note": "Layout sample: metric grid plus a ranked segment chart."},
        {"template": "flowmap", "sources": ["sample"], "title": "Follow the money: where the inflows went",
         "unit": "", "unit_label": "USD BN, SAMPLE", "left_label": "ORIGIN", "right_label": "DESTINATION",
         "flows": [
             {"from": "Japan", "to": "US Treasuries", "value": 40, "highlight": True},
             {"from": "Japan", "to": "EM debt", "value": 12},
             {"from": "Europe", "to": "US Treasuries", "value": 25},
             {"from": "Europe", "to": "US equities", "value": 30},
             {"from": "Gulf", "to": "US equities", "value": 18},
             {"from": "Gulf", "to": "EM debt", "value": 9},
         ],
         "note": "Ribbon width is proportional to each sourced value."},
        {"template": "story", "sources": ["sample"], "kicker": "Story cover", "headline": "Vertical cover\nfor **Stories and Reels**",
         "photo": {"path": "assets/test-photo.jpg", "credit": "generated test image", "position": "center bottom"}, "top": 200},
    ],
}
(HERE / "template-gallery.json").write_text(json.dumps(spec, indent=1))
print("wrote examples/template-gallery.json")

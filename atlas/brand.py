"""ATLAS TERMINAL design tokens. Every template reads colours, type and spacing from here."""
from pathlib import Path

ASSETS = Path(__file__).parent / "assets"
FONTS = ASSETS / "fonts"

COLORS = {
    "bg": "#090B0D",
    "fg": "#F2F3EE",
    "accent": "#C7FF35",
    "muted": "#858B92",
    "risk": "#FF5B61",
    "line": "#1C2126",
    "line2": "#2A3036",
    "panel": "#0E1114",
    "bar_neutral": "#3A4249",
}

FONT_FAMILIES = {
    "display": ("Barlow Condensed", "BarlowCondensed", (500, 600, 700)),
    "body": ("Inter", "Inter", (400, 500, 600, 700)),
    "mono": ("JetBrains Mono", "JetBrainsMono", (400, 500, 700)),
}

# Carousel and Story canvases, in CSS pixels (rendered at 1x).
CANVAS = {"post": (1080, 1350), "story": (1080, 1920)}
GRID = 72  # background grid pitch
GUTTER = 72  # outer padding on inner slides

# Smallest text a slide may contain, checked by QA. 15px on a 1080 canvas is roughly 5pt on a phone.
MIN_FONT_PX = 15


def font_face_css() -> str:
    rules = []
    for family, stem, weights in FONT_FAMILIES.values():
        for w in weights:
            src = (FONTS / f"{stem}-{w}.ttf").resolve().as_uri()
            rules.append(
                f"@font-face{{font-family:'{family}';font-weight:{w};font-style:normal;"
                f"font-display:block;src:url('{src}') format('truetype')}}"
            )
    return "\n".join(rules)


def root_css() -> str:
    names = {"line2": "line2", "bar_neutral": "bar"}
    return ":root{" + ";".join(f"--{names.get(k, k)}:{v}" for k, v in COLORS.items()) + "}"

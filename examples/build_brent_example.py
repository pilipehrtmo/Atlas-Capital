"""Build examples/brent-spread.json from EIA monthly spot prices in examples/data.

Every figure in the spec is computed here from the CSVs, the way the production
data module will compute chart values. The copy states only what the data shows.

Data: U.S. EIA Brent and WTI spot prices, monthly averages, via the
github.com/datasets/oil-prices mirror (data through Sep 2026).
"""
import csv
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from atlas.render.charts import short_label  # noqa: E402

HERE = Path(__file__).parent


def load(name):
    with open(HERE / "data" / name) as f:
        return {r["Date"][:7]: float(r["Price"]) for r in csv.DictReader(f)}


brent, wti = load("brent-monthly.csv"), load("wti-monthly.csv")
both = sorted(m for m in brent if m in wti)
months = [m for m in both if m >= "2024-01"]
spread = {m: round(brent[m] - wti[m], 2) for m in both}
last, prev = months[-1], months[-2]
pct = lambda s: (s[last] / s[prev] - 1) * 100

# Facts used in the copy, all derived from the data.
peaks_2026 = [m for m in months if m.startswith("2026") and brent[m] >= 110]
assert len(peaks_2026) == 2, peaks_2026
prior_wide = [m for m in both if spread[m] >= spread[last] and m < "2026-01"]
last_wide_year = prior_wide[-1][:4]  # most recent pre-2026 month with a spread this wide
wide_2026 = [m for m in months if m.startswith("2026") and spread[m] >= spread[last] - 0.5]
pts = lambda s: [[m, s[m]] for m in months]

SRC = {
    "id": "eia-spot",
    "publisher": "U.S. Energy Information Administration",
    "short": "EIA Brent & WTI spot, monthly avg",
    "title": "Brent and WTI spot prices, monthly averages (USD/bbl)",
    "url": "https://www.eia.gov/dnav/pet/pet_pri_spt_s1_m.htm",
    "retrieved": "2026-10-25",
    "note": f"Data through {short_label(last).title()}",
}

spec = {
    "story_id": "2026-10-25-brent-wti-spread",
    "date": "2026-10-25",
    "section": "ENERGY",
    "topic": "CRUDE / BENCHMARK SPREADS",
    "handle": "@atlas",
    "sources": [SRC],
    "slides": [
        {
            "template": "cover", "sources": ["eia-spot"], "kicker": "Benchmark gap",
            "headline": f"Same oil.\n**${spread[last]:.0f} apart.**",
            "dek": f"A Brent–WTI gap this wide hadn't happened since {last_wide_year}. It's happened twice this year.",
            "stats": [
                {"label": f"BRENT · {short_label(last)}", "value": f"${brent[last]:.2f}", "delta": f"▲ {pct(brent):.1f}% M/M"},
                {"label": f"WTI · {short_label(last)}", "value": f"${wti[last]:.2f}", "delta": f"▲ {pct(wti):.1f}% M/M"},
                {"label": "SPREAD", "value": f"${spread[last]:.2f}", "delta": f"▲ ${spread[last] - spread[prev]:.2f}", "tone": "risk"},
            ],
            "spark": {"points": pts(brent), "width": 952, "height": 170},
            "cta": "WHY IT MATTERS",
        },
        {
            "template": "data", "sources": ["eia-spot"], "kicker": "THE DATA",
            "title": "Two spikes in six months, and the gap widened both times",
            "chart": {
                "series": [
                    {"name": "WTI", "points": pts(wti), "color": "muted"},
                    {"name": "Brent", "points": pts(brent), "color": "accent", "emphasis": True},
                ],
                "y_unit": "$", "x_ticks": [m for m in months if m[5:] in ("01", "07")],
                "annotations": [
                    {"series": "Brent", "at": peaks_2026[0], "text": f"{short_label(peaks_2026[0])} · ${brent[peaks_2026[0]]:.2f}", "place": "left"},
                    {"series": "Brent", "at": peaks_2026[1], "text": f"{short_label(peaks_2026[1])} · ${brent[peaks_2026[1]]:.2f}"},
                ],
            },
            "bars": {"title": "BRENT – WTI SPREAD, USD/BBL", "points": [[m, spread[m]] for m in months],
                     "threshold": 10, "threshold_label": "$10", "y_unit": "$"},
        },
        {
            "template": "explainer", "sources": ["eia-spot"], "kicker": "HOW IT WORKS",
            "title": "What the Brent–WTI spread actually prices",
            "flow": [
                {"label": "WTI", "sub": "CUSHING, OKLAHOMA"},
                {"label": "U.S. GULF", "sub": "PIPELINES · EXPORTS"},
                {"label": "BRENT", "sub": "SEABORNE / GLOBAL", "emphasis": True},
            ],
            "flow_caption": ["LANDLOCKED U.S. BENCHMARK", "WATERBORNE WORLD BENCHMARK"],
            "points": [
                "Brent is the reference for crude traded by sea. WTI is priced at an inland hub in Oklahoma.",
                "In normal times the gap roughly reflects the cost of moving U.S. barrels to world buyers: pipelines, terminals and freight.",
                "When it widens far beyond that, it usually signals seaborne crude is scarcer than U.S. inland crude.",
            ],
            "callout": {"tag": "UNVERIFIED · NOT YET ATTRIBUTED", "text": "ATLAS does not state a cause until primary sources confirm one."},
        },
        {
            "template": "takeaway", "kicker": "BOTTOM LINE",
            "statement": f"The **${spread[last]:.0f} gap** is the number to watch, not the headline price.",
            "watch": [
                {"date": "MONTHLY", "item": "EIA monthly spot averages: does the spread stay above $10?"},
                {"date": "WEEKLY", "item": "U.S. crude export volumes, the channel that normally closes the gap"},
            ],
        },
        {
            "template": "story", "sources": ["eia-spot"], "kicker": "New on ATLAS",
            "headline": f"Global oil is **${spread[last]:.0f}** above U.S. oil.\nWhy?",
            "spark": {"points": pts(brent), "width": 952, "height": 220},
            "cta": "READ THE POST", "top": 160,
        },
    ],
}

(HERE / "brent-spread.json").write_text(json.dumps(spec, indent=1))
print("wrote examples/brent-spread.json")

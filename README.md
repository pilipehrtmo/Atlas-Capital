# ATLAS

Financial intelligence for people who want to understand what moves the world.

ATLAS finds important economic stories, verifies them against credible sources, writes original analysis and publishes branded Instagram carousels. This repository holds the whole pipeline. It is being built in phases; **Phase 1 (brand system and renderer) is what exists today.**

## How it will run

| Step | Runs on | LLM |
| --- | --- | --- |
| Poll feeds and official data hourly, dedup, score | Server cron (Python) | None |
| Build a research pack: sources, quotes, chart data | Server cron | None |
| Telegram ping 1: approve the story | You | None |
| Write analysis, slide copy, caption | Scheduled Claude Code routine on your Claude plan | Yes, only after approval |
| Render slides, check every figure against its source | Server cron | None |
| Telegram ping 2: approve the post | You | None |
| Publish via the Instagram Graph API | Server cron | None |

## Phase 1: brand system

Slides are HTML/CSS templates rendered to PNG by headless Chromium, so typography, spacing and colours are code and stay identical on every post.

| Template | Canvas | Use |
| --- | --- | --- |
| `cover` | 1080 × 1350 | Hook-first story cover; optional full-bleed photo blended to black |
| `data` | 1080 × 1350 | Line chart with annotations, optional threshold bars |
| `explainer` | 1080 × 1350 | Mechanism flow, numbered points, "unverified" callout |
| `company` | 1080 × 1350 | Company identity, metric grid, segment bars |
| `flowmap` | 1080 × 1350 | Capital-flow ribbons from origin to destination |
| `takeaway` | 1080 × 1350 | Bottom line, what to watch, full source list |
| `story` | 1080 × 1920 | Stories and Reels cover |

Rendered samples are in [`docs/samples`](docs/samples). The `gallery-*` files use placeholder values and are stamped "sample data".

Brand tokens live in [`atlas/brand.py`](atlas/brand.py): background `#090B0D`, text `#F2F3EE`, accent `#C7FF35`, muted `#858B92`, risk `#FF5B61`; Barlow Condensed (headlines), Inter (body), JetBrains Mono (metadata). The fonts are bundled under the SIL Open Font License.

### Visual QA

Every render is checked before it can be used, and `atlas render` exits non-zero if any slide fails:

- exact canvas size (1080 × 1350 or 1080 × 1920)
- nothing outside the canvas; headlines that cannot shrink to fit are flagged
- no text smaller than 15 px
- all three brand fonts loaded, images loaded
- a source footnote on every slide

Headlines auto-shrink to fit their box, so copy of varying length still lands cleanly.

## Usage

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'
playwright install chromium        # or set ATLAS_CHROMIUM to an existing Chromium binary

python examples/build_brent_example.py         # builds the spec from EIA data in examples/data
python -m atlas render examples/brent-spread.json --out out/brent
pytest
```

## Carousel spec

A spec is JSON or YAML. Every slide except `takeaway` must cite at least one source by id, and every source needs a publisher, title, URL and retrieval date, or rendering is refused.

```json
{
  "story_id": "2026-10-25-brent-wti-spread",
  "date": "2026-10-25",
  "section": "ENERGY",
  "topic": "CRUDE / BENCHMARK SPREADS",
  "sources": [{"id": "eia-spot", "publisher": "U.S. Energy Information Administration",
               "title": "Brent and WTI spot prices, monthly averages (USD/bbl)",
               "url": "https://www.eia.gov/...", "retrieved": "2026-10-25"}],
  "slides": [
    {"template": "cover", "sources": ["eia-spot"], "kicker": "Benchmark gap",
     "headline": "Same oil.\n**$17 apart.**", "photo": {"path": "photo.jpg", "credit": "..."}}
  ]
}
```

`**text**` marks the accent highlight. See [`examples/build_brent_example.py`](examples/build_brent_example.py) for every template field in use.

## Roadmap

1. **Brand system and renderer** (this phase)
2. Source ingestion, dedup, SQLite archive
3. Source verification, ranking, research packs
4. Copy and caption generation, figure-to-source checks
5. Scheduling, Telegram approvals, budget and resource reports
6. Instagram publishing
7. Reliability and failure testing
8. Go live

# ATLAS: notes for Claude

- Editorial rules come first: every factual claim and every number on a slide must trace to a stored source (publisher, URL, retrieval date). Never invent figures, quotes, dates or links. If a cause is not confirmed by a primary source, say it is unverified.
- Operating model chosen by the owner: deterministic Python does all polling, scoring, rendering and publishing. The LLM step (analysis, copy, caption) runs only after the owner approves a story on Telegram, as a scheduled Claude Code routine on the owner's Claude plan, not through a paid API key. The owner approves again before anything is published.
- Do not add an LLM call to anything that can be done with rules or code.
- Slides render from `atlas/render/templates` via `python -m atlas render SPEC`. Keep brand tokens in `atlas/brand.py`; templates read them as CSS variables.
- Run `pytest` before committing. Rendering tests need Chromium (`playwright install chromium`, or `ATLAS_CHROMIUM=/path/to/chrome`).
- Specs flagged `"sample": true` contain placeholder values and must never be published.

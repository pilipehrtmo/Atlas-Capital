"""ATLAS command line.

    python -m atlas render SPEC [--out DIR]   render a carousel spec to PNGs and run visual QA
    python -m atlas check SPEC                validate a spec without rendering
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from atlas.render.renderer import SpecError, build_html, load_spec, render


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="atlas")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render", help="render a carousel spec to PNG slides")
    r.add_argument("spec")
    r.add_argument("--out", default=None, help="output directory (default: out/<story_id>)")
    c = sub.add_parser("check", help="validate a spec without rendering")
    c.add_argument("spec")
    args = ap.parse_args(argv)

    try:
        spec = load_spec(args.spec)
        if args.cmd == "check":
            build_html(spec)
            print(f"ok: {len(spec['slides'])} slides")
            return 0
        out = Path(args.out or Path("out") / spec.get("story_id", Path(args.spec).stem))
        results = render(spec, out)
    except SpecError as e:
        print(f"spec error: {e}", file=sys.stderr)
        return 2

    for res in results:
        status = "ok " if res.ok else "FAIL"
        print(f"{status} {res.index:02d} {res.template:<9} {res.width}x{res.height}  {res.png}")
        for p in res.problems:
            print(f"       - {p}")
    print(f"manifest: {out / 'manifest.json'}")
    return 0 if all(r.ok for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())

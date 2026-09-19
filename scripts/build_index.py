#!/usr/bin/env python3
"""Rebuild docs/INDEX.md and the index block inside README.md.

Reads the frontmatter of every markdown piece under the content directories,
groups by track, and writes the index. Also flags files with bad or missing
frontmatter so they get fixed instead of sitting there broken.

Usage:
    python scripts/build_index.py
    python scripts/build_index.py --check    # report problems, write nothing
"""

import argparse
import pathlib
import re
import sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
INDEX = ROOT / "docs" / "INDEX.md"
README = ROOT / "README.md"

SEARCH_DIRS = [
    "content/decisions",
    "content/teardowns",
    "content/cases",
    "content/sector-notes",
    "bi/analyses",
    "bi/metric-library",
    "tools",
    "weekly",
]

TRACK_ORDER = [
    ("bi-analysis", "Business intelligence analyses"),
    ("teardown", "AI product teardowns"),
    ("metric", "Metric library"),
    ("decision-record", "Decision records from my own work"),
    ("case", "Management case notes"),
    ("sector-note", "Sector notes"),
    ("tool", "Tools"),
    ("weekly-review", "Weekly reviews"),
]

SINGULAR = {
    "bi-analysis": "business intelligence analysis",
    "teardown": "AI product teardown",
    "metric": "metric",
    "decision-record": "decision record",
    "case": "management case note",
    "sector-note": "sector note",
    "tool": "tool",
    "weekly-review": "weekly review",
}

REQUIRED = ["title", "date", "track", "summary"]
START = "<!-- INDEX:START -->"
END = "<!-- INDEX:END -->"


def parse_frontmatter(path: pathlib.Path):
    """Return (fields dict, list of problems)."""
    text = path.read_text(encoding="utf-8")
    problems = []
    if not text.startswith("---"):
        return {}, [f"{path.relative_to(ROOT)}: no frontmatter block"]
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, [f"{path.relative_to(ROOT)}: frontmatter not closed"]
    fields = {}
    for line in parts[1].strip().splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip().strip('"').strip("'")
    for key in REQUIRED:
        if not fields.get(key):
            problems.append(f"{path.relative_to(ROOT)}: missing '{key}'")
    date = fields.get("date", "")
    if date and not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        problems.append(f"{path.relative_to(ROOT)}: date '{date}' is not YYYY-MM-DD")
    return fields, problems


def collect():
    pieces, problems = [], []
    for rel in SEARCH_DIRS:
        d = ROOT / rel
        if not d.exists():
            continue
        for path in sorted(d.rglob("*.md")):
            if path.name.upper() == "README.MD":
                continue
            fields, probs = parse_frontmatter(path)
            problems.extend(probs)
            if not fields.get("title"):
                continue
            pieces.append(
                {
                    "title": fields["title"],
                    "date": fields.get("date", ""),
                    "track": fields.get("track", "unsorted"),
                    "summary": fields.get("summary", ""),
                    "sources": fields.get("sources", "0"),
                    "path": path.relative_to(ROOT).as_posix(),
                }
            )
    return pieces, problems


def plural(n: int) -> str:
    return "piece" if n == 1 else "pieces"


def render_index(pieces):
    by_track = defaultdict(list)
    for p in pieces:
        by_track[p["track"]].append(p)

    out = ["# Index", ""]
    out.append(f"{len(pieces)} {plural(len(pieces))} in the repo.")
    out.append("")
    out.append("| Track | Pieces |")
    out.append("| --- | --- |")
    for track_id, label in TRACK_ORDER:
        out.append(f"| {label} | {len(by_track.get(track_id, []))} |")
    out.append("")

    for track_id, label in TRACK_ORDER:
        items = sorted(by_track.get(track_id, []), key=lambda x: x["date"], reverse=True)
        if not items:
            continue
        out.append(f"## {label}")
        out.append("")
        for p in items:
            out.append(f"- **[{p['title']}]({'../' + p['path']})** ({p['date']})  ")
            out.append(f"  {p['summary']}")
        out.append("")

    leftovers = {k: v for k, v in by_track.items() if k not in dict(TRACK_ORDER)}
    if leftovers:
        out.append("## Unsorted")
        out.append("")
        for track_id, items in sorted(leftovers.items()):
            for p in items:
                out.append(f"- [{p['title']}]({'../' + p['path']}) (track: {track_id})")
        out.append("")

    return "\n".join(out).rstrip() + "\n"


def render_readme_block(pieces):
    latest = sorted(pieces, key=lambda x: x["date"], reverse=True)[:8]
    by_track = defaultdict(int)
    for p in pieces:
        by_track[p["track"]] += 1

    lines = [START, ""]
    counts = ", ".join(
        f"{by_track[t]} {label.lower() if by_track[t] != 1 else SINGULAR[t]}"
        for t, label in TRACK_ORDER
        if by_track.get(t)
    )
    lines.append(
        f"**{len(pieces)} {plural(len(pieces))} so far.** "
        f"{counts if counts else 'Nothing yet.'}"
    )
    lines.append("")
    if latest:
        lines.append("Most recent:")
        lines.append("")
        for p in latest:
            lines.append(f"- `{p['date']}` [{p['title']}]({p['path']}) . {p['summary']}")
        lines.append("")
    lines.append(f"Full list in [docs/INDEX.md](docs/INDEX.md).")
    lines.append("")
    lines.append(END)
    return "\n".join(lines)


def update_readme(block):
    if not README.exists():
        return False
    text = README.read_text(encoding="utf-8")
    if START not in text or END not in text:
        return False
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    new = pattern.sub(block, text)
    if new != text:
        README.write_text(new, encoding="utf-8")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report problems only")
    args = ap.parse_args()

    pieces, problems = collect()

    for problem in problems:
        print(f"PROBLEM: {problem}", file=sys.stderr)

    if args.check:
        print(f"{len(pieces)} {plural(len(pieces))}, {len(problems)} problems")
        return 1 if problems else 0

    INDEX.parent.mkdir(parents=True, exist_ok=True)
    INDEX.write_text(render_index(pieces), encoding="utf-8")
    ok = update_readme(render_readme_block(pieces))

    print(f"Wrote docs/INDEX.md with {len(pieces)} {plural(len(pieces))}.")
    if not ok:
        print("README index markers not found, README left alone.", file=sys.stderr)
    if problems:
        print(f"{len(problems)} frontmatter problems above. Fix them.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

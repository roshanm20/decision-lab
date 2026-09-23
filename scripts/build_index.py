#!/usr/bin/env python3
"""Rebuild docs/INDEX.md and the generated block in README.md.

Tools come from decisionlab/registry.py, so a registered tool always shows
up. Notes come from the frontmatter of markdown files in the note folders.
Weekly logs are listed separately and are not counted as pieces, because a
log of what happened is not a piece of work.

    python scripts/build_index.py
    python scripts/build_index.py --check    # report frontmatter problems only
"""

from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
INDEX = ROOT / "docs" / "INDEX.md"
README = ROOT / "README.md"
START, END = "<!-- INDEX:START -->", "<!-- INDEX:END -->"

NOTE_DIRS = ["content/notes", "content/decisions", "content/teardowns", "content/cases",
             "content/sector-notes", "content/scans", "bi/analyses", "bi/metric-library", "tools"]
LOG_DIRS = ["weekly"]
SKIP_NAMES = {"README.MD", "CHANGELOG.MD", "_TEMPLATE.MD"}

TRACKS = [  # (label, track ids that belong under it)
    ("Applied notes, the tools used on real data", {"note"}),
    ("Decisions from my own work", {"decision-record"}),
    ("BI analyses", {"bi-build", "bi-analysis"}),
    ("AI product teardowns", {"teardown"}),
    ("Metric definitions", {"metric"}),
    ("Case notes", {"case"}),
    ("Sector notes", {"sector-note"}),
    ("Innovation scans", {"innovation-scan"}),
    ("Tool write-ups", {"tool", "build"}),
]
LOG_TRACKS = {"weekly-log", "weekly-review"}
REQUIRED = ["title", "date", "track", "summary"]


def frontmatter(path: pathlib.Path):
    text = path.read_text(encoding="utf-8")
    where = path.relative_to(ROOT).as_posix()
    if not text.startswith("---"):
        return {}, [f"{where}: no frontmatter block"]
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, [f"{where}: frontmatter not closed"]
    fields = {}
    for line in parts[1].strip().splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip().strip('"').strip("'")
    problems = [f"{where}: missing '{k}'" for k in REQUIRED if not fields.get(k)]
    if fields.get("date") and not re.match(r"^\d{4}-\d{2}-\d{2}$", fields["date"]):
        problems.append(f"{where}: date '{fields['date']}' is not YYYY-MM-DD")
    known = set().union(*(ids for _, ids in TRACKS)) | LOG_TRACKS
    if fields.get("track") and fields["track"] not in known:
        problems.append(f"{where}: unknown track '{fields['track']}'")
    if "not yet written" in fields.get("summary", "").lower():
        problems.append(f"{where}: summary is a placeholder, not a summary")
    return fields, problems


def collect(dirs):
    items, problems = [], []
    for d in dirs:
        base = ROOT / d
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.md")):
            if path.name.upper() in SKIP_NAMES:
                continue
            fields, probs = frontmatter(path)
            problems += probs
            if fields.get("title"):
                items.append({**fields, "path": path.relative_to(ROOT).as_posix()})
    return items, problems


def test_count() -> int:
    proc = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q"], cwd=ROOT,
                          capture_output=True, text=True)
    m = re.search(r"(\d+) tests? collected", proc.stdout)
    if m:
        return int(m.group(1))
    return sum(t.read_text().count("def test_") for t in (ROOT / "tests").glob("test_*.py"))


def plural(n, word):
    return f"{n} {word}" + ("" if n == 1 else "s")


def tools_by_persona():
    from decisionlab.registry import PERSONAS, load_tools
    grouped = defaultdict(list)
    for _, meta in load_tools():
        grouped[meta["persona"]].append(meta)
    return PERSONAS, grouped


def render_tools(link_prefix: str) -> list:
    personas, grouped = tools_by_persona()
    out = []
    for key, label in personas.items():
        if not grouped.get(key):
            continue
        out += [f"**{label}**", ""]
        for meta in grouped[key]:
            out.append(f"- [`{meta['name']}`]({link_prefix}{meta['doc']}) {meta['summary']}")
        out.append("")
    return out


def render_index(notes, logs, n_tests) -> str:
    _, grouped = tools_by_persona()
    n_tools = sum(len(v) for v in grouped.values())
    out = ["# Index", "", f"{plural(n_tools, 'tool')}, {plural(n_tests, 'test')}, {plural(len(notes), 'note')}.", "",
           "## Tools", ""] + render_tools("../")
    by_track = defaultdict(list)
    for n in notes:
        by_track[n["track"]].append(n)
    out += ["## Notes", ""]
    for label, ids in TRACKS:
        group = sorted((n for t in ids for n in by_track.get(t, [])), key=lambda n: n["date"], reverse=True)
        if not group:
            continue
        out += [f"### {label}", ""]
        for n in group:
            out += [f"- **[{n['title']}](../{n['path']})** ({n['date']})  ", f"  {n['summary']}"]
        out.append("")
    if logs:
        out += ["## Weekly logs", ""]
        for n in sorted(logs, key=lambda n: n["date"], reverse=True):
            out.append(f"- [{n['title']}](../{n['path']}) ({n['date']})")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def render_readme_block(notes, n_tests) -> str:
    _, grouped = tools_by_persona()
    n_tools = sum(len(v) for v in grouped.values())
    lines = [START, "",
             f"**{plural(n_tools, 'tool')} across {len(grouped)} groups, "
             f"{plural(n_tests, 'test')}, {plural(len(notes), 'written note')}.**", ""]
    lines += render_tools("")
    latest = sorted(notes, key=lambda n: n["date"], reverse=True)[:5]
    if latest:
        lines += ["**Latest notes**", ""]
        lines += [f"- `{n['date']}` [{n['title']}]({n['path']})" for n in latest]
        lines.append("")
    lines += ["Everything, including older notes and weekly logs: [docs/INDEX.md](docs/INDEX.md).", "", END]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    notes, p1 = collect(NOTE_DIRS)
    logs_raw, p2 = collect(LOG_DIRS)
    logs = [l for l in logs_raw if l.get("track") in LOG_TRACKS]
    notes += [l for l in logs_raw if l.get("track") not in LOG_TRACKS]
    problems = p1 + p2
    for p in problems:
        print(f"PROBLEM: {p}", file=sys.stderr)
    if args.check:
        print(f"{plural(len(notes), 'note')}, {plural(len(problems), 'problem')}")
        return 1 if problems else 0
    n_tests = test_count()
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    INDEX.write_text(render_index(notes, logs, n_tests), encoding="utf-8")
    text = README.read_text(encoding="utf-8")
    if START in text and END in text:
        block = render_readme_block(notes, n_tests)
        README.write_text(re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block, text, flags=re.S),
                          encoding="utf-8")
    print(f"Index rebuilt: {plural(len(notes), 'note')}, {plural(len(logs), 'log')}, {plural(n_tests, 'test')}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

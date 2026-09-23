#!/usr/bin/env python3
"""Decide what today's run builds, and print a brief as JSON.

Weekly shape, by UTC weekday:
    Monday     build a BI tool
    Tuesday    build a consulting tool
    Wednesday  build a marketing tool
    Thursday   a decision record if journal/inbox has a note, else a product tool
    Friday     build for whichever persona has the fewest tools
    Saturday   a note, ideally using one of the tools on real sourced data
    Sunday     release and plan

The item itself comes from ROADMAP.md: the first ready item in the day's
section. The brief also lists the persona's existing tools with the
limitations their docs admit to, because extending a tool is often better
than starting a new one.

Exit codes:
    0  go ahead
    3  today's commit has already landed, commit nothing
    4  no ready item in today's section, add three to ROADMAP.md then use the first

Usage:
    python scripts/pick_track.py
    python scripts/pick_track.py --date 2026-09-28
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from daylog import landed_today, run_date  # noqa: E402
import subprocess  # noqa: E402

ROADMAP = ROOT / "ROADMAP.md"
PERSONA_ORDER = ["bi", "consulting", "marketing", "product"]
FIXED = {0: "bi", 1: "consulting", 2: "marketing", 4: None}  # 4 means least served

ITEM_RE = re.compile(r"^- \[( |x|~)\] ([A-Z]{2}-\d{2}) \| (\w+) \| (.+?) \| ([SM])\s*$")


def parse_roadmap() -> dict:
    """{section: [item dict, ...]} in file order."""
    sections, current, last = {}, None, None
    for line in ROADMAP.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = []
            last = None
            continue
        m = ITEM_RE.match(line)
        if m and current:
            last = {"status": {" ": "ready", "x": "done", "~": "blocked"}[m.group(1)],
                    "id": m.group(2), "type": m.group(3), "title": m.group(4),
                    "size": m.group(5), "why": "", "done_when": ""}
            sections[current].append(last)
            continue
        stripped = line.strip()
        if last and stripped.startswith("- why:"):
            last["why"] = stripped[len("- why:"):].strip()
        elif last and stripped.startswith("- done when:"):
            last["done_when"] = stripped[len("- done when:"):].strip()
    return sections


def ids_in_history() -> set:
    """Roadmap IDs recorded as built in a Roadmap-Item trailer, so an item
    built but not ticked is never built twice. Mentions of an ID anywhere else,
    such as 'added BI-11' or 'move BI-05 up', do not count."""
    try:
        log = subprocess.run(["git", "log", "--format=%(trailers:key=Roadmap-Item,valueonly)"], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return set()
    return set(re.findall(r"\b[A-Z]{2}-\d{2}\b", log))


def tool_inventory() -> list:
    """Every registered tool with the limitations its docs page lists."""
    from decisionlab.registry import load_tools
    out = []
    for module, meta in load_tools():
        doc = ROOT / meta["doc"]
        limits = []
        if doc.exists():
            text = doc.read_text(encoding="utf-8")
            block = text.split("## What it does not do", 1)
            if len(block) == 2:
                body = block[1].split("\n## ", 1)[0]
                limits = [l[2:].strip() for l in body.splitlines() if l.startswith("- ")]
        out.append({"name": meta["name"], "persona": meta["persona"], "module": module.__name__,
                    "doc": meta["doc"], "limitations": limits})
    return out


def inbox_notes() -> list:
    inbox = ROOT / "journal" / "inbox"
    if not inbox.exists():
        return []
    notes = [p for p in inbox.glob("*.md") if not p.name.startswith("_") and p.name.upper() != "README.MD"]
    return sorted(notes, key=lambda p: (p.stat().st_mtime, p.name))


def least_served(tools: list) -> str:
    counts = {p: 0 for p in PERSONA_ORDER}
    for t in tools:
        counts[t["persona"]] = counts.get(t["persona"], 0) + 1
    return min(PERSONA_ORDER, key=lambda p: (counts[p], PERSONA_ORDER.index(p)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="override the date, as YYYY-MM-DD")
    args = ap.parse_args()
    today = dt.date.fromisoformat(args.date) if args.date else run_date()
    weekday = today.weekday()
    roadmap = parse_roadmap()
    tools = tool_inventory()
    notes = inbox_notes()

    brief = {"date": today.isoformat(), "weekday": today.strftime("%A"),
             "commit_trailer": f"Daily-Build: {today.isoformat()}"}

    if weekday == 6:
        brief.update(day_type="release", section=None, persona=None)
    elif weekday == 5:
        brief.update(day_type="note", section="notes", persona=None)
    elif weekday == 3 and notes:
        brief.update(day_type="decision-record", section=None, persona=None,
                     journal_note=notes[0].relative_to(ROOT).as_posix(),
                     notes_waiting=len(notes))
    else:
        persona = FIXED.get(weekday, "product") if weekday != 4 else least_served(tools)
        if weekday == 3:
            persona = "product"
        brief.update(day_type="build", section=persona, persona=persona,
                     persona_tools=[t for t in tools if t["persona"] == persona])

    section = brief.get("section")
    if section:
        built = ids_in_history()
        ready = [i for i in roadmap.get(section, []) if i["status"] == "ready" and i["id"] not in built]
        brief["item"] = ready[0] if ready else None
        brief["next_items"] = [f"{i['id']} {i['title']}" for i in ready[1:3]]

    brief["tool_count"] = len(tools)
    brief["already_landed_today"] = landed_today(today) if not args.date else False
    print(json.dumps(brief, indent=2))

    if brief["already_landed_today"]:
        print("\nSTOP: today's commit has already landed. Commit nothing.", file=sys.stderr)
        return 3
    if section and brief.get("item") is None:
        print(f"\nNo ready item under '## {section}' in ROADMAP.md. Add three good ones, "
              "then build the first.", file=sys.stderr)
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main())

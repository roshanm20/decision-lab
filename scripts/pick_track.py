#!/usr/bin/env python3
"""Pick today's track and print a brief for the daily run.

Most days start with a web search for what is actually new, not with a fixed
topic. The backlog is the fallback for a day when the search turns up nothing
worth building on.

Exit codes:
    0  go ahead
    3  today's piece already exists, stop and commit nothing
    4  a backlog-only track has an empty backlog, propose topics first

Usage:
    python scripts/pick_track.py
    python scripts/pick_track.py --date 2026-09-21
"""

import argparse
import datetime as dt
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BACKLOG = ROOT / "BACKLOG.md"

# Monday is 0.
TRACKS = {
    0: {
        "id": "bi-build",
        "dir": "bi/analyses",
        "label": "Business intelligence build",
        "discovery": True,
        "search_for": (
            "a measurement or analysis problem people are actually complaining "
            "about right now: a metric that keeps getting computed wrong, a "
            "dataset that just became public, an analysis everyone does badly. "
            "Look at Hacker News, r/analytics, r/datascience, dbt and Metabase "
            "release notes, and recent posts from analytics engineering blogs."
        ),
        "brief": (
            "Build the analysis. Real data or clearly labelled synthetic data "
            "with the generator committed, the query or script, and a "
            "conclusion a manager could act on. The piece must name the problem "
            "you found in discovery and say why the usual approach to it fails."
        ),
        "extra": "Commit the SQL or Python in the same folder, and run it before you commit.",
    },
    1: {
        "id": "teardown",
        "dir": "content/teardowns",
        "label": "AI product teardown",
        "discovery": True,
        "search_for": (
            "an AI product that shipped, repriced, pivoted or raised in the last "
            "two weeks, preferably in competitive intelligence, research and "
            "analyst tooling, or B2B AI that eats part of a services engagement. "
            "Product Hunt, company changelogs and pricing pages, funding news."
        ),
        "brief": (
            "Take it apart. The wedge it entered on, the pricing and what that "
            "pricing commits them to, the moat and whether it holds, and the "
            "thing most likely to break. Prefer something that moved recently "
            "over something famous."
        ),
        "extra": "Include a pricing table with the date you checked it.",
    },
    2: {
        "id": "metric",
        "dir": "bi/metric-library",
        "label": "Metric definition",
        "discovery": False,
        "brief": (
            "Define one metric properly. Exact formula, the edge cases that "
            "break it, how a team would game it, and the metric you pair it "
            "with to stop that. Two hundred to five hundred words is fine."
        ),
        "extra": "Include the SQL against a plausible schema, with the schema stated.",
    },
    3: {
        "id": "decision-record",
        "dir": "content/decisions",
        "label": "Decision record from Roshan's own work",
        "discovery": False,
        "brief": (
            "Turn the oldest note in journal/inbox into a proper decision "
            "record. Use ONLY what the note says. Where the note is thin, ask a "
            "question in the open questions section rather than filling the gap. "
            "This is about Roshan's own companies, so an invented detail here is "
            "worse than a missing one."
        ),
        "extra": "Move the note to journal/used/ once the record is written.",
        "source": "journal",
        "fallback_id": "case",
        "fallback_dir": "content/cases",
        "fallback_label": "Management case note",
        "fallback_brief": (
            "The inbox is empty, so write an outside case note instead. "
            "Situation, the decision on the table, two or three options with "
            "numbers attached, your call, and what would change your mind."
        ),
        "fallback_extra": "The options section must have numbers, not adjectives.",
    },
    4: {
        "id": "innovation-scan",
        "dir": "content/scans",
        "label": "Innovation scan",
        "discovery": True,
        "search_for": (
            "what actually shipped or changed this week in AI products, "
            "business intelligence tooling, and the Indian sectors this repo "
            "follows. Research papers only if something in them is buildable."
        ),
        "brief": (
            "Write the scan. Three to five things that moved, what each one "
            "means for someone building in the space, and one of them picked out "
            "as the thing worth building on. End with the idea you would build "
            "next and why, so Monday and Saturday have something to pull from."
        ),
        "extra": (
            "Add the unbuilt ideas to BACKLOG.md under the track they fit, "
            "marked (auto), so nothing found here gets lost."
        ),
        "fallback_dir": "content/sector-notes",
    },
    5: {
        "id": "build",
        "dir": "tools",
        "label": "Build day",
        "discovery": True,
        "search_for": (
            "a small concrete problem someone described in public this week that "
            "a two hundred line script would solve. Also re-read this repo's own "
            "tools and their 'what it does not do' sections, because fixing a "
            "real limitation in an existing tool beats starting a new one."
        ),
        "brief": (
            "Build or improve. Under three hundred lines for something new. It "
            "must run on its own and print something useful, and you must "
            "actually run it before committing."
        ),
        "extra": "Paste the real output into the note. Never a hypothetical output.",
        "inventory": True,
    },
    6: {
        "id": "weekly-review",
        "dir": "weekly",
        "label": "Weekly review draft",
        "discovery": False,
        "brief": (
            "Prepare the review draft only. List every piece committed in the "
            "last seven days with its track and one line summary. Then write the "
            "questions section. Leave the 'My read' heading empty with a "
            "placeholder line. Roshan fills that part himself."
        ),
        "extra": "Do not write opinions in the weekly review. Only the listing and the questions.",
        "needs_topic": False,
    },
}


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text).strip("-")
    return "-".join(text.split("-")[:8])


def inbox_notes():
    """Notes waiting in journal/inbox, oldest first. Skips README and _ files."""
    inbox = ROOT / "journal" / "inbox"
    if not inbox.exists():
        return []
    notes = [
        p for p in inbox.glob("*.md")
        if not p.name.startswith("_") and p.name.upper() != "README.MD"
    ]
    return sorted(notes, key=lambda p: (p.stat().st_mtime, p.name))


def read_backlog_section(track_id: str):
    """Return (all_items, pending_items) under one track heading."""
    if not BACKLOG.exists():
        return [], []
    inside = False
    items, pending = [], []
    for line in BACKLOG.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            inside = line[3:].strip() == track_id
            continue
        if not inside:
            continue
        m = re.match(r"^- \[( |x|X)\]\s+(.+?)\s*$", line)
        if m:
            items.append(m.group(2))
            if m.group(1).lower() != "x":
                pending.append(m.group(2))
    return items, pending


def tool_inventory():
    """Existing tools with their size and the limitations they admit to."""
    tools = ROOT / "tools"
    out = []
    for script in sorted(tools.glob("*.py")):
        lines = script.read_text(encoding="utf-8").splitlines()
        note = next(
            (p for p in sorted(tools.glob("*.md")) if script.stem.split("_")[0] in p.stem),
            None,
        )
        out.append(
            {
                "script": script.relative_to(ROOT).as_posix(),
                "lines": len(lines),
                "note": note.relative_to(ROOT).as_posix() if note else None,
            }
        )
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="override the date, as YYYY-MM-DD")
    args = ap.parse_args()

    today = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    track = dict(TRACKS[today.weekday()])

    waiting = inbox_notes() if track.get("source") == "journal" else []
    if track.get("source") == "journal" and not waiting:
        track.update(
            id=track["fallback_id"],
            dir=track["fallback_dir"],
            label=track["fallback_label"],
            brief=track["fallback_brief"],
            extra=track["fallback_extra"],
            source=None,
        )

    target_dir = ROOT / track["dir"]
    target_dir.mkdir(parents=True, exist_ok=True)

    stamp = today.isoformat()
    existing_today = sorted(p.name for p in target_dir.glob(f"{stamp}-*"))

    all_items, pending = read_backlog_section(track["id"])
    topic = pending[0] if pending else None
    needs_topic = track.get("needs_topic", True)

    if track.get("source") == "journal":
        needs_topic = False
        topic = f"the note at {waiting[0].relative_to(ROOT).as_posix()}"
        suggested = f"{stamp}-{slugify(waiting[0].stem)}.md"
    elif track.get("discovery"):
        # Discovery decides the topic, so the backlog is only a safety net.
        needs_topic = False
        suggested = None
    elif not needs_topic:
        suggested = f"{stamp}-week-review.md"
    else:
        suggested = f"{stamp}-{slugify(topic)}.md" if topic else None

    brief = {
        "date": stamp,
        "weekday": today.strftime("%A"),
        "track": track["id"],
        "label": track["label"],
        "directory": track["dir"],
        "brief": track["brief"],
        "extra_requirement": track["extra"],
        "discovery": bool(track.get("discovery")),
        "search_for": track.get("search_for"),
        "discovery_log": f"discovery/{stamp[:7]}.md",
        "filename_pattern": f"{stamp}-<slug>.md",
        "fallback_directory": track.get("fallback_dir"),
        "suggested_filename": suggested,
        "source": track.get("source") or ("discovery" if track.get("discovery") else "backlog"),
        "note_to_use": waiting[0].relative_to(ROOT).as_posix() if waiting else None,
        "notes_waiting_in_inbox": len(waiting),
        "backlog_fallback_topic": topic,
        "backlog_pending_in_track": len(pending),
        "backlog_total_in_track": len(all_items),
        "already_done_today": existing_today,
    }
    if track.get("inventory"):
        brief["existing_tools"] = tool_inventory()
        brief["prefer_extending"] = len(brief["existing_tools"]) >= 3

    print(json.dumps(brief, indent=2))

    if existing_today:
        print(
            f"\nSTOP: {track['id']} already has a file for {stamp}. "
            "Nothing to do. Exit without committing.",
            file=sys.stderr,
        )
        return 3

    if track.get("discovery"):
        print(
            "\nDiscovery track. Search first, then decide what to build. "
            "Log what you found in the discovery log either way. Fall back to "
            "the backlog topic only if the search genuinely turns up nothing.",
            file=sys.stderr,
        )
        return 0

    if not needs_topic:
        return 0

    if topic is None:
        print(
            f"\nWARNING: no pending topic under '## {track['id']}' in BACKLOG.md. "
            "Propose three good topics, append them marked (auto), and use the first.",
            file=sys.stderr,
        )
        return 4

    if len(pending) <= 3:
        print(
            f"\nNOTE: only {len(pending)} topics left in this track. "
            "Append two or three more, marked (auto), after writing today's piece.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Pick today's track and the next topic from BACKLOG.md.

Prints a JSON brief for the daily run. Exits with code 3 if today's piece
already exists, so the workflow can stop without committing anything.

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

# Monday is 0. One track per day so the week has a shape and topics do not repeat.
TRACKS = {
    0: {
        "id": "bi-analysis",
        "dir": "bi/analyses",
        "label": "Business intelligence analysis",
        "brief": (
            "Do a real analysis. Find a public dataset or generate a clearly "
            "labelled synthetic one with the generator committed. Write the "
            "query or script, run it, and report what you found. The piece "
            "must end with a decision a manager could act on."
        ),
        "extra": "Commit the SQL or Python alongside the note, in the same folder.",
    },
    1: {
        "id": "teardown",
        "dir": "content/teardowns",
        "label": "AI product teardown",
        "brief": (
            "Take apart one real AI product. Cover the wedge it entered on, "
            "the pricing and what that pricing commits them to, the moat and "
            "whether it holds, and the thing most likely to break. Use their "
            "own pricing page and public filings or funding reports."
        ),
        "extra": "Include a short table of the pricing tiers with the date you checked them.",
    },
    2: {
        "id": "metric",
        "dir": "bi/metric-library",
        "label": "Metric definition",
        "brief": (
            "Define one metric properly. Exact formula, the edge cases that "
            "break it, how a team would game it, and the metric you pair it "
            "with to stop that. Short is fine. Two hundred to five hundred words."
        ),
        "extra": "Include the SQL for the metric against a plausible schema, with the schema stated.",
    },
    3: {
        "id": "case",
        "dir": "content/cases",
        "label": "Management case note",
        "brief": (
            "Write a case note on a decision. Situation, the decision on the "
            "table, two or three options with numbers attached, your call, and "
            "what would change your mind. Base it on a real company where you "
            "can, and say clearly when the figures are illustrative."
        ),
        "extra": "The options section must have numbers, not adjectives.",
    },
    4: {
        "id": "sector-note",
        "dir": "content/sector-notes",
        "label": "Sector note",
        "brief": (
            "Explain how one sector actually works. Who the players are, where "
            "the money is made along the chain, what is changing right now, and "
            "the one number that decides the outcome. Indian sectors preferred."
        ),
        "extra": "Cite at least four sources. Industry bodies and filings beat news articles.",
    },
    5: {
        "id": "tool",
        "dir": "tools",
        "label": "Small tool",
        "brief": (
            "Build one small thing that works. Under three hundred lines. It "
            "must run on its own and print something useful. Write a short "
            "README note next to it saying what it is for and how to run it."
        ),
        "extra": "Test it by actually running it before you commit. Paste the output in the note.",
    },
    6: {
        "id": "weekly-review",
        "dir": "weekly",
        "label": "Weekly review draft",
        "brief": (
            "Prepare the review draft only. List every piece committed in the "
            "last seven days with its track and one line summary. Then write "
            "the questions section. Leave the 'My read' heading empty with a "
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


def read_backlog_section(track_id: str):
    """Return (all_items, pending_items) for one track heading."""
    if not BACKLOG.exists():
        return [], []
    lines = BACKLOG.read_text(encoding="utf-8").splitlines()
    inside = False
    items, pending = [], []
    for line in lines:
        if line.startswith("## "):
            inside = line[3:].strip() == track_id
            continue
        if not inside:
            continue
        m = re.match(r"^- \[( |x|X)\]\s+(.+?)\s*$", line)
        if m:
            done = m.group(1).lower() == "x"
            topic = m.group(2)
            items.append(topic)
            if not done:
                pending.append(topic)
    return items, pending


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="override the date, as YYYY-MM-DD")
    args = ap.parse_args()

    if args.date:
        today = dt.date.fromisoformat(args.date)
    else:
        today = dt.date.today()

    track = TRACKS[today.weekday()]
    target_dir = ROOT / track["dir"]
    target_dir.mkdir(parents=True, exist_ok=True)

    stamp = today.isoformat()
    existing_today = sorted(p.name for p in target_dir.glob(f"{stamp}-*"))

    needs_topic = track.get("needs_topic", True)
    all_items, pending = read_backlog_section(track["id"])
    topic = pending[0] if pending else None

    if not needs_topic:
        suggested_name = f"{stamp}-week-review.md"
    elif topic:
        suggested_name = f"{stamp}-{slugify(topic)}.md"
    else:
        suggested_name = None

    brief = {
        "date": stamp,
        "weekday": today.strftime("%A"),
        "track": track["id"],
        "label": track["label"],
        "directory": track["dir"],
        "brief": track["brief"],
        "extra_requirement": track["extra"],
        "topic": topic,
        "suggested_filename": suggested_name,
        "backlog_pending_in_track": len(pending),
        "backlog_total_in_track": len(all_items),
        "already_done_today": existing_today,
    }

    print(json.dumps(brief, indent=2))

    if existing_today:
        print(
            f"\nSTOP: {track['id']} already has a file for {stamp}. "
            "Nothing to do. Exit without committing.",
            file=sys.stderr,
        )
        return 3

    if not needs_topic:
        return 0

    if topic is None:
        print(
            f"\nWARNING: no pending topic under '## {track['id']}' in BACKLOG.md. "
            "Propose three good topics, append them to that section marked (auto), "
            "and use the first one.",
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

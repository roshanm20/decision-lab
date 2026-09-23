#!/usr/bin/env python3
"""The only way the daily run should commit.

With --item it ticks that ROADMAP.md item and records it in a Roadmap-Item
trailer. It rebuilds the index, runs every check (against the run's starting
commit when DAILY_START is set, so an edit to a protected file is caught while
the run can still undo it), stages everything, commits with Roshan as the
author and the day's Daily-Build trailer, then confirms the author.
The author matters because commits authored by claude[bot] do not appear on
his contribution graph, and the action sets git's user to the bot.

    python scripts/commit_day.py --item BI-02 -m "build: funnel tool with step intervals"
    python scripts/commit_day.py -m "..." --push   # only when running by hand
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from daylog import run_date  # noqa: E402
from check import OWN_WORK  # noqa: E402
AUTHOR_NAME = "Muhammed Roshan M"
AUTHOR_EMAIL = "muhammedroshanmangat@gmail.com"


def git(*args, check=True):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=check)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-m", "--message", required=True, help="'<day type>: what this commit does'")
    ap.add_argument("--item", help="the ROADMAP.md item this commit finishes, e.g. BI-02")
    ap.add_argument("--push", action="store_true", help="push after committing (manual runs only)")
    args = ap.parse_args()

    if ":" not in args.message.split("\n", 1)[0]:
        print("The first line must look like '<day type>: what this commit does'.")
        return 1
    if OWN_WORK.search(args.message):
        print("The commit message names Roshan's own work. Commit messages are public and show up in "
              "logs, so describe the record instead, for example 'decision-record: pricing tiers, "
              "from a journal note'.")
        return 1
    if args.push and os.environ.get("GITHUB_ACTIONS") == "true":
        print("--push is for manual runs only. In the workflow, the push step pushes after checking.")
        return 1

    trailers = []
    if args.item:
        if not re.fullmatch(r"[A-Z]{2}-\d{2}", args.item):
            print(f"--item must look like BI-02, got {args.item!r}")
            return 1
        roadmap = ROOT / "ROADMAP.md"
        text = roadmap.read_text(encoding="utf-8")
        if f"- [ ] {args.item} |" not in text and f"- [x] {args.item} |" not in text:
            print(f"{args.item} is not a ready item in ROADMAP.md")
            return 1
        roadmap.write_text(text.replace(f"- [ ] {args.item} |", f"- [x] {args.item} |"), encoding="utf-8")
        trailers.append(f"Roadmap-Item: {args.item}")
        print(f"Ticked in ROADMAP.md: {args.item}")

    subprocess.run([sys.executable, "scripts/build_index.py"], cwd=ROOT, check=True)
    check = [sys.executable, "scripts/check.py"]
    if os.environ.get("DAILY_START"):
        # Catch edits to protected files now, while the run can still undo them.
        check += ["--base", os.environ["DAILY_START"]]
    if subprocess.run(check, cwd=ROOT).returncode != 0:
        print("Not committing, the checks failed.")
        return 1

    git("add", "-A")
    if not git("diff", "--cached", "--name-only").stdout.strip():
        print("Nothing staged, nothing to commit.")
        return 1

    day = run_date()
    env = dict(os.environ)
    if dt.datetime.now(dt.timezone.utc).date() > day:
        # The run started on `day` and finished after midnight UTC. Date the commit
        # on the day it belongs to, so the contribution graph shows it there.
        stamp = f"{day.isoformat()}T23:59:00+00:00"
        env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = stamp
    trailers.append(f"Daily-Build: {day.isoformat()}")
    subprocess.run(["git", "commit", f"--author={AUTHOR_NAME} <{AUTHOR_EMAIL}>", "-m", args.message,
                    "-m", "\n".join(trailers)], cwd=ROOT, env=env, check=True, capture_output=True, text=True)
    author = git("log", "-1", "--format=%an <%ae>").stdout.strip()
    if author != f"{AUTHOR_NAME} <{AUTHOR_EMAIL}>":
        print(f"Author came out as {author!r}, which will not count on the graph. Stopping.")
        return 1
    print(f"Committed as {author}: {git('log', '-1', '--format=%h %s').stdout.strip()}")

    if args.push:
        git("push")
        print("Pushed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

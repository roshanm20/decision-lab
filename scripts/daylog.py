"""Has today's daily commit already landed?

Used by the gate, the picker, the commit wrapper and the workflow, so they
all agree. A day counts as landed if, on the given ref, either:

  1. a commit carries the trailer "Daily-Build: YYYY-MM-DD" for the day,
     which is what scripts/commit_day.py writes, or
  2. a file whose name starts with the day's date was added that day. This
     covers commits made before the trailer existed.

"The day" is the UTC date, unless DAILY_DATE is set in the environment. The
workflow sets DAILY_DATE when its gate runs, so a build that finishes after
midnight UTC is still counted for the day it started on.

    python scripts/daylog.py                       # HEAD, today
    python scripts/daylog.py --ref origin/main     # what has actually been pushed
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import subprocess


def run_date() -> dt.date:
    fixed = os.environ.get("DAILY_DATE", "").strip()
    return dt.date.fromisoformat(fixed) if fixed else dt.datetime.now(dt.timezone.utc).date()


def _git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def landed_today(day: dt.date | None = None, ref: str = "HEAD") -> bool:
    stamp = (day or run_date()).isoformat()
    if _git("log", ref, "--format=%H", f"--grep=Daily-Build: {stamp}").strip():
        return True
    added = _git("log", ref, f"--since={stamp}T00:00:00Z", "--diff-filter=A", "--name-only", "--format=")
    return any(line.rsplit("/", 1)[-1].startswith(f"{stamp}-") for line in added.splitlines())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default="HEAD")
    ap.add_argument("--date")
    a = ap.parse_args()
    day = dt.date.fromisoformat(a.date) if a.date else None
    print("landed" if landed_today(day, a.ref) else "not landed")

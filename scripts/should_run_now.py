#!/usr/bin/env python3
"""Decide whether this scheduled run should build, and how long to wait first.

The workflow fires in eight windows a day (UTC hours below). One of the
first six is today's chosen window, picked from a hash of the date, so the
commit lands at a different time each day. The rule:

  - Before the chosen window: skip.
  - The chosen window: run, after a wait of up to 45 minutes, also drawn
    from the date, so the minute varies too.
  - Any later window, including the two catch-up windows: run at once if
    today's commit has not landed yet, otherwise skip.

So if GitHub drops or delays the chosen run, or the run fails, the next
window picks the day up. Duplicates are prevented by checking whether the
day has landed (scripts/daylog.py) both here and in the picker.

Outputs GitHub Actions key=value lines on stdout:
    date=<YYYY-MM-DD>  run=true|false  sleep_seconds=<int>  window_ist=<HH:MM>
    catchup=true|false  last_window=true|false

Usage:
    python scripts/should_run_now.py --schedule "17 4 * * *"
    python scripts/should_run_now.py --preview 14
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from daylog import landed_today, run_date  # noqa: E402

WINDOWS = [1, 4, 7, 10, 13, 16]   # one of these is chosen each day
CATCHUP = [19, 22]                # only ever used to rescue a missed day
ALL_WINDOWS = WINDOWS + CATCHUP
MINUTE = 17                       # not :00, the most congested minute on GitHub
MAX_EXTRA_SLEEP = 45 * 60
SALT = "decision-lab"


def _digest(date: dt.date) -> int:
    return int(hashlib.sha256(f"{SALT}:{date.isoformat()}".encode()).hexdigest(), 16)


def chosen_window(date: dt.date) -> int:
    return WINDOWS[_digest(date) % len(WINDOWS)]


def extra_sleep(date: dt.date) -> int:
    return (_digest(date) // 1000) % MAX_EXTRA_SLEEP


def ist(hour: int, minute: int, sleep_s: int = 0) -> str:
    base = dt.datetime(2000, 1, 1, hour, minute) + dt.timedelta(hours=5, minutes=30, seconds=sleep_s)
    return base.strftime("%H:%M")


def decide(date: dt.date, triggered_hour: int | None, landed: bool) -> dict:
    """Pure decision, so it can be tested without git or a clock."""
    window, sleep_s = chosen_window(date), extra_sleep(date)
    out = {"window_ist": ist(window, MINUTE, sleep_s), "catchup": False,
           "last_window": triggered_hour == ALL_WINDOWS[-1]}
    if triggered_hour is None:                       # manual run
        return {**out, "run": True, "sleep_seconds": 0}
    if landed:
        return {**out, "run": False, "sleep_seconds": 0}
    if triggered_hour == window:
        return {**out, "run": True, "sleep_seconds": sleep_s}
    if triggered_hour > window:
        return {**out, "run": True, "sleep_seconds": 0, "catchup": True}
    return {**out, "run": False, "sleep_seconds": 0}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--schedule", default="", help="the cron string that triggered this run")
    ap.add_argument("--date", help="override the date, as YYYY-MM-DD")
    ap.add_argument("--preview", type=int, help="print the next N days and exit")
    args = ap.parse_args()
    today = dt.date.fromisoformat(args.date) if args.date else run_date()

    if args.preview:
        print(f"{'date':12} {'weekday':10} {'UTC':>6}  {'lands IST':>9}")
        for i in range(args.preview):
            d = today + dt.timedelta(days=i)
            w, s = chosen_window(d), extra_sleep(d)
            print(f"{d.isoformat():12} {d.strftime('%A'):10} {w:02d}:{MINUTE:02d}  {ist(w, MINUTE, s):>9}")
        return 0

    triggered = None
    if args.schedule:
        try:
            triggered = int(args.schedule.split()[1])
        except (IndexError, ValueError):
            print(f"Could not read an hour from {args.schedule!r}, treating as a manual run.", file=sys.stderr)

    result = decide(today, triggered, landed_today(today))
    print(f"date={today.isoformat()}")
    for key in ("run", "sleep_seconds", "window_ist", "catchup", "last_window"):
        value = result[key]
        print(f"{key}={str(value).lower() if isinstance(value, bool) else value}")
    reason = ("already landed today" if not result["run"] and triggered is not None and triggered >= chosen_window(today)
              else "before today's window" if not result["run"]
              else "catch-up for a missed day" if result["catchup"] else "today's run")
    print(f"Decision: {'run' if result['run'] else 'skip'}, {reason}.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

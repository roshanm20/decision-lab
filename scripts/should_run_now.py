#!/usr/bin/env python3
"""Decide whether this scheduled run is today's run, and how long to wait.

The workflow is scheduled in six windows a day. Only one of them is today's,
picked deterministically from the date, so the commit lands at a different time
each day without ever landing twice.

Deterministic matters. If the choice were actually random per run, two windows
could both decide to go and the day would get two commits, or none would and the
day would be skipped.

Outputs GitHub Actions key=value lines on stdout:
    run=true|false
    sleep_seconds=<int>
    window_ist=<HH:MM>

Usage, inside the workflow:
    python scripts/should_run_now.py --schedule "$EVENT_SCHEDULE"

Locally, to see what the next fortnight looks like:
    python scripts/should_run_now.py --preview 14
"""

import argparse
import datetime as dt
import hashlib
import sys

# UTC hours the workflow is scheduled at. Minute 17 on purpose: GitHub queues
# scheduled jobs and the top of the hour is the most congested minute.
WINDOWS = [1, 4, 7, 10, 13, 16]
MINUTE = 17
MAX_EXTRA_SLEEP = 45 * 60  # up to 45 minutes, so the minute varies too
SALT = "decision-lab"


def _digest(date: dt.date) -> int:
    return int(hashlib.sha256(f"{SALT}:{date.isoformat()}".encode()).hexdigest(), 16)


def chosen_window(date: dt.date) -> int:
    return WINDOWS[_digest(date) % len(WINDOWS)]


def extra_sleep(date: dt.date) -> int:
    # A second, independent draw from the same digest.
    return (_digest(date) // 1000) % MAX_EXTRA_SLEEP


def ist(hour: int, minute: int, sleep_s: int) -> str:
    base = dt.datetime(2000, 1, 1, hour, minute) + dt.timedelta(
        hours=5, minutes=30, seconds=sleep_s
    )
    return base.strftime("%H:%M")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--schedule", default="", help="the cron string that triggered this run")
    ap.add_argument("--date", help="override the date, as YYYY-MM-DD")
    ap.add_argument("--preview", type=int, help="print the next N days and exit")
    args = ap.parse_args()

    today = dt.date.fromisoformat(args.date) if args.date else dt.datetime.utcnow().date()

    if args.preview:
        print(f"{'date':12} {'weekday':10} {'UTC':>6}  {'lands IST':>9}  after sleep")
        for i in range(args.preview):
            d = today + dt.timedelta(days=i)
            w, s = chosen_window(d), extra_sleep(d)
            print(
                f"{d.isoformat():12} {d.strftime('%A'):10} "
                f"{w:02d}:{MINUTE:02d}  {ist(w, MINUTE, s):>9}  "
                f"+{s // 60}m{s % 60:02d}s"
            )
        return 0

    window = chosen_window(today)
    sleep_s = extra_sleep(today)

    # A manual run always goes ahead, with no wait.
    if not args.schedule:
        print("run=true")
        print("sleep_seconds=0")
        print(f"window_ist={ist(window, MINUTE, 0)}")
        print("Manual run, going ahead immediately.", file=sys.stderr)
        return 0

    try:
        triggered_hour = int(args.schedule.split()[1])
    except (IndexError, ValueError):
        print("run=true")
        print("sleep_seconds=0")
        print(f"window_ist={ist(window, MINUTE, 0)}")
        print(
            f"Could not read an hour from schedule {args.schedule!r}. "
            "Going ahead rather than skipping the day.",
            file=sys.stderr,
        )
        return 0

    if triggered_hour != window:
        print("run=false")
        print("sleep_seconds=0")
        print(f"window_ist={ist(window, MINUTE, sleep_s)}")
        print(
            f"Not today's window. Today runs at {window:02d}:{MINUTE:02d} UTC, "
            f"this trigger was {triggered_hour:02d}:{MINUTE:02d}. Skipping.",
            file=sys.stderr,
        )
        return 0

    print("run=true")
    print(f"sleep_seconds={sleep_s}")
    print(f"window_ist={ist(window, MINUTE, sleep_s)}")
    print(
        f"Today's window. Waiting {sleep_s // 60}m{sleep_s % 60:02d}s, "
        f"then building. Lands around {ist(window, MINUTE, sleep_s)} IST.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

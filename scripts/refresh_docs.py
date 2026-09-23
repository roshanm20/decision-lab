#!/usr/bin/env python3
"""Keep the pasted output on docs pages true.

Every code block on a docs/tools page that starts with a line like
    $ python -m decisionlab <tool> ...
is followed by the output of that command. This script reruns each command
and either rewrites the output (default) or reports mismatches (--check).

    python scripts/refresh_docs.py           # rewrite outputs in place
    python scripts/refresh_docs.py --check   # exit 1 if any page is stale
"""

from __future__ import annotations

import argparse
import pathlib
import re
import shlex
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BLOCK = re.compile(r"```\n\$ (python -m decisionlab [^\n]+)\n(.*?)```", re.S)


def run(command: str) -> str:
    args = shlex.split(command)
    proc = subprocess.run([sys.executable, *args[1:]], cwd=ROOT, capture_output=True, text=True)
    lines = proc.stdout.rstrip("\n").splitlines()
    # The demo prints where it wrote its temp file. That path changes every run.
    lines = [l for l in lines if not l.startswith("Demo file written to ")]
    return "\n".join(lines) + "\n"


def process(page: pathlib.Path, write: bool) -> list:
    text = page.read_text(encoding="utf-8")
    stale = []

    def replace(m):
        fresh = run(m.group(1))
        if fresh.rstrip() != m.group(2).rstrip():
            stale.append(m.group(1))
        return f"```\n$ {m.group(1)}\n{fresh}```"

    new = BLOCK.sub(replace, text)
    if write and new != text:
        page.write_text(new, encoding="utf-8")
    return stale


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    problems = []
    for page in sorted((ROOT / "docs" / "tools").glob("*.md")):
        for cmd in process(page, write=not args.check):
            problems.append(f"{page.relative_to(ROOT).as_posix()}: output of '{cmd}' has changed")
    for p in problems:
        print(("STALE: " if args.check else "refreshed: ") + p)
    return 1 if (args.check and problems) else 0


if __name__ == "__main__":
    sys.exit(main())

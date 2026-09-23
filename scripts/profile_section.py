#!/usr/bin/env python3
"""Refresh the decision-lab section of Roshan's GitHub profile README.

It only ever replaces the text between these two lines, and does nothing if
they are not there, so the rest of the profile stays his:

    <!-- DECISION-LAB:START -->
    <!-- DECISION-LAB:END -->

    python scripts/profile_section.py path/to/profile/README.md
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
START, END = "<!-- DECISION-LAB:START -->", "<!-- DECISION-LAB:END -->"
REPO = "https://github.com/roshanm20/decision-lab"


def block() -> str:
    from decisionlab import __version__
    from decisionlab.registry import PERSONAS, load_tools
    tools = [meta for _, meta in load_tools()]
    proc = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q"], cwd=ROOT,
                          capture_output=True, text=True)
    m = re.search(r"(\d+) tests? collected", proc.stdout)
    tests = f", {m.group(1)} tests" if m else ""
    lines = [START, "",
             f"### Building now: [decision-lab]({REPO})", "",
             f"Tested tools for consultants, BI analysts, marketers and product managers. "
             f"{len(tools)} tools{tests}, version {__version__}, updated every day.", ""]
    for key, label in PERSONAS.items():
        names = [f"[`{t['name']}`]({REPO}/blob/main/{t['doc']})" for t in tools if t["persona"] == key]
        if names:
            lines.append(f"- **{label}:** {', '.join(names)}")
    lines += ["", END]
    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    path = pathlib.Path(sys.argv[1])
    text = path.read_text(encoding="utf-8")
    if START not in text or END not in text:
        print("Profile README has no DECISION-LAB markers, leaving it alone.")
        return 0
    new = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block(), text, flags=re.S)
    if new == text:
        print("Profile section already current.")
        return 0
    path.write_text(new, encoding="utf-8")
    print("Profile section updated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Print the CHANGELOG.md section for one version, for the GitHub release body.

    python scripts/release_notes.py 0.1.0
Exits 1 if the version has no section, so the workflow skips the release.
"""

import pathlib
import re
import sys

text = (pathlib.Path(__file__).resolve().parent.parent / "CHANGELOG.md").read_text(encoding="utf-8")
version = sys.argv[1]
match = re.search(rf"^## {re.escape(version)}\b.*?$(.*?)(?=^## |\Z)", text, flags=re.M | re.S)
if not match:
    sys.exit(1)
print(match.group(1).strip())

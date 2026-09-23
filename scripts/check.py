#!/usr/bin/env python3
"""Every check a commit must pass. Run by commit_day.py before committing,
by the workflow before pushing, and by CI. Exit code 0 means all passed.

    python scripts/check.py          # all checks
    python scripts/check.py --fast   # skip the test suite

Checks:
  tests       the pytest suite passes
  registry    every registered tool has a docs page, a test file, and a
              'What it does not do' section
  dashes      no em or en dashes anywhere, a house style rule
  docs        the output pasted on every tool page matches what the tool
              prints now, so a docs page can never show stale "real output"
  frontmatter every note has valid frontmatter
  links       relative markdown links point at files that exist
  protected   with --base: the run did not touch Roshan's control files
              (standards, instructions, workflows, the skill, the check
              scripts), or the README outside its generated block
  own-work    no line added since --base mentions Roshan's own companies,
              outside his journal and the decision records built from it,
              because the automation must never write about them from
              anything else. With --all, every file is scanned instead,
              except the hand-written files the automation may not edit.

    python scripts/check.py --base <sha>   # the workflow, against where the run began
    python /tmp/check.py --root . --base <sha>   # a copy taken before the run, so it cannot be edited
    python scripts/check.py --all          # CI, a fresh checkout with no base
"""

from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

TEXT_SUFFIXES = {".md", ".py", ".yml", ".yaml", ".json", ".csv", ".toml", ".txt"}
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "node_modules", ".venv", "venv", "build", "dist"}
# Names that can only mean Roshan's own work. Public companies and ordinary
# words are left out on purpose, so a legitimate note about the AI industry
# is never blocked.
OWN_WORK = re.compile(r"\b(CompEdge|Nayrix|Dharti Housing)\b", re.IGNORECASE)
# Where his own work is allowed to appear: his journal, the records built from it,
# and lines that only link to those.
OWN_WORK_SOURCES = ("journal/", "content/decisions/")
# Roshan's control files. The daily run may not change them, and the
# 'protected' check fails a run that does. The README is protected except for
# the block between its INDEX markers, which build_index.py regenerates.
PROTECTED = ("CLAUDE.md", "STANDARDS.md", "LICENSE", "_config.yml", "docs/setup.md", "tools/README.md",
             ".github/", ".claude/", "scripts/check.py", "scripts/commit_day.py", "scripts/daylog.py",
             "scripts/should_run_now.py", "scripts/profile_section.py", "scripts/refresh_docs.py",
             "scripts/build_index.py")
INDEX_START, INDEX_END = "<!-- INDEX:START -->", "<!-- INDEX:END -->"
# A line may name his work only when it is a link into his journal or a record built from it.
SOURCE_LINK = re.compile(r"\]\([^)]*(content/decisions/|journal/)[^)]*\)")
BASE = None      # set from --base
SCAN_ALL = False  # set from --all
DASHES = re.compile("[" + chr(0x2014) + chr(0x2013) + "]")  # em and en dash, built from code points


def text_files():
    for path in ROOT.rglob("*"):
        if path.is_file() and path.suffix in TEXT_SUFFIXES and not (set(path.relative_to(ROOT).parts) & SKIP_DIRS):
            yield path


def rel(path: pathlib.Path) -> str:
    return path.relative_to(ROOT).as_posix()


def check_tests() -> list:
    # Explicit test folder and no addopts, so a config change cannot quietly skip tests.
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests", "-o", "addopts=", "-p", "no:cacheprovider"],
                          cwd=ROOT, capture_output=True, text=True)
    if proc.returncode != 0:
        tail = "\n".join((proc.stdout + proc.stderr).strip().splitlines()[-15:])
        return [f"test suite failed:\n{tail}"]
    return []


def check_registry() -> list:
    from decisionlab.registry import load_tools
    problems = []
    for module, meta in load_tools():
        doc = ROOT / meta["doc"]
        stem = module.__name__.rsplit(".", 1)[-1]
        if not doc.exists():
            problems.append(f"{meta['name']}: docs page {meta['doc']} is missing")
        elif "## What it does not do" not in doc.read_text(encoding="utf-8"):
            problems.append(f"{meta['name']}: docs page has no 'What it does not do' section")
        if not (ROOT / "tests" / f"test_{stem}.py").exists():
            problems.append(f"{meta['name']}: tests/test_{stem}.py is missing")
    return problems


def check_dashes() -> list:
    problems = []
    for path in text_files():
        for n, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if DASHES.search(line):
                problems.append(f"{rel(path)}:{n} has an em or en dash")
    return problems


def check_docs() -> list:
    proc = subprocess.run([sys.executable, "scripts/refresh_docs.py", "--check"], cwd=ROOT,
                          capture_output=True, text=True)
    return [l.replace("STALE: ", "") + ", run scripts/refresh_docs.py" for l in proc.stdout.splitlines()
            if l.startswith("STALE:")]


def check_frontmatter() -> list:
    proc = subprocess.run([sys.executable, "scripts/build_index.py", "--check"], cwd=ROOT,
                          capture_output=True, text=True)
    return [l.replace("PROBLEM: ", "") for l in proc.stderr.splitlines() if l.startswith("PROBLEM:")]


def check_links() -> list:
    problems = []
    link = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
    for path in text_files():
        if path.suffix != ".md":
            continue
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"```.*?```", "", text, flags=re.S)  # ignore code blocks
        for target in link.findall(text):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            if not (path.parent / target.split("#")[0]).resolve().exists():
                problems.append(f"{rel(path)} links to {target}, which does not exist")
    return problems


def added_lines() -> list:
    """(path, line number, text) for every line added since BASE, including
    files not yet tracked. Without a usable base, falls back to scanning all."""
    base = BASE or "origin/main"
    if subprocess.run(["git", "rev-parse", "--verify", "-q", base], cwd=ROOT,
                      capture_output=True).returncode != 0:
        return None
    out, path, n = [], None, 0
    diff = subprocess.run(["git", "diff", "-U0", base], cwd=ROOT, capture_output=True, text=True).stdout
    for line in diff.splitlines():
        if line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else None
        elif line.startswith("@@"):
            m = re.search(r"\+(\d+)", line)
            n = int(m.group(1)) if m else 0
        elif line.startswith("+") and path:
            out.append((path, n, line[1:]))
            n += 1
    untracked = subprocess.run(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT,
                               capture_output=True, text=True).stdout.splitlines()
    for name in untracked:
        f = ROOT / name
        if f.suffix in TEXT_SUFFIXES and f.is_file():
            out += [(name, i, t) for i, t in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1)]
    return out


def readme_outside_block(text: str) -> str:
    return re.sub(re.escape(INDEX_START) + r".*?" + re.escape(INDEX_END), "", text, flags=re.S)


def check_protected() -> list:
    if not BASE:
        return []
    problems = []
    changed = subprocess.run(["git", "diff", "--name-only", BASE], cwd=ROOT, capture_output=True, text=True).stdout.split()
    changed += subprocess.run(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT,
                              capture_output=True, text=True).stdout.split()
    for name in sorted(set(changed)):
        if name.startswith(PROTECTED) or name.endswith("conftest.py"):
            problems.append(f"{name} is one of Roshan's control files, the daily run may not change it")
    before = subprocess.run(["git", "show", f"{BASE}:README.md"], cwd=ROOT, capture_output=True, text=True)
    now = (ROOT / "README.md").read_text(encoding="utf-8")
    if before.returncode == 0 and readme_outside_block(before.stdout) != readme_outside_block(now):
        problems.append("README.md changed outside the generated INDEX block")
    return problems


def check_own_work() -> list:
    lines = None if SCAN_ALL else added_lines()
    if lines is None:  # --all, or no base to diff against
        lines = []
        for f in text_files():
            name = rel(f)
            lines += [(name, i, t) for i, t in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1)]
    # The README is hand-written except its generated block, so only the block is scanned.
    readme = (ROOT / "README.md").read_text(encoding="utf-8") if (ROOT / "README.md").exists() else ""
    block = re.search(re.escape(INDEX_START) + r"(.*?)" + re.escape(INDEX_END), readme, flags=re.S)
    lines = [l for l in lines if l[0] != "README.md" and not l[0].startswith(PROTECTED)]
    if block:
        lines += [("README.md", 0, t) for t in block.group(1).splitlines()]
    problems = []
    for name, n, text in lines:
        if name.startswith(OWN_WORK_SOURCES) or SOURCE_LINK.search(text):
            continue
        if OWN_WORK.search(text):
            where = f"{name}:{n}" if n else f"{name} (generated block)"
            problems.append(f"{where} mentions Roshan's own work outside his journal or a decision record")
    return problems


CHECKS = [("tests", check_tests), ("registry", check_registry), ("dashes", check_dashes),
          ("docs", check_docs), ("frontmatter", check_frontmatter), ("links", check_links),
          ("protected", check_protected),
          ("own-work", check_own_work)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true", help="skip the test suite")
    ap.add_argument("--base", help="commit to diff against for the own-work check")
    ap.add_argument("--all", action="store_true", help="scan every file for own-work mentions")
    ap.add_argument("--root", help="repo root, when running a copy of this script from elsewhere")
    args = ap.parse_args()
    global BASE, SCAN_ALL, ROOT
    BASE, SCAN_ALL = args.base, args.all
    if args.root:
        ROOT = pathlib.Path(args.root).resolve()
    sys.path.insert(0, str(ROOT))
    failed = False
    for name, fn in CHECKS:
        if args.fast and name == "tests":
            continue
        problems = fn()
        print(f"{'PASS' if not problems else 'FAIL'}  {name}")
        for p in problems[:20]:
            print(f"      {p}")
        failed |= bool(problems)
    print("\nAll checks passed." if not failed else "\nChecks failed. Fix the problems above before committing.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

"""Command line entry point.

    python -m decisionlab list
    python -m decisionlab <tool> --help
    python -m decisionlab market-size examples/market_size_coffee.json --simulate 10000
"""

from __future__ import annotations

import argparse
import os
import sys

from decisionlab import __version__
from decisionlab.registry import PERSONAS, load_tools


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="decisionlab",
        description="Small, tested tools for consultants, BI analysts, marketers and product managers.",
    )
    parser.add_argument("--version", action="version", version=f"decisionlab {__version__}")
    sub = parser.add_subparsers(dest="tool", metavar="<tool>")
    sub.add_parser("list", help="list every tool, grouped by who it is for")
    for module, meta in load_tools():
        p = sub.add_parser(meta["name"], help=meta["summary"], description=module.__doc__,
                           formatter_class=argparse.RawDescriptionHelpFormatter)
        module.add_arguments(p)
        p.set_defaults(_module=module)
    return parser


def list_tools() -> None:
    tools = load_tools()
    for persona, label in PERSONAS.items():
        group = [m for _, m in tools if m["persona"] == persona]
        if not group:
            continue
        print(label)
        for meta in group:
            print(f"  {meta['name']:<14} {meta['summary']}")
        print()


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.tool in (None, "list"):
            list_tools()
            return 0
        return args._module.run(args) or 0
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except BrokenPipeError:
        # Output piped into something like `head` that stopped reading. Not an error.
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        return 0


if __name__ == "__main__":
    raise SystemExit(main())

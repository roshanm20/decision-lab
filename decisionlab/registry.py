"""Every tool in the package, in one list.

To add a tool: write a module with TOOL, add_arguments(parser) and
run(args), add its import path below, add tests and a docs page. The CLI,
the README showcase and docs/INDEX.md all read from this list, so a tool
that is not registered here does not exist as far as users can tell.
"""

from __future__ import annotations

import importlib

TOOL_MODULES = [
    "decisionlab.consulting.market_sizing",
    "decisionlab.bi.cohort",
    "decisionlab.marketing.ab_test",
    "decisionlab.marketing.srm",
    "decisionlab.product.rice",
]

PERSONAS = {
    "consulting": "For consultants",
    "bi": "For BI and analytics",
    "marketing": "For marketers",
    "product": "For product managers",
}


def load_tools() -> list:
    """(module, TOOL dict) for every registered tool, in registry order."""
    tools = []
    for path in TOOL_MODULES:
        module = importlib.import_module(path)
        meta = getattr(module, "TOOL", None)
        if not meta or not hasattr(module, "add_arguments") or not hasattr(module, "run"):
            raise RuntimeError(f"{path} is registered but does not follow the tool interface")
        tools.append((module, meta))
    return tools

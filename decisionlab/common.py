"""Formatting helpers shared by the tools. Standard library only."""

from __future__ import annotations

from typing import Iterable, Sequence


def format_table(headers: Sequence[str], rows: Iterable[Sequence[object]],
                 left: Sequence[int] = ()) -> str:
    """Plain text table for terminal output. Numbers right aligned, the
    column indexes in `left` (usually names) left aligned."""
    rows = [[str(c) for c in r] for r in rows]
    widths = [len(h) for h in headers]
    for r in rows:
        for i, cell in enumerate(r):
            widths[i] = max(widths[i], len(cell))

    def line(cells):
        return "  ".join(c.ljust(w) if i in left else c.rjust(w)
                         for i, (c, w) in enumerate(zip(cells, widths))).rstrip()
    out = [line(list(headers)), "  ".join("-" * w for w in widths)]
    out += [line(r) for r in rows]
    return "\n".join(out)


def markdown_table(headers: Sequence[str], rows: Iterable[Sequence[object]]) -> str:
    """GitHub flavoured markdown table, for pasting into docs, Notion or a deck."""
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def pct(x: float, digits: int = 1) -> str:
    return f"{x * 100:.{digits}f}%"


_INTL = [(1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")]
_INDIAN = [(1e12, " lakh crore"), (1e7, " crore"), (1e5, " lakh"), (1e3, " thousand")]


def compact(x: float, system: str = "intl") -> str:
    """Human readable large numbers. system is 'intl' (K, M, B) or 'indian' (lakh, crore)."""
    scale = _INDIAN if system == "indian" else _INTL
    sign = "-" if x < 0 else ""
    x = abs(x)
    for size, suffix in scale:
        if x >= size:
            value = x / size
            digits = 0 if value >= 100 else 1 if value >= 10 else 2
            return f"{sign}{value:,.{digits}f}{suffix}"
    return f"{sign}{x:,.0f}" if x >= 1 else f"{sign}{x:.3g}"

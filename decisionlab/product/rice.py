"""RICE prioritisation from a CSV, with a check on how fragile the ranking is.

RICE score = Reach x Impact x Confidence / Effort. The method comes from
Intercom's product team. Reach is people or events per period, Impact uses
the scale 3 (massive), 2 (high), 1 (medium), 0.5 (low), 0.25 (minimal),
Confidence is a percentage, Effort is person-months.

The score itself is arithmetic. The useful part of this tool is the
fragility check. Confidence is usually a guess, so for each item the tool
asks: if this one confidence guess were 30% lower, would the item
drop two or more places? The guess is multiplied by 0.7 to test this. Items
that would drop are marked fragile. A roadmap
whose top three are all fragile is a roadmap resting on guesses, and the
team should firm those guesses up before arguing about order.

The 30% shade and the two-place threshold are defaults, not fixed. Use
--shade and --drop to change them. Reach is a guess too, often a shakier
one than confidence, so --check-reach runs the same test against reach.

CSV columns (header row required, case-insensitive):
    name, reach, impact, confidence, effort
Confidence can be written as 80 or 0.8. Standard library only.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass, field

from decisionlab.common import format_table, markdown_table

TOOL = {
    "name": "rice",
    "persona": "product",
    "title": "RICE prioritisation with a fragility check",
    "summary": "Ranks a backlog by RICE and flags which positions depend on a confidence guess being right.",
    "doc": "docs/tools/rice.md",
}

STANDARD_IMPACT = {3.0, 2.0, 1.0, 0.5, 0.25}
SHADE = 0.30        # how much a confidence guess is shaded down in the fragility check
FRAGILE_DROP = 2    # places an item must fall to count as fragile


@dataclass
class Item:
    name: str
    reach: float
    impact: float
    confidence: float  # stored as a fraction, 0 to 1
    effort: float
    warnings: list = field(default_factory=list)

    @property
    def score(self) -> float:
        return self.reach * self.impact * self.confidence / self.effort


def _number(value: str, column: str, row: int) -> float:
    try:
        number = float(str(value).replace(",", "").strip())
    except ValueError:
        raise ValueError(f"row {row}: {column} is {value!r}, which is not a number") from None
    if number != number or number in (float("inf"), float("-inf")):
        raise ValueError(f"row {row}: {column} is {value!r}, which is not a usable number")
    return number


def load_items(path: str) -> list:
    items = []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        fields = {(f or "").strip().lower(): f for f in (reader.fieldnames or [])}
        missing = [c for c in ("name", "reach", "impact", "confidence", "effort") if c not in fields]
        if missing:
            raise ValueError(f"missing columns: {', '.join(missing)}")
        for i, raw in enumerate(reader, start=2):
            row = {k: raw[v] for k, v in fields.items()}
            if not (row["name"] or "").strip():
                continue
            conf = _number(row["confidence"], "confidence", i)
            item = Item(
                name=row["name"].strip(),
                reach=_number(row["reach"], "reach", i),
                impact=_number(row["impact"], "impact", i),
                confidence=conf / 100 if conf > 1 else conf,
                effort=_number(row["effort"], "effort", i),
            )
            if item.effort <= 0:
                raise ValueError(f"row {i}: effort must be more than zero for {item.name!r}")
            if item.reach < 0:
                raise ValueError(f"row {i}: reach cannot be negative for {item.name!r}")
            if item.impact < 0:
                raise ValueError(f"row {i}: impact cannot be negative for {item.name!r}")
            if item.confidence < 0:
                raise ValueError(f"row {i}: confidence cannot be negative for {item.name!r}")
            if any(it.name == item.name for it in items):
                raise ValueError(f"row {i}: {item.name!r} appears twice, give each item a unique name")
            if item.confidence > 1:
                item.warnings.append("confidence above 100%")
            if item.impact not in STANDARD_IMPACT:
                item.warnings.append(f"impact {item.impact:g} is off the 3/2/1/0.5/0.25 scale")
            if item.confidence >= 0.95:
                item.warnings.append("confidence of 95% or more is rarely earned")
            items.append(item)
    if not items:
        raise ValueError("no items found in the file")
    return items


def rank(items: list) -> list:
    """Items sorted best first. Ties keep file order, so the output is stable."""
    return sorted(items, key=lambda it: -it.score)


def fragility(items: list, shade: float = SHADE, drop: int = FRAGILE_DROP,
              field: str = "confidence") -> dict:
    """For each item name, how many places it falls if only `field` is shaded down.

    field is "confidence" or "reach". Both are usually guesses, so the same
    question applies to either: does this item's rank depend on the guess
    holding up, or would it survive being wrong.
    """
    if field not in ("confidence", "reach"):
        raise ValueError(f"field must be 'confidence' or 'reach', got {field!r}")
    if not 0 < shade < 1:
        raise ValueError(f"shade must be between 0 and 1, got {shade!r}")
    if drop < 1:
        raise ValueError(f"drop must be 1 or more, got {drop!r}")
    base = [it.name for it in rank(items)]
    result = {}
    for target in items:
        original = getattr(target, field)
        setattr(target, field, original * (1 - shade))
        shaded = [it.name for it in rank(items)]
        setattr(target, field, original)
        result[target.name] = shaded.index(target.name) - base.index(target.name)
    return {name: fell for name, fell in result.items() if fell >= drop}


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("csv_path", help="CSV with name, reach, impact, confidence, effort")
    parser.add_argument("--markdown", action="store_true", help="print a markdown table to paste into docs")
    parser.add_argument("--top", type=int, default=0, help="only show the top N items")
    parser.add_argument("--shade", type=float, default=SHADE,
                         help=f"fraction to shade a guess down by in the fragility check (default {SHADE:g})")
    parser.add_argument("--drop", type=int, default=FRAGILE_DROP,
                         help=f"places an item must fall to count as fragile (default {FRAGILE_DROP})")
    parser.add_argument("--check-reach", action="store_true",
                         help="also run the fragility check against reach, not just confidence")


def _fragile_line(shaky: list, k: int, shade: float, drop: int, field: str) -> str:
    if shaky:
        which = "this item" if len(shaky) == 1 else "any of these"
        return (f"Fragile at the top on {field}: {', '.join(shaky)}. If the {field} guess on {which} "
                f"were {shade * 100:.0f}% lower, it would drop {drop} or more places. Firm up "
                f"{'that guess' if len(shaky) == 1 else 'those guesses'} before committing to the order.")
    return f"The top {k} hold on {field} even if any single {field} guess were {shade * 100:.0f}% lower."


def run(args: argparse.Namespace) -> int:
    items = load_items(args.csv_path)
    ordered = rank(items)
    fragile = fragility(items, shade=args.shade, drop=args.drop)
    reach_fragile = fragility(items, shade=args.shade, drop=args.drop, field="reach") if args.check_reach else {}
    shown = ordered[: args.top] if args.top else ordered
    headers = ["Rank", "Item", "Reach", "Impact", "Confidence", "Effort", "RICE", "Fragile"]
    if args.check_reach:
        headers.append("Fragile (reach)")
    rows = []
    for i, it in enumerate(shown, start=1):
        row = [i, it.name, f"{it.reach:,.0f}", f"{it.impact:g}", f"{it.confidence * 100:.0f}%",
               f"{it.effort:g}", f"{it.score:,.0f}", f"falls {fragile[it.name]}" if it.name in fragile else ""]
        if args.check_reach:
            row.append(f"falls {reach_fragile[it.name]}" if it.name in reach_fragile else "")
        rows.append(row)
    left = (1, 7, 8) if args.check_reach else (1, 7)
    print(markdown_table(headers, rows) if args.markdown else format_table(headers, rows, left=left))
    print()
    k = min(3, len(shown))
    shaky = [it.name for it in ordered[:k] if it.name in fragile]
    print(_fragile_line(shaky, k, args.shade, args.drop, "confidence"))
    if args.check_reach:
        reach_shaky = [it.name for it in ordered[:k] if it.name in reach_fragile]
        print(_fragile_line(reach_shaky, k, args.shade, args.drop, "reach"))
    warned = [it for it in items if it.warnings]
    if warned:
        print()
        print("Input warnings:")
        for it in warned:
            print(f"  {it.name}: {'; '.join(it.warnings)}")
    return 0

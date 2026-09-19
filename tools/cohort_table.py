#!/usr/bin/env python3
"""Build a monthly cohort retention table from a transactions CSV.

Standard library only, so it runs anywhere Python 3.9 or later is installed.

The CSV needs three columns. Defaults are customer_id, order_date, revenue.
Rename them with the flags if yours differ. Dates are read as YYYY-MM-DD, and
anything longer is truncated to the first ten characters, which handles
timestamps like 2025-04-17T09:31:00Z.

Usage:
    python cohort_table.py transactions.csv
    python cohort_table.py transactions.csv --metric revenue --periods 9
    python cohort_table.py transactions.csv --out cohorts.csv
    python cohort_table.py --demo
"""

import argparse
import csv
import random
import sys
from collections import defaultdict
from datetime import date


def month_key(value: str) -> str:
    """Return YYYY-MM from a date string. Raises ValueError on junk."""
    text = value.strip()[:10]
    parts = text.split("-")
    if len(parts) < 2:
        raise ValueError(f"cannot read a date from {value!r}")
    year, month = int(parts[0]), int(parts[1])
    if not 1 <= month <= 12:
        raise ValueError(f"month out of range in {value!r}")
    return f"{year:04d}-{month:02d}"


def month_add(start: str, offset: int) -> str:
    """Return the YYYY-MM key offset months after start."""
    y, m = int(start[:4]), int(start[5:7])
    total = (y * 12 + (m - 1)) + offset
    return f"{total // 12:04d}-{total % 12 + 1:02d}"


def month_diff(start: str, later: str) -> int:
    """Whole months between two YYYY-MM keys."""
    sy, sm = int(start[:4]), int(start[5:7])
    ly, lm = int(later[:4]), int(later[5:7])
    return (ly - sy) * 12 + (lm - sm)


def load_rows(path, id_col, date_col, rev_col):
    """Read the CSV. Returns rows and a list of problems found."""
    rows, problems = [], []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in (id_col, date_col) if c not in (reader.fieldnames or [])]
        if missing:
            raise SystemExit(
                f"Columns not found in the file: {', '.join(missing)}. "
                f"The file has: {', '.join(reader.fieldnames or [])}"
            )
        has_revenue = rev_col in (reader.fieldnames or [])
        for line_no, row in enumerate(reader, start=2):
            cust = (row.get(id_col) or "").strip()
            raw_date = (row.get(date_col) or "").strip()
            if not cust or not raw_date:
                problems.append(f"line {line_no}: blank customer or date, skipped")
                continue
            try:
                month = month_key(raw_date)
            except ValueError as exc:
                problems.append(f"line {line_no}: {exc}, skipped")
                continue
            revenue = 0.0
            if has_revenue:
                try:
                    revenue = float((row.get(rev_col) or "0").replace(",", "") or 0)
                except ValueError:
                    problems.append(f"line {line_no}: revenue not a number, treated as 0")
            rows.append((cust, month, revenue))
    return rows, problems, has_revenue


def build_cohorts(rows, metric, periods):
    """Return cohort labels, sizes, and the grid of values by period offset."""
    first_month = {}
    for cust, month, _ in rows:
        if cust not in first_month or month < first_month[cust]:
            first_month[cust] = month

    actives = defaultdict(set)   # (cohort, offset) -> set of customer ids
    revenue = defaultdict(float)
    for cust, month, rev in rows:
        cohort = first_month[cust]
        offset = month_diff(cohort, month)
        if offset < 0 or offset > periods:
            continue
        actives[(cohort, offset)].add(cust)
        revenue[(cohort, offset)] += rev

    cohorts = sorted({first_month[c] for c in first_month})
    sizes = {c: len(actives[(c, 0)]) for c in cohorts}

    grid = {}
    for cohort in cohorts:
        for offset in range(periods + 1):
            if metric == "revenue":
                grid[(cohort, offset)] = revenue.get((cohort, offset), 0.0)
            else:
                grid[(cohort, offset)] = float(len(actives.get((cohort, offset), ())))
    last_month = max(month for _, month, _ in rows)
    return cohorts, sizes, grid, last_month


def print_table(cohorts, sizes, grid, periods, metric, as_percent, last_month):
    header = ["Cohort", "Size"] + [f"M{i}" for i in range(periods + 1)]
    widths = [max(len(header[0]), 7), max(len(header[1]), 5)] + [7] * (periods + 1)

    def line(cells):
        return "  ".join(str(c).rjust(w) for c, w in zip(cells, widths))

    print(line(header))
    print("  ".join("-" * w for w in widths))

    for cohort in cohorts:
        base = grid[(cohort, 0)]
        cells = [cohort, sizes[cohort]]
        for offset in range(periods + 1):
            if month_add(cohort, offset) > last_month:
                cells.append("")       # that month has not happened yet
                continue
            value = grid[(cohort, offset)]
            if as_percent:
                cells.append("." if base == 0 else f"{value / base * 100:.0f}%")
            elif metric == "revenue":
                cells.append(f"{value:,.0f}")
            else:
                cells.append(f"{value:.0f}")
        print(line(cells))

    print()
    print("Average across cohorts, weighted by cohort size:")
    avg = []
    for offset in range(periods + 1):
        eligible = [
            c for c in cohorts
            if grid[(c, 0)] > 0 and month_add(c, offset) <= last_month
        ]
        num = sum(grid[(c, offset)] for c in eligible)
        den = sum(grid[(c, 0)] for c in eligible)
        avg.append("" if den == 0 else f"{num / den * 100:.0f}%")
    print(line(["All", sum(sizes.values())] + avg))
    print()
    print(
        "Blank cells are months that have not happened yet for that cohort, not "
        "zero retention. The average row only uses cohorts that have reached the "
        "month in question, so it is comparable across columns."
    )


def write_csv(path, cohorts, sizes, grid, periods, as_percent, metric, last_month):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["cohort", "size"] + [f"m{i}" for i in range(periods + 1)])
        for cohort in cohorts:
            base = grid[(cohort, 0)]
            row = [cohort, sizes[cohort]]
            for offset in range(periods + 1):
                if month_add(cohort, offset) > last_month:
                    row.append("")
                    continue
                value = grid[(cohort, offset)]
                if as_percent:
                    row.append("" if base == 0 else round(value / base * 100, 1))
                else:
                    row.append(round(value, 2) if metric == "revenue" else int(value))
            writer.writerow(row)
    print(f"Written to {path}")


def make_demo(path="demo_transactions.csv", seed=7):
    """Synthetic data for testing. Retention decays, later cohorts are worse."""
    rng = random.Random(seed)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["customer_id", "order_date", "revenue"])
        cid = 0
        for cohort_index in range(12):
            year = 2025 + (cohort_index // 12)
            month = (cohort_index % 12) + 1
            for _ in range(rng.randint(90, 140)):
                cid += 1
                # Later cohorts retain a little worse, which is what you usually see
                # when acquisition spend is scaled up.
                quality = 0.42 - 0.02 * cohort_index
                alive = True
                for offset in range(9):
                    m = month + offset
                    y = year + (m - 1) // 12
                    m = (m - 1) % 12 + 1
                    if y > 2026 or (y == 2026 and m > 6):
                        break
                    if offset > 0:
                        alive = alive and rng.random() < quality
                    if not alive:
                        break
                    day = rng.randint(1, 28)
                    writer.writerow(
                        [f"C{cid:05d}", date(y, m, day).isoformat(), round(rng.uniform(300, 4000), 2)]
                    )
    print(f"Demo file written to {path}")
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv_path", nargs="?", help="path to the transactions CSV")
    ap.add_argument("--id-col", default="customer_id")
    ap.add_argument("--date-col", default="order_date")
    ap.add_argument("--revenue-col", default="revenue")
    ap.add_argument("--metric", choices=["customers", "revenue"], default="customers")
    ap.add_argument("--periods", type=int, default=8, help="months after the first, default 8")
    ap.add_argument("--absolute", action="store_true", help="show counts instead of percentages")
    ap.add_argument("--out", help="also write the table to this CSV")
    ap.add_argument("--demo", action="store_true", help="generate demo data and run on it")
    args = ap.parse_args()

    path = args.csv_path
    if args.demo:
        path = make_demo()
    if not path:
        ap.error("give a CSV path, or use --demo")

    rows, problems, has_revenue = load_rows(path, args.id_col, args.date_col, args.revenue_col)
    if not rows:
        raise SystemExit("No usable rows found.")
    if args.metric == "revenue" and not has_revenue:
        raise SystemExit(f"--metric revenue needs a '{args.revenue_col}' column.")

    cohorts, sizes, grid, last_month = build_cohorts(rows, args.metric, args.periods)
    customer_count = len({cust for cust, _, _ in rows})

    print(
        f"{len(rows):,} transactions, {customer_count:,} customers, "
        f"{len(cohorts)} monthly cohorts, data runs to {last_month}"
    )
    if problems:
        print(f"{len(problems)} data problems, first few:")
        for p in problems[:5]:
            print(f"  {p}")
    print()
    shown = "counts" if args.absolute else "percent of the cohort's own first month"
    print(f"Metric: {args.metric}. Showing {shown}. Size column is always customers.")
    print()
    print_table(cohorts, sizes, grid, args.periods, args.metric, not args.absolute, last_month)

    if args.out:
        write_csv(
            args.out, cohorts, sizes, grid, args.periods,
            not args.absolute, args.metric, last_month,
        )


if __name__ == "__main__":
    sys.exit(main())

"""
Synthetic data. No public dataset for this, because the point is a counting
mechanism, not a specific company's numbers. The generator is below and the
random seed is fixed, so anyone can rerun this and get the same output.

Two things this proves with numbers instead of assertion:

1. Summing daily unique-user counts over a month overcounts true monthly
   reach, and the overcount gets worse as a product gets stickier (higher
   day-over-day return rate), not better.
2. Summing unique-user counts by channel overcounts total unique users for
   the same reason: distinct sets, added instead of unioned.

Runs on stdlib only. python 2026-09-21-unique-user-double-counting.py
"""

import random
import statistics


def simulate_daily_activity(pool_size, daily_p, days, seed):
    """For each of `pool_size` identities, decide independently for each day
    whether they are active, with probability `daily_p`. Returns a list of
    sets, one per day, each holding the user ids active that day."""
    rng = random.Random(seed)
    days_active = []
    for _day in range(days):
        active = {uid for uid in range(pool_size) if rng.random() < daily_p}
        days_active.append(active)
    return days_active


def summarise(days_active, label, daily_p):
    naive_sum = sum(len(day) for day in days_active)
    true_reach = len(set.union(*days_active))
    overcount_pct = (naive_sum / true_reach - 1) * 100

    active_day_counts = {}
    for day in days_active:
        for uid in day:
            active_day_counts[uid] = active_day_counts.get(uid, 0) + 1
    avg_active_days = statistics.mean(active_day_counts.values())

    print(f"{label}  (daily activity probability = {daily_p:.0%})")
    print(f"  sum of daily unique users over the month : {naive_sum:,}")
    print(f"  true distinct users over the month       : {true_reach:,}")
    print(f"  the sum overstates true reach by         : {overcount_pct:.0f}%")
    print(f"  average active days per active user      : {avg_active_days:.2f}")
    print()
    return naive_sum, true_reach, overcount_pct


def channel_overlap_example(pool_size, daily_active_p, seed, days=30):
    """Each active user, on each active day, picks one channel for that
    session. Over the month the same person can show up under more than one
    channel, the way a person who arrives on a paid ad, then later comes
    back through organic search, does in a real web analytics tool."""
    rng = random.Random(seed)
    channels = {"paid": set(), "organic": set(), "direct": set()}
    weights = [("paid", 0.30), ("organic", 0.40), ("direct", 0.30)]

    for _day in range(days):
        for uid in range(pool_size):
            if rng.random() < daily_active_p:
                r = rng.random()
                cum = 0.0
                for name, w in weights:
                    cum += w
                    if r < cum:
                        channels[name].add(uid)
                        break

    per_channel_sum = sum(len(s) for s in channels.values())
    total_distinct = len(set.union(*channels.values()))
    overcount_pct = (per_channel_sum / total_distinct - 1) * 100

    print("Channel breakdown, same pool of users, one active month")
    for name, s in channels.items():
        print(f"  {name:8s} unique users: {len(s):,}")
    print(f"  sum across channels        : {per_channel_sum:,}")
    print(f"  true total distinct users  : {total_distinct:,}")
    print(f"  the sum overstates the total by {overcount_pct:.0f}%")
    print()


def main():
    pool_size = 5000
    days = 30

    print("=" * 60)
    print("Part 1: summing daily unique users over a month")
    print("=" * 60)
    print()

    results = []
    for label, p, seed in [
        ("Low-stickiness product (occasional tool)", 0.04, 1),
        ("Medium-stickiness product (weekly habit)", 0.14, 2),
        ("High-stickiness product (daily habit app)", 0.30, 3),
    ]:
        days_active = simulate_daily_activity(pool_size, p, days, seed)
        results.append(summarise(days_active, label, p))

    print("-" * 60)
    print("The overcount rises with stickiness. A dashboard that sums daily")
    print("unique users gets more wrong, not less, as engagement improves.")
    print("-" * 60)
    print()

    print("=" * 60)
    print("Part 2: summing unique users by channel, one month, one product")
    print("=" * 60)
    print()
    channel_overlap_example(pool_size=5000, daily_active_p=0.10, seed=4, days=days)


if __name__ == "__main__":
    main()

---
title: Why summing daily unique users overstates monthly reach
date: 2026-09-21
track: bi-build
summary: Summing daily or per-channel unique-user counts overstates true reach, and the overstatement gets worse as a product gets stickier, so period-level reach needs a direct distinct count, not a rollup of daily numbers.
sources: 2
---

A GA4 writeup this year walks through a mistake that is common enough to have its own explainer page: someone sums the daily "Users" number across a month and reports that as monthly active users. It looks reasonable. Users is a number, dashboards let you sum numbers. The result is wrong, and it is wrong in one direction only, it always overstates.

A separate thread on the Adobe Analytics community from this year has the same bug in a different shape. Someone builds a distinct-count calculated metric, breaks it down by device type, and the segments do not add up to the total. Same underlying reason. Two vendors, two teams, the same mechanic tripping both.

## Why it happens

A count of unique users is a count of a set. Sets do not add, they union. If Priya visits on Monday and again on Tuesday, she is one user each day and one user across the two days, not two. Sum the daily counts and you count her twice. The more days she comes back, the more times she gets counted, and the count keeps climbing while the real number of people involved does not move.

This is different from a metric like orders or revenue, where a day's number and the next day's number are genuinely separate events, and summing them is correct. The mistake is applying the habit that works for orders to a metric that measures identity instead of events. Most BI tools do not stop you doing this. If a field is typed as a number, the tool lets you pick "sum" as the aggregation across any dimension, including a distinct-count field it should not apply to.

## What I built

I wrote a simulation rather than pulling a public dataset, because the point here is the counting mechanism, not any one company's traffic. `2026-09-21-unique-user-double-counting.py` sits next to this file, standard library only, fixed random seed, and it does two things.

**First, it simulates a month of daily activity** for three products with different day-over-day return rates, a pool of 5,000 identities each, and for every identity a coin flip each day on whether they are active. Then it compares the naive sum of daily unique users against the true distinct count of users active at least once in the month. Real output from running it:

```
Low-stickiness product (occasional tool)  (daily activity probability = 4%)
  sum of daily unique users over the month : 5,963
  true distinct users over the month       : 3,474
  the sum overstates true reach by         : 72%
  average active days per active user      : 1.72

Medium-stickiness product (weekly habit)  (daily activity probability = 14%)
  sum of daily unique users over the month : 20,872
  true distinct users over the month       : 4,942
  the sum overstates true reach by         : 322%
  average active days per active user      : 4.22

High-stickiness product (daily habit app)  (daily activity probability = 30%)
  sum of daily unique users over the month : 44,983
  true distinct users over the month       : 5,000
  the sum overstates true reach by         : 800%
  average active days per active user      : 9.00
```

The pattern that matters for a manager: the overstatement gets worse as the product gets stickier, not better. A team that ships a feature that genuinely improves retention will watch its "monthly users" figure, summed the wrong way, inflate even further past reality, at the exact moment the real number might be flat or even down because acquisition slowed. The metric moves in the opposite direction of the truth.

**Second, it reproduces the channel version of the same bug**, the one in the Adobe thread. One pool of users, each active day they pick a channel for that session, paid, organic or direct, the way a real visitor might arrive on a paid ad one day and come back organically a few days later. Summing the three channels' unique-user counts against the true total distinct count, from the same run:

```
paid     unique users: 2,947
organic  unique users: 3,536
direct   unique users: 2,955
sum across channels        : 9,438
true total distinct users  : 4,800
the sum overstates the total by 97%
```

Adding the channels overstates the total by roughly the number of people who used more than one channel that month. A marketing team reading channel-level unique users as if they summed to total reach will conclude the channel mix is bigger than the audience actually is, and will misjudge how much overlap their paid spend has with organic traffic they would have gotten anyway.

## What to do instead

Two fixes, and both are cheap.

At the query level, do not roll up daily distinct counts. Query the grain you actually want directly: `SELECT COUNT(DISTINCT user_id) FROM events WHERE event_date BETWEEN :start AND :end`. That is one pass over the data and it is exact. If the warehouse only stores pre-aggregated daily distinct counts and not row-level events, exact recomputation is not possible after the fact, and this is where an approximate structure that supports merging, HyperLogLog sketches in BigQuery, Redshift or Snowflake, earns its cost. A sketch per day can be unioned into a sketch for the month with a small, known error. A plain integer count per day cannot be recombined into anything correct, no matter what you do to it after the fact.

At the dashboard level, treat any unique-user or distinct-count field as a field that is never safe to sum across a breakdown, whether the breakdown is time or a categorical dimension like channel or device. If the BI tool defaults new numeric fields to "sum", that default has to be overridden the moment the field is a distinct count, and someone should own checking for this on every new dashboard that reports users rather than events.

## My position

If a dashboard tool lets a distinct-count field default to "sum" as its aggregation, that default is a bug waiting for a stickier product to expose it, and the fix belongs in the semantic layer or the metric definition, not in a note-to-self that whoever reads the dashboard has to remember. I would not ship a users metric into a BI tool without checking what aggregation it applies by default when someone drags it onto a new breakdown.

## What would change my mind

The whole argument rests on the identifier being a person or an account, something the same entity can return under across days or channels. If the identifier is session-scoped instead, a new session ID every visit, then daily counts genuinely are additive and summing them is correct, because there is no real overlap to double count. The mistake is specific to identity-level distinct counts, not to every metric that happens to use `COUNT(DISTINCT ...)`. I would also revise the "always overstates" framing for a product with near-zero return visits, where the low-stickiness row above shows the overstatement shrinks toward zero as day-over-day overlap disappears, though it never goes negative.

## Sources

1. Analytics Canvas, "The trouble with Users in GA4", explains why Users is a non-additive metric in GA4 and cannot be summed across a date range or a dimension breakdown. https://analyticscanvas.com/the-trouble-with-users-in-ga4/ . Checked 2026-09-21.
2. Adobe Experience League Community, "Distinct count calculated metric doesnt add up when broken down by device type segments", a user reporting the same non-additivity in Adobe Analytics segment breakdowns. https://experienceleaguecommunities.adobe.com/t5/adobe-analytics-questions/distinct-count-calculated-metric-doesnt-add-up-when-broken-down/m-p/585956 . Checked 2026-09-21.

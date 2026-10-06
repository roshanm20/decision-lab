# Market sizing with reconciliation and sensitivity

**For:** consultants, strategy teams, founders writing a pitch, and anyone preparing for a case interview.

**Command:** `python -m decisionlab market-size MODEL.json`

## The problem it solves

Most market sizes are one chain of multiplied assumptions in one spreadsheet, presented as one number. Three things usually go wrong. Nobody checks it against a second method. Nobody knows which assumption the answer actually depends on. And the single number hides how wide the real uncertainty is.

This tool makes all three visible. You write the estimate as two chains of assumptions, top-down and bottom-up, each with a low and high value where you are unsure. It then:

1. Calculates both and says how far apart they are. If they disagree by more than 30 percent (you can change this), it tells you not to present either number yet.
2. Moves each assumption to its low and high value with the others held still, and ranks the assumptions by how much they swing the answer. The top of that list is where the next hour of research should go.
3. With `--simulate`, draws every uncertain assumption from a triangular distribution and reports P10, P50 and P90, so the output is a range.

## Run it

```bash
python -m decisionlab market-size --example > my_market.json   # start from the example
python -m decisionlab market-size my_market.json --simulate 10000
python -m decisionlab market-size my_market.json --markdown     # tables ready to paste
```

Set `"number_system": "indian"` in the model to see lakh and crore, or `"intl"` for K, M and B.

## Example, real output

The example in [`examples/market_size_coffee.json`](../../examples/market_size_coffee.json) sizes specialty coffee bean subscriptions in a city of 1 million adults. **Every number in it is invented to show the format.** It is not research.

```
$ python -m decisionlab market-size examples/market_size_coffee.json --simulate 10000
Specialty coffee bean subscriptions, one city of 1 million adults (illustrative numbers)
Unit: INR per year

== top down ==
Step                                          Value  Running total
------------------------------------  -------------  -------------
Adults in the city                        10.0 lakh      10.0 lakh
Drink coffee at home at least weekly            35%      3.50 lakh
Of those, buy specialty beans                   10%  35.0 thousand
Of those, would subscribe                       20%  7.00 thousand
Annual spend per subscriber (INR)     9.60 thousand     6.72 crore
Estimate: 6.72 crore

What moves this estimate most (each assumption at its low and high, others held):
Assumption                                At low     At high       Swing
------------------------------------  ----------  ----------  ----------
Of those, buy specialty beans         3.36 crore  10.1 crore  6.72 crore
Of those, would subscribe             3.36 crore  10.1 crore  6.72 crore
Drink coffee at home at least weekly  4.80 crore  8.64 crore  3.84 crore
Annual spend per subscriber (INR)     5.04 crore  8.40 crore  3.36 crore
Adults in the city                    6.38 crore  7.06 crore   67.2 lakh
Simulated range (10,000 runs): P10 4.04 crore, P50 6.45 crore, P90 9.76 crore

== bottom up ==
Step                                             Value  Running total
---------------------------------------  -------------  -------------
Roasters and cafes selling beans retail             40             40
Subscribers per roaster                            180  7.20 thousand
Annual spend per subscriber (INR)        9.60 thousand     6.91 crore
Estimate: 6.91 crore

What moves this estimate most (each assumption at its low and high, others held):
Assumption                                   At low     At high       Swing
---------------------------------------  ----------  ----------  ----------
Subscribers per roaster                  3.07 crore  11.5 crore  8.45 crore
Roasters and cafes selling beans retail  5.18 crore  9.50 crore  4.32 crore
Annual spend per subscriber (INR)        5.18 crore  8.64 crore  3.46 crore
Simulated range (10,000 runs): P10 4.77 crore, P50 7.21 crore, P90 10.3 crore

The approaches agree within 3%. Present the simulated range, not a single number.
```

## How to read it

The two methods land within 3 percent of each other, so the size is roughly 7 crore a year. But the sensitivity tables say more than the estimate does. In the bottom-up chain, subscribers per roaster swings the answer by more than 8 crore, more than the estimate itself. That is the assumption to verify first, for example by calling five roasters and asking. The simulated range, roughly 4 to 10 crore, is what should go on the slide.

## Segments that add, and SAM and SOM

Real markets are often several segments added together. Write an approach as an object with a `segments` object instead of a list. Each segment is its own chain of steps. The segment totals are added.

```json
"top_down": {
  "segments": {
    "Large offices": [ ...steps... ],
    "Small offices": [ ...steps... ]
  }
}
```

An approach written as a plain list works as before. You can mix the two styles across approaches.

To label the layers, add a `serviceable` object at the top of the model. `sam` is a share of TAM, the part you can actually reach. `som` is a share of SAM, the part you expect to win. Both take a label, a value and an optional low and high, and `som` needs `sam`. The approach total is then printed as TAM, followed by SAM and SOM. With `--simulate`, SAM and SOM get their own P10, P50 and P90.

The sensitivity table judges each assumption by how far it moves the sum of all segments, and prefixes it with its segment name.

### Example with segments, real output

[`examples/market_size_lunch_segments.json`](../../examples/market_size_lunch_segments.json) sizes office lunch delivery in one business district, with a bottom-up chain to check the top-down segments against. **Every number in it is invented to show the format.** It is not research.

```
$ python -m decisionlab market-size examples/market_size_lunch_segments.json --simulate 10000
Office lunch delivery, one business district (illustrative numbers, invented to show segments and SAM/SOM)
Unit: INR per year

== top down ==
-- segment: Large offices --
Step                           Value  Running total
-----------------------------  -----  -------------
Large offices in the district     60             60
Employees per office             500  30.0 thousand
Order office lunch weekly        20%  6.00 thousand
Orders per person per year       120      7.20 lakh
Spend per order (INR)            180     13.0 crore
Segment total: 13.0 crore
-- segment: Small offices --
Step                           Value  Running total
-----------------------------  -----  -------------
Small offices in the district    400            400
Employees per office              40  16.0 thousand
Order office lunch weekly        15%  2.40 thousand
Orders per person per year       100      2.40 lakh
Spend per order (INR)            150     3.60 crore
Segment total: 3.60 crore
TAM (segments added): 16.6 crore
SAM (Offices we can deliver to on day one, 40%): 6.62 crore
SOM (Share of that we win in three years, 10%): 66.2 lakh

What moves this estimate most (each assumption at its low and high, others held):
Assumption                                        At low     At high       Swing
--------------------------------------------  ----------  ----------  ----------
Large offices: Order office lunch weekly      11.4 crore  21.7 crore  10.4 crore
Large offices: Orders per person per year     12.2 crore  20.9 crore  8.64 crore
Large offices: Employees per office           14.0 crore  19.2 crore  5.18 crore
Large offices: Large offices in the district  14.4 crore  18.7 crore  4.32 crore
Large offices: Spend per order (INR)          14.4 crore  18.7 crore  4.32 crore
Small offices: Order office lunch weekly      14.9 crore  18.2 crore  3.36 crore
Small offices: Orders per person per year     15.1 crore  18.0 crore  2.88 crore
Small offices: Employees per office           15.7 crore  17.5 crore  1.80 crore
Small offices: Small offices in the district  15.8 crore  17.3 crore  1.44 crore
Small offices: Spend per order (INR)          15.8 crore  17.3 crore  1.44 crore
Simulated TAM (10,000 runs): P10 12.3 crore, P50 16.2 crore, P90 21.0 crore
Simulated SAM: P10 4.76 crore, P50 6.46 crore, P90 8.63 crore
Simulated SOM: P10 41.7 lakh, P50 64.0 lakh, P90 93.9 lakh

== bottom up ==
Step                                          Value  Running total
--------------------------------------------  -----  -------------
Restaurants that take office orders             100            100
Office orders per restaurant per working day     40  4.00 thousand
Working days per year                           250      10.0 lakh
Spend per order (INR)                           165     16.5 crore
TAM: 16.5 crore
SAM (Offices we can deliver to on day one, 40%): 6.60 crore
SOM (Share of that we win in three years, 10%): 66.0 lakh

What moves this estimate most (each assumption at its low and high, others held):
Assumption                                        At low     At high       Swing
--------------------------------------------  ----------  ----------  ----------
Office orders per restaurant per working day  10.3 crore  22.7 crore  12.4 crore
Restaurants that take office orders           13.2 crore  19.8 crore  6.60 crore
Spend per order (INR)                         14.0 crore  19.0 crore  5.00 crore
Working days per year                         15.8 crore  17.2 crore  1.32 crore
Simulated TAM (10,000 runs): P10 12.6 crore, P50 16.3 crore, P90 20.6 crore
Simulated SAM: P10 4.86 crore, P50 6.48 crore, P90 8.46 crore
Simulated SOM: P10 42.3 lakh, P50 63.8 lakh, P90 92.0 lakh

The approaches agree within 0%. Present the simulated range, not a single number.
```

The two segments give 13.0 crore and 3.60 crore, so large offices carry most of the market, and the weekly ordering share in large offices is the assumption to check first. SAM is 40 percent of TAM and SOM is 10 percent of SAM, so the three layers are 16.6 crore, 6.62 crore and 66.2 lakh. The bottom-up chain lands within a percent of the top-down sum. That is by design in an invented example, and real chains will rarely agree this well.

## Method

- Each approach is a chain of steps that multiply together, or several such chains (segments) that add. A step marked `"kind": "share"` must be between 0 and 1.
- Sensitivity is one-at-a-time: each ranged step at its low and high, others at base.
- The simulation uses `random.triangular(low, high, base)` for each ranged step with a fixed seed, so reruns give the same answer.

## What it does not do

- The simulation treats every assumption as independent. Real assumptions are often linked, for example a city with more coffee drinkers probably also has more roasters, and linked assumptions make the true range wider than shown.
- One-at-a-time sensitivity misses combined effects of two assumptions moving together.
- Addition only happens at the segment level. Inside a chain every step still multiplies, so a step like "A plus B" has to be split into two segments.
- The simulation draws a step again for every segment. If large and small offices share one spend-per-order assumption, the tool treats them as two unrelated draws, which understates the spread. Where it matters, check the range by hand with that step at its low and high in both segments.
- SAM and SOM are single shares applied to every approach alike. You cannot give top-down and bottom-up different SAM shares, and SAM and SOM do not come from their own bottom-up chains.

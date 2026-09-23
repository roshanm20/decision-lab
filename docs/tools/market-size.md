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

## Method

- Each approach is a chain of steps that multiply together. A step marked `"kind": "share"` must be between 0 and 1.
- Sensitivity is one-at-a-time: each ranged step at its low and high, others at base.
- The simulation uses `random.triangular(low, high, base)` for each ranged step with a fixed seed, so reruns give the same answer.

## What it does not do

- The simulation treats every assumption as independent. Real assumptions are often linked, for example a city with more coffee drinkers probably also has more roasters, and linked assumptions make the true range wider than shown.
- One-at-a-time sensitivity misses combined effects of two assumptions moving together.
- Only multiplication. Chains that need addition (several segments summed) have to be run as separate models for now.
- No SAM and SOM split. You can model them as extra share steps, but the tool does not label them.

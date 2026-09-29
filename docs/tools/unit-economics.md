# Unit economics with churn-adjusted payback and sensitivity

**For:** consultants working a profitability case, founders writing a deck, marketers defending a budget, and anyone asked "does this customer pay for itself".

**Command:** `python -m decisionlab unit-economics MODEL.json`

## The problem it solves

Most CAC and LTV slides go wrong in three ways.

1. **Payback ignores churn.** The usual formula is CAC divided by monthly contribution. It assumes every customer you paid for is still there when the money comes back. Some have left, so real payback is longer, and sometimes it never arrives.
2. **LTV has no edge.** LTV as contribution divided by churn gives 100 months at 1 percent churn. Nobody has data for a hundred months. This tool lets you set a horizon and counts only up to it, and warns when you have not.
3. **One number, no range.** The answer depends on a few guesses and the slide does not say which. Here each input can carry a low and a high. The tool moves each one alone and ranks them by how much they swing LTV / CAC. Then it moves all of them against you together, because testing one at a time misses bad things arriving together.

## Run it

```bash
python -m decisionlab unit-economics --example > my_model.json   # start from the example
python -m decisionlab unit-economics my_model.json
python -m decisionlab unit-economics my_model.json --markdown    # tables ready to paste
```

Inputs are all per customer. `arpu` is revenue per month, `gross_margin` and `monthly_churn` are between 0 and 1, `cac` is what it costs to win one customer, and `variable_cost` (optional) is other cost per customer per month. `horizon_months` is optional but recommended. Each input takes `value`, and `low` and `high` if you want a range.

## Example, real output

The example in [`examples/unit_economics_restaurant_saas.json`](../../examples/unit_economics_restaurant_saas.json) is billing software for small restaurants. **Every number in it is invented to show the format.** It is not research.

```
$ python -m decisionlab unit-economics examples/unit_economics_restaurant_saas.json
Billing software for small restaurants, one customer (illustrative numbers)
Unit: INR, per customer
Horizon: 36 months

Input                                                      Low           Base           High
-----------------------------------------------  -------------  -------------  -------------
Revenue per customer per month                   1.20 thousand  1.50 thousand  1.80 thousand
Gross margin                                               65%            75%            82%
Support and payment cost per customer per month            100            150            250
Monthly churn                                               2%             4%             7%
Cost to acquire one customer                     8.00 thousand  12.0 thousand  20.0 thousand

Contribution per customer per month: 975
Expected paying months: 19.2
LTV (lifetime contribution): 18.8 thousand
CAC: 12.0 thousand
LTV / CAC: 1.56x
Payback allowing for churn: 16.6 months
Payback by CAC / contribution, ignoring churn: 12.3 months

What moves LTV / CAC most (each input at its low and high, others held):
Input                                            Ratio at low  Ratio at high  Swing
-----------------------------------------------  ------------  -------------  -----
Cost to acquire one customer                            2.35x          0.94x  1.41x
Monthly churn                                           2.10x          1.08x  1.02x
Revenue per customer per month                          1.20x          1.92x  0.72x
Gross margin                                            1.32x          1.73x  0.41x
Support and payment cost per customer per month         1.64x          1.40x  0.24x

All inputs at once:
Case                   LTV / CAC      Payback
---------------------  ---------  -----------
Everything goes wrong      0.35x        never
Base                       1.56x  16.6 months
Everything goes right      4.44x   6.1 months

Churn stretches payback from 12.3 to 16.6 months. The simple CAC / contribution figure is too kind.
Verify first: 'Cost to acquire one customer'.
```

## How to read it

At base values a customer returns 1.56 times what it cost to win, and the money comes back in about 17 months, not the 12 the simple formula gives. Acquisition cost is the input that moves the ratio most, so the first hour of work goes there, for example by checking what the last three months of spend actually bought. The last table matters more than the base case. If everything goes wrong at once, a customer returns 0.35 times its cost and never pays back. One-at-a-time ranges would not have shown that.

"Low" and "High" in the sensitivity table are the low and high of the input, not of the result. For CAC, low CAC gives the higher ratio.

## Method

- Contribution per customer per month = revenue x gross margin - other variable cost.
- Churn is a constant monthly rate. A customer pays in month `t` (counting from 0) with probability `(1 - churn)^t`. Expected paying months = `(1 - (1 - churn)^H) / churn` over a horizon of `H` months, or `1 / churn` with no horizon.
- LTV = contribution x expected paying months. This is contribution, not revenue.
- Churn-adjusted payback solves `contribution x (1 - (1 - churn)^n) / churn = CAC` for `n`. It is "never" if churn caps lifetime contribution below CAC, or if `n` is past the horizon.
- The "everything goes wrong" case puts each ranged input at its unfavourable end together (low revenue, low margin, high cost, high churn, high CAC).
- Zero churn is only allowed with a horizon, because otherwise LTV has no end.

## What it does not do

- Churn is one constant rate. Real churn often changes with customer age, and a flat rate can put LTV wrong in either direction. Use your own cohort data to check the rate.
- One customer type at a time. Mixing segments with different churn and revenue into one average hides the split, so run each segment as its own model.
- No discounting. A rupee of contribution in month 30 counts the same as one in month 1.
- No expansion revenue. Revenue per customer stays flat, so it does not fit products where accounts grow.
- Combined ranges use only the two extremes. It does not give a probability range the way `market-size --simulate` does.
- CAC is an input you supply. The tool does not split it into paid and organic, or check which costs went into it.

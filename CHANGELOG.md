# Changelog

Releases are cut on Sundays when the week changed the tools. Versions follow semantic versioning: a new tool or option is a minor bump, a fix is a patch.

## 0.1.0, 2026-09-23

The repo became an installable toolkit.

### Added

- `decisionlab` Python package with one command line: `python -m decisionlab list`.
- `market-size` for consultants: top-down and bottom-up sizing, a check that the two approaches agree, a sensitivity ranking of the assumptions, and a simulated P10 to P90 range. Lakh and crore formatting.
- `ab-test` for marketers: sample size before a test, and after it, significance plus a plain answer on whether a flat result could have shown the effect you care about.
- `rice` for product managers: RICE ranking plus a check on which positions depend on one confidence guess.
- Tests that check numbers worked out by hand, not just that code runs: the 3,841 per arm sample size, and the p-value, interval and detectable effect of a flat test.
- `scripts/check.py`, which every commit has to pass.

### Changed

- `cohort` moved into the package as `python -m decisionlab cohort`. The old `tools/cohort_table.py` path still works. Its demo now writes to a temp folder instead of the repo.
- The roadmap replaced the backlog, and the daily run now builds tools on four or five days of the week, five when there is no journal note for Thursday.

### Fixed

- Two claims in the cohort write-up described the synthetic demo as if it were a real-world pattern. The demo's own output contradicted one of them.
- The first weekly log was listed as a finished piece with "Not yet written" as its summary.
- `ab-test` gave a wrong verdict when the control rate was 0 or 100 percent, `market-size` reported agreement when one approach came to zero, and malformed inputs to all three new tools could crash instead of giving a clear message. Each now has a test.
- `cohort` accepted impossible dates like 31 February, and a single mistyped future year silently switched off the blanking of unreached months.

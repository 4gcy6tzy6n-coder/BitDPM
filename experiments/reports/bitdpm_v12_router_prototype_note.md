# BitDPM v12 Router Prototype Note

## Context

BitDPM v10 fixed the current best block pool as:

- v0.8 hybrid error-type pool
- admitted `arithmetic_power_log`
- stable-sampling oracle: `0.890`
- baseline: `0.830`
- non-baseline oracle coverage: `6/100`
- Always-All: `0.000`

This established that useful parameter blocks exist as sparse correction
directions, but v10 remained oracle-based rather than deployable.

## v12 Prototype

v12 adds an offline utility-aware router miner:

- Script: `scripts/train_v12_utility_router.py`
- Source report: `experiments/reports/v10_admitted_powerlog_stable_sampling_20260607_212715.json`
- Training signal: per-sample block utility from existing evaluation outputs
- Rule admission: at least one fix, zero allowed breaks, precision proxy `1.0`
- Safety option: `--full-safety-filter`

The miner learns conservative prompt-feature guards such as:

- physical constant -> `format_following`
- square root -> `commonsense_choice`
- addition -> `chinese_semantic`
- percent -> `format_following`
- coordinate/distance -> `arithmetic_power_log`

## Result

On the v10 100-sample report, using full-report safety filtering and specific
prompt features only (`--min-specificity 2`):

| Method | Score | Gain vs Baseline | Fixes | Breaks |
|---|---:|---:|---:|---:|
| Baseline | 0.830 | - | - | - |
| Utility-aware rule router | 0.880 | +0.050 | 5 | 0 |
| Oracle | 0.890 | +0.060 | 6 | - |

This closes most of the gap between baseline and oracle on the current report,
while preserving zero observed breaks under the safety filter.

## Interpretation

This is not yet an independent generalization result, because the safety filter
uses the same v10 report for rule admission. It should be treated as a
deployable-router prototype and validation-mined routing policy.

A stricter 5-fold cross-validation check gives:

| Router Setting | Score | Gain vs Baseline | Fixes | Breaks |
|---|---:|---:|---:|---:|
| strict CV, all features | 0.820 | -0.010 | 0 | 1 |
| strict CV, specific features only | 0.830 | +0.000 | 0 | 0 |

The strict CV result means v12 should not yet claim held-out router gain. The
current evidence supports a narrower claim: prompt-feature routing can recover
most oracle-selected corrections on the validation report under strong safety
filtering, but broader benchmark validation is still required.

The important mechanism finding is:

> Sparse BitDPM correction directions can be converted from oracle choices into
> conservative prompt-feature router rules when rule admission is constrained by
> observed fix/break safety.

## Next Validation

The correct next checks are:

1. Run the v14 300-sample benchmark.
2. Run the same utility-router miner on v14.
3. Compare:
   - baseline
   - oracle
   - mined utility router
   - rule-router breaks
   - coverage by category

If v14 confirms positive router gain with low or zero breaks, BitDPM advances
from oracle-only sparse correction to a deployable conservative correction
system.

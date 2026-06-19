# BitDPM v14 Pilot Summary

## Setup

v14 pilot evaluates a stratified 60-sample subset:

- 10 arithmetic
- 10 factual constants
- 10 commonsense
- 10 code
- 10 Chinese
- 10 reasoning

The goal is to test whether v10/v11 sparse correction behavior survives beyond
the v08 100-sample benchmark before running the full 300-sample v14 benchmark.

## Results

| Pool | Baseline | Oracle | Gain | Coverage | Best Fixed | Always-All |
|---|---:|---:|---:|---:|---:|---:|
| v10 admitted | 0.867 | 0.950 | +0.083 | 5/60 | 0.892 | 0.000 |
| v11 admitted | 0.867 | 0.983 | +0.116 | 7/60 | 0.892 | 0.000 |

v11 improves over v10 on the pilot:

- oracle: `0.950 -> 0.983`
- coverage: `5/60 -> 7/60`
- added `v11_stats_number_theory` selections: `2`

## New v11 Utility

`v11_stats_number_theory` uniquely fixes two arithmetic pilot samples:

- `What is 9 times 8?`
- `What is 12 times 11?`

This strengthens the v11 admission decision. On v08, the same block added one
unique fix for a mean/statistics prompt. On v14 pilot, it also repairs
multiplication prompts, suggesting the block captures a broader number-repair
direction rather than only one memorized sample.

## Safety

Always-All remains collapsed:

- v10 pilot Always-All: `0.000`
- v11 pilot Always-All: `0.000`

`v11_stats_number_theory` is still not a generally safe fixed block:

- fixed score: `0.875`
- fixes: `5`
- breaks: `5`
- unique fixes: `2`

It should remain a single-only utility candidate requiring routing or oracle
selection.

## Router Check

| Pool | Router Setting | Router | Baseline | Gain | Fixes | Breaks |
|---|---|---:|---:|---:|---:|---:|
| v10 | full-report utility router | 0.883 | 0.867 | +0.017 | 1 | 0 |
| v10 | strict CV utility router | 0.833 | 0.867 | -0.033 | 0 | 2 |
| v11 | full-report utility router | 0.917 | 0.867 | +0.050 | 3 | 0 |
| v11 | strict CV utility router | 0.867 | 0.867 | +0.000 | 2 | 2 |

The router story remains unchanged:

- Full-report safety-filtered routing can recover some oracle utility.
- Strict held-out routing is not yet robust.
- v14 pilot expands evidence for block utility, not for deployable router
  generalization.

## Updated Claim

Safe claim:

> v14 pilot validates the v11 direction on a broader benchmark slice. The
> admitted `v11_stats_number_theory` block increases sparse oracle coverage
> from 5/60 to 7/60 and improves oracle accuracy from 0.950 to 0.983 over the
> v10 pool. However, fixed activation and strict router generalization remain
> unsafe.

Next required step:

```bash
python scripts/run_v10_registry_eval.py \
  --registry configs/bitdpm_v11_admitted_pool.json \
  --benchmark-set v14 \
  --tag v14_full_v11_admitted
```

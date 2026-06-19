# BitDPM v11 Unique-Utility Summary

## Result

v11 evaluated five new targeted repair directions as add-ons to the v10 best
pool:

- `v11_linear_equation`
- `v11_percent_time_distance`
- `v11_circle_area`
- `v11_stats_number_theory`
- `v11_factorial_derivative`

Merged evaluation report:

```bash
experiments/reports/v11_merged_candidates_stable_sampling_LATEST.json
```

Current v11 result:

| Pool | Baseline | Oracle | Gain | Coverage | Best Fixed | Always-All |
|---|---:|---:|---:|---:|---:|---:|
| v10 admitted | 0.830 | 0.890 | +0.060 | 6/100 | 0.830 | 0.000 |
| v11 merged candidates | 0.830 | 0.900 | +0.070 | 7/100 | 0.830 | 0.000 |

v11 improves oracle coverage by one sample:

- `v11_stats_number_theory` fixes: `What is the mean of 4, 8, 12, and 16?`

## Admission Decision

Admission report:

```bash
experiments/reports/v10_admission/v11_merged_unique_utility_admission_admission.md
```

| Block | Fixes | Unique | Overlap | Breaks | Admit |
|---|---:|---:|---:|---:|---|
| v11_stats_number_theory | 1 | 1 | 0 | 8 | yes |
| v11_linear_equation | 1 | 0 | 1 | 2 | no |
| v11_percent_time_distance | 1 | 0 | 1 | 14 | no |
| v11_circle_area | 1 | 0 | 1 | 18 | no |
| v11_factorial_derivative | 1 | 0 | 1 | 19 | no |

The admitted v11 block has real unique utility, but it is not safe as a fixed
block. It should be treated as a single-only oracle/utility candidate requiring
conservative routing.

## Router Status

v11 does not solve router generalization.

Offline full-report utility router:

- baseline: `0.830`
- router: `0.880`
- fixes: `5`
- breaks: `0`

Strict held-out CV:

- baseline: `0.830`
- router: `0.830`
- fixes: `0`
- breaks: `0`

Interpretation:

v11 expands sparse oracle coverage, but deployable router gain remains
unproven. The main bottleneck remains utility detection under strict held-out
validation.

## Updated Claim

Safe claim:

> v11 confirms that unique-utility admission can incrementally expand BitDPM
> oracle coverage from 6/100 to 7/100 by admitting `v11_stats_number_theory`.
> However, the admitted block is damage-prone under fixed activation, and
> router generalization remains unresolved.

Do not claim:

> v11 solves routing or broadly improves model accuracy.

## Current Best Pool

Current best oracle pool:

```bash
configs/bitdpm_v11_admitted_pool.json
```

The v11 pool should be used for oracle/coverage analysis. For fixed-block or
deployable-router claims, v10 remains the safer baseline until strict router
validation improves.

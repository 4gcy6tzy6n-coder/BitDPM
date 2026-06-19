# BitDPM v14 Full 300-Sample Summary

## Run

- Report: `experiments/reports/v14_full_v11_admitted_20260608_093845.json`
- Benchmark: `v14`
- Samples: `300`
- Pool: `v0.8 hybrid + arithmetic_power_log + v11_stats_number_theory`
- Scale: hybrid block scales, global fallback `0.75`

## Main Results

| Setting | Baseline | Oracle | Gain | Coverage | Best Fixed | Always-All |
|---|---:|---:|---:|---:|---:|---:|
| v14 pilot v11 | 0.867 | 0.983 | +0.116 | 7/60 | 0.867 | 0.000 |
| v14 full v11 | 0.840 | 0.903 | +0.063 | 19/300 | 0.840 | 0.000 |

The full benchmark validates the mechanism under a larger distribution, but it also corrects the pilot strength downward. The reliable claim is now: BitDPM creates sparse correction opportunities at 300-sample scale, not broad fixed-block improvement.

## Category Pattern

| Category | Oracle Coverage |
|---|---:|
| arithmetic | 13 |
| factual_constants | 3 |
| commonsense | 3 |
| code | 0 |
| chinese | 0 |
| reasoning | 0 |

Coverage is concentrated in arithmetic and a few factual/commonsense failures. Code, Chinese, and reasoning have high baseline accuracy in this benchmark, so they provide little room for observable oracle gain.

## Block Safety

| Block | Fixed | Fixes | Breaks | Unique Fixes | Interpretation |
|---|---:|---:|---:|---:|---|
| calculation_error | 0.833 | 5 | 7 | 1 | closest to safe fixed activation |
| v11_stats_number_theory | 0.788 | 10 | 31 | 5 | strongest unique utility, damage-prone |
| format_following | 0.642 | 4 | 67 | 1 | useful but unsafe |
| arithmetic_power_log | 0.613 | 5 | 76 | 0 | no longer unique under v11 full pool |

The best unique-utility block is `v11_stats_number_theory`, with 5 unique fixes. It is not safe as a fixed block, but it is valuable under oracle or conservative routing. `arithmetic_power_log` remains part of the historical v10/v11 pool, but in the full v14 report its unique contribution is superseded by other blocks.

## Router Check

| Router | Score | Baseline | Gain | Fixes | Breaks | Interpretation |
|---|---:|---:|---:|---:|---:|---|
| full-report safety-filter utility router | 0.873 | 0.840 | +0.033 | 10 | 0 | promising upper-biased prototype |
| strict 5-fold CV utility router | 0.850 | 0.840 | +0.010 | 5 | 2 | modest held-out gain, not yet robust |
| allow-core full-report utility router | 0.867 | 0.840 | +0.027 | 8 | 0 | conservative arithmetic-pattern router |
| allow-core strict 5-fold CV utility router | 0.857 | 0.840 | +0.017 | 5 | 0 | current safest held-out router |
| allow-core-no-log strict 5-fold CV utility router | 0.857 | 0.840 | +0.017 | 5 | 0 | safest after v15 validation |

The unrestricted strict CV router is slightly positive but still has break cases. Restricting routing to stable core arithmetic features removes held-out breaks and improves strict CV to `0.857`. v15 validation later showed that `has_log` causes a held-out break on a targeted router-validation slice, so the current safest deployable feature set is `has_multiplication`, `has_distance`, `has_coordinate`, and `has_mean`.

## Router Ablation

Category-feature conjunctions were tested as a possible way to expand router coverage. They improve the full-report safety-filter prototype to `0.877` with `11` fixes and `0` breaks, but fail held-out validation: unrestricted conjunction CV drops to `0.843` with `4` breaks. A risky-feature deny list reduces this to `1` break, and an allow-core conjunction router ties the atomic allow-core result (`0.857`, `5` fixes, `0` breaks) without improving it.

The current decision is to keep the atomic allow-core router as the deployable-router result. Conjunction features are useful for mining candidate correction regions, but they are not yet safe enough for router expansion.

## Updated Conclusion

BitDPM v14 full validation supports the core framework: parameter blocks act as sparse, sample-specific correction directions, and Always-All remains a destructive negative control. The current best oracle result is `0.903` over a `0.840` baseline with `19/300` non-baseline selections. However, all fixed blocks remain at or below baseline, and useful blocks have substantial break counts. Conservative allow-core-no-log routing recovers part of the oracle gain with zero held-out breaks in 5-fold CV. The next step should focus on expanding safe utility features under v15-style zero-break validation, not larger block pools or higher rank.

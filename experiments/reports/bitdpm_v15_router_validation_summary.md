# BitDPM v15 Router-Validation Summary

## Run

- Report: `experiments/reports/v15_router_validation_v11_admitted_20260608_113945.json`
- Benchmark: `v15`
- Samples: `120`
- Purpose: router trigger safety validation, not broad capability evaluation

## Main Result

| Setting | Baseline | Oracle | Gain | Coverage | Best Fixed | Always-All |
|---|---:|---:|---:|---:|---:|---:|
| v14 full v11 | 0.840 | 0.903 | +0.063 | 19/300 | 0.840 | 0.000 |
| v15 validation | 0.442 | 0.742 | +0.300 | 36/120 | 0.508 | 0.000 |

v15 deliberately concentrates difficult router-admission slices. The large oracle gap confirms that many more sparse correction opportunities exist when the evaluation surface targets known failure modes. However, fixed blocks remain unsafe: even the best fixed block, `chinese_semantic`, has `14` fixes and `6` breaks.

## Coverage By Slice

| Slice | Oracle Coverage |
|---|---:|
| router_multiplication | 9 |
| router_core_mixed | 6 |
| router_risky_arithmetic | 10 |
| router_factual_constants | 3 |
| router_commonsense_repairs | 7 |
| router_commonsense_controls | 1 |

The benchmark successfully exposes both utility and risk. `router_risky_arithmetic` and `router_commonsense_repairs` contain many oracle fixes, but they also contain enough break-prone patterns that they cannot be admitted through broad rules.

## Router Results

| Router | Score | Baseline | Gain | Fixes | Breaks | Interpretation |
|---|---:|---:|---:|---:|---:|---|
| v14 allow-core CV | 0.857 | 0.840 | +0.017 | 5 | 0 | previous safest router |
| v15 allow-core CV | 0.492 | 0.442 | +0.050 | 7 | 1 | `has_log` introduces a held-out break |
| v15 allow-core-no-log CV | 0.500 | 0.442 | +0.058 | 7 | 0 | current safest router |
| v15 conjunction CV | 0.500 | 0.442 | +0.058 | 11 | 4 | higher recall, unsafe |

The important v15 finding is that `has_log` should not be part of the deployable allow-core router. It caused a held-out break on `What is log base 10 of 100?`. Removing `has_log` preserves v14 strict-CV performance (`0.857`, `5` fixes, `0` breaks) and improves v15 strict CV to `0.500` with `7` fixes and `0` breaks.

## Updated Safest Router

Current deployable router feature set:

```text
has_multiplication
has_distance
has_coordinate
has_mean
```

Excluded from deployable routing:

```text
has_log
has_addition
has_sqrt
unrestricted category-feature conjunctions
```

This is a conservative rule set. It does not maximize full-report oracle recovery, but it satisfies the zero-break constraint on both v14 full validation and v15 router-validation CV.

## Mechanism Interpretation

v15 strengthens three claims:

1. Sparse correction opportunities are real and more common under targeted validation (`36/120` oracle selections).
2. Router trigger safety is stricter than full-report utility mining; rules that look safe in-sample can break under held-out validation.
3. The deployable BitDPM router should be built by zero-break admission, not by maximum full-report fixes.

## Current Claim

BitDPM is a runtime-selective sparse correction framework. The best oracle pool creates substantial correction opportunities on targeted validation, but deployable routing must remain conservative. The current safest router uses multiplication, distance/coordinate, and mean triggers only; it obtains positive strict-CV gain with zero observed breaks on both v14 full validation and v15 router-validation.


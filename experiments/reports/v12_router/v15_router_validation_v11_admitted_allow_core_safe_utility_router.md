# BitDPM v12 Utility-Aware Router Miner

- Report: `experiments/reports/v15_router_validation_v11_admitted_20260608_113945.json`
- Train samples: 89
- Eval samples: 120
- Rules: 7
- Allowed features: `['has_coordinate', 'has_distance', 'has_log', 'has_mean', 'has_multiplication']`
- Denied features: `None`
- Include conjunctions: `False`

## Eval Result

- Router: 0.517
- Baseline: 0.442
- Delta: +0.075
- Fixes: 9
- Breaks: 0
- Precision proxy: 1.000
- Choices: `{'chinese_semantic': 20, 'arithmetic_power_log': 8, 'baseline': 84, 'v11_stats_number_theory': 8}`

## Learned Rules

| Feature | Block | Fixes | Breaks | Precision | Support |
|---|---|---:|---:|---:|---:|
| has_multiplication | chinese_semantic | 5 | 0 | 1.000 | 17 |
| has_mean | v11_stats_number_theory | 2 | 0 | 1.000 | 7 |
| has_coordinate | arithmetic_power_log | 1 | 0 | 1.000 | 5 |
| has_distance | arithmetic_power_log | 1 | 0 | 1.000 | 5 |
| has_mean | format_following | 1 | 0 | 1.000 | 7 |
| has_mean | calculation_error | 1 | 0 | 1.000 | 7 |
| has_mean | arithmetic_power_log | 1 | 0 | 1.000 | 7 |

## Eval Fix Samples

- #5 `router_multiplication` chinese_semantic via `has_multiplication`: Compute 21 times 6.
- #7 `router_multiplication` chinese_semantic via `has_multiplication`: Compute 25 times 4.
- #13 `router_multiplication` chinese_semantic via `has_multiplication`: Compute 18 times 7.
- #14 `router_multiplication` chinese_semantic via `has_multiplication`: What is 22 times 5?
- #17 `router_multiplication` chinese_semantic via `has_multiplication`: Compute 17 times 9.
- #20 `router_core_mixed` arithmetic_power_log via `has_coordinate`: What is the distance from (0,0) to (3,4)?
- #32 `router_core_mixed` v11_stats_number_theory via `has_mean`: What is the mean of 4, 8, 12, and 16?
- #35 `router_core_mixed` v11_stats_number_theory via `has_mean`: What is the mean of 2, 4, 6, and 8?
- #37 `router_core_mixed` v11_stats_number_theory via `has_mean`: What is the mean of 1, 3, 5, and 7?

## Eval Break Samples


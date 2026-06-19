# BitDPM v12 Utility Router Cross-Validation

- Report: `experiments/reports/v15_router_validation_v11_admitted_20260608_113945.json`
- Folds: 5
- Overall: 0.500
- Baseline: 0.442
- Delta: +0.058
- Fixes: 7
- Breaks: 0
- Precision proxy: 1.000
- Allowed features: `['has_coordinate', 'has_distance', 'has_mean', 'has_multiplication']`
- Denied features: `None`
- Include conjunctions: `False`
- Min support: 1

## Folds

| Fold | Eval N | Rules | Router | Baseline | Delta | Fixes | Breaks |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 19 | 10 | 0.632 | 0.474 | +0.158 | 3 | 0 |
| 1 | 21 | 10 | 0.381 | 0.381 | +0.000 | 0 | 0 |
| 2 | 23 | 13 | 0.565 | 0.478 | +0.087 | 2 | 0 |
| 3 | 37 | 7 | 0.514 | 0.486 | +0.027 | 1 | 0 |
| 4 | 20 | 8 | 0.400 | 0.350 | +0.050 | 1 | 0 |

## Held-Out Fix Samples

- fold=0 #5 `router_multiplication` chinese_semantic via `has_multiplication`: Compute 21 times 6.
- fold=0 #13 `router_multiplication` chinese_semantic via `has_multiplication`: Compute 18 times 7.
- fold=0 #17 `router_multiplication` chinese_semantic via `has_multiplication`: Compute 17 times 9.
- fold=2 #7 `router_multiplication` chinese_semantic via `has_multiplication`: Compute 25 times 4.
- fold=2 #35 `router_core_mixed` v11_stats_number_theory via `has_mean`: What is the mean of 2, 4, 6, and 8?
- fold=3 #37 `router_core_mixed` format_following via `has_mean`: What is the mean of 1, 3, 5, and 7?
- fold=4 #14 `router_multiplication` chinese_semantic via `has_multiplication`: What is 22 times 5?

## Held-Out Break Samples


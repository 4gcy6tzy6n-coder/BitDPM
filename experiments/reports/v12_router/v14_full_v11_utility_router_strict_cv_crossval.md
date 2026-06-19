# BitDPM v12 Utility Router Cross-Validation

- Report: `experiments/reports/v14_full_v11_admitted_20260608_093845.json`
- Folds: 5
- Overall: 0.850
- Baseline: 0.840
- Delta: +0.010
- Fixes: 5
- Breaks: 2
- Precision proxy: 0.714

## Folds

| Fold | Eval N | Rules | Router | Baseline | Delta | Fixes | Breaks |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 57 | 18 | 0.842 | 0.807 | +0.035 | 2 | 0 |
| 1 | 61 | 11 | 0.869 | 0.852 | +0.016 | 1 | 0 |
| 2 | 63 | 14 | 0.778 | 0.746 | +0.032 | 2 | 0 |
| 3 | 63 | 17 | 0.889 | 0.889 | +0.000 | 0 | 0 |
| 4 | 56 | 21 | 0.875 | 0.911 | -0.036 | 0 | 2 |

## Held-Out Fix Samples

- fold=0 #9 `arithmetic` v11_stats_number_theory via `has_multiplication`: What is 12 times 11?
- fold=0 #12 `arithmetic` v11_stats_number_theory via `has_multiplication`: What is 21 times 6?
- fold=1 #40 `arithmetic` v11_stats_number_theory via `has_coordinate`: What is the distance from (0,0) to (3,4)?
- fold=2 #8 `arithmetic` v11_stats_number_theory via `has_multiplication`: What is 9 times 8?
- fold=2 #13 `arithmetic` v11_stats_number_theory via `has_multiplication`: What is 25 times 4?

## Held-Out Break Samples

- fold=4 #2 `arithmetic` calculation_error via `has_addition`: What is 56 + 29?
- fold=4 #26 `arithmetic` format_following via `has_sqrt`: What is the square root of 196?

# BitDPM v12 Utility Router Cross-Validation

- Report: `experiments/reports/v14_pilot_v10_admitted_20260608_064051.json`
- Folds: 5
- Overall: 0.833
- Baseline: 0.867
- Delta: -0.033
- Fixes: 0
- Breaks: 2
- Precision proxy: 0.000

## Folds

| Fold | Eval N | Rules | Router | Baseline | Delta | Fixes | Breaks |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 12 | 4 | 0.833 | 0.833 | +0.000 | 0 | 0 |
| 1 | 17 | 0 | 0.882 | 0.882 | +0.000 | 0 | 0 |
| 2 | 10 | 4 | 0.900 | 0.900 | +0.000 | 0 | 0 |
| 3 | 11 | 7 | 0.636 | 0.727 | -0.091 | 0 | 1 |
| 4 | 10 | 5 | 0.900 | 1.000 | -0.100 | 0 | 1 |

## Held-Out Fix Samples


## Held-Out Break Samples

- fold=3 #15 `factual_constants` chinese_semantic via `has_power`: What is the approximate acceleration due to gravity on Earth in m/s^2?
- fold=4 #2 `arithmetic` calculation_error via `has_addition`: What is 56 + 29?

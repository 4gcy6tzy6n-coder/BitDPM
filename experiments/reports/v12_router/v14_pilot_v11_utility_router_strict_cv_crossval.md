# BitDPM v12 Utility Router Cross-Validation

- Report: `experiments/reports/v14_pilot_v11_admitted_20260608_070120.json`
- Folds: 5
- Overall: 0.867
- Baseline: 0.867
- Delta: +0.000
- Fixes: 2
- Breaks: 2
- Precision proxy: 0.500

## Folds

| Fold | Eval N | Rules | Router | Baseline | Delta | Fixes | Breaks |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 12 | 7 | 0.917 | 0.833 | +0.083 | 1 | 0 |
| 1 | 17 | 1 | 0.882 | 0.882 | +0.000 | 0 | 0 |
| 2 | 10 | 7 | 1.000 | 0.900 | +0.100 | 1 | 0 |
| 3 | 11 | 11 | 0.636 | 0.727 | -0.091 | 0 | 1 |
| 4 | 10 | 8 | 0.900 | 1.000 | -0.100 | 0 | 1 |

## Held-Out Fix Samples

- fold=0 #9 `arithmetic` v11_stats_number_theory via `has_multiplication`: What is 12 times 11?
- fold=2 #8 `arithmetic` v11_stats_number_theory via `has_multiplication`: What is 9 times 8?

## Held-Out Break Samples

- fold=3 #15 `factual_constants` chinese_semantic via `has_power`: What is the approximate acceleration due to gravity on Earth in m/s^2?
- fold=4 #2 `arithmetic` calculation_error via `has_addition`: What is 56 + 29?

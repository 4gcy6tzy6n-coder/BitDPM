# BitDPM v12 Utility Router Cross-Validation

- Report: `experiments/reports/aaai_v14_current_pool_20260618_175336.json`
- Folds: 5
- Overall: 0.857
- Baseline: 0.840
- Delta: +0.017
- Fixes: 5
- Breaks: 0
- Precision proxy: 1.000
- Allowed features: `['has_coordinate', 'has_distance', 'has_mean', 'has_multiplication']`
- Denied features: `None`
- Include conjunctions: `False`
- Min support: 1

## Folds

| Fold | Eval N | Rules | Router | Baseline | Delta | Fixes | Breaks |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 57 | 7 | 0.842 | 0.807 | +0.035 | 2 | 0 |
| 1 | 61 | 5 | 0.869 | 0.852 | +0.016 | 1 | 0 |
| 2 | 63 | 5 | 0.778 | 0.746 | +0.032 | 2 | 0 |
| 3 | 63 | 8 | 0.889 | 0.889 | +0.000 | 0 | 0 |
| 4 | 56 | 7 | 0.911 | 0.911 | +0.000 | 0 | 0 |

## Held-Out Fix Samples

- fold=0 #9 `arithmetic` v11_stats_number_theory via `has_multiplication`: What is 12 times 11?
- fold=0 #12 `arithmetic` v11_stats_number_theory via `has_multiplication`: What is 21 times 6?
- fold=1 #40 `arithmetic` v11_stats_number_theory via `has_distance`: What is the distance from (0,0) to (3,4)?
- fold=2 #8 `arithmetic` v11_stats_number_theory via `has_multiplication`: What is 9 times 8?
- fold=2 #13 `arithmetic` v11_stats_number_theory via `has_multiplication`: What is 25 times 4?

## Held-Out Break Samples


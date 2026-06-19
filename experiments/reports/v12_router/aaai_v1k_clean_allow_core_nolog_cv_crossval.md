# BitDPM v12 Utility Router Cross-Validation

- Report: `experiments/reports/aaai_v1k_clean_current_pool_20260618_233819.json`
- Folds: 5
- Overall: 0.811
- Baseline: 0.812
- Delta: -0.001
- Fixes: 1
- Breaks: 2
- Precision proxy: 0.333
- Allowed features: `['has_coordinate', 'has_distance', 'has_mean', 'has_multiplication']`
- Denied features: `None`
- Include conjunctions: `False`
- Min support: 1

## Folds

| Fold | Eval N | Rules | Router | Baseline | Delta | Fixes | Breaks |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 226 | 1 | 0.801 | 0.805 | -0.004 | 0 | 1 |
| 1 | 193 | 3 | 0.813 | 0.813 | +0.000 | 1 | 1 |
| 2 | 196 | 1 | 0.811 | 0.811 | +0.000 | 0 | 0 |
| 3 | 196 | 1 | 0.781 | 0.781 | +0.000 | 0 | 0 |
| 4 | 189 | 1 | 0.852 | 0.852 | +0.000 | 0 | 0 |

## Held-Out Fix Samples

- fold=1 #244 `arithmetic` chinese_semantic via `has_coordinate`: Clean number theory check: report gcd(54, 81).

## Held-Out Break Samples

- fold=0 #237 `arithmetic` commonsense_choice via `has_mean`: Clean arithmetic check: compute the average of these four values: 65; 71; 75; 85.
- fold=1 #248 `arithmetic` chinese_semantic via `has_coordinate`: Clean number theory check: report gcd(84, 126).

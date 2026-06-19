# BitDPM v12 Utility Router Cross-Validation

- Report: `experiments/reports/v14_full_v11_admitted_20260608_093845.json`
- Folds: 5
- Overall: 0.853
- Baseline: 0.840
- Delta: +0.013
- Fixes: 5
- Breaks: 1
- Precision proxy: 0.833
- Allowed features: `None`
- Denied features: `['asks_brief', 'has_addition', 'has_division', 'has_power', 'has_sqrt', 'short_prompt']`
- Include conjunctions: `True`
- Min support: 3

## Folds

| Fold | Eval N | Rules | Router | Baseline | Delta | Fixes | Breaks |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 57 | 12 | 0.842 | 0.807 | +0.035 | 2 | 0 |
| 1 | 61 | 5 | 0.869 | 0.852 | +0.016 | 1 | 0 |
| 2 | 63 | 11 | 0.778 | 0.746 | +0.032 | 2 | 0 |
| 3 | 63 | 12 | 0.889 | 0.889 | +0.000 | 0 | 0 |
| 4 | 56 | 14 | 0.893 | 0.911 | -0.018 | 0 | 1 |

## Held-Out Fix Samples

- fold=0 #9 `arithmetic` v11_stats_number_theory via `category=arithmetic&has_multiplication`: What is 12 times 11?
- fold=0 #12 `arithmetic` v11_stats_number_theory via `category=arithmetic&has_multiplication`: What is 21 times 6?
- fold=1 #40 `arithmetic` v11_stats_number_theory via `category=arithmetic&has_3plus_numbers`: What is the distance from (0,0) to (3,4)?
- fold=2 #8 `arithmetic` v11_stats_number_theory via `category=arithmetic&has_multiplication`: What is 9 times 8?
- fold=2 #13 `arithmetic` v11_stats_number_theory via `category=arithmetic&has_multiplication`: What is 25 times 4?

## Held-Out Break Samples

- fold=4 #2 `arithmetic` calculation_error via `category=arithmetic&has_2plus_numbers`: What is 56 + 29?

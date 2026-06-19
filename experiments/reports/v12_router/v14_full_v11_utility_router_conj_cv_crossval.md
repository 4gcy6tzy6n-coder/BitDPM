# BitDPM v12 Utility Router Cross-Validation

- Report: `experiments/reports/v14_full_v11_admitted_20260608_093845.json`
- Folds: 5
- Overall: 0.843
- Baseline: 0.840
- Delta: +0.003
- Fixes: 5
- Breaks: 4
- Precision proxy: 0.556
- Allowed features: `None`
- Denied features: `None`
- Include conjunctions: `True`

## Folds

| Fold | Eval N | Rules | Router | Baseline | Delta | Fixes | Breaks |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 57 | 24 | 0.842 | 0.807 | +0.035 | 2 | 0 |
| 1 | 61 | 14 | 0.869 | 0.852 | +0.016 | 1 | 0 |
| 2 | 63 | 22 | 0.762 | 0.746 | +0.016 | 2 | 1 |
| 3 | 63 | 22 | 0.889 | 0.889 | +0.000 | 0 | 0 |
| 4 | 56 | 31 | 0.857 | 0.911 | -0.054 | 0 | 3 |

## Held-Out Fix Samples

- fold=0 #9 `arithmetic` v11_stats_number_theory via `category=arithmetic&has_multiplication`: What is 12 times 11?
- fold=0 #12 `arithmetic` v11_stats_number_theory via `category=arithmetic&has_multiplication`: What is 21 times 6?
- fold=1 #40 `arithmetic` v11_stats_number_theory via `category=arithmetic&has_3plus_numbers`: What is the distance from (0,0) to (3,4)?
- fold=2 #8 `arithmetic` v11_stats_number_theory via `category=arithmetic&has_multiplication`: What is 9 times 8?
- fold=2 #13 `arithmetic` v11_stats_number_theory via `category=arithmetic&has_multiplication`: What is 25 times 4?

## Held-Out Break Samples

- fold=2 #132 `commonsense` short_reasoning via `category=commonsense&short_prompt`: What fruit is typically yellow and curved?
- fold=4 #2 `arithmetic` calculation_error via `category=arithmetic&has_addition`: What is 56 + 29?
- fold=4 #26 `arithmetic` format_following via `category=arithmetic&has_sqrt`: What is the square root of 196?
- fold=4 #63 `factual_constants` v11_stats_number_theory via `category=factual_constants&asks_brief`: In one short answer, What is Avogadro's number approximately?

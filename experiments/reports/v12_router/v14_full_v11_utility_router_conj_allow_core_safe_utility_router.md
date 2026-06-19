# BitDPM v12 Utility-Aware Router Miner

- Report: `experiments/reports/v14_full_v11_admitted_20260608_093845.json`
- Train samples: 211
- Eval samples: 300
- Rules: 7
- Allowed features: `['has_coordinate', 'has_distance', 'has_log', 'has_mean', 'has_multiplication']`
- Denied features: `None`
- Include conjunctions: `True`

## Eval Result

- Router: 0.867
- Baseline: 0.840
- Delta: +0.027
- Fixes: 8
- Breaks: 0
- Precision proxy: 1.000
- Choices: `{'baseline': 284, 'v11_stats_number_theory': 14, 'format_following': 2}`

## Learned Rules

| Feature | Block | Fixes | Breaks | Precision | Support |
|---|---|---:|---:|---:|---:|
| category=arithmetic&has_coordinate | v11_stats_number_theory | 2 | 0 | 1.000 | 3 |
| category=arithmetic&has_distance | v11_stats_number_theory | 2 | 0 | 1.000 | 3 |
| category=arithmetic&has_multiplication | v11_stats_number_theory | 2 | 0 | 1.000 | 5 |
| category=arithmetic&has_log | format_following | 1 | 0 | 1.000 | 1 |
| category=arithmetic&has_mean | v11_stats_number_theory | 1 | 0 | 1.000 | 1 |
| category=arithmetic&has_coordinate | arithmetic_power_log | 1 | 0 | 1.000 | 3 |
| category=arithmetic&has_distance | arithmetic_power_log | 1 | 0 | 1.000 | 3 |

## Eval Fix Samples

- #8 `arithmetic` v11_stats_number_theory via `category=arithmetic&has_multiplication`: What is 9 times 8?
- #9 `arithmetic` v11_stats_number_theory via `category=arithmetic&has_multiplication`: What is 12 times 11?
- #12 `arithmetic` v11_stats_number_theory via `category=arithmetic&has_multiplication`: What is 21 times 6?
- #13 `arithmetic` v11_stats_number_theory via `category=arithmetic&has_multiplication`: What is 25 times 4?
- #40 `arithmetic` v11_stats_number_theory via `category=arithmetic&has_coordinate`: What is the distance from (0,0) to (3,4)?
- #42 `arithmetic` v11_stats_number_theory via `category=arithmetic&has_coordinate`: What is the distance from (0,0) to (8,15)?
- #45 `arithmetic` format_following via `category=arithmetic&has_log`: What is log base 10 of 1000?
- #47 `arithmetic` v11_stats_number_theory via `category=arithmetic&has_mean`: What is the mean of 4, 8, 12, and 16?

## Eval Break Samples


# BitDPM v12 Utility-Aware Router Miner

- Report: `experiments/reports/v14_full_v11_admitted_20260608_093845.json`
- Train samples: 211
- Eval samples: 300
- Rules: 6
- Allowed features: `['has_coordinate', 'has_distance', 'has_mean', 'has_multiplication']`
- Denied features: `None`
- Include conjunctions: `False`

## Eval Result

- Router: 0.863
- Baseline: 0.840
- Delta: +0.023
- Fixes: 7
- Breaks: 0
- Precision proxy: 1.000
- Choices: `{'baseline': 281, 'v11_stats_number_theory': 19}`

## Learned Rules

| Feature | Block | Fixes | Breaks | Precision | Support |
|---|---|---:|---:|---:|---:|
| has_distance | v11_stats_number_theory | 2 | 0 | 1.000 | 3 |
| has_coordinate | v11_stats_number_theory | 2 | 0 | 1.000 | 3 |
| has_multiplication | v11_stats_number_theory | 2 | 0 | 1.000 | 5 |
| has_distance | arithmetic_power_log | 1 | 0 | 1.000 | 3 |
| has_coordinate | arithmetic_power_log | 1 | 0 | 1.000 | 3 |
| has_mean | v11_stats_number_theory | 1 | 0 | 1.000 | 5 |

## Eval Fix Samples

- #8 `arithmetic` v11_stats_number_theory via `has_multiplication`: What is 9 times 8?
- #9 `arithmetic` v11_stats_number_theory via `has_multiplication`: What is 12 times 11?
- #12 `arithmetic` v11_stats_number_theory via `has_multiplication`: What is 21 times 6?
- #13 `arithmetic` v11_stats_number_theory via `has_multiplication`: What is 25 times 4?
- #40 `arithmetic` v11_stats_number_theory via `has_distance`: What is the distance from (0,0) to (3,4)?
- #42 `arithmetic` v11_stats_number_theory via `has_distance`: What is the distance from (0,0) to (8,15)?
- #47 `arithmetic` v11_stats_number_theory via `has_mean`: What is the mean of 4, 8, 12, and 16?

## Eval Break Samples


# BitDPM v12 Utility-Aware Router Miner

- Report: `experiments/reports/v14_full_v11_admitted_20260608_093845.json`
- Train samples: 211
- Eval samples: 300
- Rules: 17

## Eval Result

- Router: 0.873
- Baseline: 0.840
- Delta: +0.033
- Fixes: 10
- Breaks: 0
- Precision proxy: 1.000
- Choices: `{'baseline': 266, 'v11_stats_number_theory': 32, 'format_following': 2}`

## Learned Rules

| Feature | Block | Fixes | Breaks | Precision | Support |
|---|---|---:|---:|---:|---:|
| has_distance | v11_stats_number_theory | 2 | 0 | 1.000 | 3 |
| has_coordinate | v11_stats_number_theory | 2 | 0 | 1.000 | 3 |
| has_multiplication | v11_stats_number_theory | 2 | 0 | 1.000 | 5 |
| has_division | v11_stats_number_theory | 2 | 0 | 1.000 | 9 |
| has_power | v11_stats_number_theory | 2 | 0 | 1.000 | 12 |
| has_log | format_following | 1 | 0 | 1.000 | 1 |
| has_distance | arithmetic_power_log | 1 | 0 | 1.000 | 3 |
| has_coordinate | arithmetic_power_log | 1 | 0 | 1.000 | 3 |
| has_mean | v11_stats_number_theory | 1 | 0 | 1.000 | 5 |
| has_division | format_following | 1 | 0 | 1.000 | 9 |
| has_division | chinese_semantic | 1 | 0 | 1.000 | 9 |
| has_division | calculation_error | 1 | 0 | 1.000 | 9 |
| has_power | commonsense_choice | 1 | 0 | 1.000 | 12 |
| has_power | format_following | 1 | 0 | 1.000 | 12 |
| has_power | chinese_semantic | 1 | 0 | 1.000 | 12 |
| has_power | calculation_error | 1 | 0 | 1.000 | 12 |
| has_power | short_reasoning | 1 | 0 | 1.000 | 12 |

## Eval Fix Samples

- #8 `arithmetic` v11_stats_number_theory via `has_multiplication`: What is 9 times 8?
- #9 `arithmetic` v11_stats_number_theory via `has_multiplication`: What is 12 times 11?
- #12 `arithmetic` v11_stats_number_theory via `has_multiplication`: What is 21 times 6?
- #13 `arithmetic` v11_stats_number_theory via `has_multiplication`: What is 25 times 4?
- #40 `arithmetic` v11_stats_number_theory via `has_distance`: What is the distance from (0,0) to (3,4)?
- #42 `arithmetic` v11_stats_number_theory via `has_distance`: What is the distance from (0,0) to (8,15)?
- #45 `arithmetic` format_following via `has_log`: What is log base 10 of 1000?
- #47 `arithmetic` v11_stats_number_theory via `has_mean`: What is the mean of 4, 8, 12, and 16?
- #55 `factual_constants` v11_stats_number_theory via `has_division`: What is the approximate acceleration due to gravity on Earth in m/s^2?
- #56 `factual_constants` v11_stats_number_theory via `has_division`: Answer briefly: What is the approximate acceleration due to gravity on Earth in m/s^2?

## Eval Break Samples


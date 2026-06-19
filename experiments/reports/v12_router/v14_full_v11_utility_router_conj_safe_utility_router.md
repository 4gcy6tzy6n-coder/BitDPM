# BitDPM v12 Utility-Aware Router Miner

- Report: `experiments/reports/v14_full_v11_admitted_20260608_093845.json`
- Train samples: 211
- Eval samples: 300
- Rules: 23
- Allowed features: `None`
- Denied features: `None`
- Include conjunctions: `True`

## Eval Result

- Router: 0.877
- Baseline: 0.840
- Delta: +0.037
- Fixes: 11
- Breaks: 0
- Precision proxy: 1.000
- Choices: `{'baseline': 271, 'v11_stats_number_theory': 19, 'commonsense_choice': 8, 'format_following': 2}`

## Learned Rules

| Feature | Block | Fixes | Breaks | Precision | Support |
|---|---|---:|---:|---:|---:|
| category=arithmetic&has_3plus_numbers | v11_stats_number_theory | 3 | 0 | 1.000 | 4 |
| category=arithmetic&has_distance | v11_stats_number_theory | 2 | 0 | 1.000 | 3 |
| category=arithmetic&has_coordinate | v11_stats_number_theory | 2 | 0 | 1.000 | 3 |
| category=arithmetic&has_multiplication | v11_stats_number_theory | 2 | 0 | 1.000 | 5 |
| category=factual_constants&has_power | v11_stats_number_theory | 2 | 0 | 1.000 | 5 |
| category=factual_constants&has_division | v11_stats_number_theory | 2 | 0 | 1.000 | 5 |
| category=factual_constants&has_number | v11_stats_number_theory | 2 | 0 | 1.000 | 5 |
| category=arithmetic&has_log | format_following | 1 | 0 | 1.000 | 1 |
| category=arithmetic&has_mean | v11_stats_number_theory | 1 | 0 | 1.000 | 1 |
| category=arithmetic&has_distance | arithmetic_power_log | 1 | 0 | 1.000 | 3 |
| category=arithmetic&has_coordinate | arithmetic_power_log | 1 | 0 | 1.000 | 3 |
| category=arithmetic&has_3plus_numbers | arithmetic_power_log | 1 | 0 | 1.000 | 4 |
| category=factual_constants&has_power | format_following | 1 | 0 | 1.000 | 5 |
| category=factual_constants&has_division | format_following | 1 | 0 | 1.000 | 5 |
| category=factual_constants&has_number | format_following | 1 | 0 | 1.000 | 5 |
| category=factual_constants&has_power | chinese_semantic | 1 | 0 | 1.000 | 5 |
| category=factual_constants&has_division | chinese_semantic | 1 | 0 | 1.000 | 5 |
| category=factual_constants&has_number | chinese_semantic | 1 | 0 | 1.000 | 5 |
| category=factual_constants&has_power | calculation_error | 1 | 0 | 1.000 | 5 |
| category=factual_constants&has_division | calculation_error | 1 | 0 | 1.000 | 5 |
| category=factual_constants&has_number | calculation_error | 1 | 0 | 1.000 | 5 |
| category=arithmetic&has_power | commonsense_choice | 1 | 0 | 1.000 | 7 |
| category=arithmetic&has_power | short_reasoning | 1 | 0 | 1.000 | 7 |

## Eval Fix Samples

- #8 `arithmetic` v11_stats_number_theory via `category=arithmetic&has_multiplication`: What is 9 times 8?
- #9 `arithmetic` v11_stats_number_theory via `category=arithmetic&has_multiplication`: What is 12 times 11?
- #12 `arithmetic` v11_stats_number_theory via `category=arithmetic&has_multiplication`: What is 21 times 6?
- #13 `arithmetic` v11_stats_number_theory via `category=arithmetic&has_multiplication`: What is 25 times 4?
- #38 `arithmetic` commonsense_choice via `category=arithmetic&has_power`: What is 7^2?
- #40 `arithmetic` v11_stats_number_theory via `category=arithmetic&has_3plus_numbers`: What is the distance from (0,0) to (3,4)?
- #42 `arithmetic` v11_stats_number_theory via `category=arithmetic&has_3plus_numbers`: What is the distance from (0,0) to (8,15)?
- #45 `arithmetic` format_following via `category=arithmetic&has_log`: What is log base 10 of 1000?
- #47 `arithmetic` v11_stats_number_theory via `category=arithmetic&has_3plus_numbers`: What is the mean of 4, 8, 12, and 16?
- #55 `factual_constants` v11_stats_number_theory via `category=factual_constants&has_power`: What is the approximate acceleration due to gravity on Earth in m/s^2?
- #56 `factual_constants` v11_stats_number_theory via `category=factual_constants&has_power`: Answer briefly: What is the approximate acceleration due to gravity on Earth in m/s^2?

## Eval Break Samples


# BitDPM v12 Utility-Aware Router Miner

- Report: `experiments/reports/v15_router_validation_v11_admitted_20260608_113945.json`
- Train samples: 89
- Eval samples: 120
- Rules: 37
- Allowed features: `None`
- Denied features: `None`
- Include conjunctions: `True`

## Eval Result

- Router: 0.575
- Baseline: 0.442
- Delta: +0.133
- Fixes: 16
- Breaks: 0
- Precision proxy: 1.000
- Choices: `{'chinese_semantic': 48, 'arithmetic_power_log': 8, 'calculation_error': 4, 'v11_stats_number_theory': 8, 'short_reasoning': 24, 'baseline': 28}`

## Learned Rules

| Feature | Block | Fixes | Breaks | Precision | Support |
|---|---|---:|---:|---:|---:|
| category=router_multiplication&has_2plus_numbers | chinese_semantic | 5 | 0 | 1.000 | 17 |
| category=router_multiplication&has_number | chinese_semantic | 5 | 0 | 1.000 | 17 |
| category=router_multiplication&short_prompt | chinese_semantic | 5 | 0 | 1.000 | 17 |
| category=router_multiplication&has_multiplication | chinese_semantic | 5 | 0 | 1.000 | 17 |
| category=router_risky_arithmetic&has_number | short_reasoning | 3 | 0 | 1.000 | 15 |
| category=router_risky_arithmetic&short_prompt | short_reasoning | 3 | 0 | 1.000 | 15 |
| category=router_factual_constants&has_power | short_reasoning | 2 | 0 | 1.000 | 3 |
| category=router_factual_constants&has_number | short_reasoning | 2 | 0 | 1.000 | 3 |
| category=router_factual_constants&has_division | short_reasoning | 2 | 0 | 1.000 | 3 |
| category=router_risky_arithmetic&has_addition | short_reasoning | 2 | 0 | 1.000 | 6 |
| category=router_risky_arithmetic&has_2plus_numbers | short_reasoning | 2 | 0 | 1.000 | 6 |
| category=router_core_mixed&has_mean | v11_stats_number_theory | 2 | 0 | 1.000 | 7 |
| category=router_risky_arithmetic&has_sqrt | arithmetic_power_log | 2 | 0 | 1.000 | 9 |
| category=router_core_mixed&has_3plus_numbers | arithmetic_power_log | 2 | 0 | 1.000 | 12 |
| category=router_core_mixed&has_3plus_numbers | v11_stats_number_theory | 2 | 0 | 1.000 | 12 |
| category=router_factual_constants&has_power | chinese_semantic | 1 | 0 | 1.000 | 3 |
| category=router_factual_constants&has_number | chinese_semantic | 1 | 0 | 1.000 | 3 |
| category=router_factual_constants&has_division | chinese_semantic | 1 | 0 | 1.000 | 3 |
| category=router_core_mixed&has_coordinate | arithmetic_power_log | 1 | 0 | 1.000 | 5 |
| category=router_core_mixed&has_distance | arithmetic_power_log | 1 | 0 | 1.000 | 5 |
| category=router_commonsense_controls&asks_brief | chinese_semantic | 1 | 0 | 1.000 | 6 |
| category=router_commonsense_controls&asks_brief | calculation_error | 1 | 0 | 1.000 | 6 |
| category=router_core_mixed&has_mean | format_following | 1 | 0 | 1.000 | 7 |
| category=router_core_mixed&has_mean | calculation_error | 1 | 0 | 1.000 | 7 |
| category=router_core_mixed&has_mean | arithmetic_power_log | 1 | 0 | 1.000 | 7 |
| category=router_risky_arithmetic&has_sqrt | commonsense_choice | 1 | 0 | 1.000 | 9 |
| category=router_risky_arithmetic&has_sqrt | format_following | 1 | 0 | 1.000 | 9 |
| category=router_risky_arithmetic&has_sqrt | calculation_error | 1 | 0 | 1.000 | 9 |
| category=router_risky_arithmetic&has_sqrt | short_reasoning | 1 | 0 | 1.000 | 9 |
| category=router_factual_constants&has_physical_constant | chinese_semantic | 1 | 0 | 1.000 | 10 |
| category=router_core_mixed&has_3plus_numbers | format_following | 1 | 0 | 1.000 | 12 |
| category=router_core_mixed&has_3plus_numbers | calculation_error | 1 | 0 | 1.000 | 12 |
| category=router_commonsense_controls&short_prompt | chinese_semantic | 1 | 0 | 1.000 | 13 |
| category=router_commonsense_controls&short_prompt | calculation_error | 1 | 0 | 1.000 | 13 |
| category=router_core_mixed&short_prompt | calculation_error | 1 | 0 | 1.000 | 14 |
| category=router_core_mixed&has_2plus_numbers | calculation_error | 1 | 0 | 1.000 | 14 |
| category=router_core_mixed&has_number | calculation_error | 1 | 0 | 1.000 | 14 |

## Eval Fix Samples

- #5 `router_multiplication` chinese_semantic via `category=router_multiplication&has_2plus_numbers`: Compute 21 times 6.
- #7 `router_multiplication` chinese_semantic via `category=router_multiplication&has_2plus_numbers`: Compute 25 times 4.
- #13 `router_multiplication` chinese_semantic via `category=router_multiplication&has_2plus_numbers`: Compute 18 times 7.
- #14 `router_multiplication` chinese_semantic via `category=router_multiplication&has_2plus_numbers`: What is 22 times 5?
- #17 `router_multiplication` chinese_semantic via `category=router_multiplication&has_2plus_numbers`: Compute 17 times 9.
- #20 `router_core_mixed` arithmetic_power_log via `category=router_core_mixed&has_3plus_numbers`: What is the distance from (0,0) to (3,4)?
- #32 `router_core_mixed` v11_stats_number_theory via `category=router_core_mixed&has_mean`: What is the mean of 4, 8, 12, and 16?
- #35 `router_core_mixed` v11_stats_number_theory via `category=router_core_mixed&has_mean`: What is the mean of 2, 4, 6, and 8?
- #37 `router_core_mixed` v11_stats_number_theory via `category=router_core_mixed&has_mean`: What is the mean of 1, 3, 5, and 7?
- #44 `router_risky_arithmetic` short_reasoning via `category=router_risky_arithmetic&has_number`: What is 91 + 64?
- #47 `router_risky_arithmetic` short_reasoning via `category=router_risky_arithmetic&has_number`: What is 333 + 444?
- #49 `router_risky_arithmetic` short_reasoning via `category=router_risky_arithmetic&has_number`: What is 19 + 27?
- #52 `router_risky_arithmetic` short_reasoning via `category=router_risky_arithmetic&has_number`: What is the square root of 196?
- #61 `router_factual_constants` short_reasoning via `category=router_factual_constants&has_power`: Answer briefly: What is the approximate acceleration due to gravity on Earth in m/s^2?
- #62 `router_factual_constants` short_reasoning via `category=router_factual_constants&has_power`: Give the standard value: What is the approximate acceleration due to gravity on Earth in m/s^2?
- #115 `router_commonsense_controls` chinese_semantic via `category=router_commonsense_controls&asks_brief`: Answer briefly: What is the opposite of hot?

## Eval Break Samples


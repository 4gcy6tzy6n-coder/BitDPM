# BitDPM v12 Utility-Aware Router Miner

- Report: `experiments/reports/v14_pilot_v11_admitted_20260608_070120.json`
- Train samples: 43
- Eval samples: 60
- Rules: 7

## Eval Result

- Router: 0.917
- Baseline: 0.867
- Delta: +0.050
- Fixes: 3
- Breaks: 0
- Precision proxy: 1.000
- Choices: `{'baseline': 18, 'v11_stats_number_theory': 2, 'calculation_error': 11, 'chinese_semantic': 29}`

## Learned Rules

| Feature | Block | Fixes | Breaks | Precision | Support |
|---|---|---:|---:|---:|---:|
| has_multiplication | v11_stats_number_theory | 1 | 0 | 1.000 | 1 |
| has_power | calculation_error | 1 | 0 | 1.000 | 5 |
| has_power | v11_stats_number_theory | 1 | 0 | 1.000 | 5 |
| has_division | calculation_error | 1 | 0 | 1.000 | 6 |
| has_division | v11_stats_number_theory | 1 | 0 | 1.000 | 6 |
| has_physical_constant | calculation_error | 1 | 0 | 1.000 | 9 |
| asks_brief | chinese_semantic | 1 | 0 | 1.000 | 25 |

## Eval Fix Samples

- #8 `arithmetic` v11_stats_number_theory via `has_multiplication`: What is 9 times 8?
- #9 `arithmetic` v11_stats_number_theory via `has_multiplication`: What is 12 times 11?
- #17 `factual_constants` calculation_error via `has_power`: Give the standard value: What is the approximate acceleration due to gravity on Earth in m/s^2?

## Eval Break Samples


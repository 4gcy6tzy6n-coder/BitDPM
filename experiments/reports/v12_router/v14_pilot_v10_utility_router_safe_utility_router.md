# BitDPM v12 Utility-Aware Router Miner

- Report: `experiments/reports/v14_pilot_v10_admitted_20260608_064051.json`
- Train samples: 43
- Eval samples: 60
- Rules: 4

## Eval Result

- Router: 0.883
- Baseline: 0.867
- Delta: +0.017
- Fixes: 1
- Breaks: 0
- Precision proxy: 1.000
- Choices: `{'baseline': 20, 'calculation_error': 11, 'chinese_semantic': 29}`

## Learned Rules

| Feature | Block | Fixes | Breaks | Precision | Support |
|---|---|---:|---:|---:|---:|
| has_power | calculation_error | 1 | 0 | 1.000 | 5 |
| has_division | calculation_error | 1 | 0 | 1.000 | 6 |
| has_physical_constant | calculation_error | 1 | 0 | 1.000 | 9 |
| asks_brief | chinese_semantic | 1 | 0 | 1.000 | 25 |

## Eval Fix Samples

- #17 `factual_constants` calculation_error via `has_power`: Give the standard value: What is the approximate acceleration due to gravity on Earth in m/s^2?

## Eval Break Samples


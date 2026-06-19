# BitDPM v12 Utility Router Cross-Validation

- Report: `experiments/reports/v15_router_validation_v11_admitted_20260608_113945.json`
- Folds: 5
- Overall: 0.500
- Baseline: 0.442
- Delta: +0.058
- Fixes: 11
- Breaks: 4
- Precision proxy: 0.733
- Allowed features: `None`
- Denied features: `None`
- Include conjunctions: `True`
- Min support: 1

## Folds

| Fold | Eval N | Rules | Router | Baseline | Delta | Fixes | Breaks |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 19 | 62 | 0.526 | 0.474 | +0.053 | 3 | 2 |
| 1 | 21 | 45 | 0.381 | 0.381 | +0.000 | 0 | 0 |
| 2 | 23 | 61 | 0.652 | 0.478 | +0.174 | 5 | 1 |
| 3 | 37 | 50 | 0.514 | 0.486 | +0.027 | 1 | 0 |
| 4 | 20 | 52 | 0.400 | 0.350 | +0.050 | 2 | 1 |

## Held-Out Fix Samples

- fold=0 #5 `router_multiplication` chinese_semantic via `category=router_multiplication&has_multiplication`: Compute 21 times 6.
- fold=0 #13 `router_multiplication` chinese_semantic via `category=router_multiplication&has_multiplication`: Compute 18 times 7.
- fold=0 #17 `router_multiplication` chinese_semantic via `category=router_multiplication&has_multiplication`: Compute 17 times 9.
- fold=2 #7 `router_multiplication` chinese_semantic via `category=router_multiplication&has_multiplication`: Compute 25 times 4.
- fold=2 #35 `router_core_mixed` v11_stats_number_theory via `category=router_core_mixed&has_mean`: What is the mean of 2, 4, 6, and 8?
- fold=2 #44 `router_risky_arithmetic` short_reasoning via `category=router_risky_arithmetic&has_2plus_numbers`: What is 91 + 64?
- fold=2 #52 `router_risky_arithmetic` short_reasoning via `category=router_risky_arithmetic&short_prompt`: What is the square root of 196?
- fold=2 #99 `router_commonsense_repairs` chinese_semantic via `category=router_commonsense_repairs&asks_brief`: In one short answer, What fruit is typically yellow and curved?
- fold=3 #37 `router_core_mixed` arithmetic_power_log via `category=router_core_mixed&has_3plus_numbers`: What is the mean of 1, 3, 5, and 7?
- fold=4 #14 `router_multiplication` chinese_semantic via `category=router_multiplication&has_multiplication`: What is 22 times 5?
- fold=4 #49 `router_risky_arithmetic` calculation_error via `category=router_risky_arithmetic&short_prompt`: What is 19 + 27?

## Held-Out Break Samples

- fold=0 #30 `router_core_mixed` format_following via `category=router_core_mixed&has_number`: What is log base 10 of 100?
- fold=0 #71 `router_factual_constants` short_reasoning via `category=router_factual_constants&asks_brief`: In one short answer, What is Avogadro's number approximately?
- fold=2 #81 `router_commonsense_repairs` chinese_semantic via `category=router_commonsense_repairs&asks_brief`: Answer briefly: How many continents are commonly counted on Earth?
- fold=4 #46 `router_risky_arithmetic` calculation_error via `category=router_risky_arithmetic&short_prompt`: What is 145 + 255?

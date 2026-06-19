# BitDPM v14 Report Summary

- Report: `experiments/reports/v15_router_validation_v11_admitted_20260608_113945.json`
- Benchmark: `v15`
- Total prompts: 120
- Baseline: 0.442
- Oracle: 0.742
- Oracle gain: +0.300
- Non-baseline oracle coverage: 36/120 (0.300)
- Always-All: 0.000
- Selection frequency: `{'baseline': 84, 'commonsense_choice': 14, 'format_following': 4, 'chinese_semantic': 6, 'calculation_error': 3, 'short_reasoning': 3, 'arithmetic_power_log': 3, 'v11_stats_number_theory': 3, 'always_all': 0}`
- Coverage by category: `{'router_multiplication': 9, 'router_core_mixed': 6, 'router_risky_arithmetic': 10, 'router_factual_constants': 3, 'router_commonsense_repairs': 7, 'router_commonsense_controls': 1}`

## Fixed Blocks

| Config | Overall | Delta | Active |
|---|---:|---:|---:|
| chinese_semantic | 0.508 | +0.067 | 3.00 |
| short_reasoning | 0.475 | +0.033 | 3.00 |
| commonsense_choice | 0.433 | -0.008 | 3.00 |
| calculation_error | 0.425 | -0.017 | 3.00 |
| v11_stats_number_theory | 0.417 | -0.025 | 3.00 |
| arithmetic_power_log | 0.383 | -0.058 | 3.00 |
| format_following | 0.358 | -0.083 | 3.00 |

## Non-Baseline Oracle Samples

- #0 `router_multiplication` `short_reasoning` baseline=0.0 score=1.0: What is 9 times 8?
- #4 `router_multiplication` `v11_stats_number_theory` baseline=0.0 score=1.0: What is 21 times 6?
- #5 `router_multiplication` `chinese_semantic` baseline=0.0 score=1.0: Compute 21 times 6.
- #6 `router_multiplication` `arithmetic_power_log` baseline=0.0 score=1.0: What is 25 times 4?
- #7 `router_multiplication` `chinese_semantic` baseline=0.0 score=1.0: Compute 25 times 4.
- #13 `router_multiplication` `chinese_semantic` baseline=0.0 score=1.0: Compute 18 times 7.
- #14 `router_multiplication` `chinese_semantic` baseline=0.0 score=1.0: What is 22 times 5?
- #15 `router_multiplication` `commonsense_choice` baseline=0.0 score=1.0: Compute 22 times 5.
- #17 `router_multiplication` `chinese_semantic` baseline=0.0 score=1.0: Compute 17 times 9.
- #20 `router_core_mixed` `arithmetic_power_log` baseline=0.0 score=1.0: What is the distance from (0,0) to (3,4)?
- #28 `router_core_mixed` `commonsense_choice` baseline=0.0 score=1.0: What is log base 10 of 1000?
- #31 `router_core_mixed` `format_following` baseline=0.0 score=1.0: What is log base 10 of 1000000?
- #32 `router_core_mixed` `v11_stats_number_theory` baseline=0.0 score=1.0: What is the mean of 4, 8, 12, and 16?
- #35 `router_core_mixed` `format_following` baseline=0.0 score=1.0: What is the mean of 2, 4, 6, and 8?
- #37 `router_core_mixed` `commonsense_choice` baseline=0.0 score=1.0: What is the mean of 1, 3, 5, and 7?
- #40 `router_risky_arithmetic` `commonsense_choice` baseline=0.0 score=1.0: What is 37 + 45?
- #41 `router_risky_arithmetic` `v11_stats_number_theory` baseline=0.0 score=1.0: What is 56 + 29?
- #44 `router_risky_arithmetic` `format_following` baseline=0.0 score=1.0: What is 91 + 64?
- #47 `router_risky_arithmetic` `format_following` baseline=0.0 score=1.0: What is 333 + 444?
- #48 `router_risky_arithmetic` `commonsense_choice` baseline=0.0 score=1.0: What is 88 + 67?
- #49 `router_risky_arithmetic` `commonsense_choice` baseline=0.0 score=1.0: What is 19 + 27?
- #50 `router_risky_arithmetic` `commonsense_choice` baseline=0.0 score=1.0: What is the square root of 144?
- #52 `router_risky_arithmetic` `short_reasoning` baseline=0.0 score=1.0: What is the square root of 196?
- #53 `router_risky_arithmetic` `arithmetic_power_log` baseline=0.0 score=1.0: What is the square root of 225?
- #56 `router_risky_arithmetic` `calculation_error` baseline=0.0 score=1.0: What is the square root of 121?
- #61 `router_factual_constants` `short_reasoning` baseline=0.0 score=1.0: Answer briefly: What is the approximate acceleration due to gravity on Earth in m/s^2?
- #62 `router_factual_constants` `commonsense_choice` baseline=0.0 score=1.0: Give the standard value: What is the approximate acceleration due to gravity on Earth in m/s^2?
- #68 `router_factual_constants` `commonsense_choice` baseline=0.0 score=1.0: What is Avogadro's number approximately?
- #80 `router_commonsense_repairs` `commonsense_choice` baseline=0.0 score=1.0: How many continents are commonly counted on Earth?
- #82 `router_commonsense_repairs` `calculation_error` baseline=0.0 score=1.0: Give the common answer: How many continents are commonly counted on Earth?
- #85 `router_commonsense_repairs` `chinese_semantic` baseline=0.0 score=1.0: Answer briefly: Which animal is often called the king of the jungle?
- #86 `router_commonsense_repairs` `calculation_error` baseline=0.0 score=1.0: Give the common answer: Which animal is often called the king of the jungle?
- #88 `router_commonsense_repairs` `commonsense_choice` baseline=0.0 score=1.0: What do you call money borrowed that must be repaid?
- #98 `router_commonsense_repairs` `commonsense_choice` baseline=0.0 score=1.0: Give the common answer: What fruit is typically yellow and curved?
- #99 `router_commonsense_repairs` `commonsense_choice` baseline=0.0 score=1.0: In one short answer, What fruit is typically yellow and curved?
- #115 `router_commonsense_controls` `commonsense_choice` baseline=0.0 score=1.0: Answer briefly: What is the opposite of hot?

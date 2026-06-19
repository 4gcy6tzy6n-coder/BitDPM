# BitDPM v14 Report Summary

- Report: `experiments/reports/v11_merged_candidates_stable_sampling_LATEST.json`
- Benchmark: `v08`
- Total prompts: 100
- Baseline: 0.830
- Oracle: 0.900
- Oracle gain: +0.070
- Non-baseline oracle coverage: 7/100 (0.070)
- Always-All: 0.000
- Selection frequency: `{'baseline': 93, 'commonsense_choice': 2, 'format_following': 2, 'chinese_semantic': 1, 'calculation_error': 0, 'short_reasoning': 0, 'arithmetic_power_log': 1, 'v11_linear_equation': 0, 'v11_percent_time_distance': 0, 'v11_circle_area': 0, 'v11_stats_number_theory': 1, 'v11_factorial_derivative': 0, 'always_all': 0}`
- Coverage by category: `{'commonsense': 1, 'math': 6}`

## Fixed Blocks

| Config | Overall | Delta | Active |
|---|---:|---:|---:|
| commonsense_choice | 0.820 | -0.010 | 3.00 |
| short_reasoning | 0.820 | -0.010 | 3.00 |
| v11_linear_equation | 0.820 | -0.010 | 3.00 |
| calculation_error | 0.810 | -0.020 | 3.00 |
| chinese_semantic | 0.800 | -0.030 | 3.00 |
| v11_stats_number_theory | 0.785 | -0.045 | 3.00 |
| arithmetic_power_log | 0.755 | -0.075 | 3.00 |
| v11_percent_time_distance | 0.710 | -0.120 | 3.00 |
| v11_circle_area | 0.670 | -0.160 | 3.00 |
| v11_factorial_derivative | 0.660 | -0.170 | 3.00 |
| format_following | 0.640 | -0.190 | 3.00 |

## Non-Baseline Oracle Samples

- #8 `commonsense` `format_following` baseline=0.0 score=1.0: What is the speed of light in vacuum?
- #25 `math` `commonsense_choice` baseline=0.0 score=1.0: What is the square root of 144?
- #30 `math` `chinese_semantic` baseline=0.0 score=1.0: What is 18 + 24?
- #32 `math` `format_following` baseline=0.0 score=1.0: What is 15% of 80?
- #33 `math` `v11_stats_number_theory` baseline=0.0 score=1.0: What is the mean of 4, 8, 12, and 16?
- #38 `math` `commonsense_choice` baseline=0.0 score=1.0: What is log base 10 of 1000?
- #39 `math` `arithmetic_power_log` baseline=0.0 score=1.0: What is the distance from (0,0) to (3,4)?

# BitDPM v14 Report Summary

- Report: `experiments/reports/v14_pilot_v11_admitted_20260608_070120.json`
- Benchmark: `v14`
- Total prompts: 60
- Baseline: 0.867
- Oracle: 0.983
- Oracle gain: +0.117
- Non-baseline oracle coverage: 7/60 (0.117)
- Always-All: 0.000
- Selection frequency: `{'baseline': 53, 'commonsense_choice': 1, 'format_following': 0, 'chinese_semantic': 4, 'calculation_error': 0, 'short_reasoning': 0, 'arithmetic_power_log': 0, 'v11_stats_number_theory': 2, 'always_all': 0}`
- Coverage by category: `{'arithmetic': 4, 'factual_constants': 2, 'commonsense': 1}`

## Fixed Blocks

| Config | Overall | Delta | Active |
|---|---:|---:|---:|
| calculation_error | 0.892 | +0.025 | 3.00 |
| chinese_semantic | 0.883 | +0.017 | 3.00 |
| v11_stats_number_theory | 0.875 | +0.008 | 3.00 |
| short_reasoning | 0.817 | -0.050 | 3.00 |
| commonsense_choice | 0.767 | -0.100 | 3.00 |
| arithmetic_power_log | 0.692 | -0.175 | 3.00 |
| format_following | 0.667 | -0.200 | 3.00 |

## Non-Baseline Oracle Samples

- #5 `arithmetic` `chinese_semantic` baseline=0.0 score=1.0: What is 91 + 64?
- #7 `arithmetic` `chinese_semantic` baseline=0.0 score=1.0: What is 145 + 255?
- #8 `arithmetic` `v11_stats_number_theory` baseline=0.0 score=1.0: What is 9 times 8?
- #9 `arithmetic` `v11_stats_number_theory` baseline=0.0 score=1.0: What is 12 times 11?
- #16 `factual_constants` `chinese_semantic` baseline=0.0 score=1.0: Answer briefly: What is the approximate acceleration due to gravity on Earth in m/s^2?
- #17 `factual_constants` `chinese_semantic` baseline=0.0 score=1.0: Give the standard value: What is the approximate acceleration due to gravity on Earth in m/s^2?
- #24 `commonsense` `commonsense_choice` baseline=0.0 score=1.0: How many continents are commonly counted on Earth?

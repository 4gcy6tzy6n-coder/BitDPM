# BitDPM v14 Report Summary

- Report: `experiments/reports/v14_full_v11_admitted_20260608_093845.json`
- Benchmark: `v14`
- Total prompts: 300
- Baseline: 0.840
- Oracle: 0.903
- Oracle gain: +0.063
- Non-baseline oracle coverage: 19/300 (0.063)
- Always-All: 0.000
- Selection frequency: `{'baseline': 281, 'commonsense_choice': 2, 'format_following': 3, 'chinese_semantic': 4, 'calculation_error': 2, 'short_reasoning': 1, 'arithmetic_power_log': 2, 'v11_stats_number_theory': 5, 'always_all': 0}`
- Coverage by category: `{'arithmetic': 13, 'factual_constants': 3, 'commonsense': 3}`

## Fixed Blocks

| Config | Overall | Delta | Active |
|---|---:|---:|---:|
| calculation_error | 0.833 | -0.007 | 3.00 |
| short_reasoning | 0.805 | -0.035 | 3.00 |
| chinese_semantic | 0.793 | -0.047 | 3.00 |
| v11_stats_number_theory | 0.788 | -0.052 | 3.00 |
| commonsense_choice | 0.735 | -0.105 | 3.00 |
| format_following | 0.642 | -0.198 | 3.00 |
| arithmetic_power_log | 0.613 | -0.227 | 3.00 |

## Non-Baseline Oracle Samples

- #5 `arithmetic` `chinese_semantic` baseline=0.0 score=1.0: What is 91 + 64?
- #7 `arithmetic` `chinese_semantic` baseline=0.0 score=1.0: What is 145 + 255?
- #8 `arithmetic` `v11_stats_number_theory` baseline=0.0 score=1.0: What is 9 times 8?
- #9 `arithmetic` `v11_stats_number_theory` baseline=0.0 score=1.0: What is 12 times 11?
- #12 `arithmetic` `arithmetic_power_log` baseline=0.0 score=1.0: What is 21 times 6?
- #13 `arithmetic` `short_reasoning` baseline=0.0 score=1.0: What is 25 times 4?
- #24 `arithmetic` `commonsense_choice` baseline=0.0 score=1.0: What is the square root of 144?
- #27 `arithmetic` `format_following` baseline=0.0 score=1.0: What is the square root of 225?
- #38 `arithmetic` `commonsense_choice` baseline=0.0 score=1.0: What is 7^2?
- #40 `arithmetic` `arithmetic_power_log` baseline=0.0 score=1.0: What is the distance from (0,0) to (3,4)?
- #42 `arithmetic` `v11_stats_number_theory` baseline=0.0 score=1.0: What is the distance from (0,0) to (8,15)?
- #45 `arithmetic` `format_following` baseline=0.0 score=1.0: What is log base 10 of 1000?
- #47 `arithmetic` `v11_stats_number_theory` baseline=0.0 score=1.0: What is the mean of 4, 8, 12, and 16?
- #55 `factual_constants` `format_following` baseline=0.0 score=1.0: What is the approximate acceleration due to gravity on Earth in m/s^2?
- #56 `factual_constants` `v11_stats_number_theory` baseline=0.0 score=1.0: Answer briefly: What is the approximate acceleration due to gravity on Earth in m/s^2?
- #57 `factual_constants` `chinese_semantic` baseline=0.0 score=1.0: Give the standard value: What is the approximate acceleration due to gravity on Earth in m/s^2?
- #104 `commonsense` `calculation_error` baseline=0.0 score=1.0: How many continents are commonly counted on Earth?
- #111 `commonsense` `calculation_error` baseline=0.0 score=1.0: Which animal is often called the king of the jungle?
- #145 `commonsense` `chinese_semantic` baseline=0.0 score=1.0: What do you call money borrowed that must be repaid?

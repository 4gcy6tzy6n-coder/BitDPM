# Utility Mining: v14_pilot_v11_admitted

- Report: `experiments/reports/v14_pilot_v11_admitted_20260608_070120.json`
- Benchmark: `v14`
- Total prompts: `60`
- Block scale: `0.75`
- Oracle overall: `0.983`
- Selection frequency: `{'baseline': 53, 'commonsense_choice': 1, 'format_following': 0, 'chinese_semantic': 4, 'calculation_error': 0, 'short_reasoning': 0, 'arithmetic_power_log': 0, 'v11_stats_number_theory': 2, 'always_all': 0}`

## Bucket Counts

- `baseline_correct_block_wrong`: 48
- `baseline_wrong_block_correct`: 17
- `baseline_wrong_all_wrong`: 1
- `near_miss`: 0

## Unique Utility Counts

- `v11_stats_number_theory`: 2

## Positive Delta Samples

- #5 `arithmetic` `chinese_semantic` 0.0 -> 1.0: What is 91 + 64?
- #7 `arithmetic` `chinese_semantic` 0.0 -> 1.0: What is 145 + 255?
- #8 `arithmetic` `v11_stats_number_theory` 0.0 -> 1.0: What is 9 times 8?
- #9 `arithmetic` `v11_stats_number_theory` 0.0 -> 1.0: What is 12 times 11?
- #16 `factual_constants` `chinese_semantic` 0.0 -> 1.0: Answer briefly: What is the approximate acceleration due to gravity on Earth in m/s^2?
- #17 `factual_constants` `chinese_semantic` 0.0 -> 1.0: Give the standard value: What is the approximate acceleration due to gravity on Earth in m/s^2?
- #24 `commonsense` `commonsense_choice` 0.0 -> 1.0: How many continents are commonly counted on Earth?

## Outputs

- JSON: `experiments/reports/v08_utility_mining/v14_pilot_v11_admitted_utility_mining.json`
- Training texts: `experiments/reports/v08_utility_mining/v14_pilot_v11_admitted_training_texts.json`

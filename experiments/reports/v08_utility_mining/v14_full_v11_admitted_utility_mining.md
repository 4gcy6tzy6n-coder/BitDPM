# Utility Mining: v14_full_v11_admitted

- Report: `experiments/reports/v14_full_v11_admitted_20260608_093845.json`
- Benchmark: `v14`
- Total prompts: `300`
- Block scale: `0.75`
- Oracle overall: `0.903`
- Selection frequency: `{'baseline': 281, 'commonsense_choice': 2, 'format_following': 3, 'chinese_semantic': 4, 'calculation_error': 2, 'short_reasoning': 1, 'arithmetic_power_log': 2, 'v11_stats_number_theory': 5, 'always_all': 0}`

## Bucket Counts

- `baseline_correct_block_wrong`: 255
- `baseline_wrong_block_correct`: 34
- `baseline_wrong_all_wrong`: 29
- `near_miss`: 0

## Unique Utility Counts

- `v11_stats_number_theory`: 5
- `format_following`: 1
- `calculation_error`: 1

## Positive Delta Samples

- #5 `arithmetic` `chinese_semantic` 0.0 -> 1.0: What is 91 + 64?
- #7 `arithmetic` `chinese_semantic` 0.0 -> 1.0: What is 145 + 255?
- #8 `arithmetic` `v11_stats_number_theory` 0.0 -> 1.0: What is 9 times 8?
- #9 `arithmetic` `v11_stats_number_theory` 0.0 -> 1.0: What is 12 times 11?
- #12 `arithmetic` `arithmetic_power_log` 0.0 -> 1.0: What is 21 times 6?
- #13 `arithmetic` `short_reasoning` 0.0 -> 1.0: What is 25 times 4?
- #24 `arithmetic` `commonsense_choice` 0.0 -> 1.0: What is the square root of 144?
- #27 `arithmetic` `format_following` 0.0 -> 1.0: What is the square root of 225?
- #38 `arithmetic` `commonsense_choice` 0.0 -> 1.0: What is 7^2?
- #40 `arithmetic` `arithmetic_power_log` 0.0 -> 1.0: What is the distance from (0,0) to (3,4)?
- #42 `arithmetic` `v11_stats_number_theory` 0.0 -> 1.0: What is the distance from (0,0) to (8,15)?
- #45 `arithmetic` `format_following` 0.0 -> 1.0: What is log base 10 of 1000?
- #47 `arithmetic` `v11_stats_number_theory` 0.0 -> 1.0: What is the mean of 4, 8, 12, and 16?
- #55 `factual_constants` `format_following` 0.0 -> 1.0: What is the approximate acceleration due to gravity on Earth in m/s^2?
- #56 `factual_constants` `v11_stats_number_theory` 0.0 -> 1.0: Answer briefly: What is the approximate acceleration due to gravity on Earth in m/s^2?
- #57 `factual_constants` `chinese_semantic` 0.0 -> 1.0: Give the standard value: What is the approximate acceleration due to gravity on Earth in m/s^2?
- #104 `commonsense` `calculation_error` 0.0 -> 1.0: How many continents are commonly counted on Earth?
- #111 `commonsense` `calculation_error` 0.0 -> 1.0: Which animal is often called the king of the jungle?
- #145 `commonsense` `chinese_semantic` 0.0 -> 1.0: What do you call money borrowed that must be repaid?

## Outputs

- JSON: `experiments/reports/v08_utility_mining/v14_full_v11_admitted_utility_mining.json`
- Training texts: `experiments/reports/v08_utility_mining/v14_full_v11_admitted_training_texts.json`

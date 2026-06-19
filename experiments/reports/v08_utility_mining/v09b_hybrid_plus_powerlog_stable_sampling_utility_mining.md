# Utility Mining: v09b_hybrid_plus_powerlog_stable_sampling

- Report: `experiments/reports/v09b_hybrid_plus_powerlog_stable_sampling_20260607_203029.json`
- Benchmark: `v08`
- Total prompts: `100`
- Block scale: `0.75`
- Oracle overall: `0.890`
- Selection frequency: `{'baseline': 94, 'commonsense_choice': 2, 'format_following': 2, 'chinese_semantic': 1, 'calculation_error': 0, 'short_reasoning': 0, 'arithmetic_power_log': 1, 'always_all': 0}`

## Bucket Counts

- `baseline_correct_block_wrong`: 47
- `baseline_wrong_block_correct`: 9
- `baseline_wrong_all_wrong`: 11
- `near_miss`: 0

## Unique Utility Counts

- `chinese_semantic`: 1
- `format_following`: 1
- `arithmetic_power_log`: 1

## Positive Delta Samples

- #8 `commonsense` `format_following` 0.0 -> 1.0: What is the speed of light in vacuum?
- #25 `math` `commonsense_choice` 0.0 -> 1.0: What is the square root of 144?
- #30 `math` `chinese_semantic` 0.0 -> 1.0: What is 18 + 24?
- #32 `math` `format_following` 0.0 -> 1.0: What is 15% of 80?
- #38 `math` `commonsense_choice` 0.0 -> 1.0: What is log base 10 of 1000?
- #39 `math` `arithmetic_power_log` 0.0 -> 1.0: What is the distance from (0,0) to (3,4)?

## Outputs

- JSON: `experiments/reports/v08_utility_mining/v09b_hybrid_plus_powerlog_stable_sampling_utility_mining.json`
- Training texts: `experiments/reports/v08_utility_mining/v09b_hybrid_plus_powerlog_stable_sampling_training_texts.json`

# Utility Mining: v08_rank16_scale075_stable_sampling

- Report: `experiments/reports/v08_rank16_scale075_v08_stable_sampling_20260607_180805.json`
- Benchmark: `v08`
- Total prompts: `100`
- Block scale: `0.75`
- Oracle overall: `0.870`
- Selection frequency: `{'baseline': 96, 'calculation_error': 0, 'chinese_semantic': 1, 'commonsense_choice': 0, 'format_following': 3, 'short_reasoning': 0, 'always_all': 0}`

## Bucket Counts

- `baseline_correct_block_wrong`: 69
- `baseline_wrong_block_correct`: 5
- `baseline_wrong_all_wrong`: 13
- `near_miss`: 0

## Unique Utility Counts

- `format_following`: 3

## Positive Delta Samples

- #8 `commonsense` `format_following` 0.0 -> 1.0: What is the speed of light in vacuum?
- #25 `math` `format_following` 0.0 -> 1.0: What is the square root of 144?
- #30 `math` `chinese_semantic` 0.0 -> 1.0: What is 18 + 24?
- #32 `math` `format_following` 0.0 -> 1.0: What is 15% of 80?

## Outputs

- JSON: `experiments/reports/v08_utility_mining/v08_rank16_scale075_stable_sampling_utility_mining.json`
- Training texts: `experiments/reports/v08_utility_mining/v08_rank16_scale075_stable_sampling_training_texts.json`

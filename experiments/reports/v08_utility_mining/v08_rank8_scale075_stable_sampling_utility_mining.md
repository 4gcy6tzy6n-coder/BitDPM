# Utility Mining: v08_rank8_scale075_stable_sampling

- Report: `experiments/reports/v08_rank8_scale075_v08_stable_sampling_20260607_172636.json`
- Benchmark: `v08`
- Total prompts: `100`
- Block scale: `0.75`
- Oracle overall: `0.860`
- Selection frequency: `{'baseline': 97, 'calculation_error': 0, 'chinese_semantic': 0, 'commonsense_choice': 1, 'format_following': 1, 'short_reasoning': 1, 'always_all': 0}`

## Bucket Counts

- `baseline_correct_block_wrong`: 73
- `baseline_wrong_block_correct`: 4
- `baseline_wrong_all_wrong`: 14
- `near_miss`: 0

## Unique Utility Counts

- `format_following`: 1
- `short_reasoning`: 1

## Positive Delta Samples

- #25 `math` `commonsense_choice` 0.0 -> 1.0: What is the square root of 144?
- #30 `math` `format_following` 0.0 -> 1.0: What is 18 + 24?
- #32 `math` `short_reasoning` 0.0 -> 1.0: What is 15% of 80?

## Outputs

- JSON: `experiments/reports/v08_utility_mining/v08_rank8_scale075_stable_sampling_utility_mining.json`
- Training texts: `experiments/reports/v08_utility_mining/v08_rank8_scale075_stable_sampling_training_texts.json`

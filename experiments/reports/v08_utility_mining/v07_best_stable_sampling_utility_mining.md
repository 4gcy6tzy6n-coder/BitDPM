# Utility Mining: v07_best_stable_sampling

- Report: `experiments/reports/v07_error_l22_l24_down_scale075_stable_sampling_20260607_162332.json`
- Benchmark: `unknown`
- Total prompts: `45`
- Block scale: `0.75`
- Oracle overall: `0.867`
- Selection frequency: `{'baseline': 43, 'calculation_error': 1, 'chinese_semantic': 0, 'commonsense_choice': 1, 'format_following': 0, 'short_reasoning': 0, 'always_all': 0}`

## Bucket Counts

- `baseline_correct_block_wrong`: 26
- `baseline_wrong_block_correct`: 4
- `baseline_wrong_all_wrong`: 6
- `near_miss`: 0

## Unique Utility Counts

- `calculation_error`: 1

## Positive Delta Samples

- #15 `math` `commonsense_choice` 0.0 -> 1.0: What is the square root of 144?
- #18 `math` `calculation_error` 0.0 -> 1.0: What is 2^10?

## Outputs

- JSON: `experiments/reports/v08_utility_mining/v07_best_stable_sampling_utility_mining.json`
- Training texts: `experiments/reports/v08_utility_mining/v07_best_stable_sampling_training_texts.json`

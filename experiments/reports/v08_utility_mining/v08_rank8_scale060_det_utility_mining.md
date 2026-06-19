# Utility Mining: v08_rank8_scale060_det

- Report: `experiments/reports/v08_rank8_scale060_v08_det_20260607_171409.json`
- Benchmark: `v08`
- Total prompts: `100`
- Block scale: `0.6`
- Oracle overall: `0.840`
- Selection frequency: `{'baseline': 96, 'calculation_error': 1, 'chinese_semantic': 1, 'commonsense_choice': 0, 'format_following': 2, 'short_reasoning': 0, 'always_all': 0}`

## Bucket Counts

- `baseline_correct_block_wrong`: 29
- `baseline_wrong_block_correct`: 7
- `baseline_wrong_all_wrong`: 16
- `near_miss`: 0

## Unique Utility Counts

- `format_following`: 2

## Positive Delta Samples

- #5 `commonsense` `chinese_semantic` 0.0 -> 1.0: Who wrote Romeo and Juliet?
- #25 `math` `format_following` 0.0 -> 1.0: What is the square root of 144?
- #30 `math` `format_following` 0.0 -> 1.0: What is 18 + 24?
- #31 `math` `calculation_error` 0.0 -> 1.0: What is 9 times 8?

## Outputs

- JSON: `experiments/reports/v08_utility_mining/v08_rank8_scale060_det_utility_mining.json`
- Training texts: `experiments/reports/v08_utility_mining/v08_rank8_scale060_det_training_texts.json`

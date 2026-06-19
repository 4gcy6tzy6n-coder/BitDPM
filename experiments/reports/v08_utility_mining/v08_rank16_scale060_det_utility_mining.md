# Utility Mining: v08_rank16_scale060_det

- Report: `experiments/reports/v08_rank16_scale060_v08_det_20260607_175023.json`
- Benchmark: `v08`
- Total prompts: `100`
- Block scale: `0.6`
- Oracle overall: `0.840`
- Selection frequency: `{'baseline': 96, 'calculation_error': 1, 'chinese_semantic': 0, 'commonsense_choice': 3, 'format_following': 0, 'short_reasoning': 0, 'always_all': 0}`

## Bucket Counts

- `baseline_correct_block_wrong`: 20
- `baseline_wrong_block_correct`: 5
- `baseline_wrong_all_wrong`: 16
- `near_miss`: 0

## Unique Utility Counts

- `commonsense_choice`: 2
- `calculation_error`: 1

## Positive Delta Samples

- #5 `commonsense` `commonsense_choice` 0.0 -> 1.0: Who wrote Romeo and Juliet?
- #25 `math` `commonsense_choice` 0.0 -> 1.0: What is the square root of 144?
- #28 `math` `calculation_error` 0.0 -> 1.0: What is 2^10?
- #38 `math` `commonsense_choice` 0.0 -> 1.0: What is log base 10 of 1000?

## Outputs

- JSON: `experiments/reports/v08_utility_mining/v08_rank16_scale060_det_utility_mining.json`
- Training texts: `experiments/reports/v08_utility_mining/v08_rank16_scale060_det_training_texts.json`

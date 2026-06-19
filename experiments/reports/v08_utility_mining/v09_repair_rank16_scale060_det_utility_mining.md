# Utility Mining: v09_repair_rank16_scale060_det

- Report: `experiments/reports/v09_repair_rank16_scale060_v08_det_20260607_194909.json`
- Benchmark: `v08`
- Total prompts: `100`
- Block scale: `0.6`
- Oracle overall: `0.840`
- Selection frequency: `{'baseline': 96, 'arithmetic_addition': 0, 'arithmetic_percent': 2, 'arithmetic_power_log': 0, 'arithmetic_sqrt': 0, 'factual_constants': 2, 'always_all': 0}`

## Bucket Counts

- `baseline_correct_block_wrong`: 21
- `baseline_wrong_block_correct`: 7
- `baseline_wrong_all_wrong`: 16
- `near_miss`: 0

## Unique Utility Counts

- `factual_constants`: 2

## Positive Delta Samples

- #5 `commonsense` `arithmetic_percent` 0.0 -> 1.0: Who wrote Romeo and Juliet?
- #8 `commonsense` `factual_constants` 0.0 -> 1.0: What is the speed of light in vacuum?
- #25 `math` `factual_constants` 0.0 -> 1.0: What is the square root of 144?
- #31 `math` `arithmetic_percent` 0.0 -> 1.0: What is 9 times 8?

## Outputs

- JSON: `experiments/reports/v08_utility_mining/v09_repair_rank16_scale060_det_utility_mining.json`
- Training texts: `experiments/reports/v08_utility_mining/v09_repair_rank16_scale060_det_training_texts.json`

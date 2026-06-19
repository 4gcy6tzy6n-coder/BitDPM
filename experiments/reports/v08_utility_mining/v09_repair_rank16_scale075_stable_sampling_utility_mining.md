# Utility Mining: v09_repair_rank16_scale075_stable_sampling

- Report: `experiments/reports/v09_repair_rank16_scale075_v08_stable_sampling_20260607_200504.json`
- Benchmark: `v08`
- Total prompts: `100`
- Block scale: `0.75`
- Oracle overall: `0.860`
- Selection frequency: `{'baseline': 97, 'arithmetic_addition': 0, 'arithmetic_percent': 0, 'arithmetic_power_log': 2, 'arithmetic_sqrt': 0, 'factual_constants': 1, 'always_all': 0}`

## Bucket Counts

- `baseline_correct_block_wrong`: 82
- `baseline_wrong_block_correct`: 3
- `baseline_wrong_all_wrong`: 14
- `near_miss`: 0

## Unique Utility Counts

- `arithmetic_power_log`: 2
- `factual_constants`: 1

## Positive Delta Samples

- #8 `commonsense` `arithmetic_power_log` 0.0 -> 1.0: What is the speed of light in vacuum?
- #25 `math` `factual_constants` 0.0 -> 1.0: What is the square root of 144?
- #39 `math` `arithmetic_power_log` 0.0 -> 1.0: What is the distance from (0,0) to (3,4)?

## Outputs

- JSON: `experiments/reports/v08_utility_mining/v09_repair_rank16_scale075_stable_sampling_utility_mining.json`
- Training texts: `experiments/reports/v08_utility_mining/v09_repair_rank16_scale075_stable_sampling_training_texts.json`

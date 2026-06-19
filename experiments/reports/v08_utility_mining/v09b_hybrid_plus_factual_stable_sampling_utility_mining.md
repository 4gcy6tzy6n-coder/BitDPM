# Utility Mining: v09b_hybrid_plus_factual_stable_sampling

- Report: `experiments/reports/v09b_hybrid_plus_factual_stable_sampling_20260607_204440.json`
- Benchmark: `v08`
- Total prompts: `100`
- Block scale: `0.75`
- Oracle overall: `0.880`
- Selection frequency: `{'baseline': 95, 'commonsense_choice': 2, 'format_following': 2, 'chinese_semantic': 1, 'calculation_error': 0, 'short_reasoning': 0, 'factual_constants': 0, 'always_all': 0}`

## Bucket Counts

- `baseline_correct_block_wrong`: 62
- `baseline_wrong_block_correct`: 8
- `baseline_wrong_all_wrong`: 12
- `near_miss`: 0

## Unique Utility Counts

- `format_following`: 2
- `chinese_semantic`: 1

## Positive Delta Samples

- #8 `commonsense` `format_following` 0.0 -> 1.0: What is the speed of light in vacuum?
- #25 `math` `commonsense_choice` 0.0 -> 1.0: What is the square root of 144?
- #30 `math` `chinese_semantic` 0.0 -> 1.0: What is 18 + 24?
- #32 `math` `format_following` 0.0 -> 1.0: What is 15% of 80?
- #38 `math` `commonsense_choice` 0.0 -> 1.0: What is log base 10 of 1000?

## Outputs

- JSON: `experiments/reports/v08_utility_mining/v09b_hybrid_plus_factual_stable_sampling_utility_mining.json`
- Training texts: `experiments/reports/v08_utility_mining/v09b_hybrid_plus_factual_stable_sampling_training_texts.json`

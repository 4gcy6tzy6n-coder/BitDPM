# BitDPM v13 Block Safety Cards

- Safety report: `experiments/reports/v08_block_safety/v10_admitted_powerlog_stable_sampling_block_safety.json`
- Registry: `configs/bitdpm_v10_admitted_pool.json`

| Block | Rank | Scale | Fixed | Unique | Overlap | Breaks | Net Unique | Damage Rate | Admitted | Activation |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| arithmetic_power_log | 16 | 0.75 | 0.755 | 1 | 1 | 11 | -10 | 0.133 | yes | single-only |
| short_reasoning | 16 | 0.45 | 0.820 | 0 | 0 | 1 | -1 | 0.012 | yes | single-only |
| commonsense_choice | 16 | 0.60 | 0.820 | 0 | 2 | 3 | -3 | 0.036 | yes | single-only |
| calculation_error | 16 | 0.30 | 0.810 | 0 | 1 | 3 | -3 | 0.036 | yes | single-only |
| chinese_semantic | 16 | 0.75 | 0.800 | 0 | 1 | 6 | -6 | 0.072 | yes | single-only |
| format_following | 16 | 0.75 | 0.640 | 0 | 3 | 23 | -23 | 0.277 | yes | single-only |

## Card Details

### arithmetic_power_log
- Structure: `l22_l24_down`
- Rank: `16`
- Scale: `0.75`
- Unique fixes: 1
- Overlap fixes: 1
- Breaks: 11
- Activation mode: `single-only`
- Damaged categories: `{'chinese': 3, 'code': 2, 'commonsense': 4, 'math': 1, 'reasoning': 1}`

### short_reasoning
- Structure: `l22_l24_down`
- Rank: `16`
- Scale: `0.45`
- Unique fixes: 0
- Overlap fixes: 0
- Breaks: 1
- Activation mode: `single-only`
- Damaged categories: `{'math': 1}`

### commonsense_choice
- Structure: `l22_l24_down`
- Rank: `16`
- Scale: `0.6`
- Unique fixes: 0
- Overlap fixes: 2
- Breaks: 3
- Activation mode: `single-only`
- Damaged categories: `{'commonsense': 2, 'math': 1}`

### calculation_error
- Structure: `l22_l24_down`
- Rank: `16`
- Scale: `0.3`
- Unique fixes: 0
- Overlap fixes: 1
- Breaks: 3
- Activation mode: `single-only`
- Damaged categories: `{'commonsense': 3}`

### chinese_semantic
- Structure: `l22_l24_down`
- Rank: `16`
- Scale: `0.75`
- Unique fixes: 0
- Overlap fixes: 1
- Breaks: 6
- Activation mode: `single-only`
- Damaged categories: `{'chinese': 4, 'commonsense': 1, 'math': 1}`

### format_following
- Structure: `l22_l24_down`
- Rank: `16`
- Scale: `0.75`
- Unique fixes: 0
- Overlap fixes: 3
- Breaks: 23
- Activation mode: `single-only`
- Damaged categories: `{'chinese': 15, 'commonsense': 4, 'math': 1, 'reasoning': 3}`


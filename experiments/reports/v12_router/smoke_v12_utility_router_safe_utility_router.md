# BitDPM v12 Utility-Aware Router Miner

- Report: `experiments/reports/v10_admitted_powerlog_stable_sampling_20260607_212715.json`
- Train samples: 71
- Eval samples: 100
- Rules: 11

## Eval Result

- Router: 0.880
- Baseline: 0.830
- Delta: +0.050
- Fixes: 5
- Breaks: 0
- Precision proxy: 1.000
- Choices: `{'baseline': 87, 'format_following': 4, 'chinese_semantic': 2, 'commonsense_choice': 1, 'arithmetic_power_log': 6}`

## Learned Rules

| Feature | Block | Fixes | Breaks | Precision | Support |
|---|---|---:|---:|---:|---:|
| has_physical_constant | format_following | 1 | 0 | 1.000 | 1 |
| has_speed_light | format_following | 1 | 0 | 1.000 | 1 |
| has_physical_constant | arithmetic_power_log | 1 | 0 | 1.000 | 1 |
| has_speed_light | arithmetic_power_log | 1 | 0 | 1.000 | 1 |
| has_sqrt | commonsense_choice | 1 | 0 | 1.000 | 1 |
| has_sqrt | format_following | 1 | 0 | 1.000 | 1 |
| has_coordinate | arithmetic_power_log | 1 | 0 | 1.000 | 1 |
| has_distance | arithmetic_power_log | 1 | 0 | 1.000 | 1 |
| has_addition | chinese_semantic | 1 | 0 | 1.000 | 2 |
| has_percent | format_following | 1 | 0 | 1.000 | 3 |
| has_3plus_numbers | arithmetic_power_log | 1 | 0 | 1.000 | 2 |

## Eval Fix Samples

- #8 `commonsense` format_following via `has_physical_constant`: What is the speed of light in vacuum?
- #25 `math` commonsense_choice via `has_sqrt`: What is the square root of 144?
- #30 `math` chinese_semantic via `has_addition`: What is 18 + 24?
- #32 `math` format_following via `has_percent`: What is 15% of 80?
- #39 `math` arithmetic_power_log via `has_coordinate`: What is the distance from (0,0) to (3,4)?

## Eval Break Samples


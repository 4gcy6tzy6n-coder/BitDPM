# BitDPM v12 Utility-Aware Router Miner

- Report: `experiments/reports/v10_admitted_powerlog_stable_sampling_20260607_212715.json`
- Train samples: 71
- Eval samples: 100
- Rules: 21

## Eval Result

- Router: 0.850
- Baseline: 0.830
- Delta: +0.020
- Fixes: 3
- Breaks: 1
- Precision proxy: 0.750
- Choices: `{'baseline': 64, 'format_following': 27, 'commonsense_choice': 6, 'arithmetic_power_log': 3}`

## Learned Rules

| Feature | Block | Fixes | Breaks | Precision | Support |
|---|---|---:|---:|---:|---:|
| category=math | format_following | 2 | 0 | 1.000 | 14 |
| has_speed_light | format_following | 1 | 0 | 1.000 | 1 |
| has_physical_constant | format_following | 1 | 0 | 1.000 | 1 |
| has_speed_light | arithmetic_power_log | 1 | 0 | 1.000 | 1 |
| has_physical_constant | arithmetic_power_log | 1 | 0 | 1.000 | 1 |
| has_sqrt | commonsense_choice | 1 | 0 | 1.000 | 1 |
| has_sqrt | format_following | 1 | 0 | 1.000 | 1 |
| has_coordinate | arithmetic_power_log | 1 | 0 | 1.000 | 1 |
| has_distance | arithmetic_power_log | 1 | 0 | 1.000 | 1 |
| has_addition | chinese_semantic | 1 | 0 | 1.000 | 2 |
| has_3plus_numbers | arithmetic_power_log | 1 | 0 | 1.000 | 2 |
| has_percent | format_following | 1 | 0 | 1.000 | 3 |
| has_2plus_numbers | format_following | 1 | 0 | 1.000 | 13 |
| has_2plus_numbers | chinese_semantic | 1 | 0 | 1.000 | 13 |
| has_2plus_numbers | arithmetic_power_log | 1 | 0 | 1.000 | 13 |
| category=math | commonsense_choice | 1 | 0 | 1.000 | 14 |
| category=math | chinese_semantic | 1 | 0 | 1.000 | 14 |
| category=math | arithmetic_power_log | 1 | 0 | 1.000 | 14 |
| has_number | commonsense_choice | 1 | 0 | 1.000 | 23 |
| has_number | chinese_semantic | 1 | 0 | 1.000 | 23 |
| has_number | arithmetic_power_log | 1 | 0 | 1.000 | 23 |

## Eval Fix Samples

- #8 `commonsense` format_following via `has_speed_light`: What is the speed of light in vacuum?
- #25 `math` format_following via `category=math`: What is the square root of 144?
- #32 `math` format_following via `category=math`: What is 15% of 80?

## Eval Break Samples

- #31 `math` format_following via `category=math`: What is 9 times 8?

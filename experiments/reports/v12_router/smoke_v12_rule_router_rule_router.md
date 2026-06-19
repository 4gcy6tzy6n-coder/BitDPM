# BitDPM v12 Rule Router

- Report: `experiments/reports/v10_admitted_powerlog_stable_sampling_20260607_212715.json`
- Router overall: 0.870
- Baseline: 0.830
- Delta: +0.040
- Fixes: 4
- Breaks: 0
- Precision proxy: 1.000
- Chosen counts: `{'baseline': 91, 'format_following': 4, 'commonsense_choice': 1, 'arithmetic_power_log': 4}`

## Rules

- `coordinate_distance_to_power_log` -> `arithmetic_power_log`: `\bdistance\b.*\([^)]*\).*\([^)]*\)|\([^)]*\).*\([^)]*\).*\bdistance\b`
- `log_power_to_power_log` -> `arithmetic_power_log`: `\blog\b|log10|\^|\bpower\b|\bexponent`
- `sqrt_to_commonsense` -> `commonsense_choice`: `\bsqrt\b|square root|√`
- `percent_to_format` -> `format_following`: `%|\bpercent\b|百分`
- `physical_constant_to_format` -> `format_following`: `speed of light|gravity|gravitational|electron|proton|avogadro|planck|boltzmann`

## Fix Samples

- #8 `commonsense` format_following via `physical_constant_to_format`: What is the speed of light in vacuum?
- #25 `math` commonsense_choice via `sqrt_to_commonsense`: What is the square root of 144?
- #32 `math` format_following via `percent_to_format`: What is 15% of 80?
- #39 `math` arithmetic_power_log via `coordinate_distance_to_power_log`: What is the distance from (0,0) to (3,4)?

## Break Samples


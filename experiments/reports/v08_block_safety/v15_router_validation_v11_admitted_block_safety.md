# BitDPM Block Safety Analysis

- Benchmark: `v15`
- Total prompts: `120`
- Global block scale: `0.75`
- Block-specific scales: `{'commonsense_choice': 0.6, 'format_following': 0.75, 'chinese_semantic': 0.75, 'calculation_error': 0.3, 'short_reasoning': 0.45, 'arithmetic_power_log': 0.75, 'v11_stats_number_theory': 0.75}`

| Block | Fixed | Delta | Fixes | Breaks | Net | Unique Fixes | Damaged Categories |
|---|---:|---:|---:|---:|---:|---:|---|
| chinese_semantic | 0.508 | +0.067 | 14 | 6 | 8 | 4 | `{'router_commonsense_repairs': 3, 'router_core_mixed': 1, 'router_factual_constants': 1, 'router_risky_arithmetic': 1}` |
| short_reasoning | 0.475 | +0.033 | 13 | 9 | 4 | 1 | `{'router_commonsense_repairs': 5, 'router_factual_constants': 3, 'router_multiplication': 1}` |
| commonsense_choice | 0.433 | -0.008 | 14 | 15 | -1 | 3 | `{'router_commonsense_controls': 1, 'router_commonsense_repairs': 5, 'router_factual_constants': 4, 'router_multiplication': 1, 'router_risky_arithmetic': 4}` |
| calculation_error | 0.425 | -0.017 | 8 | 10 | -2 | 1 | `{'router_commonsense_repairs': 5, 'router_factual_constants': 3, 'router_multiplication': 1, 'router_risky_arithmetic': 1}` |
| v11_stats_number_theory | 0.417 | -0.025 | 12 | 15 | -3 | 3 | `{'router_commonsense_controls': 1, 'router_commonsense_repairs': 7, 'router_core_mixed': 1, 'router_factual_constants': 4, 'router_multiplication': 1, 'router_risky_arithmetic': 1}` |
| arithmetic_power_log | 0.383 | -0.058 | 13 | 20 | -7 | 2 | `{'router_commonsense_controls': 1, 'router_commonsense_repairs': 6, 'router_core_mixed': 1, 'router_factual_constants': 7, 'router_multiplication': 1, 'router_risky_arithmetic': 4}` |
| format_following | 0.358 | -0.083 | 9 | 19 | -10 | 1 | `{'router_commonsense_controls': 5, 'router_commonsense_repairs': 6, 'router_core_mixed': 1, 'router_factual_constants': 3, 'router_multiplication': 1, 'router_risky_arithmetic': 3}` |

## Unique Fix Samples

### chinese_semantic
- #5 `router_multiplication`: Compute 21 times 6.
- #7 `router_multiplication`: Compute 25 times 4.
- #13 `router_multiplication`: Compute 18 times 7.
- #17 `router_multiplication`: Compute 17 times 9.

### short_reasoning
- #61 `router_factual_constants`: Answer briefly: What is the approximate acceleration due to gravity on Earth in m/s^2?

### commonsense_choice
- #15 `router_multiplication`: Compute 22 times 5.
- #28 `router_core_mixed`: What is log base 10 of 1000?
- #68 `router_factual_constants`: What is Avogadro's number approximately?

### calculation_error
- #82 `router_commonsense_repairs`: Give the common answer: How many continents are commonly counted on Earth?

### v11_stats_number_theory
- #4 `router_multiplication`: What is 21 times 6?
- #32 `router_core_mixed`: What is the mean of 4, 8, 12, and 16?
- #41 `router_risky_arithmetic`: What is 56 + 29?

### arithmetic_power_log
- #20 `router_core_mixed`: What is the distance from (0,0) to (3,4)?
- #53 `router_risky_arithmetic`: What is the square root of 225?

### format_following
- #31 `router_core_mixed`: What is log base 10 of 1000000?


## Break Samples

### chinese_semantic
- #30 `router_core_mixed`: What is log base 10 of 100?
- #42 `router_risky_arithmetic`: What is 123 + 77?
- #74 `router_factual_constants`: Give the standard value: What is the boiling point of water in Celsius?
- #81 `router_commonsense_repairs`: Answer briefly: How many continents are commonly counted on Earth?
- #84 `router_commonsense_repairs`: Which animal is often called the king of the jungle?
- #92 `router_commonsense_repairs`: Which star is closest to Earth?

### short_reasoning
- #11 `router_multiplication`: Compute 16 times 15.
- #66 `router_factual_constants`: Give the standard value: What is the speed of light in vacuum in meters per second?
- #71 `router_factual_constants`: In one short answer, What is Avogadro's number approximately?
- #74 `router_factual_constants`: Give the standard value: What is the boiling point of water in Celsius?
- #81 `router_commonsense_repairs`: Answer briefly: How many continents are commonly counted on Earth?
- #84 `router_commonsense_repairs`: Which animal is often called the king of the jungle?
- #87 `router_commonsense_repairs`: In one short answer, Which animal is often called the king of the jungle?
- #89 `router_commonsense_repairs`: Answer briefly: What do you call money borrowed that must be repaid?
- #96 `router_commonsense_repairs`: What fruit is typically yellow and curved?

### commonsense_choice
- #11 `router_multiplication`: Compute 16 times 15.
- #42 `router_risky_arithmetic`: What is 123 + 77?
- #43 `router_risky_arithmetic`: What is 208 + 315?
- #45 `router_risky_arithmetic`: What is 72 + 38?
- #46 `router_risky_arithmetic`: What is 145 + 255?
- #60 `router_factual_constants`: What is the approximate acceleration due to gravity on Earth in m/s^2?
- #64 `router_factual_constants`: What is the speed of light in vacuum in meters per second?
- #71 `router_factual_constants`: In one short answer, What is Avogadro's number approximately?
- #78 `router_factual_constants`: Give the standard value: What is the freezing point of water in Celsius?
- #81 `router_commonsense_repairs`: Answer briefly: How many continents are commonly counted on Earth?
- #84 `router_commonsense_repairs`: Which animal is often called the king of the jungle?
- #90 `router_commonsense_repairs`: Give the common answer: What do you call money borrowed that must be repaid?
- #92 `router_commonsense_repairs`: Which star is closest to Earth?
- #93 `router_commonsense_repairs`: Answer briefly: Which star is closest to Earth?
- #117 `router_commonsense_controls`: Answer briefly: What vehicle runs on rails?

### calculation_error
- #11 `router_multiplication`: Compute 16 times 15.
- #46 `router_risky_arithmetic`: What is 145 + 255?
- #60 `router_factual_constants`: What is the approximate acceleration due to gravity on Earth in m/s^2?
- #64 `router_factual_constants`: What is the speed of light in vacuum in meters per second?
- #78 `router_factual_constants`: Give the standard value: What is the freezing point of water in Celsius?
- #84 `router_commonsense_repairs`: Which animal is often called the king of the jungle?
- #87 `router_commonsense_repairs`: In one short answer, Which animal is often called the king of the jungle?
- #89 `router_commonsense_repairs`: Answer briefly: What do you call money borrowed that must be repaid?
- #90 `router_commonsense_repairs`: Give the common answer: What do you call money borrowed that must be repaid?
- #96 `router_commonsense_repairs`: What fruit is typically yellow and curved?

### v11_stats_number_theory
- #11 `router_multiplication`: Compute 16 times 15.
- #30 `router_core_mixed`: What is log base 10 of 100?
- #42 `router_risky_arithmetic`: What is 123 + 77?
- #63 `router_factual_constants`: In one short answer, What is the approximate acceleration due to gravity on Earth in m/s^2?
- #66 `router_factual_constants`: Give the standard value: What is the speed of light in vacuum in meters per second?
- #71 `router_factual_constants`: In one short answer, What is Avogadro's number approximately?
- #74 `router_factual_constants`: Give the standard value: What is the boiling point of water in Celsius?
- #81 `router_commonsense_repairs`: Answer briefly: How many continents are commonly counted on Earth?
- #84 `router_commonsense_repairs`: Which animal is often called the king of the jungle?
- #90 `router_commonsense_repairs`: Give the common answer: What do you call money borrowed that must be repaid?
- #91 `router_commonsense_repairs`: In one short answer, What do you call money borrowed that must be repaid?
- #93 `router_commonsense_repairs`: Answer briefly: Which star is closest to Earth?
- #95 `router_commonsense_repairs`: In one short answer, Which star is closest to Earth?
- #96 `router_commonsense_repairs`: What fruit is typically yellow and curved?
- #112 `router_commonsense_controls`: Answer briefly: Which organ pumps blood through the body?

### arithmetic_power_log
- #11 `router_multiplication`: Compute 16 times 15.
- #30 `router_core_mixed`: What is log base 10 of 100?
- #42 `router_risky_arithmetic`: What is 123 + 77?
- #43 `router_risky_arithmetic`: What is 208 + 315?
- #45 `router_risky_arithmetic`: What is 72 + 38?
- #46 `router_risky_arithmetic`: What is 145 + 255?
- #60 `router_factual_constants`: What is the approximate acceleration due to gravity on Earth in m/s^2?
- #64 `router_factual_constants`: What is the speed of light in vacuum in meters per second?
- #66 `router_factual_constants`: Give the standard value: What is the speed of light in vacuum in meters per second?
- #69 `router_factual_constants`: Answer briefly: What is Avogadro's number approximately?
- #71 `router_factual_constants`: In one short answer, What is Avogadro's number approximately?
- #72 `router_factual_constants`: What is the boiling point of water in Celsius?
- #73 `router_factual_constants`: Answer briefly: What is the boiling point of water in Celsius?
- #81 `router_commonsense_repairs`: Answer briefly: How many continents are commonly counted on Earth?
- #84 `router_commonsense_repairs`: Which animal is often called the king of the jungle?
- #87 `router_commonsense_repairs`: In one short answer, Which animal is often called the king of the jungle?
- #90 `router_commonsense_repairs`: Give the common answer: What do you call money borrowed that must be repaid?
- #91 `router_commonsense_repairs`: In one short answer, What do you call money borrowed that must be repaid?
- #96 `router_commonsense_repairs`: What fruit is typically yellow and curved?
- #117 `router_commonsense_controls`: Answer briefly: What vehicle runs on rails?

### format_following
- #11 `router_multiplication`: Compute 16 times 15.
- #30 `router_core_mixed`: What is log base 10 of 100?
- #42 `router_risky_arithmetic`: What is 123 + 77?
- #43 `router_risky_arithmetic`: What is 208 + 315?
- #46 `router_risky_arithmetic`: What is 145 + 255?
- #66 `router_factual_constants`: Give the standard value: What is the speed of light in vacuum in meters per second?
- #69 `router_factual_constants`: Answer briefly: What is Avogadro's number approximately?
- #71 `router_factual_constants`: In one short answer, What is Avogadro's number approximately?
- #81 `router_commonsense_repairs`: Answer briefly: How many continents are commonly counted on Earth?
- #89 `router_commonsense_repairs`: Answer briefly: What do you call money borrowed that must be repaid?
- #90 `router_commonsense_repairs`: Give the common answer: What do you call money borrowed that must be repaid?
- #91 `router_commonsense_repairs`: In one short answer, What do you call money borrowed that must be repaid?
- #93 `router_commonsense_repairs`: Answer briefly: Which star is closest to Earth?
- #96 `router_commonsense_repairs`: What fruit is typically yellow and curved?
- #102 `router_commonsense_controls`: Which organ pumps blood through the body?
- #107 `router_commonsense_controls`: What vehicle runs on rails?
- #112 `router_commonsense_controls`: Answer briefly: Which organ pumps blood through the body?
- #116 `router_commonsense_controls`: Answer briefly: What do we call frozen water?
- #117 `router_commonsense_controls`: Answer briefly: What vehicle runs on rails?


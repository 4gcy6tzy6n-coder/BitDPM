# BitDPM Block Safety Analysis

- Benchmark: `v08`
- Total prompts: `100`
- Global block scale: `0.6`
- Block-specific scales: `{'arithmetic_addition': 0.6, 'arithmetic_percent': 0.6, 'arithmetic_power_log': 0.6, 'arithmetic_sqrt': 0.6, 'factual_constants': 0.6}`

| Block | Fixed | Delta | Fixes | Breaks | Net | Unique Fixes | Damaged Categories |
|---|---:|---:|---:|---:|---:|---:|---|
| arithmetic_power_log | 0.800 | +0.000 | 2 | 3 | -1 | 0 | `{'chinese': 2, 'code': 1}` |
| arithmetic_percent | 0.790 | -0.010 | 2 | 3 | -1 | 0 | `{'chinese': 1, 'commonsense': 1, 'reasoning': 1}` |
| factual_constants | 0.790 | -0.010 | 2 | 4 | -2 | 2 | `{'chinese': 3, 'commonsense': 1}` |
| arithmetic_addition | 0.780 | -0.020 | 0 | 3 | -3 | 0 | `{'chinese': 3}` |
| arithmetic_sqrt | 0.735 | -0.065 | 1 | 8 | -7 | 0 | `{'chinese': 7, 'commonsense': 1}` |

## Unique Fix Samples

### factual_constants
- #8 `commonsense`: What is the speed of light in vacuum?
- #25 `math`: What is the square root of 144?


## Break Samples

### arithmetic_power_log
- #55 `code`: Write SQL to select all rows from a users table.
- #62 `chinese`: 一年有多少个月？
- #66 `chinese`: 请列举三种水果。

### arithmetic_percent
- #19 `commonsense`: What do bees produce?
- #62 `chinese`: 一年有多少个月？
- #88 `reasoning`: What comes next in the sequence: 2, 3, 5, 7, 11, ___?

### factual_constants
- #12 `commonsense`: Which animal is known as the king of the jungle?
- #62 `chinese`: 一年有多少个月？
- #68 `chinese`: 请用中文写一句问候语。
- #71 `chinese`: 中国的四大发明是什么？

### arithmetic_addition
- #62 `chinese`: 一年有多少个月？
- #68 `chinese`: 请用中文写一句问候语。
- #71 `chinese`: 中国的四大发明是什么？

### arithmetic_sqrt
- #12 `commonsense`: Which animal is known as the king of the jungle?
- #60 `chinese`: 中国的首都是哪个城市？
- #62 `chinese`: 一年有多少个月？
- #64 `chinese`: 什么是机器学习？请用中文回答。
- #67 `chinese`: 太阳从哪个方向升起？
- #71 `chinese`: 中国的四大发明是什么？
- #74 `chinese`: 长城位于哪个国家？
- #76 `chinese`: 什么是高铁？


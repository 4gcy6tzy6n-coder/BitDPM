# BitDPM Block Safety Analysis

- Benchmark: `v08`
- Total prompts: `100`
- Global block scale: `0.6`
- Block-specific scales: `{'commonsense_choice': 0.6, 'calculation_error': 0.6, 'format_following': 0.3, 'chinese_semantic': 0.45, 'short_reasoning': 0.45}`

| Block | Fixed | Delta | Fixes | Breaks | Net | Unique Fixes | Damaged Categories |
|---|---:|---:|---:|---:|---:|---:|---|
| commonsense_choice | 0.830 | +0.030 | 3 | 0 | 3 | 3 | `{}` |
| chinese_semantic | 0.800 | +0.000 | 0 | 0 | 0 | 0 | `{}` |
| calculation_error | 0.790 | -0.010 | 1 | 3 | -2 | 1 | `{'chinese': 2, 'math': 1}` |
| format_following | 0.785 | -0.015 | 0 | 2 | -2 | 0 | `{'chinese': 2}` |
| short_reasoning | 0.785 | -0.015 | 0 | 2 | -2 | 0 | `{'chinese': 1, 'commonsense': 1}` |

## Unique Fix Samples

### commonsense_choice
- #5 `commonsense`: Who wrote Romeo and Juliet?
- #25 `math`: What is the square root of 144?
- #38 `math`: What is log base 10 of 1000?

### calculation_error
- #28 `math`: What is 2^10?


## Break Samples

### calculation_error
- #20 `math`: Calculate 15 + 27 =
- #68 `chinese`: 请用中文写一句问候语。
- #74 `chinese`: 长城位于哪个国家？

### format_following
- #62 `chinese`: 一年有多少个月？
- #65 `chinese`: 水的化学式是什么？

### short_reasoning
- #12 `commonsense`: Which animal is known as the king of the jungle?
- #65 `chinese`: 水的化学式是什么？


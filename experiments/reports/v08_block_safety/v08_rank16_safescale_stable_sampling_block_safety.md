# BitDPM Block Safety Analysis

- Benchmark: `v08`
- Total prompts: `100`
- Global block scale: `0.75`
- Block-specific scales: `{'commonsense_choice': 0.6, 'format_following': 0.45, 'calculation_error': 0.3, 'chinese_semantic': 0.45, 'short_reasoning': 0.45}`

| Block | Fixed | Delta | Fixes | Breaks | Net | Unique Fixes | Damaged Categories |
|---|---:|---:|---:|---:|---:|---:|---|
| commonsense_choice | 0.820 | -0.010 | 2 | 3 | -1 | 0 | `{'commonsense': 2, 'math': 1}` |
| short_reasoning | 0.820 | -0.010 | 0 | 1 | -1 | 0 | `{'math': 1}` |
| calculation_error | 0.810 | -0.020 | 1 | 3 | -2 | 0 | `{'commonsense': 3}` |
| chinese_semantic | 0.810 | -0.020 | 0 | 2 | -2 | 0 | `{'commonsense': 1, 'math': 1}` |
| format_following | 0.790 | -0.040 | 1 | 6 | -5 | 0 | `{'chinese': 4, 'commonsense': 1, 'math': 1}` |

## Unique Fix Samples


## Break Samples

### commonsense_choice
- #5 `commonsense`: Who wrote Romeo and Juliet?
- #7 `commonsense`: How many continents are there?
- #31 `math`: What is 9 times 8?

### short_reasoning
- #31 `math`: What is 9 times 8?

### calculation_error
- #5 `commonsense`: Who wrote Romeo and Juliet?
- #7 `commonsense`: How many continents are there?
- #12 `commonsense`: Which animal is known as the king of the jungle?

### chinese_semantic
- #7 `commonsense`: How many continents are there?
- #31 `math`: What is 9 times 8?

### format_following
- #7 `commonsense`: How many continents are there?
- #31 `math`: What is 9 times 8?
- #62 `chinese`: 一年有多少个月？
- #65 `chinese`: 水的化学式是什么？
- #67 `chinese`: 太阳从哪个方向升起？
- #71 `chinese`: 中国的四大发明是什么？


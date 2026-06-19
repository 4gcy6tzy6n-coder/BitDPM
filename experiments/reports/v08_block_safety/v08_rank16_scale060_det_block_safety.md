# BitDPM Block Safety Analysis

- Benchmark: `v08`
- Total prompts: `100`
- Global block scale: `0.6`
- Block-specific scales: `{}`

| Block | Fixed | Delta | Fixes | Breaks | Net | Unique Fixes | Damaged Categories |
|---|---:|---:|---:|---:|---:|---:|---|
| commonsense_choice | 0.830 | +0.030 | 3 | 0 | 3 | 2 | `{}` |
| calculation_error | 0.790 | -0.010 | 1 | 3 | -2 | 1 | `{'chinese': 2, 'math': 1}` |
| chinese_semantic | 0.790 | -0.010 | 0 | 2 | -2 | 0 | `{'chinese': 2}` |
| short_reasoning | 0.790 | -0.010 | 0 | 2 | -2 | 0 | `{'chinese': 2}` |
| format_following | 0.705 | -0.095 | 1 | 13 | -12 | 0 | `{'chinese': 12, 'commonsense': 1}` |

## Unique Fix Samples

### commonsense_choice
- #25 `math`: What is the square root of 144?
- #38 `math`: What is log base 10 of 1000?

### calculation_error
- #28 `math`: What is 2^10?


## Break Samples

### calculation_error
- #20 `math`: Calculate 15 + 27 =
- #68 `chinese`: 请用中文写一句问候语。
- #74 `chinese`: 长城位于哪个国家？

### chinese_semantic
- #65 `chinese`: 水的化学式是什么？
- #68 `chinese`: 请用中文写一句问候语。

### short_reasoning
- #65 `chinese`: 水的化学式是什么？
- #71 `chinese`: 中国的四大发明是什么？

### format_following
- #12 `commonsense`: Which animal is known as the king of the jungle?
- #60 `chinese`: 中国的首都是哪个城市？
- #62 `chinese`: 一年有多少个月？
- #64 `chinese`: 什么是机器学习？请用中文回答。
- #65 `chinese`: 水的化学式是什么？
- #67 `chinese`: 太阳从哪个方向升起？
- #68 `chinese`: 请用中文写一句问候语。
- #69 `chinese`: 什么是自然语言处理？
- #71 `chinese`: 中国的四大发明是什么？
- #74 `chinese`: 长城位于哪个国家？
- #76 `chinese`: 什么是高铁？
- #78 `chinese`: 孔子是中国古代的什么人物？
- #79 `chinese`: 请写一句关于学习的中文句子。


# BitDPM Block Safety Analysis

- Benchmark: `v08`
- Total prompts: `100`
- Global block scale: `0.75`
- Block-specific scales: `{'commonsense_choice': 0.6, 'format_following': 0.75, 'chinese_semantic': 0.75, 'calculation_error': 0.3, 'short_reasoning': 0.45}`

| Block | Fixed | Delta | Fixes | Breaks | Net | Unique Fixes | Damaged Categories |
|---|---:|---:|---:|---:|---:|---:|---|
| commonsense_choice | 0.820 | -0.010 | 2 | 3 | -1 | 0 | `{'commonsense': 2, 'math': 1}` |
| short_reasoning | 0.820 | -0.010 | 0 | 1 | -1 | 0 | `{'math': 1}` |
| calculation_error | 0.810 | -0.020 | 1 | 3 | -2 | 0 | `{'commonsense': 3}` |
| chinese_semantic | 0.800 | -0.030 | 1 | 6 | -5 | 1 | `{'chinese': 4, 'commonsense': 1, 'math': 1}` |
| format_following | 0.640 | -0.190 | 3 | 23 | -20 | 2 | `{'chinese': 15, 'commonsense': 4, 'math': 1, 'reasoning': 3}` |

## Unique Fix Samples

### chinese_semantic
- #30 `math`: What is 18 + 24?

### format_following
- #8 `commonsense`: What is the speed of light in vacuum?
- #32 `math`: What is 15% of 80?


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
- #65 `chinese`: 水的化学式是什么？
- #68 `chinese`: 请用中文写一句问候语。
- #70 `chinese`: 中秋节通常会吃什么？
- #74 `chinese`: 长城位于哪个国家？

### format_following
- #7 `commonsense`: How many continents are there?
- #9 `commonsense`: Which gas do plants absorb from the atmosphere?
- #12 `commonsense`: Which animal is known as the king of the jungle?
- #17 `commonsense`: Which organ pumps blood through the body?
- #31 `math`: What is 9 times 8?
- #60 `chinese`: 中国的首都是哪个城市？
- #62 `chinese`: 一年有多少个月？
- #64 `chinese`: 什么是机器学习？请用中文回答。
- #65 `chinese`: 水的化学式是什么？
- #66 `chinese`: 请列举三种水果。
- #67 `chinese`: 太阳从哪个方向升起？
- #68 `chinese`: 请用中文写一句问候语。
- #69 `chinese`: 什么是自然语言处理？
- #70 `chinese`: 中秋节通常会吃什么？
- #71 `chinese`: 中国的四大发明是什么？
- #73 `chinese`: 春节有哪些常见习俗？
- #74 `chinese`: 长城位于哪个国家？
- #76 `chinese`: 什么是高铁？
- #78 `chinese`: 孔子是中国古代的什么人物？
- #79 `chinese`: 请写一句关于学习的中文句子。
- ... 3 more


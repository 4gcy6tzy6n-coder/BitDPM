# BitDPM Block Safety Analysis

- Benchmark: `v14`
- Total prompts: `60`
- Global block scale: `0.75`
- Block-specific scales: `{'commonsense_choice': 0.6, 'format_following': 0.75, 'chinese_semantic': 0.75, 'calculation_error': 0.3, 'short_reasoning': 0.45, 'arithmetic_power_log': 0.75}`

| Block | Fixed | Delta | Fixes | Breaks | Net | Unique Fixes | Damaged Categories |
|---|---:|---:|---:|---:|---:|---:|---|
| calculation_error | 0.892 | +0.025 | 3 | 2 | 1 | 0 | `{'arithmetic': 1, 'chinese': 1}` |
| chinese_semantic | 0.883 | +0.017 | 4 | 3 | 1 | 1 | `{'arithmetic': 2, 'factual_constants': 1}` |
| short_reasoning | 0.817 | -0.050 | 2 | 5 | -3 | 0 | `{'arithmetic': 3, 'factual_constants': 2}` |
| commonsense_choice | 0.767 | -0.100 | 1 | 7 | -6 | 0 | `{'arithmetic': 3, 'chinese': 1, 'commonsense': 1, 'factual_constants': 2}` |
| arithmetic_power_log | 0.692 | -0.175 | 2 | 13 | -11 | 0 | `{'arithmetic': 5, 'chinese': 1, 'factual_constants': 6, 'reasoning': 1}` |
| format_following | 0.667 | -0.200 | 0 | 13 | -13 | 0 | `{'arithmetic': 2, 'chinese': 9, 'commonsense': 2}` |

## Unique Fix Samples

### chinese_semantic
- #16 `factual_constants`: Answer briefly: What is the approximate acceleration due to gravity on Earth in m/s^2?


## Break Samples

### calculation_error
- #2 `arithmetic`: What is 56 + 29?
- #49 `chinese`: 长城位于哪个国家？ 请简短回答。版本1。

### chinese_semantic
- #2 `arithmetic`: What is 56 + 29?
- #3 `arithmetic`: What is 123 + 77?
- #15 `factual_constants`: What is the approximate acceleration due to gravity on Earth in m/s^2?

### short_reasoning
- #1 `arithmetic`: What is 37 + 45?
- #2 `arithmetic`: What is 56 + 29?
- #3 `arithmetic`: What is 123 + 77?
- #12 `factual_constants`: Give the standard value: What is the speed of light in vacuum in meters per second?
- #15 `factual_constants`: What is the approximate acceleration due to gravity on Earth in m/s^2?

### commonsense_choice
- #2 `arithmetic`: What is 56 + 29?
- #3 `arithmetic`: What is 123 + 77?
- #4 `arithmetic`: What is 208 + 315?
- #10 `factual_constants`: What is the speed of light in vacuum in meters per second?
- #15 `factual_constants`: What is the approximate acceleration due to gravity on Earth in m/s^2?
- #26 `commonsense`: What do bees produce?
- #40 `chinese`: 中国的首都是哪个城市？ 请简短回答。版本1。

### arithmetic_power_log
- #1 `arithmetic`: What is 37 + 45?
- #2 `arithmetic`: What is 56 + 29?
- #3 `arithmetic`: What is 123 + 77?
- #4 `arithmetic`: What is 208 + 315?
- #6 `arithmetic`: What is 72 + 38?
- #10 `factual_constants`: What is the speed of light in vacuum in meters per second?
- #11 `factual_constants`: Answer briefly: What is the speed of light in vacuum in meters per second?
- #12 `factual_constants`: Give the standard value: What is the speed of light in vacuum in meters per second?
- #15 `factual_constants`: What is the approximate acceleration due to gravity on Earth in m/s^2?
- #18 `factual_constants`: In one short answer, What is the approximate acceleration due to gravity on Earth in m/s^2?
- #19 `factual_constants`: State the commonly used answer: What is the approximate acceleration due to gravity on Earth in m/s^2?
- #40 `chinese`: 中国的首都是哪个城市？ 请简短回答。版本1。
- #52 `reasoning`: If today is Monday, what day will it be in 10 days? Explain briefly. Variant 1.

### format_following
- #3 `arithmetic`: What is 123 + 77?
- #4 `arithmetic`: What is 208 + 315?
- #25 `commonsense`: Which organ pumps blood through the body?
- #27 `commonsense`: Which gas do plants absorb from the atmosphere?
- #40 `chinese`: 中国的首都是哪个城市？ 请简短回答。版本1。
- #41 `chinese`: 请用中文解释什么是人工智能。 请简短回答。版本1。
- #42 `chinese`: 一年有多少个月？ 请简短回答。版本1。
- #43 `chinese`: 请写一句关于学习的中文句子。 请简短回答。版本1。
- #44 `chinese`: 水的化学式是什么？ 请简短回答。版本1。
- #45 `chinese`: 太阳从哪个方向升起？ 请简短回答。版本1。
- #46 `chinese`: 什么是自然语言处理？ 请简短回答。版本1。
- #47 `chinese`: 中秋节通常会吃什么？ 请简短回答。版本1。
- #49 `chinese`: 长城位于哪个国家？ 请简短回答。版本1。


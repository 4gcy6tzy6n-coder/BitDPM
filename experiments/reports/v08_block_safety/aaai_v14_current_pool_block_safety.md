# BitDPM Block Safety Analysis

- Benchmark: `v14`
- Total prompts: `300`
- Global block scale: `0.75`
- Block-specific scales: `{'commonsense_choice': 0.6, 'format_following': 0.75, 'chinese_semantic': 0.75, 'calculation_error': 0.3, 'short_reasoning': 0.45, 'arithmetic_power_log': 0.75, 'v11_stats_number_theory': 0.75}`

| Block | Fixed | Delta | Fixes | Breaks | Net | Unique Fixes | Damaged Categories |
|---|---:|---:|---:|---:|---:|---:|---|
| calculation_error | 0.833 | -0.007 | 5 | 7 | -2 | 1 | `{'arithmetic': 1, 'commonsense': 3, 'factual_constants': 3}` |
| short_reasoning | 0.805 | -0.035 | 4 | 18 | -14 | 0 | `{'arithmetic': 3, 'chinese': 7, 'commonsense': 1, 'factual_constants': 5, 'reasoning': 2}` |
| chinese_semantic | 0.793 | -0.047 | 4 | 22 | -18 | 0 | `{'arithmetic': 3, 'chinese': 12, 'commonsense': 2, 'factual_constants': 5}` |
| v11_stats_number_theory | 0.788 | -0.052 | 10 | 31 | -21 | 5 | `{'arithmetic': 3, 'chinese': 20, 'commonsense': 3, 'factual_constants': 3, 'reasoning': 2}` |
| commonsense_choice | 0.735 | -0.105 | 2 | 34 | -32 | 0 | `{'arithmetic': 5, 'chinese': 11, 'commonsense': 3, 'factual_constants': 7, 'reasoning': 8}` |
| format_following | 0.642 | -0.198 | 4 | 67 | -63 | 1 | `{'arithmetic': 4, 'chinese': 41, 'commonsense': 9, 'factual_constants': 11, 'reasoning': 2}` |
| arithmetic_power_log | 0.613 | -0.227 | 5 | 76 | -71 | 0 | `{'arithmetic': 8, 'chinese': 12, 'code': 11, 'commonsense': 1, 'factual_constants': 11, 'reasoning': 33}` |

## Unique Fix Samples

### calculation_error
- #111 `commonsense`: Which animal is often called the king of the jungle?

### v11_stats_number_theory
- #8 `arithmetic`: What is 9 times 8?
- #9 `arithmetic`: What is 12 times 11?
- #42 `arithmetic`: What is the distance from (0,0) to (8,15)?
- #47 `arithmetic`: What is the mean of 4, 8, 12, and 16?
- #56 `factual_constants`: Answer briefly: What is the approximate acceleration due to gravity on Earth in m/s^2?

### format_following
- #45 `arithmetic`: What is log base 10 of 1000?


## Break Samples

### calculation_error
- #2 `arithmetic`: What is 56 + 29?
- #60 `factual_constants`: What is Avogadro's number approximately?
- #87 `factual_constants`: Give the standard value: How many bytes are in one kilobyte in binary computing?
- #93 `factual_constants`: In one short answer, How many centimeters are in one meter?
- #114 `commonsense`: Who wrote Romeo and Juliet?
- #132 `commonsense`: What fruit is typically yellow and curved?
- #144 `commonsense`: What is the opposite of left?

### short_reasoning
- #1 `arithmetic`: What is 37 + 45?
- #2 `arithmetic`: What is 56 + 29?
- #3 `arithmetic`: What is 123 + 77?
- #52 `factual_constants`: Give the standard value: What is the speed of light in vacuum in meters per second?
- #60 `factual_constants`: What is Avogadro's number approximately?
- #63 `factual_constants`: In one short answer, What is Avogadro's number approximately?
- #64 `factual_constants`: State the commonly used answer: What is Avogadro's number approximately?
- #77 `factual_constants`: Give the standard value: What is the boiling point of water in Celsius?
- #132 `commonsense`: What fruit is typically yellow and curved?
- #214 `chinese`: 水的化学式是什么？ 请简短回答。版本2。
- #224 `chinese`: 水的化学式是什么？ 请简短回答。版本3。
- #233 `chinese`: 请写一句关于学习的中文句子。 请简短回答。版本4。
- #234 `chinese`: 水的化学式是什么？ 请简短回答。版本4。
- #235 `chinese`: 太阳从哪个方向升起？ 请简短回答。版本4。
- #244 `chinese`: 水的化学式是什么？ 请简短回答。版本5。
- #248 `chinese`: 请列举三种水果。 请简短回答。版本5。
- #276 `reasoning`: If one box holds 6 bottles, how many boxes are needed for 26 bottles? Explain briefly. Variant 3.
- #286 `reasoning`: If one box holds 6 bottles, how many boxes are needed for 26 bottles? Explain briefly. Variant 4.

### chinese_semantic
- #2 `arithmetic`: What is 56 + 29?
- #3 `arithmetic`: What is 123 + 77?
- #26 `arithmetic`: What is the square root of 196?
- #60 `factual_constants`: What is Avogadro's number approximately?
- #63 `factual_constants`: In one short answer, What is Avogadro's number approximately?
- #82 `factual_constants`: Give the standard value: What is the freezing point of water in Celsius?
- #91 `factual_constants`: Answer briefly: How many centimeters are in one meter?
- #93 `factual_constants`: In one short answer, How many centimeters are in one meter?
- #114 `commonsense`: Who wrote Romeo and Juliet?
- #117 `commonsense`: Which star is closest to Earth?
- #202 `chinese`: 一年有多少个月？ 请简短回答。版本1。
- #212 `chinese`: 一年有多少个月？ 请简短回答。版本2。
- #213 `chinese`: 请写一句关于学习的中文句子。 请简短回答。版本2。
- #214 `chinese`: 水的化学式是什么？ 请简短回答。版本2。
- #222 `chinese`: 一年有多少个月？ 请简短回答。版本3。
- #223 `chinese`: 请写一句关于学习的中文句子。 请简短回答。版本3。
- #225 `chinese`: 太阳从哪个方向升起？ 请简短回答。版本3。
- #229 `chinese`: 长城位于哪个国家？ 请简短回答。版本3。
- #232 `chinese`: 一年有多少个月？ 请简短回答。版本4。
- #242 `chinese`: 一年有多少个月？ 请简短回答。版本5。
- ... 2 more

### v11_stats_number_theory
- #2 `arithmetic`: What is 56 + 29?
- #3 `arithmetic`: What is 123 + 77?
- #26 `arithmetic`: What is the square root of 196?
- #52 `factual_constants`: Give the standard value: What is the speed of light in vacuum in meters per second?
- #60 `factual_constants`: What is Avogadro's number approximately?
- #63 `factual_constants`: In one short answer, What is Avogadro's number approximately?
- #117 `commonsense`: Which star is closest to Earth?
- #132 `commonsense`: What fruit is typically yellow and curved?
- #133 `commonsense`: What do you call the place where books are kept for borrowing?
- #202 `chinese`: 一年有多少个月？ 请简短回答。版本1。
- #207 `chinese`: 中秋节通常会吃什么？ 请简短回答。版本1。
- #210 `chinese`: 中国的首都是哪个城市？ 请简短回答。版本2。
- #212 `chinese`: 一年有多少个月？ 请简短回答。版本2。
- #213 `chinese`: 请写一句关于学习的中文句子。 请简短回答。版本2。
- #214 `chinese`: 水的化学式是什么？ 请简短回答。版本2。
- #220 `chinese`: 中国的首都是哪个城市？ 请简短回答。版本3。
- #222 `chinese`: 一年有多少个月？ 请简短回答。版本3。
- #223 `chinese`: 请写一句关于学习的中文句子。 请简短回答。版本3。
- #225 `chinese`: 太阳从哪个方向升起？ 请简短回答。版本3。
- #230 `chinese`: 中国的首都是哪个城市？ 请简短回答。版本4。
- ... 11 more

### commonsense_choice
- #2 `arithmetic`: What is 56 + 29?
- #3 `arithmetic`: What is 123 + 77?
- #4 `arithmetic`: What is 208 + 315?
- #26 `arithmetic`: What is the square root of 196?
- #29 `arithmetic`: What is the square root of 81?
- #50 `factual_constants`: What is the speed of light in vacuum in meters per second?
- #52 `factual_constants`: Give the standard value: What is the speed of light in vacuum in meters per second?
- #63 `factual_constants`: In one short answer, What is Avogadro's number approximately?
- #64 `factual_constants`: State the commonly used answer: What is Avogadro's number approximately?
- #82 `factual_constants`: Give the standard value: What is the freezing point of water in Celsius?
- #96 `factual_constants`: Answer briefly: How many millimeters are in one centimeter?
- #99 `factual_constants`: State the commonly used answer: How many millimeters are in one centimeter?
- #130 `commonsense`: Which sense uses the ears?
- #142 `commonsense`: What machine is used to take photographs?
- #144 `commonsense`: What is the opposite of left?
- #200 `chinese`: 中国的首都是哪个城市？ 请简短回答。版本1。
- #210 `chinese`: 中国的首都是哪个城市？ 请简短回答。版本2。
- #216 `chinese`: 什么是自然语言处理？ 请简短回答。版本2。
- #219 `chinese`: 长城位于哪个国家？ 请简短回答。版本2。
- #220 `chinese`: 中国的首都是哪个城市？ 请简短回答。版本3。
- ... 14 more

### format_following
- #3 `arithmetic`: What is 123 + 77?
- #4 `arithmetic`: What is 208 + 315?
- #14 `arithmetic`: What is 32 times 3?
- #26 `arithmetic`: What is the square root of 196?
- #52 `factual_constants`: Give the standard value: What is the speed of light in vacuum in meters per second?
- #60 `factual_constants`: What is Avogadro's number approximately?
- #61 `factual_constants`: Answer briefly: What is Avogadro's number approximately?
- #63 `factual_constants`: In one short answer, What is Avogadro's number approximately?
- #64 `factual_constants`: State the commonly used answer: What is Avogadro's number approximately?
- #87 `factual_constants`: Give the standard value: How many bytes are in one kilobyte in binary computing?
- #91 `factual_constants`: Answer briefly: How many centimeters are in one meter?
- #93 `factual_constants`: In one short answer, How many centimeters are in one meter?
- #94 `factual_constants`: State the commonly used answer: How many centimeters are in one meter?
- #96 `factual_constants`: Answer briefly: How many millimeters are in one centimeter?
- #98 `factual_constants`: In one short answer, How many millimeters are in one centimeter?
- #105 `commonsense`: Which organ pumps blood through the body?
- #106 `commonsense`: What do bees produce?
- #107 `commonsense`: Which gas do plants absorb from the atmosphere?
- #119 `commonsense`: Which direction does the sun rise from?
- #122 `commonsense`: What vehicle runs on rails?
- ... 47 more

### arithmetic_power_log
- #1 `arithmetic`: What is 37 + 45?
- #2 `arithmetic`: What is 56 + 29?
- #3 `arithmetic`: What is 123 + 77?
- #4 `arithmetic`: What is 208 + 315?
- #6 `arithmetic`: What is 72 + 38?
- #14 `arithmetic`: What is 32 times 3?
- #26 `arithmetic`: What is the square root of 196?
- #37 `arithmetic`: What is 6^2?
- #50 `factual_constants`: What is the speed of light in vacuum in meters per second?
- #52 `factual_constants`: Give the standard value: What is the speed of light in vacuum in meters per second?
- #58 `factual_constants`: In one short answer, What is the approximate acceleration due to gravity on Earth in m/s^2?
- #59 `factual_constants`: State the commonly used answer: What is the approximate acceleration due to gravity on Earth in m/s^2?
- #60 `factual_constants`: What is Avogadro's number approximately?
- #61 `factual_constants`: Answer briefly: What is Avogadro's number approximately?
- #63 `factual_constants`: In one short answer, What is Avogadro's number approximately?
- #64 `factual_constants`: State the commonly used answer: What is Avogadro's number approximately?
- #75 `factual_constants`: What is the boiling point of water in Celsius?
- #80 `factual_constants`: What is the freezing point of water in Celsius?
- #82 `factual_constants`: Give the standard value: What is the freezing point of water in Celsius?
- #132 `commonsense`: What fruit is typically yellow and curved?
- ... 56 more


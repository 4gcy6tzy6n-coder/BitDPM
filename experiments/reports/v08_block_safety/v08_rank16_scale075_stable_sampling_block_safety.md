# BitDPM Block Safety Analysis

- Benchmark: `v08`
- Total prompts: `100`
- Global block scale: `0.75`
- Block-specific scales: `{}`

| Block | Fixed | Delta | Fixes | Breaks | Net | Unique Fixes | Damaged Categories |
|---|---:|---:|---:|---:|---:|---:|---|
| chinese_semantic | 0.800 | -0.030 | 1 | 6 | -5 | 0 | `{'chinese': 4, 'commonsense': 1, 'math': 1}` |
| commonsense_choice | 0.785 | -0.045 | 1 | 6 | -5 | 0 | `{'chinese': 3, 'commonsense': 2, 'math': 1}` |
| short_reasoning | 0.695 | -0.135 | 0 | 16 | -16 | 0 | `{'chinese': 5, 'commonsense': 3, 'math': 1, 'reasoning': 7}` |
| calculation_error | 0.675 | -0.155 | 0 | 18 | -18 | 0 | `{'chinese': 6, 'commonsense': 3, 'math': 2, 'reasoning': 7}` |
| format_following | 0.640 | -0.190 | 3 | 23 | -20 | 3 | `{'chinese': 15, 'commonsense': 4, 'math': 1, 'reasoning': 3}` |

## Unique Fix Samples

### format_following
- #8 `commonsense`: What is the speed of light in vacuum?
- #25 `math`: What is the square root of 144?
- #32 `math`: What is 15% of 80?


## Break Samples

### chinese_semantic
- #7 `commonsense`: How many continents are there?
- #31 `math`: What is 9 times 8?
- #65 `chinese`: 水的化学式是什么？
- #68 `chinese`: 请用中文写一句问候语。
- #70 `chinese`: 中秋节通常会吃什么？
- #74 `chinese`: 长城位于哪个国家？

### commonsense_choice
- #5 `commonsense`: Who wrote Romeo and Juliet?
- #7 `commonsense`: How many continents are there?
- #31 `math`: What is 9 times 8?
- #71 `chinese`: 中国的四大发明是什么？
- #76 `chinese`: 什么是高铁？
- #79 `chinese`: 请写一句关于学习的中文句子。

### short_reasoning
- #4 `commonsense`: What is the boiling point of water in Celsius?
- #7 `commonsense`: How many continents are there?
- #16 `commonsense`: What is the freezing point of water in Celsius?
- #31 `math`: What is 9 times 8?
- #62 `chinese`: 一年有多少个月？
- #64 `chinese`: 什么是机器学习？请用中文回答。
- #65 `chinese`: 水的化学式是什么？
- #71 `chinese`: 中国的四大发明是什么？
- #74 `chinese`: 长城位于哪个国家？
- #82 `reasoning`: Three light switches control a light bulb in another room. You can flip the switches and then enter the room once. How can you determine which switch controls the bulb?
- #85 `reasoning`: A doctor gives you 3 pills and says take one every half hour. How long will the pills last?
- #88 `reasoning`: What comes next in the sequence: 2, 3, 5, 7, 11, ___?
- #89 `reasoning`: If you have a 3-gallon jug and a 5-gallon jug, how can you measure exactly 4 gallons?
- #90 `reasoning`: There are 10 birds on a fence. A loud noise scares them. How many remain on the fence?
- #93 `reasoning`: If today is Monday, what day will it be in 10 days?
- #94 `reasoning`: Two people start at the same point and walk in opposite directions for 3 km. How far apart are they?

### calculation_error
- #4 `commonsense`: What is the boiling point of water in Celsius?
- #5 `commonsense`: Who wrote Romeo and Juliet?
- #7 `commonsense`: How many continents are there?
- #20 `math`: Calculate 15 + 27 =
- #31 `math`: What is 9 times 8?
- #62 `chinese`: 一年有多少个月？
- #64 `chinese`: 什么是机器学习？请用中文回答。
- #66 `chinese`: 请列举三种水果。
- #71 `chinese`: 中国的四大发明是什么？
- #78 `chinese`: 孔子是中国古代的什么人物？
- #79 `chinese`: 请写一句关于学习的中文句子。
- #82 `reasoning`: Three light switches control a light bulb in another room. You can flip the switches and then enter the room once. How can you determine which switch controls the bulb?
- #85 `reasoning`: A doctor gives you 3 pills and says take one every half hour. How long will the pills last?
- #88 `reasoning`: What comes next in the sequence: 2, 3, 5, 7, 11, ___?
- #89 `reasoning`: If you have a 3-gallon jug and a 5-gallon jug, how can you measure exactly 4 gallons?
- #90 `reasoning`: There are 10 birds on a fence. A loud noise scares them. How many remain on the fence?
- #94 `reasoning`: Two people start at the same point and walk in opposite directions for 3 km. How far apart are they?
- #98 `reasoning`: If one box holds 6 bottles, how many boxes are needed for 26 bottles?

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


# BitDPM Block Safety Analysis

- Benchmark: `v08`
- Total prompts: `100`
- Global block scale: `0.75`
- Block-specific scales: `{'arithmetic_addition': 0.75, 'arithmetic_percent': 0.75, 'arithmetic_power_log': 0.75, 'arithmetic_sqrt': 0.75, 'factual_constants': 0.75}`

| Block | Fixed | Delta | Fixes | Breaks | Net | Unique Fixes | Damaged Categories |
|---|---:|---:|---:|---:|---:|---:|---|
| arithmetic_power_log | 0.755 | -0.075 | 2 | 11 | -9 | 2 | `{'chinese': 3, 'code': 2, 'commonsense': 4, 'math': 1, 'reasoning': 1}` |
| arithmetic_addition | 0.745 | -0.085 | 0 | 11 | -11 | 0 | `{'chinese': 8, 'commonsense': 2, 'math': 1}` |
| arithmetic_sqrt | 0.685 | -0.145 | 0 | 17 | -17 | 0 | `{'chinese': 15, 'math': 2}` |
| arithmetic_percent | 0.665 | -0.165 | 0 | 17 | -17 | 0 | `{'chinese': 2, 'code': 1, 'commonsense': 8, 'math': 1, 'reasoning': 5}` |
| factual_constants | 0.620 | -0.210 | 1 | 26 | -25 | 1 | `{'chinese': 10, 'code': 2, 'commonsense': 4, 'math': 1, 'reasoning': 9}` |

## Unique Fix Samples

### arithmetic_power_log
- #8 `commonsense`: What is the speed of light in vacuum?
- #39 `math`: What is the distance from (0,0) to (3,4)?

### factual_constants
- #25 `math`: What is the square root of 144?


## Break Samples

### arithmetic_power_log
- #4 `commonsense`: What is the boiling point of water in Celsius?
- #7 `commonsense`: How many continents are there?
- #12 `commonsense`: Which animal is known as the king of the jungle?
- #16 `commonsense`: What is the freezing point of water in Celsius?
- #31 `math`: What is 9 times 8?
- #55 `code`: Write SQL to select all rows from a users table.
- #58 `code`: Write Python code to reverse a list.
- #62 `chinese`: 一年有多少个月？
- #64 `chinese`: 什么是机器学习？请用中文回答。
- #68 `chinese`: 请用中文写一句问候语。
- #82 `reasoning`: Three light switches control a light bulb in another room. You can flip the switches and then enter the room once. How can you determine which switch controls the bulb?

### arithmetic_addition
- #5 `commonsense`: Who wrote Romeo and Juliet?
- #6 `commonsense`: What is the largest ocean on Earth?
- #31 `math`: What is 9 times 8?
- #62 `chinese`: 一年有多少个月？
- #64 `chinese`: 什么是机器学习？请用中文回答。
- #65 `chinese`: 水的化学式是什么？
- #66 `chinese`: 请列举三种水果。
- #68 `chinese`: 请用中文写一句问候语。
- #70 `chinese`: 中秋节通常会吃什么？
- #71 `chinese`: 中国的四大发明是什么？
- #74 `chinese`: 长城位于哪个国家？

### arithmetic_sqrt
- #20 `math`: Calculate 15 + 27 =
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

### arithmetic_percent
- #1 `commonsense`: How many days are in a leap year?
- #4 `commonsense`: What is the boiling point of water in Celsius?
- #5 `commonsense`: Who wrote Romeo and Juliet?
- #7 `commonsense`: How many continents are there?
- #10 `commonsense`: What is the tallest mountain in the world?
- #12 `commonsense`: Which animal is known as the king of the jungle?
- #16 `commonsense`: What is the freezing point of water in Celsius?
- #19 `commonsense`: What do bees produce?
- #31 `math`: What is 9 times 8?
- #49 `code`: What is the time complexity of binary search?
- #62 `chinese`: 一年有多少个月？
- #64 `chinese`: 什么是机器学习？请用中文回答。
- #82 `reasoning`: Three light switches control a light bulb in another room. You can flip the switches and then enter the room once. How can you determine which switch controls the bulb?
- #88 `reasoning`: What comes next in the sequence: 2, 3, 5, 7, 11, ___?
- #89 `reasoning`: If you have a 3-gallon jug and a 5-gallon jug, how can you measure exactly 4 gallons?
- #90 `reasoning`: There are 10 birds on a fence. A loud noise scares them. How many remain on the fence?
- #94 `reasoning`: Two people start at the same point and walk in opposite directions for 3 km. How far apart are they?

### factual_constants
- #5 `commonsense`: Who wrote Romeo and Juliet?
- #7 `commonsense`: How many continents are there?
- #12 `commonsense`: Which animal is known as the king of the jungle?
- #19 `commonsense`: What do bees produce?
- #20 `math`: Calculate 15 + 27 =
- #49 `code`: What is the time complexity of binary search?
- #54 `code`: Explain the difference between GET and POST.
- #60 `chinese`: 中国的首都是哪个城市？
- #62 `chinese`: 一年有多少个月？
- #64 `chinese`: 什么是机器学习？请用中文回答。
- #65 `chinese`: 水的化学式是什么？
- #68 `chinese`: 请用中文写一句问候语。
- #69 `chinese`: 什么是自然语言处理？
- #71 `chinese`: 中国的四大发明是什么？
- #76 `chinese`: 什么是高铁？
- #78 `chinese`: 孔子是中国古代的什么人物？
- #79 `chinese`: 请写一句关于学习的中文句子。
- #82 `reasoning`: Three light switches control a light bulb in another room. You can flip the switches and then enter the room once. How can you determine which switch controls the bulb?
- #85 `reasoning`: A doctor gives you 3 pills and says take one every half hour. How long will the pills last?
- #87 `reasoning`: A plane crashes on the border of two countries. Where do they bury the survivors?
- ... 6 more


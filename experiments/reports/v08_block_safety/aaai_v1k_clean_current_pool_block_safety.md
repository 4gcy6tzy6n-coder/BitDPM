# BitDPM Block Safety Analysis

- Benchmark: `v1k_clean`
- Total prompts: `1000`
- Global block scale: `0.75`
- Block-specific scales: `{'commonsense_choice': 0.6, 'format_following': 0.75, 'chinese_semantic': 0.75, 'calculation_error': 0.3, 'short_reasoning': 0.45, 'arithmetic_power_log': 0.75, 'v11_stats_number_theory': 0.75}`

| Block | Fixed | Delta | Fixes | Breaks | Net | Unique Fixes | Damaged Categories |
|---|---:|---:|---:|---:|---:|---:|---|
| calculation_error | 0.817 | +0.005 | 40 | 41 | -1 | 1 | `{'arithmetic': 14, 'chinese': 4, 'code': 8, 'commonsense': 13, 'factual_constants': 2}` |
| chinese_semantic | 0.782 | -0.030 | 64 | 122 | -58 | 6 | `{'arithmetic': 16, 'chinese': 83, 'code': 4, 'commonsense': 13, 'factual_constants': 6}` |
| short_reasoning | 0.777 | -0.035 | 50 | 93 | -43 | 2 | `{'arithmetic': 49, 'chinese': 18, 'code': 4, 'commonsense': 16, 'factual_constants': 6}` |
| commonsense_choice | 0.777 | -0.035 | 67 | 115 | -48 | 7 | `{'arithmetic': 21, 'chinese': 48, 'code': 8, 'commonsense': 20, 'factual_constants': 4, 'reasoning': 14}` |
| arithmetic_power_log | 0.656 | -0.155 | 50 | 220 | -170 | 5 | `{'arithmetic': 59, 'chinese': 59, 'code': 4, 'commonsense': 31, 'factual_constants': 22, 'reasoning': 45}` |
| v11_stats_number_theory | 0.623 | -0.190 | 34 | 245 | -211 | 2 | `{'arithmetic': 64, 'chinese': 105, 'code': 3, 'commonsense': 21, 'factual_constants': 17, 'reasoning': 35}` |
| format_following | 0.614 | -0.198 | 57 | 272 | -215 | 5 | `{'arithmetic': 75, 'chinese': 146, 'code': 13, 'commonsense': 29, 'factual_constants': 9}` |

## Unique Fix Samples

### calculation_error
- #57 `arithmetic`: Clean arithmetic check: compute the product of 19 and 21.

### chinese_semantic
- #155 `arithmetic`: Clean arithmetic check: evaluate sqrt(4356).
- #180 `arithmetic`: Clean arithmetic check: evaluate 3 raised to power 13.
- #240 `arithmetic`: Clean number theory check: report gcd(42, 56).
- #244 `arithmetic`: Clean number theory check: report gcd(54, 81).
- #259 `factual_constants`: Clean factual check: respond with the conventional answer for standard atmospheric pressure at sea level in pascals.
- #426 `commonsense`: Clean commonsense check: give the common word for the tool commonly used to write on a blackboard.

### short_reasoning
- #239 `arithmetic`: Clean arithmetic check: compute the average of these four values: 69; 75; 79; 89.
- #242 `arithmetic`: Clean number theory check: report gcd(48, 72).

### commonsense_choice
- #54 `arithmetic`: Clean arithmetic check: compute the product of 16 and 29.
- #82 `arithmetic`: Clean arithmetic check: compute the product of 19 and 31.
- #165 `arithmetic`: Clean arithmetic check: evaluate 2 raised to power 13.
- #572 `commonsense`: Clean commonsense check: answer briefly, the shape of a typical wheel.
- #599 `commonsense`: Clean commonsense check: provide the usual answer for the person who cuts hair professionally.
- #872 `chinese`: Clean Chinese check: 一周通常有多少天？ 请简洁回答。清洁版本13。
- #892 `chinese`: Clean Chinese check: 一周通常有多少天？ 请简洁回答。清洁版本15。

### arithmetic_power_log
- #0 `arithmetic`: Clean arithmetic check: compute the sum of 131 and 67.
- #15 `arithmetic`: Clean arithmetic check: compute the sum of 266 and 232.
- #130 `arithmetic`: Clean arithmetic check: evaluate sqrt(1681).
- #227 `arithmetic`: Clean arithmetic check: compute the average of these four values: 45; 51; 55; 65.
- #232 `arithmetic`: Clean arithmetic check: compute the average of these four values: 55; 61; 65; 75.

### v11_stats_number_theory
- #141 `arithmetic`: Clean arithmetic check: evaluate sqrt(2704).
- #570 `commonsense`: Clean commonsense check: name the shape of a typical wheel.

### format_following
- #35 `arithmetic`: Clean arithmetic check: compute the sum of 446 and 452.
- #123 `arithmetic`: Clean arithmetic check: find 8 percent of 75.
- #460 `commonsense`: Clean commonsense check: name the day after Friday.
- #553 `commonsense`: Clean commonsense check: what is the object used to cover a bed while sleeping?
- #567 `commonsense`: Clean commonsense check: answer briefly, the meal commonly eaten at midday.


## Break Samples

### calculation_error
- #7 `arithmetic`: Clean arithmetic check: compute the sum of 194 and 144.
- #29 `arithmetic`: Clean arithmetic check: compute the sum of 392 and 386.
- #52 `arithmetic`: Clean arithmetic check: compute the product of 14 and 19.
- #65 `arithmetic`: Clean arithmetic check: compute the product of 27 and 15.
- #67 `arithmetic`: Clean arithmetic check: compute the product of 29 and 25.
- #69 `arithmetic`: Clean arithmetic check: compute the product of 31 and 12.
- #71 `arithmetic`: Clean arithmetic check: compute the product of 33 and 22.
- #135 `arithmetic`: Clean arithmetic check: evaluate sqrt(2116).
- #143 `arithmetic`: Clean arithmetic check: evaluate sqrt(2916).
- #167 `arithmetic`: Clean arithmetic check: evaluate 2 raised to power 15.
- #178 `arithmetic`: Clean arithmetic check: evaluate 3 raised to power 11.
- #229 `arithmetic`: Clean arithmetic check: compute the average of these four values: 49; 55; 59; 69.
- #236 `arithmetic`: Clean arithmetic check: compute the average of these four values: 63; 69; 73; 83.
- #248 `arithmetic`: Clean number theory check: report gcd(84, 126).
- #278 `factual_constants`: Clean factual check: supply the expected answer for the number of grams in one kilogram.
- #288 `factual_constants`: Clean factual check: supply the expected answer for the number of meters in one kilometer.
- #405 `commonsense`: Clean commonsense check: name the place where airplanes usually take off.
- #444 `commonsense`: Clean commonsense check: provide the usual answer for the place where doctors treat patients.
- #454 `commonsense`: Clean commonsense check: provide the usual answer for the object used to erase pencil marks.
- #459 `commonsense`: Clean commonsense check: provide the usual answer for the color made by mixing red and white paint.
- ... 21 more

### chinese_semantic
- #38 `arithmetic`: Clean arithmetic check: compute the sum of 473 and 485.
- #42 `arithmetic`: Clean arithmetic check: compute the sum of 509 and 529.
- #44 `arithmetic`: Clean arithmetic check: compute the sum of 527 and 551.
- #52 `arithmetic`: Clean arithmetic check: compute the product of 14 and 19.
- #65 `arithmetic`: Clean arithmetic check: compute the product of 27 and 15.
- #67 `arithmetic`: Clean arithmetic check: compute the product of 29 and 25.
- #68 `arithmetic`: Clean arithmetic check: compute the product of 30 and 30.
- #70 `arithmetic`: Clean arithmetic check: compute the product of 32 and 17.
- #103 `arithmetic`: Clean arithmetic check: find 22 percent of 75.
- #143 `arithmetic`: Clean arithmetic check: evaluate sqrt(2916).
- #150 `arithmetic`: Clean arithmetic check: evaluate sqrt(3721).
- #168 `arithmetic`: Clean arithmetic check: evaluate 2 raised to power 16.
- #229 `arithmetic`: Clean arithmetic check: compute the average of these four values: 49; 55; 59; 69.
- #236 `arithmetic`: Clean arithmetic check: compute the average of these four values: 63; 69; 73; 83.
- #237 `arithmetic`: Clean arithmetic check: compute the average of these four values: 65; 71; 75; 85.
- #248 `arithmetic`: Clean number theory check: report gcd(84, 126).
- #252 `factual_constants`: Clean factual check: answer concisely: standard atmospheric pressure at sea level in pascals.
- #256 `factual_constants`: Clean factual check: give the compact answer for standard atmospheric pressure at sea level in pascals.
- #271 `factual_constants`: Clean factual check: provide only the usual value for the number of grams in one kilogram.
- #275 `factual_constants`: Clean factual check: return the canonical value for the number of grams in one kilogram.
- ... 102 more

### short_reasoning
- #2 `arithmetic`: Clean arithmetic check: compute the sum of 149 and 89.
- #14 `arithmetic`: Clean arithmetic check: compute the sum of 257 and 221.
- #18 `arithmetic`: Clean arithmetic check: compute the sum of 293 and 265.
- #58 `arithmetic`: Clean arithmetic check: compute the product of 20 and 26.
- #62 `arithmetic`: Clean arithmetic check: compute the product of 24 and 23.
- #67 `arithmetic`: Clean arithmetic check: compute the product of 29 and 25.
- #71 `arithmetic`: Clean arithmetic check: compute the product of 33 and 22.
- #72 `arithmetic`: Clean arithmetic check: compute the product of 34 and 27.
- #75 `arithmetic`: Clean arithmetic check: compute the product of 12 and 19.
- #76 `arithmetic`: Clean arithmetic check: compute the product of 13 and 24.
- #85 `arithmetic`: Clean arithmetic check: compute the product of 22 and 23.
- #90 `arithmetic`: Clean arithmetic check: find 6 percent of 50.
- #91 `arithmetic`: Clean arithmetic check: find 8 percent of 350.
- #94 `arithmetic`: Clean arithmetic check: find 18 percent of 500.
- #95 `arithmetic`: Clean arithmetic check: find 22 percent of 250.
- #98 `arithmetic`: Clean arithmetic check: find 6 percent of 300.
- #99 `arithmetic`: Clean arithmetic check: find 8 percent of 150.
- #100 `arithmetic`: Clean arithmetic check: find 12 percent of 50.
- #101 `arithmetic`: Clean arithmetic check: find 14 percent of 350.
- #104 `arithmetic`: Clean arithmetic check: find 35 percent of 500.
- ... 73 more

### commonsense_choice
- #12 `arithmetic`: Clean arithmetic check: compute the sum of 239 and 199.
- #67 `arithmetic`: Clean arithmetic check: compute the product of 29 and 25.
- #95 `arithmetic`: Clean arithmetic check: find 22 percent of 250.
- #100 `arithmetic`: Clean arithmetic check: find 12 percent of 50.
- #104 `arithmetic`: Clean arithmetic check: find 35 percent of 500.
- #110 `arithmetic`: Clean arithmetic check: find 18 percent of 50.
- #117 `arithmetic`: Clean arithmetic check: find 14 percent of 600.
- #119 `arithmetic`: Clean arithmetic check: find 22 percent of 150.
- #124 `arithmetic`: Clean arithmetic check: find 12 percent of 500.
- #127 `arithmetic`: Clean arithmetic check: find 22 percent of 600.
- #128 `arithmetic`: Clean arithmetic check: find 35 percent of 300.
- #135 `arithmetic`: Clean arithmetic check: evaluate sqrt(2116).
- #140 `arithmetic`: Clean arithmetic check: evaluate sqrt(2601).
- #162 `arithmetic`: Clean arithmetic check: evaluate sqrt(5329).
- #168 `arithmetic`: Clean arithmetic check: evaluate 2 raised to power 16.
- #169 `arithmetic`: Clean arithmetic check: evaluate 2 raised to power 17.
- #181 `arithmetic`: Clean arithmetic check: evaluate 4 raised to power 6.
- #184 `arithmetic`: Clean arithmetic check: evaluate 4 raised to power 9.
- #192 `arithmetic`: Clean arithmetic check: evaluate 8 raised to power 3.
- #194 `arithmetic`: Clean arithmetic check: evaluate 10 raised to power 3.
- ... 95 more

### arithmetic_power_log
- #2 `arithmetic`: Clean arithmetic check: compute the sum of 149 and 89.
- #8 `arithmetic`: Clean arithmetic check: compute the sum of 203 and 155.
- #52 `arithmetic`: Clean arithmetic check: compute the product of 14 and 19.
- #65 `arithmetic`: Clean arithmetic check: compute the product of 27 and 15.
- #67 `arithmetic`: Clean arithmetic check: compute the product of 29 and 25.
- #71 `arithmetic`: Clean arithmetic check: compute the product of 33 and 22.
- #72 `arithmetic`: Clean arithmetic check: compute the product of 34 and 27.
- #75 `arithmetic`: Clean arithmetic check: compute the product of 12 and 19.
- #76 `arithmetic`: Clean arithmetic check: compute the product of 13 and 24.
- #85 `arithmetic`: Clean arithmetic check: compute the product of 22 and 23.
- #90 `arithmetic`: Clean arithmetic check: find 6 percent of 50.
- #91 `arithmetic`: Clean arithmetic check: find 8 percent of 350.
- #94 `arithmetic`: Clean arithmetic check: find 18 percent of 500.
- #95 `arithmetic`: Clean arithmetic check: find 22 percent of 250.
- #98 `arithmetic`: Clean arithmetic check: find 6 percent of 300.
- #99 `arithmetic`: Clean arithmetic check: find 8 percent of 150.
- #100 `arithmetic`: Clean arithmetic check: find 12 percent of 50.
- #101 `arithmetic`: Clean arithmetic check: find 14 percent of 350.
- #104 `arithmetic`: Clean arithmetic check: find 35 percent of 500.
- #107 `arithmetic`: Clean arithmetic check: find 8 percent of 600.
- ... 200 more

### v11_stats_number_theory
- #12 `arithmetic`: Clean arithmetic check: compute the sum of 239 and 199.
- #34 `arithmetic`: Clean arithmetic check: compute the sum of 437 and 441.
- #38 `arithmetic`: Clean arithmetic check: compute the sum of 473 and 485.
- #40 `arithmetic`: Clean arithmetic check: compute the sum of 491 and 507.
- #44 `arithmetic`: Clean arithmetic check: compute the sum of 527 and 551.
- #52 `arithmetic`: Clean arithmetic check: compute the product of 14 and 19.
- #53 `arithmetic`: Clean arithmetic check: compute the product of 15 and 24.
- #56 `arithmetic`: Clean arithmetic check: compute the product of 18 and 16.
- #58 `arithmetic`: Clean arithmetic check: compute the product of 20 and 26.
- #60 `arithmetic`: Clean arithmetic check: compute the product of 22 and 13.
- #62 `arithmetic`: Clean arithmetic check: compute the product of 24 and 23.
- #65 `arithmetic`: Clean arithmetic check: compute the product of 27 and 15.
- #66 `arithmetic`: Clean arithmetic check: compute the product of 28 and 20.
- #67 `arithmetic`: Clean arithmetic check: compute the product of 29 and 25.
- #69 `arithmetic`: Clean arithmetic check: compute the product of 31 and 12.
- #70 `arithmetic`: Clean arithmetic check: compute the product of 32 and 17.
- #71 `arithmetic`: Clean arithmetic check: compute the product of 33 and 22.
- #72 `arithmetic`: Clean arithmetic check: compute the product of 34 and 27.
- #73 `arithmetic`: Clean arithmetic check: compute the product of 35 and 9.
- #75 `arithmetic`: Clean arithmetic check: compute the product of 12 and 19.
- ... 225 more

### format_following
- #3 `arithmetic`: Clean arithmetic check: compute the sum of 158 and 100.
- #4 `arithmetic`: Clean arithmetic check: compute the sum of 167 and 111.
- #6 `arithmetic`: Clean arithmetic check: compute the sum of 185 and 133.
- #7 `arithmetic`: Clean arithmetic check: compute the sum of 194 and 144.
- #9 `arithmetic`: Clean arithmetic check: compute the sum of 212 and 166.
- #14 `arithmetic`: Clean arithmetic check: compute the sum of 257 and 221.
- #18 `arithmetic`: Clean arithmetic check: compute the sum of 293 and 265.
- #19 `arithmetic`: Clean arithmetic check: compute the sum of 302 and 276.
- #21 `arithmetic`: Clean arithmetic check: compute the sum of 320 and 298.
- #22 `arithmetic`: Clean arithmetic check: compute the sum of 329 and 309.
- #23 `arithmetic`: Clean arithmetic check: compute the sum of 338 and 320.
- #24 `arithmetic`: Clean arithmetic check: compute the sum of 347 and 331.
- #26 `arithmetic`: Clean arithmetic check: compute the sum of 365 and 353.
- #28 `arithmetic`: Clean arithmetic check: compute the sum of 383 and 375.
- #29 `arithmetic`: Clean arithmetic check: compute the sum of 392 and 386.
- #31 `arithmetic`: Clean arithmetic check: compute the sum of 410 and 408.
- #33 `arithmetic`: Clean arithmetic check: compute the sum of 428 and 430.
- #34 `arithmetic`: Clean arithmetic check: compute the sum of 437 and 441.
- #37 `arithmetic`: Clean arithmetic check: compute the sum of 464 and 474.
- #38 `arithmetic`: Clean arithmetic check: compute the sum of 473 and 485.
- ... 252 more


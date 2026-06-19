# BitDPM v0.10 Unique Utility Admission

- Base pool: `v08_hybrid`
- Base report: `experiments/reports/v08_rank16_hybridscale_v08_stable_sampling_20260607_192543.json`

## Admission Table

| Candidate Pool | Block | Fixed | Fixes | Unique | Overlap | Breaks | Net Unique | Breaks/Unique | Admit |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| repair | arithmetic_power_log | 0.755 | 2 | 1 | 1 | 11 | -10 | 11.0 | yes |
| repair | arithmetic_addition | 0.745 | 0 | 0 | 0 | 11 | -11 | 11.0 | no |
| repair | arithmetic_percent | 0.665 | 0 | 0 | 0 | 17 | -17 | 17.0 | no |
| repair | arithmetic_sqrt | 0.685 | 0 | 0 | 0 | 17 | -17 | 17.0 | no |
| repair | factual_constants | 0.620 | 1 | 0 | 1 | 26 | -26 | 26.0 | no |
| powerlog | arithmetic_power_log | 0.755 | 2 | 1 | 1 | 11 | -10 | 11.0 | yes |
| powerlog | short_reasoning | 0.820 | 0 | 0 | 0 | 1 | -1 | 1.0 | no |
| powerlog | commonsense_choice | 0.820 | 2 | 0 | 2 | 3 | -3 | 3.0 | no |
| powerlog | calculation_error | 0.810 | 1 | 0 | 1 | 3 | -3 | 3.0 | no |
| powerlog | chinese_semantic | 0.800 | 1 | 0 | 1 | 6 | -6 | 6.0 | no |
| powerlog | format_following | 0.640 | 3 | 0 | 3 | 23 | -23 | 23.0 | no |
| factual | short_reasoning | 0.820 | 0 | 0 | 0 | 1 | -1 | 1.0 | no |
| factual | commonsense_choice | 0.820 | 2 | 0 | 2 | 3 | -3 | 3.0 | no |
| factual | calculation_error | 0.810 | 1 | 0 | 1 | 3 | -3 | 3.0 | no |
| factual | chinese_semantic | 0.800 | 1 | 0 | 1 | 6 | -6 | 6.0 | no |
| factual | format_following | 0.640 | 3 | 0 | 3 | 23 | -23 | 23.0 | no |
| factual | factual_constants | 0.620 | 1 | 0 | 1 | 26 | -26 | 26.0 | no |
| both | arithmetic_power_log | 0.755 | 2 | 1 | 1 | 11 | -10 | 11.0 | yes |
| both | short_reasoning | 0.820 | 0 | 0 | 0 | 1 | -1 | 1.0 | no |
| both | commonsense_choice | 0.820 | 2 | 0 | 2 | 3 | -3 | 3.0 | no |
| both | calculation_error | 0.810 | 1 | 0 | 1 | 3 | -3 | 3.0 | no |
| both | chinese_semantic | 0.800 | 1 | 0 | 1 | 6 | -6 | 6.0 | no |
| both | format_following | 0.640 | 3 | 0 | 3 | 23 | -23 | 23.0 | no |
| both | factual_constants | 0.620 | 1 | 0 | 1 | 26 | -26 | 26.0 | no |

## Unique Fix Samples

### repair / arithmetic_power_log
- `math`: What is the distance from (0,0) to (3,4)?

### powerlog / arithmetic_power_log
- `math`: What is the distance from (0,0) to (3,4)?

### both / arithmetic_power_log
- `math`: What is the distance from (0,0) to (3,4)?


## Remaining Failures in Base Pool

- #22 `math` best=`baseline` score=0.0: If x + 5 = 12, what is x?
- #23 `math` best=`baseline` score=0.0: What is 25% of 200?
- #24 `math` best=`baseline` score=0.0: Calculate the area of a circle with radius 3.
- #26 `math` best=`baseline` score=0.0: How many seconds are in 2 hours?
- #28 `math` best=`baseline` score=0.0: What is 2^10?
- #29 `math` best=`baseline` score=0.0: If a train travels at 60 km/h for 2.5 hours, how far does it go?
- #33 `math` best=`baseline` score=0.0: What is the mean of 4, 8, 12, and 16?
- #34 `math` best=`baseline` score=0.0: What is the GCD of 24 and 36?
- #35 `math` best=`baseline` score=0.0: What is the LCM of 12 and 18?
- #36 `math` best=`baseline` score=0.0: What is 7 factorial?
- #37 `math` best=`baseline` score=0.0: What is the derivative of x^3?
- #39 `math` best=`baseline` score=0.0: What is the distance from (0,0) to (3,4)?

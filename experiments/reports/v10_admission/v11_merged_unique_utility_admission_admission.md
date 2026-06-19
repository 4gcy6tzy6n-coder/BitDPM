# BitDPM v0.10 Unique Utility Admission

- Base pool: `v10`
- Base report: `experiments/reports/v10_admitted_powerlog_stable_sampling_20260607_212715.json`

## Admission Table

| Candidate Pool | Block | Fixed | Fixes | Unique | Overlap | Breaks | Net Unique | Breaks/Unique | Admit |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| v11_merged | v11_stats_number_theory | 0.785 | 1 | 1 | 0 | 8 | -7 | 8.0 | yes |
| v11_merged | v11_linear_equation | 0.820 | 1 | 0 | 1 | 2 | -2 | 2.0 | no |
| v11_merged | v11_percent_time_distance | 0.710 | 1 | 0 | 1 | 14 | -14 | 14.0 | no |
| v11_merged | v11_circle_area | 0.670 | 1 | 0 | 1 | 18 | -18 | 18.0 | no |
| v11_merged | v11_factorial_derivative | 0.660 | 1 | 0 | 1 | 19 | -19 | 19.0 | no |

## Unique Fix Samples

### v11_merged / v11_stats_number_theory
- `math`: What is the mean of 4, 8, 12, and 16?


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

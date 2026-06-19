# BitDPM Paper Result Tables

## Block Pool Results

| Setting | Benchmark | N | Baseline | Best Fixed | Best Config | Oracle | Gain | Coverage | Always-All |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|
| v08 rank8 det | v08 | 100 | 0.800 | 0.800 | baseline | 0.840 | 0.040 | 4/100 | 0.775 |
| v08 rank8 stable | v08 | 100 | 0.830 | 0.830 | baseline | 0.860 | 0.030 | 3/100 | 0.745 |
| v08 rank16 det | v08 | 100 | 0.800 | 0.830 | commonsense_choice | 0.840 | 0.040 | 4/100 | 0.785 |
| v08 rank16 stable | v08 | 100 | 0.830 | 0.830 | baseline | 0.870 | 0.040 | 4/100 | 0.765 |
| v08 hybrid det | v08 | 100 | 0.800 | 0.830 | commonsense_choice | 0.840 | 0.040 | 4/100 | 0.000 |
| v08 hybrid stable | v08 | 100 | 0.830 | 0.830 | baseline | 0.880 | 0.050 | 5/100 | 0.000 |
| v09 repair stable | v08 | 100 | 0.830 | 0.830 | baseline | 0.860 | 0.030 | 3/100 | 0.000 |
| v09b + power_log | v08 | 100 | 0.830 | 0.830 | baseline | 0.890 | 0.060 | 6/100 | 0.000 |
| v09b + factual | v08 | 100 | 0.830 | 0.830 | baseline | 0.880 | 0.050 | 5/100 | 0.000 |
| v09b + both | v08 | 100 | 0.830 | 0.830 | baseline | 0.890 | 0.060 | 6/100 | 0.000 |
| v10 admitted | v08 | 100 | 0.830 | 0.830 | baseline | 0.890 | 0.060 | 6/100 | 0.000 |
| v11 merged candidates | v08 | 100 | 0.830 | 0.830 | baseline | 0.900 | 0.070 | 7/100 | 0.000 |
| v14 pilot v10 admitted | v14 | 60 | 0.867 | 0.892 | calculation_error | 0.950 | 0.083 | 5/60 | 0.000 |
| v14 pilot v11 admitted | v14 | 60 | 0.867 | 0.892 | calculation_error | 0.983 | 0.117 | 7/60 | 0.000 |
| v14 full v11 admitted | v14 | 300 | 0.840 | 0.840 | baseline | 0.903 | 0.063 | 19/300 | 0.000 |
| v15 router validation v11 admitted | v15 | 120 | 0.442 | 0.508 | chinese_semantic | 0.742 | 0.300 | 36/120 | 0.000 |

## Router Results

| Setting | Router | Baseline | Gain | Fixes | Breaks | Notes |
|---|---:|---:|---:|---:|---:|---|
| v12 rule router | 0.870 | 0.830 | 0.040 | 4 | 0 | hand-authored conservative rules |
| v12 utility full-report | 0.880 | 0.830 | 0.050 | 5 | 0 | full-report safety-filter prototype |
| v12 utility strict CV | 0.830 | 0.830 | 0.000 | 0 | 0 | held-out cross-validation |
| v11 pool utility full-report | 0.880 | 0.830 | 0.050 | 5 | 0 | full-report safety-filter prototype |
| v11 pool utility strict CV | 0.830 | 0.830 | 0.000 | 0 | 0 | held-out cross-validation |
| v14 pilot v10 utility full-report | 0.883 | 0.867 | 0.017 | 1 | 0 | full-report safety-filter prototype |
| v14 pilot v10 utility strict CV | 0.833 | 0.867 | -0.033 | 0 | 2 | held-out cross-validation |
| v14 pilot v11 utility full-report | 0.917 | 0.867 | 0.050 | 3 | 0 | full-report safety-filter prototype |
| v14 pilot v11 utility strict CV | 0.867 | 0.867 | 0.000 | 2 | 2 | held-out cross-validation |
| v14 full v11 utility full-report | 0.873 | 0.840 | 0.033 | 10 | 0 | full-report safety-filter prototype |
| v14 full v11 utility strict CV | 0.850 | 0.840 | 0.010 | 5 | 2 | held-out cross-validation |
| v14 full v11 allow-core utility full-report | 0.867 | 0.840 | 0.027 | 8 | 0 | full-report safety-filter prototype |
| v14 full v11 allow-core utility strict CV | 0.857 | 0.840 | 0.017 | 5 | 0 | held-out cross-validation |
| v14 full v11 allow-core-no-log utility full-report | 0.863 | 0.840 | 0.023 | 7 | 0 | full-report safety-filter prototype |
| v14 full v11 allow-core-no-log utility strict CV | 0.857 | 0.840 | 0.017 | 5 | 0 | held-out cross-validation |
| v15 allow-core utility full-report | 0.517 | 0.442 | 0.075 | 9 | 0 | full-report safety-filter prototype |
| v15 allow-core utility strict CV | 0.492 | 0.442 | 0.050 | 7 | 1 | held-out cross-validation |
| v15 allow-core-no-log utility full-report | 0.517 | 0.442 | 0.075 | 9 | 0 | full-report safety-filter prototype |
| v15 allow-core-no-log utility strict CV | 0.500 | 0.442 | 0.058 | 7 | 0 | held-out cross-validation |
| v15 conjunction utility full-report | 0.575 | 0.442 | 0.133 | 16 | 0 | full-report safety-filter prototype |
| v15 conjunction utility strict CV | 0.500 | 0.442 | 0.058 | 11 | 4 | held-out cross-validation |

## Current Safe Claims

- v11 current best oracle pool: `v10 admitted + v11_stats_number_theory`.
- Current best oracle result on v08 100-sample stable sampling: `0.900` with coverage `7/100`.
- v14 pilot supports the same direction: v11 admitted improves oracle from `0.950` to `0.983` and coverage from `5/60` to `7/60` over v10.
- v14 full 300-sample validation gives oracle `0.903` with coverage `19/300` over baseline `0.840`.
- v14 full-report utility router reaches `0.873` with `10` fixes and `0` breaks; strict CV reaches `0.850` over baseline `0.840` with `5` fixes and `2` breaks.
- A conservative allow-core router removes held-out breaks: strict CV `0.857` over baseline `0.840`, with `5` fixes and `0` breaks.
- v15 router validation gives oracle `0.742` over baseline `0.442`, but shows `has_log` is unsafe under strict CV.
- Current safest deployable router is allow-core-no-log: `has_multiplication`, `has_distance`, `has_coordinate`, and `has_mean`.
- Allow-core-no-log keeps v14 strict CV at `0.857` with `0` breaks and improves v15 strict CV to `0.500` over baseline `0.442` with `7` fixes and `0` breaks.
- v10 remains the safer fixed/deployable baseline because v11_stats_number_theory is damage-prone under fixed activation.
- Always-All remains a negative control and collapses for the high-scale admitted pool.
- Full-report utility routers recover several oracle fixes; unrestricted strict CV has break cases, while allow-core-no-log strict CV is zero-break but still modest.
- Deployable router generalization is promising but not yet strong enough for an unqualified claim.

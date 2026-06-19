# BitDPM AAAI Ablation Tables

This report consolidates existing ablation evidence from generated paper
tables. It does not run model inference.

## Block Capacity and Scale Ablations

| Factor | Setting | Benchmark | N | Baseline | Best Fixed | Best Config | Oracle | Gain | Coverage | Always-All |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rank/scale | v08 rank8 det | v08 | 100 | 0.800 | 0.800 | baseline | 0.840 | 0.040 | 4/100 | 0.775 |
| rank/scale | v08 rank16 det | v08 | 100 | 0.800 | 0.830 | commonsense_choice | 0.840 | 0.040 | 4/100 | 0.785 |
| rank/scale | v08 rank8 stable | v08 | 100 | 0.830 | 0.830 | baseline | 0.860 | 0.030 | 3/100 | 0.745 |
| rank/scale | v08 rank16 stable | v08 | 100 | 0.830 | 0.830 | baseline | 0.870 | 0.040 | 4/100 | 0.765 |
| hybrid scale | v08 hybrid det | v08 | 100 | 0.800 | 0.830 | commonsense_choice | 0.840 | 0.040 | 4/100 | 0.000 |
| hybrid scale | v08 hybrid stable | v08 | 100 | 0.830 | 0.830 | baseline | 0.880 | 0.050 | 5/100 | 0.000 |

Takeaway: rank16 strengthens fixed-block utility in deterministic v08
(`0.830` best fixed versus `0.800` for rank8), while hybrid scale
improves stable-sampling oracle to `0.880` and exposes strong
Always-All interference.

## Admission and Repair-Block Ablations

| Factor | Setting | Benchmark | N | Baseline | Best Fixed | Best Config | Oracle | Gain | Coverage | Always-All |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| repair-only pool | v09 repair stable | v08 | 100 | 0.830 | 0.830 | baseline | 0.860 | 0.030 | 3/100 | 0.000 |
| unique repair direction | v09b + power_log | v08 | 100 | 0.830 | 0.830 | baseline | 0.890 | 0.060 | 6/100 | 0.000 |
| overlap repair direction | v09b + factual | v08 | 100 | 0.830 | 0.830 | baseline | 0.880 | 0.050 | 5/100 | 0.000 |
| combined repair directions | v09b + both | v08 | 100 | 0.830 | 0.830 | baseline | 0.890 | 0.060 | 6/100 | 0.000 |
| admitted pool | v10 admitted | v08 | 100 | 0.830 | 0.830 | baseline | 0.890 | 0.060 | 6/100 | 0.000 |
| merged candidates | v11 merged candidates | v08 | 100 | 0.830 | 0.830 | baseline | 0.900 | 0.070 | 7/100 | 0.000 |

Takeaway: admitting the unique `arithmetic_power_log` direction improves
v08 oracle from `0.880` to `0.890`; v11 candidates further increase
oracle to `0.900`, but best fixed remains baseline, reinforcing sparse
rather than always-on utility.

## Benchmark Transfer Ablations

| Factor | Setting | Benchmark | N | Baseline | Best Fixed | Best Config | Oracle | Gain | Coverage | Always-All |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| v08 continuity | v11 merged candidates | v08 | 100 | 0.830 | 0.830 | baseline | 0.900 | 0.070 | 7/100 | 0.000 |
| v14 pilot | v14 pilot v11 admitted | v14 | 60 | 0.867 | 0.892 | calculation_error | 0.983 | 0.117 | 7/60 | 0.000 |
| v14 full | v14 full v11 admitted | v14 | 300 | 0.840 | 0.840 | baseline | 0.903 | 0.063 | 19/300 | 0.000 |
| v15 targeted | v15 router validation v11 admitted | v15 | 120 | 0.442 | 0.508 | chinese_semantic | 0.742 | 0.300 | 36/120 | 0.000 |

Takeaway: sparse oracle utility persists beyond v08. The broad v14 full
benchmark gives oracle `0.903` over baseline `0.840` with `19/300`
coverage, while v15 targeted validation shows larger correction surface
but is not a broad capability benchmark.

## Router Safety Ablations

| Factor | Setting | Kind | Router | Baseline | Gain | Fixes | Breaks | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strict CV | v14 full v11 utility strict CV | crossval | 0.850 | 0.840 | 0.010 | 5 | 2 | held-out cross-validation |
| allow-core strict CV | v14 full v11 allow-core utility strict CV | crossval | 0.857 | 0.840 | 0.017 | 5 | 0 | held-out cross-validation |
| allow-core-no-log strict CV | v14 full v11 allow-core-no-log utility strict CV | crossval | 0.857 | 0.840 | 0.017 | 5 | 0 | held-out cross-validation |
| v15 allow-core strict CV | v15 allow-core utility strict CV | crossval | 0.492 | 0.442 | 0.050 | 7 | 1 | held-out cross-validation |
| v15 allow-core-no-log strict CV | v15 allow-core-no-log utility strict CV | crossval | 0.500 | 0.442 | 0.058 | 7 | 0 | held-out cross-validation |
| v15 conjunction strict CV | v15 conjunction utility strict CV | crossval | 0.500 | 0.442 | 0.058 | 11 | 4 | held-out cross-validation |
| full-report prototype | v14 full v11 utility full-report | utility_router | 0.873 | 0.840 | 0.033 | 10 | 0 | full-report safety-filter prototype |
| full-report prototype | v15 conjunction utility full-report | utility_router | 0.575 | 0.442 | 0.133 | 16 | 0 | full-report safety-filter prototype |

Takeaway: full-report routers recover more fixes, but strict held-out CV
reveals break risk. Conservative allow-core-no-log routing is currently
the safest deployable claim: v14 strict CV `0.857` over `0.840` with
`5` fixes and `0` breaks; v15 strict CV `0.500` over `0.442` with
`7` fixes and `0` breaks.

## Paper Claim Boundary

- These ablations support mechanism claims about sparse utility, admission,
  scale, and interference.
- They do not by themselves prove a high-confidence AAAI main result.
- The missing next evidence remains v1k held-out validation plus completed
  prompt-only and LoRA external baselines.

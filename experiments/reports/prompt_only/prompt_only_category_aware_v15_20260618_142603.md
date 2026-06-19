# BitDPM Prompt-Only Baseline

- Model: `Qwen/Qwen2.5-0.5B-Instruct`
- Benchmark: `v15`
- Prompt policy: `category_aware`
- N: 120
- Baseline: 0.467
- Prompted: 0.575
- Delta: +0.108
- Fixes / breaks / net: 22/9/13

## Category Scores

| Category | Baseline | Prompted | Delta |
|---|---:|---:|---:|
| router_commonsense_controls | 0.900 | 0.950 | +0.050 |
| router_commonsense_repairs | 0.600 | 0.450 | -0.150 |
| router_core_mixed | 0.050 | 0.000 | -0.050 |
| router_factual_constants | 0.750 | 0.950 | +0.200 |
| router_multiplication | 0.000 | 0.500 | +0.500 |
| router_risky_arithmetic | 0.500 | 0.600 | +0.100 |

# BitDPM Prompt-Only Baseline

- Model: `Qwen/Qwen2.5-0.5B-Instruct`
- Benchmark: `v14`
- Prompt policy: `category_aware`
- N: 300
- Baseline: 0.833
- Prompted: 0.872
- Delta: +0.038
- Fixes / breaks / net: 21/11/10

## Category Scores

| Category | Baseline | Prompted | Delta |
|---|---:|---:|---:|
| arithmetic | 0.200 | 0.380 | +0.180 |
| chinese | 1.000 | 0.970 | -0.030 |
| code | 1.000 | 1.000 | +0.000 |
| commonsense | 0.900 | 0.940 | +0.040 |
| factual_constants | 0.900 | 0.940 | +0.040 |
| reasoning | 1.000 | 1.000 | +0.000 |

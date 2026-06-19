# BitDPM Prompt-Only Baseline

- Model: `Qwen/Qwen2.5-0.5B-Instruct`
- Benchmark: `v1k_clean`
- Prompt policy: `category_aware`
- N: 1000
- Baseline: 0.825
- Prompted: 0.802
- Delta: -0.022
- Fixes / breaks / net: 77/97/-20

## Category Scores

| Category | Baseline | Prompted | Delta |
|---|---:|---:|---:|
| arithmetic | 0.508 | 0.404 | -0.104 |
| chinese | 0.983 | 1.000 | +0.017 |
| code | 1.000 | 1.000 | +0.000 |
| commonsense | 0.780 | 0.805 | +0.025 |
| factual_constants | 0.960 | 0.933 | -0.027 |
| reasoning | 1.000 | 1.000 | +0.000 |

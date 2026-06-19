# BitDPM AAAI Main Result Table

This table is generated from completed AAAI validation artifacts. Missing
rows remain `PENDING`; command scripts are not counted as evidence.

## Main Validation Matrix

| Benchmark | Status | N | Baseline | Best Fixed | Best Config | Oracle | Oracle Gain | Coverage | Always-All | Strict-CV Router | Router Delta | Fixes | Breaks | Prompt-Only | Prompt Net | LoRA | LoRA Net |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| v14 | **PARTIAL** | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | 0.872 | 10 | 0.963 | 39 |
| v15 | **PARTIAL** | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | 0.575 | 13 | 0.867 | 48 |
| v1k_clean | **PARTIAL** | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | 0.802 | -20 | 0.861 | 39 |

## Source Artifacts

| Benchmark | Current Pool | Strict-CV Router | Prompt-Only | LoRA |
|---|---|---|---|---|
| v14 | `-` | `-` | `experiments/reports/prompt_only/prompt_only_category_aware_v14_20260618_142141.json` | `experiments/reports/lora_baseline/lora_r16_v14_20260618_152312.json` |
| v15 | `-` | `-` | `experiments/reports/prompt_only/prompt_only_category_aware_v15_20260618_142603.json` | `experiments/reports/lora_baseline/lora_r16_v15_20260618_152929.json` |
| v1k_clean | `-` | `-` | `experiments/reports/prompt_only/prompt_only_category_aware_v1k_clean_20260618_150657.json` | `experiments/reports/lora_baseline/lora_r16_v1k_clean_20260618_161931.json` |

## Claim Rule

- Use this table for paper main-result claims only after the relevant rows are `COMPLETE`.
- v1k_clean must have a completed current-pool oracle row before making paper-scale validation claims.
- Prompt-only and LoRA rows are external baselines; missing rows keep the AAAI gate open.
- Historical v31 results are intentionally excluded from this table until provenance is recovered.

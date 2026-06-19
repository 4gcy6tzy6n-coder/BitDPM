# BitDPM AAAI Baseline and Gap Table

This report is generated from saved block-pool JSON files. It includes
baselines computable without new model inference and marks external
baselines that still require new experiments.

## Computable Baselines

- Random router seeds: 200
- Random candidates include baseline: `False`
- Random candidates include Always-All: `False`

| Setting | Benchmark | N | Frozen Backbone | Best Fixed | Best Fixed Config | Oracle | Coverage | Always-All | Random Router Mean | Random Std | Random Fixes | Random Breaks | Random Net | Prompt-Only | Prompt Net | LoRA | LoRA Net |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| v14 full current pool | v14 | 300 | 0.840 | 0.840 | `baseline` | 0.903 | 19/300 | 0.000 | 0.745 | 0.016 | 5.080 | 36.415 | -31.335 | 0.872 | 10 | 0.963 | 39 |
| v15 targeted current pool | v15 | 120 | 0.442 | 0.508 | `chinese_semantic` | 0.742 | 36/120 | 0.000 | 0.429 | 0.029 | 12.015 | 13.490 | -1.475 | 0.575 | 13 | 0.867 | 48 |
| v08 current pool | v08 | 100 | 0.830 | 0.830 | `baseline` | 0.900 | 7/100 | 0.000 | 0.753 | 0.024 | 1.370 | 9.915 | -8.545 | pending | pending | pending | pending |

## Prompt-Only Baselines

| Setting | Benchmark | Policy | Source | Prompted | Baseline | Delta | Fixes | Breaks | Net |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| v14 full current pool | v14 | `category_aware` | `experiments/reports/prompt_only/prompt_only_category_aware_v14_20260618_142141.json` | 0.872 | 0.833 | 0.038 | 21 | 11 | 10 |
| v15 targeted current pool | v15 | `category_aware` | `experiments/reports/prompt_only/prompt_only_category_aware_v15_20260618_142603.json` | 0.575 | 0.467 | 0.108 | 22 | 9 | 13 |

## Standard LoRA Baselines

| Setting | Benchmark | Rank | Epochs | Source | LoRA | Baseline | Delta | Fixes | Breaks | Net |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| v14 full current pool | v14 | 16 | 1 | `experiments/reports/lora_baseline/lora_r16_v14_20260618_152312.json` | 0.963 | 0.833 | 0.130 | 45 | 6 | 39 |
| v15 targeted current pool | v15 | 16 | 1 | `experiments/reports/lora_baseline/lora_r16_v15_20260618_152929.json` | 0.867 | 0.467 | 0.400 | 55 | 7 | 48 |

## Missing External Baselines

| Baseline | Status | Required Evidence |
|---|---|---|
| Standard LoRA adapter | runnable pending | Install `.[peft]` and run `experiments/reports/lora_baseline_commands.sh`; this table will auto-ingest latest LoRA JSON outputs. |
| Prompt-only rules | runnable pending | Run `experiments/reports/external_baseline_commands.sh`; this table will auto-ingest the latest prompt-only JSON outputs. |
| Best fixed adapter/block | partially covered | Best fixed block is computed from current reports; a separately trained always-on LoRA adapter is still missing. |
| Random router | covered from saved reports | This report simulates random selection from existing per-sample block scores. |
| Frozen backbone | covered from saved reports | Baseline row in block-pool reports. |
| Oracle upper bound | covered from saved reports | Per-sample best config from block-pool reports. |

## Interpretation

- The random router is a routing negative control, not a deployment strategy.
- Always-All remains a parameter-interference negative control.
- Prompt-only has a runnable evaluation path; completed outputs are auto-ingested when present.
- LoRA has a runnable PEFT-based evaluation path; completed outputs are auto-ingested when present.

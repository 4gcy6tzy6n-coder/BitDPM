# BitDPM AAAI Experiment Status

Overall execution status: **INCOMPLETE**

This report summarizes current experiment outputs only. Command scripts are
listed as next actions when matching result JSON files are missing.

| Group | Benchmark | Status | N | Baseline | Method/Oracle | Delta | Fixes | Breaks | Net | Latest Artifact | Notes |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| current-pool oracle | v14 | **MISSING** | - | - | - | - | - | - | - | `-` | Run experiments/reports/aaai_main_experiment_commands.sh. |
| strict-CV router | v14 | **MISSING** | - | - | - | - | - | - | - | `-` | Generated after each current-pool report by aaai_main_experiment_commands.sh. |
| prompt-only baseline | v14 | **DONE** | 300 | 0.833 | 0.872 | 0.038 | 21 | 11 | 10 | `experiments/reports/prompt_only/prompt_only_category_aware_v14_20260618_142141.json` | policy=category_aware |
| standard LoRA baseline | v14 | **DONE** | 300 | 0.833 | 0.963 | 0.130 | 45 | 6 | 39 | `experiments/reports/lora_baseline/lora_r16_v14_20260618_152312.json` | rank=16, train=120 |
| current-pool oracle | v15 | **MISSING** | - | - | - | - | - | - | - | `-` | Run experiments/reports/aaai_main_experiment_commands.sh. |
| strict-CV router | v15 | **MISSING** | - | - | - | - | - | - | - | `-` | Generated after each current-pool report by aaai_main_experiment_commands.sh. |
| prompt-only baseline | v15 | **DONE** | 120 | 0.467 | 0.575 | 0.108 | 22 | 9 | 13 | `experiments/reports/prompt_only/prompt_only_category_aware_v15_20260618_142603.json` | policy=category_aware |
| standard LoRA baseline | v15 | **DONE** | 120 | 0.467 | 0.867 | 0.400 | 55 | 7 | 48 | `experiments/reports/lora_baseline/lora_r16_v15_20260618_152929.json` | rank=16, train=120 |
| current-pool oracle | v1k_clean | **MISSING** | - | - | - | - | - | - | - | `-` | Run experiments/reports/aaai_main_experiment_commands.sh. |
| strict-CV router | v1k_clean | **MISSING** | - | - | - | - | - | - | - | `-` | Generated after each current-pool report by aaai_main_experiment_commands.sh. |
| prompt-only baseline | v1k_clean | **DONE** | 1000 | 0.825 | 0.802 | -0.022 | 77 | 97 | -20 | `experiments/reports/prompt_only/prompt_only_category_aware_v1k_clean_20260618_150657.json` | policy=category_aware |
| standard LoRA baseline | v1k_clean | **DONE** | 1000 | 0.825 | 0.861 | 0.036 | 92 | 53 | 39 | `experiments/reports/lora_baseline/lora_r16_v1k_clean_20260618_161931.json` | rank=16, train=120 |

## Immediate Commands

Run these only if the corresponding rows are still `MISSING`:

```bash
bash experiments/reports/aaai_main_experiment_commands.sh
bash experiments/reports/external_baseline_commands.sh
pip install -e '.[peft]'
bash experiments/reports/lora_baseline_commands.sh
python scripts/build_paper_package.py
```

## Interpretation

- `DONE` means the expected artifact exists and was summarized.
- `PASS` means the strict-CV router artifact exists and has positive delta, fixes>0, and zero breaks.
- `MISSING` means no matching result JSON exists yet.
- `REVIEW` means an artifact exists but does not satisfy the conservative status rule.

#!/usr/bin/env bash
set -euo pipefail

# BitDPM external baseline commands.
# These commands evaluate prompt-only baselines. Standard LoRA remains a
# required pending baseline and should be added once a LoRA training/eval
# recipe is finalized.

# Prompt-only baseline on v14.
python scripts/run_prompt_only_baseline.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --benchmark-set v14 \
  --prompt-policy category_aware \
  --deterministic \
  --save-outputs \
  --tag prompt_only_category_aware_v14

# Prompt-only baseline on v15.
python scripts/run_prompt_only_baseline.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --benchmark-set v15 \
  --prompt-policy category_aware \
  --deterministic \
  --save-outputs \
  --tag prompt_only_category_aware_v15

# Prompt-only baseline on v1k_clean.
python scripts/run_prompt_only_baseline.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --benchmark-set v1k_clean \
  --prompt-policy category_aware \
  --deterministic \
  --save-outputs \
  --tag prompt_only_category_aware_v1k_clean

python scripts/build_aaai_baseline_gap_table.py
python scripts/build_paper_package.py

echo 'External baseline commands complete.'

#!/usr/bin/env bash
set -euo pipefail

# BitDPM standard LoRA baseline commands.
# Requires PEFT: pip install -e '.[peft]'

# Standard LoRA baseline on v14.
python scripts/run_lora_baseline.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --benchmark-set v14 \
  --rank 16 \
  --alpha 32 \
  --train-samples 120 \
  --epochs 1 \
  --deterministic \
  --save-outputs \
  --tag lora_r16_v14

# Standard LoRA baseline on v15.
python scripts/run_lora_baseline.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --benchmark-set v15 \
  --rank 16 \
  --alpha 32 \
  --train-samples 120 \
  --epochs 1 \
  --deterministic \
  --save-outputs \
  --tag lora_r16_v15

# Standard LoRA baseline on v1k_clean.
python scripts/run_lora_baseline.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --benchmark-set v1k_clean \
  --rank 16 \
  --alpha 32 \
  --train-samples 120 \
  --epochs 1 \
  --deterministic \
  --save-outputs \
  --tag lora_r16_v1k_clean

python scripts/build_aaai_baseline_gap_table.py
python scripts/build_paper_package.py

echo 'LoRA baseline commands complete.'

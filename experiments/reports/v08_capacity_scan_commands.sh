#!/usr/bin/env bash
set -euo pipefail

# BitDPM v0.8 capacity scan commands.
# Run this whole file or copy individual blocks.

echo '=== Train rank 8 ==='
BITDPM_FORCE_CPU=1 python scripts/train_v07_blocks.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --output-dir experiments/outputs/blocks_v08_error_l22_l24_down_rank8 \
  --datasets calculation_error commonsense_choice format_following chinese_semantic short_reasoning \
  --structure l22_l24_down \
  --rank 8 \
  --epochs 5 \
  --batch-size 1 \
  --lr 0.0002 \
  --max-length 96

echo '=== Eval rank 8 scale 0.45 deterministic ==='
BITDPM_FORCE_CPU=1 python scripts/run_v05_router_calibration.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --load-blocks experiments/outputs/blocks_v08_error_l22_l24_down_rank8 \
  --benchmark-set v08 \
  --save-outputs \
  --block-scale 0.45 \
  --tag v08_rank8_scale045_v08_det \
  --deterministic

echo '=== Eval rank 8 scale 0.45 stable sampling ==='
BITDPM_FORCE_CPU=1 python scripts/run_v05_router_calibration.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --load-blocks experiments/outputs/blocks_v08_error_l22_l24_down_rank8 \
  --benchmark-set v08 \
  --save-outputs \
  --block-scale 0.45 \
  --tag v08_rank8_scale045_v08_stable_sampling \
  --seed 0 \
  --stable-sampling-seeds

echo '=== Eval rank 8 scale 0.60 deterministic ==='
BITDPM_FORCE_CPU=1 python scripts/run_v05_router_calibration.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --load-blocks experiments/outputs/blocks_v08_error_l22_l24_down_rank8 \
  --benchmark-set v08 \
  --save-outputs \
  --block-scale 0.60 \
  --tag v08_rank8_scale06_v08_det \
  --deterministic

echo '=== Eval rank 8 scale 0.60 stable sampling ==='
BITDPM_FORCE_CPU=1 python scripts/run_v05_router_calibration.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --load-blocks experiments/outputs/blocks_v08_error_l22_l24_down_rank8 \
  --benchmark-set v08 \
  --save-outputs \
  --block-scale 0.60 \
  --tag v08_rank8_scale06_v08_stable_sampling \
  --seed 0 \
  --stable-sampling-seeds

echo '=== Eval rank 8 scale 0.75 deterministic ==='
BITDPM_FORCE_CPU=1 python scripts/run_v05_router_calibration.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --load-blocks experiments/outputs/blocks_v08_error_l22_l24_down_rank8 \
  --benchmark-set v08 \
  --save-outputs \
  --block-scale 0.75 \
  --tag v08_rank8_scale075_v08_det \
  --deterministic

echo '=== Eval rank 8 scale 0.75 stable sampling ==='
BITDPM_FORCE_CPU=1 python scripts/run_v05_router_calibration.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --load-blocks experiments/outputs/blocks_v08_error_l22_l24_down_rank8 \
  --benchmark-set v08 \
  --save-outputs \
  --block-scale 0.75 \
  --tag v08_rank8_scale075_v08_stable_sampling \
  --seed 0 \
  --stable-sampling-seeds

echo '=== Train rank 16 ==='
BITDPM_FORCE_CPU=1 python scripts/train_v07_blocks.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --output-dir experiments/outputs/blocks_v08_error_l22_l24_down_rank16 \
  --datasets calculation_error commonsense_choice format_following chinese_semantic short_reasoning \
  --structure l22_l24_down \
  --rank 16 \
  --epochs 5 \
  --batch-size 1 \
  --lr 0.0002 \
  --max-length 96

echo '=== Eval rank 16 scale 0.45 deterministic ==='
BITDPM_FORCE_CPU=1 python scripts/run_v05_router_calibration.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --load-blocks experiments/outputs/blocks_v08_error_l22_l24_down_rank16 \
  --benchmark-set v08 \
  --save-outputs \
  --block-scale 0.45 \
  --tag v08_rank16_scale045_v08_det \
  --deterministic

echo '=== Eval rank 16 scale 0.45 stable sampling ==='
BITDPM_FORCE_CPU=1 python scripts/run_v05_router_calibration.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --load-blocks experiments/outputs/blocks_v08_error_l22_l24_down_rank16 \
  --benchmark-set v08 \
  --save-outputs \
  --block-scale 0.45 \
  --tag v08_rank16_scale045_v08_stable_sampling \
  --seed 0 \
  --stable-sampling-seeds

echo '=== Eval rank 16 scale 0.60 deterministic ==='
BITDPM_FORCE_CPU=1 python scripts/run_v05_router_calibration.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --load-blocks experiments/outputs/blocks_v08_error_l22_l24_down_rank16 \
  --benchmark-set v08 \
  --save-outputs \
  --block-scale 0.60 \
  --tag v08_rank16_scale06_v08_det \
  --deterministic

echo '=== Eval rank 16 scale 0.60 stable sampling ==='
BITDPM_FORCE_CPU=1 python scripts/run_v05_router_calibration.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --load-blocks experiments/outputs/blocks_v08_error_l22_l24_down_rank16 \
  --benchmark-set v08 \
  --save-outputs \
  --block-scale 0.60 \
  --tag v08_rank16_scale06_v08_stable_sampling \
  --seed 0 \
  --stable-sampling-seeds

echo '=== Eval rank 16 scale 0.75 deterministic ==='
BITDPM_FORCE_CPU=1 python scripts/run_v05_router_calibration.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --load-blocks experiments/outputs/blocks_v08_error_l22_l24_down_rank16 \
  --benchmark-set v08 \
  --save-outputs \
  --block-scale 0.75 \
  --tag v08_rank16_scale075_v08_det \
  --deterministic

echo '=== Eval rank 16 scale 0.75 stable sampling ==='
BITDPM_FORCE_CPU=1 python scripts/run_v05_router_calibration.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --load-blocks experiments/outputs/blocks_v08_error_l22_l24_down_rank16 \
  --benchmark-set v08 \
  --save-outputs \
  --block-scale 0.75 \
  --tag v08_rank16_scale075_v08_stable_sampling \
  --seed 0 \
  --stable-sampling-seeds

echo '=== Train rank 32 ==='
BITDPM_FORCE_CPU=1 python scripts/train_v07_blocks.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --output-dir experiments/outputs/blocks_v08_error_l22_l24_down_rank32 \
  --datasets calculation_error commonsense_choice format_following chinese_semantic short_reasoning \
  --structure l22_l24_down \
  --rank 32 \
  --epochs 5 \
  --batch-size 1 \
  --lr 0.0002 \
  --max-length 96

echo '=== Eval rank 32 scale 0.45 deterministic ==='
BITDPM_FORCE_CPU=1 python scripts/run_v05_router_calibration.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --load-blocks experiments/outputs/blocks_v08_error_l22_l24_down_rank32 \
  --benchmark-set v08 \
  --save-outputs \
  --block-scale 0.45 \
  --tag v08_rank32_scale045_v08_det \
  --deterministic

echo '=== Eval rank 32 scale 0.45 stable sampling ==='
BITDPM_FORCE_CPU=1 python scripts/run_v05_router_calibration.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --load-blocks experiments/outputs/blocks_v08_error_l22_l24_down_rank32 \
  --benchmark-set v08 \
  --save-outputs \
  --block-scale 0.45 \
  --tag v08_rank32_scale045_v08_stable_sampling \
  --seed 0 \
  --stable-sampling-seeds

echo '=== Eval rank 32 scale 0.60 deterministic ==='
BITDPM_FORCE_CPU=1 python scripts/run_v05_router_calibration.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --load-blocks experiments/outputs/blocks_v08_error_l22_l24_down_rank32 \
  --benchmark-set v08 \
  --save-outputs \
  --block-scale 0.60 \
  --tag v08_rank32_scale06_v08_det \
  --deterministic

echo '=== Eval rank 32 scale 0.60 stable sampling ==='
BITDPM_FORCE_CPU=1 python scripts/run_v05_router_calibration.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --load-blocks experiments/outputs/blocks_v08_error_l22_l24_down_rank32 \
  --benchmark-set v08 \
  --save-outputs \
  --block-scale 0.60 \
  --tag v08_rank32_scale06_v08_stable_sampling \
  --seed 0 \
  --stable-sampling-seeds

echo '=== Eval rank 32 scale 0.75 deterministic ==='
BITDPM_FORCE_CPU=1 python scripts/run_v05_router_calibration.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --load-blocks experiments/outputs/blocks_v08_error_l22_l24_down_rank32 \
  --benchmark-set v08 \
  --save-outputs \
  --block-scale 0.75 \
  --tag v08_rank32_scale075_v08_det \
  --deterministic

echo '=== Eval rank 32 scale 0.75 stable sampling ==='
BITDPM_FORCE_CPU=1 python scripts/run_v05_router_calibration.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --load-blocks experiments/outputs/blocks_v08_error_l22_l24_down_rank32 \
  --benchmark-set v08 \
  --save-outputs \
  --block-scale 0.75 \
  --tag v08_rank32_scale075_v08_stable_sampling \
  --seed 0 \
  --stable-sampling-seeds

echo '=== Train rank 64 ==='
BITDPM_FORCE_CPU=1 python scripts/train_v07_blocks.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --output-dir experiments/outputs/blocks_v08_error_l22_l24_down_rank64 \
  --datasets calculation_error commonsense_choice format_following chinese_semantic short_reasoning \
  --structure l22_l24_down \
  --rank 64 \
  --epochs 5 \
  --batch-size 1 \
  --lr 0.0002 \
  --max-length 96

echo '=== Eval rank 64 scale 0.45 deterministic ==='
BITDPM_FORCE_CPU=1 python scripts/run_v05_router_calibration.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --load-blocks experiments/outputs/blocks_v08_error_l22_l24_down_rank64 \
  --benchmark-set v08 \
  --save-outputs \
  --block-scale 0.45 \
  --tag v08_rank64_scale045_v08_det \
  --deterministic

echo '=== Eval rank 64 scale 0.45 stable sampling ==='
BITDPM_FORCE_CPU=1 python scripts/run_v05_router_calibration.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --load-blocks experiments/outputs/blocks_v08_error_l22_l24_down_rank64 \
  --benchmark-set v08 \
  --save-outputs \
  --block-scale 0.45 \
  --tag v08_rank64_scale045_v08_stable_sampling \
  --seed 0 \
  --stable-sampling-seeds

echo '=== Eval rank 64 scale 0.60 deterministic ==='
BITDPM_FORCE_CPU=1 python scripts/run_v05_router_calibration.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --load-blocks experiments/outputs/blocks_v08_error_l22_l24_down_rank64 \
  --benchmark-set v08 \
  --save-outputs \
  --block-scale 0.60 \
  --tag v08_rank64_scale06_v08_det \
  --deterministic

echo '=== Eval rank 64 scale 0.60 stable sampling ==='
BITDPM_FORCE_CPU=1 python scripts/run_v05_router_calibration.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --load-blocks experiments/outputs/blocks_v08_error_l22_l24_down_rank64 \
  --benchmark-set v08 \
  --save-outputs \
  --block-scale 0.60 \
  --tag v08_rank64_scale06_v08_stable_sampling \
  --seed 0 \
  --stable-sampling-seeds

echo '=== Eval rank 64 scale 0.75 deterministic ==='
BITDPM_FORCE_CPU=1 python scripts/run_v05_router_calibration.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --load-blocks experiments/outputs/blocks_v08_error_l22_l24_down_rank64 \
  --benchmark-set v08 \
  --save-outputs \
  --block-scale 0.75 \
  --tag v08_rank64_scale075_v08_det \
  --deterministic

echo '=== Eval rank 64 scale 0.75 stable sampling ==='
BITDPM_FORCE_CPU=1 python scripts/run_v05_router_calibration.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --load-blocks experiments/outputs/blocks_v08_error_l22_l24_down_rank64 \
  --benchmark-set v08 \
  --save-outputs \
  --block-scale 0.75 \
  --tag v08_rank64_scale075_v08_stable_sampling \
  --seed 0 \
  --stable-sampling-seeds

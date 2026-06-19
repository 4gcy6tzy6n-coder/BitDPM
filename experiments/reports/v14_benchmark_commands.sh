#!/usr/bin/env bash
set -euo pipefail

# BitDPM v14 300-sample stratified benchmark

if [ -f experiments/reports/v14_v10_best_pool_stable_sampling_LATEST.json ]; then
  echo 'Skip v14 eval: experiments/reports/v14_v10_best_pool_stable_sampling_LATEST.json exists'
else
  BITDPM_FORCE_CPU=1 python scripts/run_v05_router_calibration.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --load-blocks experiments/outputs/blocks_v08_error_l22_l24_down_rank16 experiments/outputs/blocks_v09_repair_l22_l24_down_rank16 \
  --benchmark-set v14 \
  --seed 0 \
  --stable-sampling-seeds \
  --save-outputs \
  --block-scale 0.75 \
  --block-scales \
  commonsense_choice=0.6 \
  format_following=0.75 \
  chinese_semantic=0.75 \
  calculation_error=0.3 \
  short_reasoning=0.45 \
  arithmetic_power_log=0.75 \
  --configs \
  baseline \
  commonsense_choice \
  format_following \
  chinese_semantic \
  calculation_error \
  short_reasoning \
  arithmetic_power_log \
  always_all \
  --tag v14_v10_best_pool_stable_sampling
  latest=$(ls -t experiments/reports/v14_v10_best_pool_stable_sampling_*.json | head -1)
  cp "$latest" experiments/reports/v14_v10_best_pool_stable_sampling_LATEST.json
fi

python scripts/analyze_v08_block_safety.py \
  --report experiments/reports/v14_v10_best_pool_stable_sampling_LATEST.json \
  --tag v14_v10_best_pool_stable_sampling

python scripts/mine_v08_utility.py \
  --report experiments/reports/v14_v10_best_pool_stable_sampling_LATEST.json \
  --tag v14_v10_best_pool_stable_sampling

python scripts/analyze_v12_rule_router.py \
  --report experiments/reports/v14_v10_best_pool_stable_sampling_LATEST.json \
  --tag v14_v10_rule_router

python scripts/train_v12_utility_router.py \
  --report experiments/reports/v14_v10_best_pool_stable_sampling_LATEST.json \
  --tag v14_v10_utility_router_safe \
  --eval-on-all \
  --min-fixes 1 \
  --max-breaks 0 \
  --min-precision 1.0 \
  --min-specificity 2 \
  --full-safety-filter

python scripts/crossval_v12_utility_router.py \
  --report experiments/reports/v14_v10_best_pool_stable_sampling_LATEST.json \
  --tag v14_v10_utility_router_strict_cv \
  --folds 5 \
  --min-fixes 1 \
  --max-breaks 0 \
  --min-precision 1.0 \
  --min-specificity 2

python scripts/summarize_v14_report.py \
  --report experiments/reports/v14_v10_best_pool_stable_sampling_LATEST.json \
  --tag v14_v10_best_pool

echo 'v14 benchmark commands complete.'

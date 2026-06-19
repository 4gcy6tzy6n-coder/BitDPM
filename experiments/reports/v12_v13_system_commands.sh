#!/usr/bin/env bash
set -euo pipefail

# BitDPM v12/v13 systemization commands

echo '=== v12 offline conservative rule router on current best report ==='
python scripts/analyze_v12_rule_router.py \
  --report experiments/reports/v10_admitted_powerlog_stable_sampling_20260607_212715.json \
  --tag v12_v10_conservative_rule_router

echo '=== v12 mined utility-aware router on current best report ==='
python scripts/train_v12_utility_router.py \
  --report experiments/reports/v10_admitted_powerlog_stable_sampling_20260607_212715.json \
  --tag v12_v10_utility_router_safe \
  --eval-on-all \
  --min-fixes 1 \
  --max-breaks 0 \
  --min-precision 1.0 \
  --min-specificity 2 \
  --full-safety-filter

echo '=== v12 strict cross-validation for utility-aware router ==='
python scripts/crossval_v12_utility_router.py \
  --report experiments/reports/v10_admitted_powerlog_stable_sampling_20260607_212715.json \
  --tag v12_v10_utility_router_strict_cv \
  --folds 5 \
  --min-fixes 1 \
  --max-breaks 0 \
  --min-precision 1.0 \
  --min-specificity 2

echo '=== v13 safety cards for current best pool ==='
python scripts/build_v13_safety_cards.py \
  --safety-report experiments/reports/v08_block_safety/v10_admitted_powerlog_stable_sampling_block_safety.json \
  --admission-report experiments/reports/v10_admission/v10_v09b_admission_admission.json \
  --registry configs/bitdpm_v10_admitted_pool.json \
  --tag v13_v10_best_pool

echo '=== v13 pairwise incompatibility eval for current best pool ==='
if [ -f experiments/reports/v13_v10_pairwise_stable_sampling_LATEST.json ]; then
  echo 'Skip pairwise eval: experiments/reports/v13_v10_pairwise_stable_sampling_LATEST.json exists'
else
  BITDPM_FORCE_CPU=1 python scripts/run_v05_router_calibration.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --load-blocks experiments/outputs/blocks_v08_error_l22_l24_down_rank16 experiments/outputs/blocks_v09_repair_l22_l24_down_rank16 \
  --benchmark-set v08 \
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
  commonsense_choice+format_following \
  commonsense_choice+chinese_semantic \
  commonsense_choice+calculation_error \
  commonsense_choice+short_reasoning \
  commonsense_choice+arithmetic_power_log \
  format_following+chinese_semantic \
  format_following+calculation_error \
  format_following+short_reasoning \
  format_following+arithmetic_power_log \
  chinese_semantic+calculation_error \
  chinese_semantic+short_reasoning \
  chinese_semantic+arithmetic_power_log \
  calculation_error+short_reasoning \
  calculation_error+arithmetic_power_log \
  short_reasoning+arithmetic_power_log \
  always_all \
  --tag v13_v10_pairwise_stable_sampling
  latest=$(ls -t experiments/reports/v13_v10_pairwise_stable_sampling_*.json | head -1)
  cp "$latest" experiments/reports/v13_v10_pairwise_stable_sampling_LATEST.json
fi

python scripts/analyze_v13_incompatibility.py \
  --report experiments/reports/v13_v10_pairwise_stable_sampling_LATEST.json \
  --tag v13_v10_pairwise

echo 'v12/v13 commands complete.'

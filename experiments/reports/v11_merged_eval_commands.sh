#!/usr/bin/env bash
set -euo pipefail

# BitDPM v11 merged unique-utility candidate evaluation

if [ ! -f experiments/outputs/blocks_v11_unique_repair_l22_l24_down_rank16/training_summary.json ]; then
  echo 'Missing v11 training outputs. Run experiments/reports/v11_unique_utility_commands.sh first.'
  exit 1
fi

if [ -f experiments/reports/v11_merged_candidates_stable_sampling_LATEST.json ]; then
  echo 'Skip merged eval: experiments/reports/v11_merged_candidates_stable_sampling_LATEST.json exists'
else
  BITDPM_FORCE_CPU=1 python scripts/run_v05_router_calibration.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --load-blocks experiments/outputs/blocks_v08_error_l22_l24_down_rank16 experiments/outputs/blocks_v09_repair_l22_l24_down_rank16 experiments/outputs/blocks_v11_unique_repair_l22_l24_down_rank16 \
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
  v11_linear_equation=0.75 \
  v11_percent_time_distance=0.75 \
  v11_circle_area=0.75 \
  v11_stats_number_theory=0.75 \
  v11_factorial_derivative=0.75 \
  --configs \
  baseline \
  commonsense_choice \
  format_following \
  chinese_semantic \
  calculation_error \
  short_reasoning \
  arithmetic_power_log \
  v11_linear_equation \
  v11_percent_time_distance \
  v11_circle_area \
  v11_stats_number_theory \
  v11_factorial_derivative \
  always_all \
  --tag v11_merged_candidates_stable_sampling
  latest=$(ls -t experiments/reports/v11_merged_candidates_stable_sampling_*.json | head -1)
  cp "$latest" experiments/reports/v11_merged_candidates_stable_sampling_LATEST.json
fi

python scripts/analyze_v08_block_safety.py \
  --report experiments/reports/v11_merged_candidates_stable_sampling_LATEST.json \
  --tag v11_merged_candidates_stable_sampling

python scripts/mine_v08_utility.py \
  --report experiments/reports/v11_merged_candidates_stable_sampling_LATEST.json \
  --tag v11_merged_candidates_stable_sampling

python scripts/analyze_v10_admission.py \
  --base v10=experiments/reports/v10_admitted_powerlog_stable_sampling_20260607_212715.json \
  --candidates v11_merged=experiments/reports/v11_merged_candidates_stable_sampling_LATEST.json \
  --candidate-blocks \
  v11_linear_equation \
  v11_percent_time_distance \
  v11_circle_area \
  v11_stats_number_theory \
  v11_factorial_derivative \
  --tag v11_merged_unique_utility_admission

python scripts/summarize_v14_report.py \
  --report experiments/reports/v11_merged_candidates_stable_sampling_LATEST.json \
  --tag v11_merged_candidates

echo 'v11 merged eval complete.'

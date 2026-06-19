#!/usr/bin/env bash
set -euo pipefail

# BitDPM v11 Unique-Utility Repair Mining

echo '=== Train v11 candidate repair blocks ==='
if [ -f experiments/outputs/blocks_v11_unique_repair_l22_l24_down_rank16/training_summary.json ]; then
  echo 'Skip training: experiments/outputs/blocks_v11_unique_repair_l22_l24_down_rank16/training_summary.json exists'
else
  BITDPM_FORCE_CPU=1 python scripts/train_v07_blocks.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --output-dir experiments/outputs/blocks_v11_unique_repair_l22_l24_down_rank16 \
  --datasets v11_linear_equation v11_percent_time_distance v11_circle_area v11_stats_number_theory v11_factorial_derivative \
  --structure l22_l24_down \
  --rank 16 \
  --epochs 5 \
  --batch-size 1 \
  --lr 2e-4 \
  --max-length 96
fi

echo '=== Eval candidate v11_linear_equation ==='
if [ -f experiments/reports/v11_add_v11_linear_equation_stable_sampling_LATEST.json ]; then
  echo 'Skip eval: experiments/reports/v11_add_v11_linear_equation_stable_sampling_LATEST.json exists'
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
  --configs \
  baseline \
  commonsense_choice \
  format_following \
  chinese_semantic \
  calculation_error \
  short_reasoning \
  arithmetic_power_log \
  v11_linear_equation \
  always_all \
  --tag v11_add_v11_linear_equation_stable_sampling

python scripts/analyze_v08_block_safety.py \
    --report "$(ls -t experiments/reports/v11_add_v11_linear_equation_stable_sampling_*.json | head -1)" \
    --tag v11_add_v11_linear_equation_stable_sampling
  python scripts/mine_v08_utility.py \
    --report "$(ls -t experiments/reports/v11_add_v11_linear_equation_stable_sampling_*.json | head -1)" \
    --tag v11_add_v11_linear_equation_stable_sampling

  latest=$(ls -t experiments/reports/v11_add_v11_linear_equation_stable_sampling_*.json | head -1)
  cp "$latest" experiments/reports/v11_add_v11_linear_equation_stable_sampling_LATEST.json
fi

echo '=== Eval candidate v11_percent_time_distance ==='
if [ -f experiments/reports/v11_add_v11_percent_time_distance_stable_sampling_LATEST.json ]; then
  echo 'Skip eval: experiments/reports/v11_add_v11_percent_time_distance_stable_sampling_LATEST.json exists'
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
  v11_percent_time_distance=0.75 \
  --configs \
  baseline \
  commonsense_choice \
  format_following \
  chinese_semantic \
  calculation_error \
  short_reasoning \
  arithmetic_power_log \
  v11_percent_time_distance \
  always_all \
  --tag v11_add_v11_percent_time_distance_stable_sampling

python scripts/analyze_v08_block_safety.py \
    --report "$(ls -t experiments/reports/v11_add_v11_percent_time_distance_stable_sampling_*.json | head -1)" \
    --tag v11_add_v11_percent_time_distance_stable_sampling
  python scripts/mine_v08_utility.py \
    --report "$(ls -t experiments/reports/v11_add_v11_percent_time_distance_stable_sampling_*.json | head -1)" \
    --tag v11_add_v11_percent_time_distance_stable_sampling

  latest=$(ls -t experiments/reports/v11_add_v11_percent_time_distance_stable_sampling_*.json | head -1)
  cp "$latest" experiments/reports/v11_add_v11_percent_time_distance_stable_sampling_LATEST.json
fi

echo '=== Eval candidate v11_circle_area ==='
if [ -f experiments/reports/v11_add_v11_circle_area_stable_sampling_LATEST.json ]; then
  echo 'Skip eval: experiments/reports/v11_add_v11_circle_area_stable_sampling_LATEST.json exists'
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
  v11_circle_area=0.75 \
  --configs \
  baseline \
  commonsense_choice \
  format_following \
  chinese_semantic \
  calculation_error \
  short_reasoning \
  arithmetic_power_log \
  v11_circle_area \
  always_all \
  --tag v11_add_v11_circle_area_stable_sampling

python scripts/analyze_v08_block_safety.py \
    --report "$(ls -t experiments/reports/v11_add_v11_circle_area_stable_sampling_*.json | head -1)" \
    --tag v11_add_v11_circle_area_stable_sampling
  python scripts/mine_v08_utility.py \
    --report "$(ls -t experiments/reports/v11_add_v11_circle_area_stable_sampling_*.json | head -1)" \
    --tag v11_add_v11_circle_area_stable_sampling

  latest=$(ls -t experiments/reports/v11_add_v11_circle_area_stable_sampling_*.json | head -1)
  cp "$latest" experiments/reports/v11_add_v11_circle_area_stable_sampling_LATEST.json
fi

echo '=== Eval candidate v11_stats_number_theory ==='
if [ -f experiments/reports/v11_add_v11_stats_number_theory_stable_sampling_LATEST.json ]; then
  echo 'Skip eval: experiments/reports/v11_add_v11_stats_number_theory_stable_sampling_LATEST.json exists'
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
  v11_stats_number_theory=0.75 \
  --configs \
  baseline \
  commonsense_choice \
  format_following \
  chinese_semantic \
  calculation_error \
  short_reasoning \
  arithmetic_power_log \
  v11_stats_number_theory \
  always_all \
  --tag v11_add_v11_stats_number_theory_stable_sampling

python scripts/analyze_v08_block_safety.py \
    --report "$(ls -t experiments/reports/v11_add_v11_stats_number_theory_stable_sampling_*.json | head -1)" \
    --tag v11_add_v11_stats_number_theory_stable_sampling
  python scripts/mine_v08_utility.py \
    --report "$(ls -t experiments/reports/v11_add_v11_stats_number_theory_stable_sampling_*.json | head -1)" \
    --tag v11_add_v11_stats_number_theory_stable_sampling

  latest=$(ls -t experiments/reports/v11_add_v11_stats_number_theory_stable_sampling_*.json | head -1)
  cp "$latest" experiments/reports/v11_add_v11_stats_number_theory_stable_sampling_LATEST.json
fi

echo '=== Eval candidate v11_factorial_derivative ==='
if [ -f experiments/reports/v11_add_v11_factorial_derivative_stable_sampling_LATEST.json ]; then
  echo 'Skip eval: experiments/reports/v11_add_v11_factorial_derivative_stable_sampling_LATEST.json exists'
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
  v11_factorial_derivative=0.75 \
  --configs \
  baseline \
  commonsense_choice \
  format_following \
  chinese_semantic \
  calculation_error \
  short_reasoning \
  arithmetic_power_log \
  v11_factorial_derivative \
  always_all \
  --tag v11_add_v11_factorial_derivative_stable_sampling

python scripts/analyze_v08_block_safety.py \
    --report "$(ls -t experiments/reports/v11_add_v11_factorial_derivative_stable_sampling_*.json | head -1)" \
    --tag v11_add_v11_factorial_derivative_stable_sampling
  python scripts/mine_v08_utility.py \
    --report "$(ls -t experiments/reports/v11_add_v11_factorial_derivative_stable_sampling_*.json | head -1)" \
    --tag v11_add_v11_factorial_derivative_stable_sampling

  latest=$(ls -t experiments/reports/v11_add_v11_factorial_derivative_stable_sampling_*.json | head -1)
  cp "$latest" experiments/reports/v11_add_v11_factorial_derivative_stable_sampling_LATEST.json
fi

echo '=== v11 admission analysis ==='
python scripts/analyze_v10_admission.py \
  --base v10=experiments/reports/v10_admitted_powerlog_stable_sampling_20260607_212715.json \
  --candidates \
  v11_linear_equation=experiments/reports/v11_add_v11_linear_equation_stable_sampling_LATEST.json \
  v11_percent_time_distance=experiments/reports/v11_add_v11_percent_time_distance_stable_sampling_LATEST.json \
  v11_circle_area=experiments/reports/v11_add_v11_circle_area_stable_sampling_LATEST.json \
  v11_stats_number_theory=experiments/reports/v11_add_v11_stats_number_theory_stable_sampling_LATEST.json \
  v11_factorial_derivative=experiments/reports/v11_add_v11_factorial_derivative_stable_sampling_LATEST.json \
  --tag v11_unique_utility_admission

echo 'v11 commands complete.'

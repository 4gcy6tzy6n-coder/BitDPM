#!/usr/bin/env bash
set -euo pipefail

# BitDPM AAAI main experiment script.
# This is a generated command file. It runs current-method validation only;
# it does not add new mechanisms or claim v31 recovery.

python scripts/build_paper_package.py

# Stage 1: Current broad validation on v14.
BITDPM_FORCE_CPU=1 python scripts/run_v10_registry_eval.py \
  --registry configs/bitdpm_v11_admitted_pool.json \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --benchmark-set v14 \
  --tag aaai_v14_current_pool \
  --resume
AAAI_V14_CURRENT_POOL_REPORT=$(ls -t experiments/reports/aaai_v14_current_pool_*.json | head -1)
echo "aaai_v14_current_pool report: $AAAI_V14_CURRENT_POOL_REPORT"

python scripts/train_v12_utility_router.py \
  --report $AAAI_V14_CURRENT_POOL_REPORT \
  --tag aaai_v14_current_pool_allow_core_nolog_safe \
  --eval-on-all \
  --min-fixes 1 \
  --max-breaks 0 \
  --min-precision 1.0 \
  --min-specificity 2 \
  --full-safety-filter \
  --allowed-features has_multiplication,has_distance,has_coordinate,has_mean

python scripts/crossval_v12_utility_router.py \
  --report $AAAI_V14_CURRENT_POOL_REPORT \
  --tag aaai_v14_current_pool_allow_core_nolog_cv \
  --folds 5 \
  --min-fixes 1 \
  --max-breaks 0 \
  --min-precision 1.0 \
  --min-specificity 2 \
  --allowed-features has_multiplication,has_distance,has_coordinate,has_mean

python scripts/bootstrap_result_ci.py \
  $AAAI_V14_CURRENT_POOL_REPORT \
  --samples 2000 \
  --seed 13 \
  --out experiments/reports/aaai_v14_current_pool_bootstrap_ci.md

# Stage 2: Targeted router-safety validation on v15.
BITDPM_FORCE_CPU=1 python scripts/run_v10_registry_eval.py \
  --registry configs/bitdpm_v11_admitted_pool.json \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --benchmark-set v15 \
  --tag aaai_v15_current_pool \
  --resume
AAAI_V15_CURRENT_POOL_REPORT=$(ls -t experiments/reports/aaai_v15_current_pool_*.json | head -1)
echo "aaai_v15_current_pool report: $AAAI_V15_CURRENT_POOL_REPORT"

python scripts/train_v12_utility_router.py \
  --report $AAAI_V15_CURRENT_POOL_REPORT \
  --tag aaai_v15_current_pool_allow_core_nolog_safe \
  --eval-on-all \
  --min-fixes 1 \
  --max-breaks 0 \
  --min-precision 1.0 \
  --min-specificity 2 \
  --full-safety-filter \
  --allowed-features has_multiplication,has_distance,has_coordinate,has_mean

python scripts/crossval_v12_utility_router.py \
  --report $AAAI_V15_CURRENT_POOL_REPORT \
  --tag aaai_v15_current_pool_allow_core_nolog_cv \
  --folds 5 \
  --min-fixes 1 \
  --max-breaks 0 \
  --min-precision 1.0 \
  --min-specificity 2 \
  --allowed-features has_multiplication,has_distance,has_coordinate,has_mean

python scripts/bootstrap_result_ci.py \
  $AAAI_V15_CURRENT_POOL_REPORT \
  --samples 2000 \
  --seed 13 \
  --out experiments/reports/aaai_v15_current_pool_bootstrap_ci.md

# Stage 3: 1k clean mixed validation. Held-out claims require a passing overlap audit.
BITDPM_FORCE_CPU=1 python scripts/run_v10_registry_eval.py \
  --registry configs/bitdpm_v11_admitted_pool.json \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --benchmark-set v1k_clean \
  --tag aaai_v1k_clean_current_pool \
  --resume
AAAI_V1K_CLEAN_CURRENT_POOL_REPORT=$(ls -t experiments/reports/aaai_v1k_clean_current_pool_*.json | head -1)
echo "aaai_v1k_clean_current_pool report: $AAAI_V1K_CLEAN_CURRENT_POOL_REPORT"

python scripts/train_v12_utility_router.py \
  --report $AAAI_V1K_CLEAN_CURRENT_POOL_REPORT \
  --tag aaai_v1k_clean_current_pool_allow_core_nolog_safe \
  --eval-on-all \
  --min-fixes 1 \
  --max-breaks 0 \
  --min-precision 1.0 \
  --min-specificity 2 \
  --full-safety-filter \
  --allowed-features has_multiplication,has_distance,has_coordinate,has_mean

python scripts/crossval_v12_utility_router.py \
  --report $AAAI_V1K_CLEAN_CURRENT_POOL_REPORT \
  --tag aaai_v1k_clean_current_pool_allow_core_nolog_cv \
  --folds 5 \
  --min-fixes 1 \
  --max-breaks 0 \
  --min-precision 1.0 \
  --min-specificity 2 \
  --allowed-features has_multiplication,has_distance,has_coordinate,has_mean

python scripts/bootstrap_result_ci.py \
  $AAAI_V1K_CLEAN_CURRENT_POOL_REPORT \
  --samples 2000 \
  --seed 13 \
  --out experiments/reports/aaai_v1k_clean_current_pool_bootstrap_ci.md

# Stage 4: Rebuild paper-facing reports after new outputs exist.
python scripts/build_paper_result_tables.py
python scripts/build_aaai_readiness_report.py
python scripts/build_paper_package.py

echo 'AAAI main experiment commands complete.'

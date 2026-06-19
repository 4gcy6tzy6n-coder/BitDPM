#!/usr/bin/env bash
set -euo pipefail

# BitDPM v15 router-validation benchmark
# This benchmark validates router trigger safety, not broad model capability.

python scripts/run_v10_registry_eval.py \
  --registry configs/bitdpm_v11_admitted_pool.json \
  --benchmark-set v15 \
  --tag v15_router_validation_v11_admitted \
  --resume

REPORT=$(ls -t experiments/reports/v15_router_validation_v11_admitted_*.json | head -1)
echo "Using report: $REPORT"

python scripts/summarize_v14_report.py \
  --report ${REPORT} \
  --tag v15_router_validation_v11_admitted

python scripts/train_v12_utility_router.py \
  --report ${REPORT} \
  --tag v15_router_validation_v11_admitted_allow_core_safe \
  --eval-on-all \
  --min-fixes 1 \
  --max-breaks 0 \
  --min-precision 1.0 \
  --min-specificity 2 \
  --full-safety-filter \
  --allowed-features has_multiplication,has_distance,has_coordinate,has_mean,has_log

python scripts/crossval_v12_utility_router.py \
  --report ${REPORT} \
  --tag v15_router_validation_v11_admitted_allow_core_cv \
  --folds 5 \
  --min-fixes 1 \
  --max-breaks 0 \
  --min-precision 1.0 \
  --min-specificity 2 \
  --allowed-features has_multiplication,has_distance,has_coordinate,has_mean,has_log

python scripts/train_v12_utility_router.py \
  --report ${REPORT} \
  --tag v15_router_validation_v11_admitted_allow_core_nolog_safe \
  --eval-on-all \
  --min-fixes 1 \
  --max-breaks 0 \
  --min-precision 1.0 \
  --min-specificity 2 \
  --full-safety-filter \
  --allowed-features has_multiplication,has_distance,has_coordinate,has_mean

python scripts/crossval_v12_utility_router.py \
  --report ${REPORT} \
  --tag v15_router_validation_v11_admitted_allow_core_nolog_cv \
  --folds 5 \
  --min-fixes 1 \
  --max-breaks 0 \
  --min-precision 1.0 \
  --min-specificity 2 \
  --allowed-features has_multiplication,has_distance,has_coordinate,has_mean

python scripts/train_v12_utility_router.py \
  --report ${REPORT} \
  --tag v15_router_validation_v11_admitted_conj_safe \
  --eval-on-all \
  --min-fixes 1 \
  --max-breaks 0 \
  --min-precision 1.0 \
  --min-specificity 3 \
  --full-safety-filter \
  --include-conjunctions

python scripts/crossval_v12_utility_router.py \
  --report ${REPORT} \
  --tag v15_router_validation_v11_admitted_conj_cv \
  --folds 5 \
  --min-fixes 1 \
  --max-breaks 0 \
  --min-precision 1.0 \
  --min-specificity 3 \
  --include-conjunctions

python scripts/build_paper_result_tables.py

echo 'v15 router-validation commands complete.'

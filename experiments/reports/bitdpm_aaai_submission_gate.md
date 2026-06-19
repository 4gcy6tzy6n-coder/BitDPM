# BitDPM AAAI Submission Gate Check

Overall status: **NOT READY**

| Gate | Status | Evidence | Requirement |
|---|---|---|---|
| Provenance-complete main result | **FAIL** | experiments/reports/bitdpm_v31_provenance_audit.md: UNRECOVERED | Recover exact v31 provenance or train/replay a compatible main block with model, block path, SHA256, benchmark, decoding, and max-token metadata. |
| Benchmark held-out audit | **PASS** | experiments/reports/bitdpm_benchmark_manifest.json: v1k_clean∩core=0, v1k_clean∩v08=0, v1k_clean∩v14=0, v1k_clean∩v15=0 | Need zero exact normalized prompt overlap between the paper-scale v1k_clean benchmark and earlier core/v08/v14/v15 validation sets before calling it held-out. |
| 1k-clean main validation | **FAIL** | No `experiments/reports/aaai_v1k_clean_current_pool_*.json` report found. | Run `bash experiments/reports/aaai_main_experiment_commands.sh` and produce v1k_clean baseline/fixed/oracle/router/Always-All results. |
| Held-out conservative router | **PASS** | experiments/reports/v12_router/v14_full_v11_utility_router_allow_core_nolog_cv_crossval.json: delta=+0.017, fixes=5, breaks=0; experiments/reports/v12_router/v15_router_validation_v11_admitted_allow_core_nolog_cv_crossval.json: delta=+0.058, fixes=7, breaks=0 | Need positive held-out router net with zero or very low breaks on at least two benchmarks. |
| External baselines | **PASS** | v14: prompt-only=experiments/reports/prompt_only/prompt_only_category_aware_v14_20260618_142141.json, lora=experiments/reports/lora_baseline/lora_r16_v14_20260618_152312.json; v15: prompt-only=experiments/reports/prompt_only/prompt_only_category_aware_v15_20260618_142603.json, lora=experiments/reports/lora_baseline/lora_r16_v15_20260618_152929.json; v1k_clean: prompt-only=experiments/reports/prompt_only/prompt_only_category_aware_v1k_clean_20260618_150657.json, lora=experiments/reports/lora_baseline/lora_r16_v1k_clean_20260618_161931.json | Need completed prompt-only and standard LoRA/always-on adapter results on v14, v15, and v1k_clean. |
| Consolidated ablations | **PASS** | experiments/reports/bitdpm_aaai_ablation_table.md: present | Need consolidated rank/scale/admission/transfer/router ablation table generated from artifacts. |
| Statistical reporting | **PASS** | experiments/reports/bitdpm_v14_full_bootstrap_ci.md=present; experiments/reports/bitdpm_v14_allow_core_nolog_cv_bootstrap_ci.md=present | Need bootstrap confidence intervals for main benchmark and deployable router deltas. |
| Paper package and claim discipline | **PASS** | paper/bitdpm_aaai_draft.md=present; paper/claim_to_evidence.md=present; paper/aaai_main_experiment_protocol.md=present; experiments/reports/bitdpm_paper_artifact_index.md=present | Need paper draft, claim-to-evidence map, experiment protocol, and artifact index. |

## Interpretation

- `PASS` means current artifacts directly support the gate.
- `PARTIAL` means infrastructure or partial results exist, but final evidence is incomplete.
- `FAIL` means the required evidence is missing or contradicted.

Do not claim high-confidence AAAI readiness while overall status is `NOT READY`.

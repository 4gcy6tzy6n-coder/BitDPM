# BitDPM Reproducibility Checklist

This checklist tracks which commands produce the current paper-facing evidence.

## Current Frozen Evidence

### One-Command Paper Package Rebuild

Command:

```bash
python scripts/build_paper_package.py
```

Outputs:

```bash
experiments/reports/block_manifest.md
experiments/reports/bitdpm_benchmark_manifest.md
experiments/reports/paper_tables/bitdpm_current_results.md
experiments/reports/paper_tables/bitdpm_aaai_main_results.md
experiments/reports/bitdpm_v31_provenance_audit.md
experiments/reports/bitdpm_v14_full_bootstrap_ci.md
experiments/reports/bitdpm_v14_allow_core_nolog_cv_bootstrap_ci.md
experiments/reports/bitdpm_aaai_readiness_report.md
experiments/reports/bitdpm_aaai_submission_gate.md
experiments/reports/bitdpm_aaai_experiment_status.md
experiments/reports/bitdpm_paper_artifact_index.md
paper/bitdpm_aaai_draft.md
paper/claim_to_evidence.md
paper/aaai_main_experiment_protocol.md
experiments/reports/aaai_main_experiment_commands.sh
experiments/reports/bitdpm_aaai_baseline_gap_table.md
experiments/reports/bitdpm_aaai_ablation_table.md
experiments/reports/external_baseline_commands.sh
experiments/reports/lora_baseline_commands.sh
```

Use this command before paper writing, result discussion, or follow-up
experiments. It refreshes saved-artifact evidence and indexes the current paper
draft/checklist files; it does not run model inference.

### AAAI Readiness Status

Command:

```bash
python scripts/build_aaai_readiness_report.py
```

Output:

```bash
experiments/reports/bitdpm_aaai_readiness_report.md
```

Current verdict:

- BitDPM is ready for a rigorous mechanism-oriented paper draft.
- It is not yet at a high-confidence AAAI main-result state.
- v31 `allow_math@0.85 -> fixes=6, breaks=0` remains a frozen historical record
  until exact block/backbone provenance is recovered or a compatible block is
  retrained and replayed.
- AAAI-level readiness requires provenance-complete main results, 1k+
  overlap-audited validation, external baselines, and stronger held-out router
  generalization.

### v14 Full 300-Sample Validation

Main report:

```bash
experiments/reports/v14_full_v11_admitted_20260608_093845.json
```

Summary:

```bash
experiments/reports/bitdpm_v14_full_summary.md
```

Current full-v14 result:

- baseline: `0.840`
- oracle: `0.903`
- coverage: `19/300`
- best fixed: `0.840`
- Always-All: `0.000`

Current safest router:

- allow-core-no-log strict CV: `0.857`
- baseline: `0.840`
- gain: `+0.017`
- fixes: `5`
- breaks: `0`

Important caveat:

- The unrestricted/full-report routers recover more fixes, but conjunction expansion overfits held-out validation.
- v15 validation shows `has_log` is unsafe under stricter router slices.
- Current deployable-router claim should be limited to conservative allow-core-no-log routing with modest zero-break gain.

### v11 Current Best Oracle Pool

Main report:

```bash
experiments/reports/v11_merged_candidates_stable_sampling_LATEST.json
```

Registry:

```bash
configs/bitdpm_v11_admitted_pool.json
```

Expected oracle result:

- baseline: `0.830`
- oracle: `0.900`
- coverage: `7/100`
- best fixed: `0.830`
- Always-All: `0.000`

Important caveat:

- `v11_stats_number_theory` is admitted for unique oracle utility, not for fixed activation.
- v10 remains the safer deployable/fixed baseline until router validation improves.

### v10 Best Pool

Main report:

```bash
experiments/reports/v10_admitted_powerlog_stable_sampling_20260607_212715.json
```

Registry:

```bash
configs/bitdpm_v10_admitted_pool.json
```

Re-run command:

```bash
python scripts/run_v10_registry_eval.py \
  --registry configs/bitdpm_v10_admitted_pool.json \
  --tag v10_admitted_powerlog_repro
```

Expected result:

- baseline: `0.830`
- oracle: `0.890`
- coverage: `6/100`
- best fixed: `0.830`
- Always-All: `0.000`

### Paper Result Tables

Command:

```bash
python scripts/build_paper_result_tables.py
```

Output:

```bash
experiments/reports/paper_tables/bitdpm_current_results.md
```

Use this as the current single source of truth for v08-v12 result tables.
Use `experiments/reports/bitdpm_v14_full_summary.md` and
`experiments/reports/bitdpm_v14_router_ablation.md` for the latest full-v14
router interpretation.

## Completed Validation

### v15 Router-Validation Benchmark

Command:

```bash
bash experiments/reports/v15_router_validation_commands.sh
```

Purpose:

- Validate router trigger safety on a 120-sample slice benchmark.
- Stress-test current allow-core triggers.
- Add risky arithmetic controls that previously caused held-out breaks.
- Probe factual/constants and commonsense trigger expansion.

Decision gates:

- Strict CV must have `0` breaks for any router expansion to be admissible.
- Full-report gains without held-out safety are diagnostic only.
- New trigger families must add held-out fixes or gain beyond allow-core.

Plan:

```bash
experiments/reports/bitdpm_v15_router_validation_plan.md
```

Result:

```bash
experiments/reports/bitdpm_v15_router_validation_summary.md
```

Key result:

- baseline: `0.442`
- oracle: `0.742`
- coverage: `36/120`
- Always-All: `0.000`
- allow-core CV: `0.492`, fixes `7`, breaks `1`
- allow-core-no-log CV: `0.500`, fixes `7`, breaks `0`

Decision:

- Remove `has_log` from deployable routing.
- Keep `has_multiplication`, `has_distance`, `has_coordinate`, and `has_mean`.
- Treat conjunction routers as diagnostic only unless they satisfy zero-break strict CV.

## Pending Validation

### v11 Unique-Utility Mining

Preferred command after v11 blocks have been trained:

```bash
bash experiments/reports/v11_merged_eval_commands.sh
```

This evaluates all v11 candidate blocks in one model run and avoids repeated
baseline/base-pool generations.

Fallback full train+eval command:

```bash
bash experiments/reports/v11_unique_utility_commands.sh
```

Purpose:

- Train candidate unique-utility repair blocks.
- Evaluate each candidate as an add-on to the v10 pool.
- Decide admission by unique fixes, overlap fixes, breaks, and net utility.

Decision gate:

- Admit only blocks with at least one unique fix.
- Reject blocks with no unique coverage even if they overlap existing fixes.
- Interpret high-break blocks conservatively.

### v12/v13 Systemization

Command:

```bash
bash experiments/reports/v12_v13_system_commands.sh
```

Purpose:

- Run conservative rule router.
- Run mined utility router.
- Run strict router cross-validation.
- Generate block safety cards.
- Evaluate pairwise block incompatibility.

Current v12/v15 router status:

- full-report utility router: positive prototype
- full-v14 allow-core-no-log strict CV: modest positive gain with zero breaks
- v15 allow-core-no-log strict CV: stronger targeted-slice gain with zero breaks

Required interpretation:

- Do not claim broad deployable router generalization yet. Claim only conservative
  allow-core-no-log routing unless future validation expands it under zero-break
  strict CV.

### v14 300-Sample Benchmark

Recommended pilot command before full v14:

```bash
bash experiments/reports/v14_registry_eval_commands.sh
```

This runs both v10 and v11 admitted pools on a 60-sample v14 pilot
(`10 prompts/category`) and prints optional full-v14 commands.

Pilot result already obtained:

- v10 admitted: baseline `0.867`, oracle `0.950`, coverage `5/60`, Always-All `0.000`
- v11 admitted: baseline `0.867`, oracle `0.983`, coverage `7/60`, Always-All `0.000`

Summary:

```bash
experiments/reports/bitdpm_v14_pilot_summary.md
```

Legacy full v10-only command:

```bash
bash experiments/reports/v14_benchmark_commands.sh
```

Purpose:

- Re-test v10 best pool on a 300-sample stratified benchmark.
- Estimate whether sparse correction coverage holds beyond the 100-sample v08 set.
- Re-run v12 router mining and strict CV on the larger sample set.

Key gates:

- oracle > baseline
- non-baseline coverage remains nonzero and preferably grows
- Always-All remains below selective/oracle
- strict router CV has non-negative gain with low or zero breaks

## Current Safe Paper Claim

BitDPM is a runtime-selective sparse correction framework. Current parameter
blocks create rare but measurable correction opportunities, while Always-All
activation consistently exposes strong interference. The best current full-v14
pool is v11 admitted (`v0.8 hybrid + arithmetic_power_log +
v11_stats_number_theory`), reaching oracle `0.903` and coverage `19/300` over
baseline `0.840`. A conservative allow-core router obtains strict-CV `0.857`
with `5` fixes and `0` breaks on v14, but v15 shows that `has_log` is unsafe.
The current safest router is allow-core-no-log (`has_multiplication`,
`has_distance`, `has_coordinate`, `has_mean`), which keeps zero breaks on v14
and reaches v15 strict-CV `0.500` over baseline `0.442` with `7` fixes and `0`
breaks. Router generalization is promising but still limited.

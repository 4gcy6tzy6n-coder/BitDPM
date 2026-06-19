# BitDPM Claim-to-Evidence Map

This file maps paper claims to current evidence. It is stricter than the
technical reports: a claim is considered paper-safe only if the current
worktree contains a generated artifact that supports it.

## Evidence Tiers

| Tier | Meaning | Current Use |
|---|---|---|
| A | Generated result table or audit from saved JSON artifacts | Safe for paper draft |
| B | Generated report summary, but not a full main-result table | Safe with caveat |
| C | Historical record with missing provenance | Mention only as frozen history |
| D | Not yet supported | Do not claim |

## Safe Core Claims

| Claim | Evidence | Tier | Paper Wording |
|---|---|---:|---|
| BitDPM creates sparse per-sample correction opportunities. | `experiments/reports/paper_tables/bitdpm_current_results.md`: v14 full baseline `0.840`, oracle `0.903`, coverage `19/300`; v15 baseline `0.442`, oracle `0.742`, coverage `36/120`. | A | "BitDPM exposes sparse correction opportunities under oracle block selection." |
| All-block activation is unsafe and should be treated as a negative control. | Paper tables show Always-All `0.000` on v08/v14/v15 high-scale admitted pools. | A | "Indiscriminate all-block composition causes severe interference." |
| Unique-utility admission is better supported than semantic-label admission. | v10/v11 rows in paper tables: v10 oracle `0.890`, coverage `6/100`; v11 oracle `0.900`, coverage `7/100`. | A | "Block admission should prioritize unique per-sample coverage." |
| Conservative routing can preserve zero-break gains. | v14 allow-core-no-log strict CV `0.857` over `0.840`, fixes `5`, breaks `0`; v15 allow-core-no-log strict CV `0.500` over `0.442`, fixes `7`, breaks `0`. | A | "A conservative router achieves modest zero-break held-out gains." |
| Bootstrap uncertainty should be reported for main tables. | `bitdpm_v14_full_bootstrap_ci.md` and `bitdpm_v14_allow_core_nolog_cv_bootstrap_ci.md`. | A | "We report prompt-level bootstrap confidence intervals." |
| v31 is not current main evidence. | `bitdpm_v31_provenance_audit.md`: status `UNRECOVERED`; missing model/block/hash/benchmark/decoding fields; no 1.5B-compatible artifacts. | A | "The historical v31 result is frozen pending provenance recovery." |

## Claims Allowed Only With Caveats

| Claim | Evidence | Tier | Required Caveat |
|---|---|---:|---|
| BitDPM has a deployable router. | Zero-break allow-core-no-log strict CV exists, but gains are small. | A | Say "conservative prototype router", not "fully learned general router". |
| BitDPM improves benchmark accuracy. | Oracle improves strongly; deployable router improves modestly. | A | Separate oracle upper bound from deployable routing. |
| Error-type blocks are useful. | v08-v15 progression supports admitted error/repair pool. | B | Frame as current empirical pattern, not a universal law. |
| Scale calibration matters. | v07-v10 reports show scale-dependent oracle and Always-All behavior. | B | Cite as mechanism analysis, not the final main result. |
| Rank/scale/admission/router ablations are consolidated. | `bitdpm_aaai_ablation_table.md` summarizes rank, hybrid scale, unique admission, benchmark transfer, and router safety. | A | Use as the ablation source table for paper drafting. |
| Current results generalize beyond core-45. | v14 300 and v15 120 support this. | A | Do not claim 1k+ scale until that benchmark exists. |

## Claims That Are Not Safe

| Claim | Why Unsafe | Evidence Needed |
|---|---|---|
| BitDPM has a confirmed Qwen2.5-1.5B main result. | Saved blocks are 0.5B-compatible; v31 lacks provenance. | Train or recover 1.5B-compatible blocks with manifest hashes and replay. |
| v31 `0.956 / fixes=6 / breaks=0` is the current best result. | v31 is unrecovered; 0.5B replay did not reproduce it. | Exact block path, SHA256, backbone, benchmark, decoding settings, and replay. |
| BitDPM broadly improves most samples. | Coverage is sparse: v14 oracle coverage `19/300`. | Large-scale evidence showing broad fixed/router gains. |
| Always-All is a deployment strategy. | Always-All collapses to `0.000` for high-scale pools. | Not applicable; current evidence argues against this claim. |
| Router generalization is solved. | Held-out gains are positive but modest, and unrestricted routers break samples. | Preregistered router train/dev/test split with strong held-out net gains. |
| BitDPM beats standard LoRA or adapter baselines. | Random/fixed/oracle baselines are reportable; prompt-only and LoRA have runnable entries; completed prompt-only/LoRA results are still missing. | Run prompt-only and LoRA baseline commands, then compare fixes/breaks/net. |

## Main Tables Needed For AAAI-Level Claim

| Table | Current Status | Required Next Evidence |
|---|---|---|
| Main benchmark table | v14 300 and v15 120 exist; v1k_clean code/manifest exist for overlap-audited validation. | v1k_clean mixed benchmark with baseline/fixed/oracle/router/Always-All. |
| External baseline table | Partially covered by `bitdpm_aaai_baseline_gap_table.md`; prompt-only and LoRA commands exist; results still need to be run. | Run prompt-only and LoRA baselines; add any task-adapter comparison if needed. |
| Router generalization table | Modest zero-break strict CV exists. | Train/dev/test router with category breakdown and CIs. |
| Block provenance table | Manifest exists for saved blocks. | Include block hash, shape, backbone, train data, seed for every paper block. |
| Ablation table | Covered by `bitdpm_aaai_ablation_table.md`. | Keep regenerated from `scripts/build_aaai_ablation_table.py` after new main runs. |

## Recommended Paper Positioning

Current safe positioning:

> BitDPM is a runtime-selective sparse parameter correction framework. It shows
> that useful correction directions exist, that all-block activation is a strong
> negative control, and that block admission/routing must be governed by unique
> per-sample utility and break control.

Current submission status:

> Mechanism-oriented draft ready; high-confidence AAAI main-result paper still
> requires provenance-complete main result, 1k+ overlap-audited validation, external
> baselines, and stronger router generalization.

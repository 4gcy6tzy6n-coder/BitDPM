# BitDPM AAAI Readiness Report

## Bottom Line

BitDPM is not yet at a high-confidence AAAI main-result state. The current
evidence is strong enough for a mechanism-oriented technical report and a
paper draft, but a competitive AAAI submission still needs reproducible
main results on larger benchmarks, stronger external baselines, and a
non-oracle deployable router with stable held-out gains.

The v31 `allow_math@0.85 -> fixes=6, breaks=0` record is explicitly frozen:
it remains historical evidence until exact block/backbone provenance is
recovered or a compatible block is retrained and replayed.

## Current Paper-Usable Evidence

### Sparse Correction Oracle

| Setting | Benchmark | N | Baseline | Oracle | Gain | Coverage | Always-All |
| --- | --- | --- | --- | --- | --- | --- | --- |
| v15 router validation v11 admitted | v15 | 120 | 0.442 | 0.742 | 0.300 | 36/120 | 0.000 |
| v14 pilot v11 admitted | v14 | 60 | 0.867 | 0.983 | 0.117 | 7/60 | 0.000 |
| v14 pilot v10 admitted | v14 | 60 | 0.867 | 0.950 | 0.083 | 5/60 | 0.000 |
| v11 merged candidates | v08 | 100 | 0.830 | 0.900 | 0.070 | 7/100 | 0.000 |
| v14 full v11 admitted | v14 | 300 | 0.840 | 0.903 | 0.063 | 19/300 | 0.000 |
| v09b + power_log | v08 | 100 | 0.830 | 0.890 | 0.060 | 6/100 | 0.000 |

Interpretation: sparse correction opportunities are real, measurable, and
persist beyond core-45. The strongest broad-scale evidence is v14 full
300-sample validation: oracle `0.903` over baseline `0.840`, coverage
`19/300`, and Always-All `0.000`.

### Deployable Router Evidence

| Setting | Router | Baseline | Gain | Fixes | Breaks | Evidence Type |
| --- | --- | --- | --- | --- | --- | --- |
| v15 allow-core-no-log utility strict CV | 0.500 | 0.442 | 0.058 | 7 | 0 | held-out cross-validation |
| v14 full v11 allow-core utility strict CV | 0.857 | 0.840 | 0.017 | 5 | 0 | held-out cross-validation |
| v14 full v11 allow-core-no-log utility strict CV | 0.857 | 0.840 | 0.017 | 5 | 0 | held-out cross-validation |
| v12 rule router | 0.870 | 0.830 | 0.040 | 4 | 0 | hand-authored conservative rules |
| v15 conjunction utility full-report | 0.575 | 0.442 | 0.133 | 16 | 0 | full-report safety-filter prototype |
| v15 allow-core utility full-report | 0.517 | 0.442 | 0.075 | 9 | 0 | full-report safety-filter prototype |
| v15 allow-core-no-log utility full-report | 0.517 | 0.442 | 0.075 | 9 | 0 | full-report safety-filter prototype |
| v12 utility full-report | 0.880 | 0.830 | 0.050 | 5 | 0 | full-report safety-filter prototype |

Interpretation: zero-break routing exists, but the gains are still modest
under strict held-out validation. The table prioritizes held-out CV over
full-report prototypes. The safest current deployable claim is conservative
allow-core-no-log routing, not broad learned routing.

## Claims That Are Safe Today

1. BitDPM parameter blocks can create sparse per-sample correction opportunities.
2. All-block activation is a negative control and often collapses for high-scale pools.
3. Unique-utility block admission is better supported than semantic-label admission.
4. Conservative safety routing can preserve zero-break gains on v14/v15 validation.
5. Engineering reproducibility now requires block/backbone dimension auditing.

## Claims That Must Not Be Made Yet

1. Do not claim v31 is a confirmed 1.5B result.
2. Do not claim the v31 `0.956` score as current reproducible main evidence.
3. Do not claim broad deployable router generalization.
4. Do not claim BitDPM improves most samples; current utility is sparse.
5. Do not claim Always-All or adapter merging is the intended deployment mode.

## AAAI-Level Gaps

| Dimension | Current State | AAAI Requirement |
| --- | --- | --- |
| Main result provenance | v31 is unrecovered | Recover exact block or retrain compatible 1.5B block with full metadata |
| Scale | 300-sample v14; 120-sample targeted v15; v1k_clean code exists for overlap-audited validation | Run v1k_clean and report confidence intervals |
| External baselines | Random/fixed/oracle covered; prompt-only and LoRA runnable | Run prompt-only and LoRA outputs; add task-adapter comparison if needed |
| Router generalization | Zero-break but modest strict-CV gains | Train/evaluate a preregistered router on train/dev/test splits |
| Ablations | Consolidated rank/scale/admission/router table exists | Refresh ablation table after v1k and external-baseline runs |
| Reproducibility | Crash doc covers six failure modes | Use `scripts/build_paper_package.py` as the one-command paper-evidence rebuild entry |

## Required Main Experiment Plan

### Stage A: Reproducible Main Path

- Freeze model, block registry, benchmark split, decoding, evaluator, and random seed.
- If pursuing 1.5B, train fresh 1.5B-compatible down-proj blocks; do not reuse 0.5B blocks.
- Run `audit_v31_provenance.py` and block manifest generation before any migration claim.

### Stage B: Paper-Scale Validation

- v14 full 300: rerun current best pool and safest router from a clean manifest.
- Use `v1k_clean`, a 1k mixed benchmark with balanced arithmetic, factual, commonsense, Chinese, code, and reasoning slices.
- Treat the benchmark as held-out only after `bitdpm_benchmark_manifest` shows zero exact prompt overlap with prior validation sets.
- Report baseline, best fixed, oracle, deployable router, Always-All, fixes, breaks, net, active ratio.

### Stage C: Baselines and Ablations

- Baselines: frozen backbone, standard LoRA adapter, always-on best adapter, random router, full-report oracle, prompt-only rules.
- Ablations: rank, scale, layer/module placement, unique-utility admission, router features, and device/dtype safety.
- Statistical reporting: bootstrap confidence intervals over prompts and per-category breakdowns.

## AAAI Submission Gate

A high-level AAAI claim should wait until all of the following are true:

- A reproducible, provenance-complete main result exists.
- Deployable router improves held-out accuracy with zero or very low breaks on at least two benchmarks.
- Oracle coverage remains meaningful on 1k+ prompts.
- External baselines are included and BitDPM wins on correction safety or parameter efficiency.
- All paper tables are generated from scripts, not hand-edited summaries.

## Recommended Current Positioning

Current best positioning is a rigorous mechanism paper draft:

> BitDPM is a runtime-selective sparse parameter correction framework. It
> shows that useful correction directions exist, that indiscriminate block
> composition is unsafe, and that block admission and routing must be
> governed by unique per-sample utility and break control. The method is
> promising but still needs provenance-complete large-scale validation for
> a strong AAAI main-result claim.

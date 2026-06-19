# BitDPM AAAI Main Experiment Plan

## Goal

Move BitDPM from a mechanism-oriented draft to a credible AAAI main-result
submission. This plan does not add new mechanisms; it defines the evidence
needed to make the current mechanism publishable at a high level.

## Current Status

Current valid positioning:

> BitDPM is a runtime-selective sparse parameter correction framework. It shows
> measurable sparse correction opportunities, strong all-block interference, and
> the need for unique-utility block admission plus conservative safety routing.

Current blocker:

- v31 `allow_math@0.85 -> fixes=6, breaks=0` is unrecovered and cannot be used
  as current main evidence.
- Current strongest broad-scale evidence is v14 full 300-sample oracle:
  baseline `0.840`, oracle `0.903`, coverage `19/300`, Always-All `0.000`.
- Current deployable router evidence is modest but safe:
  allow-core-no-log strict CV `0.857` over baseline `0.840`, fixes `5`,
  breaks `0`.

## Stage 0: Rebuild Current Evidence

Run these before changing any method, block, router, or benchmark:

```bash
python scripts/build_block_manifest.py

python scripts/audit_v31_provenance.py \
  --out experiments/reports/bitdpm_v31_provenance_audit.md

python scripts/build_paper_result_tables.py

python scripts/build_aaai_readiness_report.py
```

Expected gate:

- v31 provenance audit remains explicit about `UNRECOVERED`, unless exact block
  provenance has been recovered.
- paper tables and AAAI readiness report regenerate without hand edits.

## Stage 1: Statistical Reporting

Generate confidence intervals for current broad-scale evidence:

```bash
python scripts/bootstrap_result_ci.py \
  experiments/reports/v14_full_v11_admitted_20260608_093845.json \
  --samples 2000 \
  --seed 13 \
  --out experiments/reports/bitdpm_v14_full_bootstrap_ci.md

python scripts/bootstrap_result_ci.py \
  experiments/reports/v12_router/v14_full_v11_utility_router_allow_core_nolog_cv_crossval.json \
  --samples 2000 \
  --seed 13 \
  --out experiments/reports/bitdpm_v14_allow_core_nolog_cv_bootstrap_ci.md
```

Current observed CI examples with 1000 bootstrap samples:

- v14 full baseline: `0.840`, 95% CI `[0.797, 0.880]`
- v14 full oracle: `0.903`, 95% CI `[0.867, 0.937]`
- v14 allow-core-no-log router delta: `+0.017`, 95% CI `[0.003, 0.033]`

AAAI gate:

- Report CIs for baseline, oracle, router, and delta on every main benchmark.

## Stage 2: Reproducible Main Result

Two acceptable paths:

### Path A: Recover v31

Only use v31 if all of the following are recovered:

- exact `block_path`
- `block_sha256`
- model/backbone
- benchmark split
- deterministic/sampling settings
- max tokens and evaluator version

Then rerun:

```bash
python scripts/run_v32_router_validation.py \
  --model "$V31_BACKBONE" \
  --block-path "$V31_BLOCK" \
  --benchmark-set core \
  --routers allow_math \
  --scales 0.85 \
  --device mps \
  --dtype float16 \
  --max-tokens 64 \
  --output-path experiments/reports/v32a_core45_allow_math085.json \
  --resume \
  --tag v32a_core45_allow_math085
```

Gate:

- Must reproduce core-45 near `0.956`, fixes `>=6`, breaks `0`.
- Must then transfer to larger validation; core-only recovery is not enough.

### Path B: Retrain Compatible Main Block

If v31 provenance is not recovered, do not continue using v31. Train a fresh
compatible block with full metadata.

Required metadata:

```json
{
  "model": "...",
  "layer": "...",
  "module": "...",
  "rank": "...",
  "A_shape": "...",
  "B_shape": "...",
  "train_data": "...",
  "seed": "...",
  "created_at": "...",
  "sha256": "..."
}
```

Gate:

- block/backbone compatibility passes before evaluation
- zero or very low held-out breaks under conservative router
- positive net on at least two held-out benchmarks

## Stage 3: Paper-Scale Benchmarks

Minimum benchmark matrix:

| Benchmark | Purpose | Minimum Gate |
|---|---|---|
| core-45 | sanity/reproduction only | reproduce if using v31 |
| v08-100 | continuity with v10/v11 | oracle coverage nonzero, Always-All below oracle |
| v14-300 | broad mixed validation | router net positive with low breaks |
| v15-120 | targeted router safety | zero-break router or explain break type |
| new 1k+ held-out | AAAI main scale | positive router net, meaningful oracle coverage |

Required reported metrics:

- baseline
- best fixed
- oracle
- deployable router
- Always-All
- fixes / breaks / net
- active ratio
- per-category breakdown
- 95% bootstrap CI

## Stage 4: External Baselines

AAAI submission needs comparison beyond internal BitDPM variants.

Required baselines:

| Baseline | Purpose |
|---|---|
| frozen backbone | base capability |
| standard LoRA adapter | conventional always-on adaptation |
| best fixed adapter/block | compare against non-routed adaptation |
| random router | routing negative control |
| prompt-only rules | distinguish parameter effect from prompt/evaluator artifacts |
| oracle upper bound | separate block utility from router quality |

## Stage 5: Paper Claim Gate

Do not claim AAAI-level success until:

1. Main result has full provenance.
2. v14/v15 or larger held-out benchmarks show positive router net.
3. Breaks are zero or substantially lower than fixes.
4. Oracle coverage remains meaningful at 1k+ sample scale.
5. External baselines are included.
6. All result tables are script-generated.

## Current Recommendation

Write a mechanism-first draft now, but do not submit as a high-confidence AAAI
main-result paper until Stage 2-5 are complete.

# BitDPM v32 Fixed Migration Commands

> **Frozen after v31-R audit.** Do not run these migration commands until the
> exact v31 block artifact is recovered or a new compatible block is trained.
> The v31-R audit found no saved Qwen2.5-1.5B-compatible block and the saved
> 0.5B block pool did not reproduce the v31 `fixes=6, breaks=0` result.

Purpose: validate whether the v31 best deployable setting transfers beyond the
core-45 benchmark. This is a main-experiment validation pass, not a new
mechanism search.

## Frozen Setting

- Backbone: must match the recovered or newly trained `$V31_BLOCK`
- Block: exact v31 repair block, exported as `$V31_BLOCK`, with known sha256
- Scale: `0.85`
- Router: `allow_math`
- Decoding: deterministic, `do_sample=False`
- Metric: `baseline`, `routed`, `fixes`, `breaks`, `net`, `active`

Before running migration, the block must pass compatibility validation:

```text
block.A.shape[0] == target_layer.in_features
block.B.shape[1] == target_layer.out_features
```

Known audit result:

```text
Saved block inventory:
  Qwen2.5-0.5B-compatible: 145
  Qwen2.5-1.5B-compatible: 0

0.5B replay with saved v17/v18/v21/v24 candidates:
  positive-net candidates: 0
  zero-break candidates: 0
  best: 0.778 -> 0.733, fixes=1, breaks=3, net=-2
```

If the exact v31 block path is recovered, set:

```bash
export V31_BACKBONE=Qwen/Qwen2.5-0.5B-Instruct   # or the recovered exact model
export V31_BLOCK=/absolute/path/to/v31_repair_block.pt
```

If the block was selected by `scripts/select_v32_best_block.py`, load:

```bash
source experiments/reports/v32_best_block.env
```

## 0. Sanity Check

This command is only a metadata dry run. The non-dry-run path now performs an
explicit block/backbone shape check before injection.

```bash
python scripts/run_v32_router_validation.py \
  --model "$V31_BACKBONE" \
  --block-path "$V31_BLOCK" \
  --benchmark-set core \
  --routers allow_math \
  --scales 0.85 \
  --dry-run
```

## 1. v32-A Core-45 Reproducibility

This must reproduce the v31 target before transfer claims are made.

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

Historical target reference, not yet recovered from a reproducible block path:

| Benchmark | Router | Scale | Baseline | Routed | Fixes | Breaks | Net | Active |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| core-45 | allow_math | 0.85 | 0.822 | 0.956 | 6 | 0 | +6 | 20/45 |

## 2. v32-B v15-120 Targeted Validation

Run v15 before v08/v14 because it is the router-validation slice.

```bash
python scripts/run_v32_router_validation.py \
  --model "$V31_BACKBONE" \
  --block-path "$V31_BLOCK" \
  --benchmark-set v15 \
  --routers allow_math \
  --scales 0.85 \
  --device mps \
  --dtype float16 \
  --max-tokens 64 \
  --output-path experiments/reports/v32b_v15_120_allow_math085.json \
  --resume \
  --tag v32b_v15_120_allow_math085
```

## 3. v32-C v08-100 Expanded Benchmark

```bash
python scripts/run_v32_router_validation.py \
  --model "$V31_BACKBONE" \
  --block-path "$V31_BLOCK" \
  --benchmark-set v08 \
  --routers allow_math \
  --scales 0.85 \
  --device mps \
  --dtype float16 \
  --max-tokens 64 \
  --output-path experiments/reports/v32c_v08_100_allow_math085.json \
  --resume \
  --tag v32c_v08_100_allow_math085
```

## 4. v32-D v14-300 Stratified Validation

Only run this after core-45 reproduces and v15/v08 show positive or diagnosable
transfer.

```bash
python scripts/run_v32_router_validation.py \
  --model "$V31_BACKBONE" \
  --block-path "$V31_BLOCK" \
  --benchmark-set v14 \
  --routers allow_math \
  --scales 0.85 \
  --device mps \
  --dtype float16 \
  --max-tokens 64 \
  --output-path experiments/reports/v32d_v14_300_allow_math085.json \
  --resume \
  --tag v32d_v14_300_allow_math085
```

## 5. Optional Ablation: Unrestricted and Blacklist

Run this only after the main `allow_math` transfer pass. `blacklist_only` is an
ablation; the main deployable configuration remains `allow_math`.

```bash
python scripts/run_v32_router_validation.py \
  --model "$V31_BACKBONE" \
  --block-path "$V31_BLOCK" \
  --benchmark-set v15 \
  --routers unrestricted blacklist_only allow_math \
  --scales 0.85 \
  --device mps \
  --dtype float16 \
  --max-tokens 64 \
  --output-path experiments/reports/v32_ablation_v15_120_scale085.json \
  --resume \
  --tag v32_ablation_v15_120_scale085
```

## 6. Summarize Main Runs

```bash
python scripts/summarize_v32_results.py \
  experiments/reports/v32a_core45_allow_math085.json \
  experiments/reports/v32b_v15_120_allow_math085.json \
  experiments/reports/v32c_v08_100_allow_math085.json \
  experiments/reports/v32d_v14_300_allow_math085.json \
  --limit 20 \
  --write-report experiments/reports/bitdpm_v32_fixed_migration_summary.md
```

## Decision Criteria

- Minimum success: transfer `net > 0` and `breaks <= fixes / 2`.
- Clear success on 100/120 samples: `net >= +5` and `breaks <= 2`.
- Strong success on 300 samples: `net >= +10`, low breaks, and reasonable
  active ratio.

Diagnosis:

- Active too low: `allow_math` is too conservative.
- Active high but fixes low: block is core-pattern specific.
- Breaks high: router is too broad; add safety filters before widening.
- Fixes and breaks both high: block has transfer utility but needs finer
  feature-level routing.

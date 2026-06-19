# BitDPM v32 Router Validation Commands

Use the exact v31 repair block path as `--block-path` when known. The v30/v31
JSON reports do not record that path, so the v32 runner also supports
`--block-glob` for candidate scanning.

Recommended block placeholder:

```bash
V31_BLOCK=/absolute/path/to/v31_repair_block.pt
```

## 0. Build Block Artifact Manifest

Run this before v32 scans so every candidate block has stable metadata and a
SHA256 hash:

```bash
python scripts/build_block_manifest.py \
  --json-out experiments/reports/block_manifest.json \
  --md-out experiments/reports/block_manifest.md
```

Use the manifest to cite the final block artifact in reports:

- JSON: `experiments/reports/block_manifest.json`
- Markdown: `experiments/reports/block_manifest.md`

The v32 runner also writes `block_sha256` into every result row, so final result
JSON files are self-contained even if the manifest is regenerated later.

When `--output-path ... --resume` is used, the runner also writes a baseline
cache next to the result file, for example:

- result: `experiments/reports/v32_core_candidate_scan.json`
- baseline cache: `experiments/reports/v32_core_candidate_scan.baseline.json`

If a long run is interrupted, repeat the same command. Completed block/router
runs and completed baseline generations will be skipped.

## 0b. Lightweight Toolchain Test

Run this before long model evaluations when router/mining code has changed:

```bash
python tests/test_v33_feature_router.py
python -m py_compile \
  scripts/run_v32_router_validation.py \
  scripts/mine_v33_safety_router.py \
  scripts/summarize_v32_results.py \
  scripts/build_block_manifest.py
```

## 1. Reproduce v31 on Core 45

```bash
python scripts/run_v32_router_validation.py \
  --block-path "$V31_BLOCK" \
  --benchmark-set core \
  --routers unrestricted blacklist_only allow_math \
  --scales 0.85 1.0 \
  --device mps \
  --dtype float16 \
  --max-tokens 64 \
  --tag v32_core_v31_repro
```

Expected reference from v31:

| Router | Scale | Baseline | Routed | Fixes | Breaks | Net |
|---|---:|---:|---:|---:|---:|---:|
| unrestricted | 0.85 | 0.822 | 0.922 | 6 | 2 | +4 |
| unrestricted | 1.0 | 0.822 | 0.900 | 6 | 3 | +3 |
| blacklist_only | 0.85 | 0.822 | 0.956 | 6 | 0 | +6 |
| blacklist_only | 1.0 | 0.822 | 0.956 | 6 | 0 | +6 |
| allow_math | 0.85 | 0.822 | 0.956 | 6 | 0 | +6 |
| allow_math | 1.0 | 0.822 | 0.933 | 6 | 1 | +5 |

## 1b. Recover the v31 Block Path by Candidate Scan

If the exact v31 block path is unknown, scan the most likely saved candidates.
The script caches baseline outputs, so multiple candidate blocks are much
cheaper than running separate commands.

Fast smoke scan with one prompt per category:

Dry-run first to confirm candidate count and router activation counts:

```bash
python scripts/run_v32_router_validation.py \
  --block-glob 'experiments/outputs/blocks_v18/*r16.pt' \
  --block-glob 'experiments/outputs/blocks_v21/*.pt' \
  --block-glob 'experiments/outputs/blocks_v24/*.pt' \
  --benchmark-set core \
  --routers unrestricted blacklist_only allow_math \
  --scales 0.85 1.0 \
  --max-prompts-per-category 1 \
  --dry-run
```

Then run the fast smoke scan:

```bash
python scripts/run_v32_router_validation.py \
  --block-glob 'experiments/outputs/blocks_v18/*r16.pt' \
  --block-glob 'experiments/outputs/blocks_v21/*.pt' \
  --block-glob 'experiments/outputs/blocks_v24/*.pt' \
  --benchmark-set core \
  --routers unrestricted blacklist_only allow_math \
  --scales 0.85 1.0 \
  --device mps \
  --dtype float16 \
  --max-tokens 64 \
  --max-prompts-per-category 1 \
  --output-path experiments/reports/v32_core_candidate_smoke.json \
  --resume \
  --tag v32_core_candidate_smoke
```

Summarize the smoke result:

```bash
python scripts/summarize_v32_results.py \
  experiments/reports/v32_core_candidate_smoke.json \
  --limit 20 \
  --write-report experiments/reports/bitdpm_v32_smoke_summary.md
```

Full core-45 candidate scan:

```bash
python scripts/run_v32_router_validation.py \
  --block-glob 'experiments/outputs/blocks_v18/*r16.pt' \
  --block-glob 'experiments/outputs/blocks_v21/*.pt' \
  --block-glob 'experiments/outputs/blocks_v24/*.pt' \
  --benchmark-set core \
  --routers unrestricted blacklist_only allow_math \
  --scales 0.85 1.0 \
  --device mps \
  --dtype float16 \
  --max-tokens 64 \
  --output-path experiments/reports/v32_core_candidate_scan.json \
  --resume \
  --tag v32_core_candidate_scan
```

Expanded scan if the first scan does not recover v31:

```bash
python scripts/run_v32_router_validation.py \
  --block-glob 'experiments/outputs/blocks_v09_repair_l22_l24_down_rank16/*.pt' \
  --block-glob 'experiments/outputs/blocks_v11_unique_repair_l22_l24_down_rank16/*.pt' \
  --block-glob 'experiments/outputs/blocks_v18/*r16.pt' \
  --block-glob 'experiments/outputs/blocks_v21/*.pt' \
  --block-glob 'experiments/outputs/blocks_v24/*.pt' \
  --benchmark-set core \
  --routers unrestricted blacklist_only allow_math \
  --scales 0.85 1.0 \
  --device mps \
  --dtype float16 \
  --max-tokens 64 \
  --output-path experiments/reports/v32_core_expanded_candidate_scan.json \
  --resume \
  --tag v32_core_expanded_candidate_scan
```

Candidate match criterion:

- `blacklist_only@0.85` or `allow_math@0.85`
- baseline near `0.822`
- routed near `0.956`
- fixes `6`
- breaks `0`

If no saved candidate matches, v31 probably used an unsaved in-memory block from
the v28-v31 development run. In that case, rerun the v28/v30 training path and
save the block before v32 validation.

After any full scan, summarize zero-break candidates first:

```bash
python scripts/summarize_v32_results.py \
  experiments/reports/v32_core_candidate_scan.json \
  --only-zero-breaks \
  --min-net 1 \
  --limit 20 \
  --write-report experiments/reports/bitdpm_v32_core_candidate_summary.md
```

Select the best core block automatically:

```bash
python scripts/select_v32_best_block.py \
  experiments/reports/v32_core_candidate_scan.json \
  --benchmark core \
  --min-net 1 \
  --max-breaks 0 \
  --prefer-router allow_math \
  --env-out experiments/reports/v32_best_block.env \
  --md-out experiments/reports/v32_best_block.md
```

Then load the selected block settings:

```bash
source experiments/reports/v32_best_block.env
```

## 2. Validate on v08 100

```bash
source experiments/reports/v32_best_block.env
python scripts/run_v32_router_validation.py \
  --block-path "$V31_BLOCK" \
  --benchmark-set v08 \
  --routers unrestricted blacklist_only allow_math math_only \
  --scales "$V32_BEST_SCALE" \
  --device mps \
  --dtype float16 \
  --max-tokens 64 \
  --output-path experiments/reports/v32_v08_safety_router.json \
  --resume \
  --tag v32_v08_safety_router
```

Success criterion: positive net with low breaks. If `blacklist_only` or
`allow_math` loses the gain, the v31 router is overfit to core-45.

## 3. Validate on v15 120

```bash
source experiments/reports/v32_best_block.env
python scripts/run_v32_router_validation.py \
  --block-path "$V31_BLOCK" \
  --benchmark-set v15 \
  --routers unrestricted blacklist_only allow_math math_only \
  --scales "$V32_BEST_SCALE" \
  --device mps \
  --dtype float16 \
  --max-tokens 64 \
  --output-path experiments/reports/v32_v15_safety_router.json \
  --resume \
  --tag v32_v15_safety_router
```

Success criterion: router precision remains high. Do not require full oracle
coverage; the key question is whether safety routing preserves positive net.

## 4. Optional Full Output Capture

For paper analysis, rerun the best setting with outputs saved:

```bash
source experiments/reports/v32_best_block.env
python scripts/run_v32_router_validation.py \
  --block-path "$V31_BLOCK" \
  --benchmark-set v08 \
  --routers blacklist_only allow_math \
  --scales "$V32_BEST_SCALE" \
  --device mps \
  --dtype float16 \
  --max-tokens 64 \
  --save-outputs \
  --output-path experiments/reports/v32_v08_best_with_outputs.json \
  --resume \
  --tag v32_v08_best_with_outputs
```

## Interpretation Gate

After runs complete, compare:

- `baseline`
- `routed`
- `fixes`
- `breaks`
- `net`
- `active`
- `disabled`

The v32 result is strong only if the safety router keeps breaks low on larger
benchmarks. Core-45 reproduction is necessary but not sufficient for a
high-level claim.

Decision rules:

- **Core reproduction:** `core` reaches routed >= 0.95 with fixes >= 6 and breaks = 0.
- **Transfer evidence:** `v08` or `v15` has positive net with low breaks.
- **Strong v32:** at least one larger benchmark has zero-break positive net.
- **Overfit router:** core reproduces but v08/v15 lose net or introduce many breaks.
- **Next step if overfit:** validation-mined safety router, not stronger blocks.

Generate a combined report after v08/v15 runs:

```bash
python scripts/summarize_v32_results.py \
  experiments/reports/v32_core_candidate_scan.json \
  experiments/reports/v32_v08_safety_router.json \
  experiments/reports/v32_v15_safety_router.json \
  --limit 30 \
  --write-report experiments/reports/bitdpm_v32_result_summary.md
```

Generate the next-step decision:

```bash
python scripts/decide_v32_next.py \
  experiments/reports/v32_core_candidate_scan.json \
  experiments/reports/v32_v08_safety_router.json \
  experiments/reports/v32_v15_safety_router.json \
  --md-out experiments/reports/bitdpm_next_decision.md
```

## 5. Mine v33 Safety Router Rules

If v32 shows that a block has fixes but also breaks, mine candidate safety rules
from the per-sample result file:

```bash
python scripts/mine_v33_safety_router.py \
  experiments/reports/v32_core_candidate_scan.json \
  experiments/reports/v32_v08_safety_router.json \
  experiments/reports/v32_v15_safety_router.json \
  --only-positive-net \
  --include-conjunctions \
  --json-out experiments/reports/v33_safety_router_mining.json \
  --md-out experiments/reports/v33_safety_router_mining.md
```

Use the v33 mining report to design the next router. Prefer:

- zero-break allow rules with nonzero fixes
- deny rules that isolate observed breaks
- simple features that can be validated on v08/v15

Do not treat mined rules as final evidence until they are validated in a fresh
held-out run.

## 6. Fresh-Validate a Mined Feature Router

Replace the feature names below with rules selected from
`experiments/reports/v33_safety_router_mining.md`.

Example conservative feature router:

```bash
source experiments/reports/v32_best_block.env
python scripts/run_v32_router_validation.py \
  --block-path "$V31_BLOCK" \
  --benchmark-set v08 \
  --routers feature_rule \
  --allow-feature 'cat_math' \
  --deny-feature 'is_chinese_text' \
  --deny-feature 'has_constant_risk' \
  --deny-feature 'has_biology_risk' \
  --scales "$V32_BEST_SCALE" \
  --device mps \
  --dtype float16 \
  --max-tokens 64 \
  --output-path experiments/reports/v33_feature_router_v08.json \
  --resume \
  --tag v33_feature_router_v08
```

Then validate the same rule on v15:

```bash
source experiments/reports/v32_best_block.env
python scripts/run_v32_router_validation.py \
  --block-path "$V31_BLOCK" \
  --benchmark-set v15 \
  --routers feature_rule \
  --allow-feature 'cat_math' \
  --deny-feature 'is_chinese_text' \
  --deny-feature 'has_constant_risk' \
  --deny-feature 'has_biology_risk' \
  --scales "$V32_BEST_SCALE" \
  --device mps \
  --dtype float16 \
  --max-tokens 64 \
  --output-path experiments/reports/v33_feature_router_v15.json \
  --resume \
  --tag v33_feature_router_v15
```

Summarize the fresh validation:

```bash
python scripts/summarize_v32_results.py \
  experiments/reports/v33_feature_router_v08.json \
  experiments/reports/v33_feature_router_v15.json \
  --limit 20 \
  --write-report experiments/reports/bitdpm_v33_feature_router_summary.md
```

A mined router becomes usable evidence only if this fresh validation preserves
positive net with low or zero breaks.

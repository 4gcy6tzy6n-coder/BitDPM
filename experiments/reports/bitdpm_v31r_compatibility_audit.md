# BitDPM v31-R: Block-Backbone Compatibility Audit

Date: 2026-06-16

## Purpose

This audit checks whether the recorded v31 result can be attributed to the claimed
Qwen2.5-1.5B backbone and the currently saved repair block artifacts.

The trigger was a runtime shape mismatch when replaying v31-style validation on
Qwen2.5-1.5B:

```text
mat1: 7 x 8960
mat2: 4864 x 16
```

This indicates that the tested block expects a `4864` input dimension, while the
Qwen2.5-1.5B down projection path provides `8960`.

## Block Inventory Result

Scanned block artifacts: 145

Compatibility summary:

| Matched family | Count |
|---|---:|
| Qwen2.5-0.5B down_proj | 132 |
| Qwen2.5-0.5B attention | 8 |
| Qwen2.5-0.5B up/gate | 5 |
| Qwen2.5-1.5B-compatible | 0 |

Conclusion: the currently saved block inventory does not contain a
Qwen2.5-1.5B-compatible down_proj block.

Primary inventory files:

- `experiments/reports/block_manifest.json`
- `experiments/reports/block_manifest.md`

## 1.5B Replay Result

Attempted replay:

- Backbone: `Qwen/Qwen2.5-1.5B-Instruct`
- Router: `allow_math`
- Scale: `0.85`
- Benchmark: `core`
- Candidate blocks: `blocks_v17`, `blocks_v18/*r16`, `blocks_v21`, `blocks_v24`

Result:

- Baseline cache completed for 45 samples.
- Replay failed on the first injected block due to shape mismatch.

Conclusion: v31 cannot currently be treated as a verified 1.5B result.

## 0.5B Recovery Replay

Attempted replay:

- Backbone: `Qwen/Qwen2.5-0.5B-Instruct`
- Router: `allow_math`
- Scale: `0.85`
- Benchmark: `core`
- Candidate blocks: 31 saved 0.5B-compatible candidates from v17/v18/v21/v24

Result summary:

| Metric | Value |
|---|---:|
| Completed candidate runs | 31 |
| Baseline score | 0.778 |
| Positive-net candidates | 0 |
| Zero-break candidates | 0 |
| Best routed score | 0.733 |
| Best fixes / breaks / net | 1 / 3 / -2 |

Best candidate:

| Field | Value |
|---|---|
| Block | `experiments/outputs/blocks_v24/v24_percent_l23_down_proj_r16_ep1.pt` |
| Baseline -> routed | 0.778 -> 0.733 |
| Fixes / breaks / net | 1 / 3 / -2 |
| Active | 20 / 45 |

The 0.5B replay does not reproduce the recorded v31 pattern
`baseline ~= 0.822`, `routed ~= 0.956`, `fixes=6`, `breaks=0`.

Primary recovery files:

- `experiments/reports/v31r_recover_0p5b_core_allow_math085.baseline.json`
- `experiments/reports/v31r_recover_0p5b_core_allow_math085.json`
- `experiments/reports/bitdpm_v31r_0p5b_recovery_summary.md`

## Current Interpretation

The saved block artifacts strongly indicate that the available block pool is
0.5B-dimensional, not 1.5B-dimensional. However, replaying the saved 0.5B
candidate pool under the recorded v31-style `allow_math@0.85` setting does not
recover the v31 result.

Therefore, the v31 strong result should remain frozen until its exact block file,
router implementation, scale, benchmark split, decoding parameters, and evaluator
version are recovered.

## Conclusion

Current status:

1. No saved 1.5B-compatible block was found.
2. The attempted 1.5B replay is invalid because block dimensions do not match.
3. The attempted 0.5B replay with the saved candidate pool does not reproduce v31.
4. The recorded v31 result cannot be used as a main result until provenance is
   recovered or the experiment is rerun from a fully logged configuration.

Recommended next action:

Recover v31 provenance before running larger v32 migration:

- Find the exact v31 result JSON/report.
- Extract exact `block_path`, `block_sha256`, `model`, `router`, `scale`,
  `benchmark`, `decoding`, and evaluator settings.
- If no exact provenance exists, mark v31 as unreproducible and rerun the
  intended 1.5B path by training a fresh 1.5B-compatible block.

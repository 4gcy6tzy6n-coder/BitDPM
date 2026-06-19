# BitDPM v31 Provenance Audit

## Inputs

- v31 result: `experiments/reports/v31_router_20260610_144251.json`
- block manifest: `experiments/reports/block_manifest.json`
- 0.5B recovery replay: `experiments/reports/v31r_recover_0p5b_core_allow_math085.json`

## v31 Historical Record

| Router | Scale | Baseline | Routed | Fixes | Breaks | Net | Active | Disabled |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| allow_math | 0.85 | 0.822 | 0.956 | 6 | 0 | 6 | 20 | 25 |

Missing provenance fields: `model, block_path, block_sha256, benchmark_set, deterministic, max_tokens`

## Block Inventory Compatibility

| Family | Count |
|---|---:|
| Qwen2.5-0.5B attention | 8 |
| Qwen2.5-0.5B down_proj | 132 |
| Qwen2.5-0.5B up/gate | 5 |

## 0.5B Recovery Replay

- Completed runs: 31
- Positive-net candidates: 0
- Zero-break candidates: 0
- Best block: `experiments/outputs/blocks_v24/v24_percent_l23_down_proj_r16_ep1.pt`
- Best score: 0.778 -> 0.733; fixes/breaks/net = 1/3/-2

## Verdict

Status: **UNRECOVERED**

The v31 `fixes=6, breaks=0` result remains a historical record, not a current
main result. The saved result lacks exact block/backbone provenance, the block
inventory contains 0 Qwen2.5-1.5B-compatible artifacts, and the
saved 0.5B candidate replay did not reproduce the v31 pattern.

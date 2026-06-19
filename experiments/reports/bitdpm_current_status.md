# BitDPM Current Status (2026-06-09)

## Project Stats
- **69** Python files, **14,497** lines of code
- **13** block pools with **108+** trained parameter blocks
- Spans **v0.1 → v22** over 3 days of development

---

## Experiment Summary

| Version | Focus | Key Result | Verdict |
|---------|-------|-----------|---------|
| v0.1-3 | Routing prototype | Gating was no-op | ❌ invalid |
| v4 | Gating fix | Block control works, Always-All crashes | ✅ foundation |
| v5 | Matched protocol | Sampling vs deterministic差异 | ✅ methodology |
| v6-9 | Block training | Error-type > domain-type blocks | ✅ block design |
| v10-11 | Unique-utility admission | oracle 0.890, coverage 6/100 | ✅ admission principle |
| v12-13 | Conservative router | safety-filter + incompatibility matrix | ✅ router design |
| v14 | 300-sample validation | oracle 0.903, coverage 19/300 | ✅ scale validation |
| v15 | Router validation | allow-core-no-log, 0 breaks | ✅ safest router |
| **v16** | **Connection functions** | **norm_clip = hard_add, no difference** | **❌ NOT bottleneck** |
| **v17** | **Preservation loss** | **breaks=34/45, net=-34** | **❌ FAILED** |
| **v18** | **Large-data + scale** | **5/6 directions net≥0 at scale 0.05-0.15** | **✅ ROUTE WORKS** |
| v19-20 | Pool integration | **First deterministic fix: percent net=+1** | **✅ MILESTONE** |
| **v21** | **Multi-layer (4 layers)** | **net=-35, complete collapse** | **❌ Multi-layer fails** |

---

## Key Findings

### ✅ Validated
1. **BlockDeviceManager** — eliminated CPU→MPS parameter transfer in forward path
2. **Deterministic block repair** — `percent` block achieves fixes=1, breaks=0 under `do_sample=False`
3. **Block safety** — all v18 blocks net ≥ -1 (vs old arithmetic_power_log with 11 breaks)
4. **Always-All improvement** — v18 blocks: 0.489-0.722 (vs old 0.000)
5. **Scale calibration** — safe zone: 0.03-0.15; scale=1.0 catastrophic
6. **Mixed-data training** — 50% general text + repair data substantially reduces breaks

### ❌ Rejected Paths
1. Connection function is NOT the bottleneck (v16)
2. Small-data preservation loss CANNOT guarantee safety (v17)
3. Multi-layer simultaneous activation COLLAPSES (v21)

### 🔴 Current Bottlenecks
1. **Single block max deterministic net = +1** — rank-16 capacity ceiling reached
2. **Multi-layer composition collapses** — net=-35 when 4 layers active
3. **Power_log direction still broken** — all scales net < 0
4. **R64 untested** — may break the net=+1 ceiling

---

## Block Pool Inventory

| Pool | Blocks | Description |
|------|--------|-------------|
| `blocks/` | 8 | Original category blocks (ranks=8, layer 23) |
| `blocks_v08_*` | 30 | Rank 8/16 error-type blocks (layers 21-24) |
| `blocks_v09_*` | 15 | Targeted repair blocks (rank 16) |
| `blocks_v11_*` | 15 | Unique-utility repair blocks (rank 16) |
| `blocks_v17/` | 1 | Preservation-loss experiment (rank 16) |
| `blocks_v18/` | 12 | Rank 8+16, 5 directions × 2 ranks, best current pool |
| `blocks_v21/` | 13 | 12 checkpoints + final, percent, rank 16, 1500 samples |

---

## Current Best Evidence

### Deterministic (do_sample=False)

| Block | Scale | Fixes | Breaks | Net |
|-------|-------|-------|--------|-----|
| v21_percent (ep6-12) | 0.10-0.15 | **1** | **0** | **+1** |
| v18_commonsense_choice | 0.15 | 0 | 1 | -1 |
| v18_distance_geometry | 0.05 | 0 | 0 | 0 |
| v18_percent | 0.15 | 0 | 1 | -1 |
| v18_factual_constants | 0.05 | 0 | 0 | 0 |
| v18_integer_ops | 0.05 | 0 | 0 | 0 |
| **Always-All (5 v18 blocks)** | — | — | — | **0.500** |

### Sampling (temperature=0.1)

| Pool | Baseline | Oracle | Coverage | Always-All |
|------|---------|--------|----------|-----------|
| v10 admitted | 0.830 | 0.890 | 6/100 | 0.000 |
| v15 router (allow-core) | 0.840 | 0.857 | 5/300 | — |

---

## Scripts Available (69 Python files)

### Training
- `train_all_blocks.py` — Original category block training
- `train_v07_blocks.py` — Error-type block training
- `train_v12_utility_router.py` — Router training from utility data
- `train_v18_blocks.py` — Large-data block training (5 directions)
- `train_v21_blocks.py` — Large-scale deterministic block training

### Evaluation
- `run_v04_experiments.py` — Gating-corrected experiment runner (605 lines)
- `run_v05_router_calibration.py` — Oracle/router calibration (547 lines)
- `run_v10_registry_eval.py` — Registry-based evaluation
- `run_v16_connection_experiment.py` — Connection function comparison
- `run_v19_eval.py` — Pool integration evaluation

### Analysis
- `analyze_v08_block_safety.py` — Block safety analysis
- `analyze_v10_admission.py` — Unique-utility admission analysis
- `analyze_v12_rule_router.py` — Rule-router analysis
- `crossval_v12_utility_router.py` — Cross-validation for utility router

---

## Next Priority

**Break the net=+1 ceiling with rank-64 single-layer block.**
- Single layer (23), down_proj
- Rank 64 (4× capacity)
- Same training data (1500 percent prompts)
- Scale scan 0.03-0.30 with deterministic evaluation

# BitDPM v23 Milestone Report

**From Capacity Scaling to Data-Limited Sparse Correction**

Date: 2026-06-09
Project: 69 Python files, 14,497 lines, 13 block pools, 108+ trained blocks
Span: v0.1 → v23 over 4 days

---

## 1. Executive Summary

BitDPM validates that **runtime-selective parameter composition can produce deterministic sparse corrections** in a frozen 0.5B LLM. Over 23 versions, the project has:

- ✅ Established the core mechanism: decoupled parameter blocks with break-aware admission
- ✅ Achieved first deterministic fix (`percent`, `do_sample=False`, fixes=1, breaks=0)
- ✅ Demonstrated block safety through mixed-data training and low-scale calibration
- ❌ Rejected connection functions, preservation loss, and multi-layer composition as viable paths
- ❌ **New finding**: Rank scaling (rank64) fails under template-generated data — the bottleneck is **data quality, not parameter capacity**

---

## 2. Version History

### Phase 1: Foundation (v0.1–v9)

| Version | Focus | Result | Status |
|---------|-------|--------|--------|
| v0.1–0.3 | Routing prototype | Gating was no-op; all routing claims invalid | ❌ Invalid |
| v4 | Gating fix | Block activation truly controllable | ✅ Foundation |
| v5 | Matched generation protocol | Sampling vs deterministic gap identified | ✅ Methodology |
| v6 | Block training infrastructure | Error-type training pipeline | ✅ Tooling |
| v7 | Error-type + scale calibration | Error-type > domain-type blocks | ✅ Block design |
| v8 | Expanded benchmark (100 samples) + Rank16 | Hybrid scale improves oracle; Always-All collapses to 0.000 | ✅ Evidence |
| v9 | Targeted repair blocks | Narrow blocks fix few, break many | ❌ Safety failure |

### Phase 2: Mechanism (v10–v15)

| Version | Focus | Result | Status |
|---------|-------|--------|--------|
| v10 | Unique-utility admission | **Oracle 0.890, coverage 6/100, Always-All 0.000** | ✅ Admission principle |
| v11 | Repair mining + unique-utility expansion | Coverage 6→7/100, v11_stats_number_theory admitted | ✅ Incremental |
| v12 | Conservative utility router | Full-report router 0.880, strict CV 0.830 (0 gain) | ✅ Router prototype |
| v13 | Safety cards + incompatibility matrix | Block admission safety framework | ✅ Tooling |
| v14 | 300-sample validation | **Oracle 0.903, coverage 19/300** | ✅ Scale validation |
| v15 | Router validation | **allow-core-no-log router: 0 breaks** | ✅ Safest router |

### Phase 3: Bottleneck Search (v16–v23)

| Version | Focus | Result | Status |
|---------|-------|--------|--------|
| **v16** | **Connection functions** | **norm_clip = hard_add: no oracle gain** | ❌ **NOT bottleneck** |
| **v17** | **Preservation loss** | **breaks=34, net=-34: complete failure** | ❌ **REJECTED** |
| **v18** | **Large-data + scale calibration** | **5/6 directions net≥0 at scale 0.05–0.15** | ✅ **ROUTE WORKS** |
| v19 | Pool integration (r8 blocks) | Always-All 0.600 (vs old 0.000), but coverage low | ✅ Safety improved |
| **v20** | **Deterministic evaluation** | **percent net=+1, breaks=0, first deterministic fix** | 🏆 **MILESTONE** |
| **v21** | **Multi-layer (4 layers)** | **net=-35: complete collapse** | ❌ **REJECTED** |
| v22 | Multi-layer r8 evaluation | Same collapse pattern confirmed | ❌ Consistent |
| **v23** | **Rank64 single-layer** | **net=-3 (scale=0.03) to -35: overfitting** | ❌ **Capacity NOT bottleneck** |

---

## 3. Validated Mechanisms

### 3.1 Deterministic Sparse Correction ✅

**First evidence that BitDPM blocks can change greedy decoding output without breaking baseline-correct samples.**

| Block | Scale | Fixes | Breaks | Net | Epoch |
|-------|-------|-------|--------|-----|-------|
| v21_percent_l23_down_proj_r16 | 0.10 | 1 | 0 | +1 | ep6 |
| v21_percent_l23_down_proj_r16 | 0.15 | 1 | 0 | +1 | ep7 |
| v21_percent_l23_down_proj_r16 | 0.15 | 1 | 0 | +1 | ep12 (final) |

The fix is **reproducible across epochs and scales**, confirming it is not a sampling artifact.

### 3.2 Block Safety via Mixed-Data Training ✅

**50% general text + 50% repair data substantially reduces destructive interference.**

| Metric | Old v10 blocks | New v18/v20 blocks |
|--------|---------------|-------------------|
| Worst single-block break count | 11 (arithmetic_power_log) | 1 (commonsense_choice) |
| Always-All | 0.000 | 0.489–0.722 |
| Net range | -11 to +1 | -1 to +1 |

### 3.3 Scale Calibration ✅

**Block safety is primarily governed by activation scale, not architecture.**

```
scale=1.00:  catastrophic (30-37 breaks)
scale=0.50:  moderately destructive (10-17 breaks)  
scale=0.15:  safe zone (net≥0)
scale=0.05:  conservative safe zone (net≥0)
scale=0.03:  near-zero effect (net≈0)
```

Safe zone: **0.03–0.15**. Production blocks should always be scale-calibrated.

### 3.4 Device-Aware Scheduling ✅

**BlockDeviceManager eliminates CPU→MPS parameter transfer from forward path.**

- Routing overhead: **<0.02ms** (<0.001% of inference time)
- Blocks preloaded to compute device: zero device transfer during generation

### 3.5 Unique-Utility Admission ✅

**Blocks should be admitted by unique per-sample correction coverage, not by label or aggregate score.**

- v10 pool: `arithmetic_power_log` admitted for 1 unique fix despite 11 breaks
- v11 pool: `v11_stats_number_theory` admitted for 1 unique fix
- Mixed-data blocks show that safety and utility can coexist with proper training

---

## 4. Rejected Hypotheses

### 4.1 Connection Functions Are the Bottleneck ❌

**Tested in v16.** Norm-clipped connection vs hard-add:

| Connection | Baseline | Oracle | Coverage |
|-----------|---------|--------|----------|
| hard_add | 0.820 | 0.844 | 2/45 |
| norm_clip_0.3 | 0.860 | 0.844 | 0/45 |
| norm_clip_0.5 | 0.820 | 0.844 | 2/45 |

**Conclusion**: Connection choice does not materially change oracle coverage. Bottleneck is elsewhere.

### 4.2 Preservation Loss on Small Data Works ❌

**Tested in v17.** 10 repair + 35 preserve samples, rank16, KL(p_base||p_block) loss:

| Metric | Value |
|--------|-------|
| Fixes | 0 |
| Breaks | 34 |
| Net | -34 |
| Block score | 0.067 (vs baseline 0.800) |

**Conclusion**: Small-data KL preservation is catastrophic. Safety must come from data scale + break-aware admission, not loss regularization.

### 4.3 Multi-Layer Simultaneous Activation Works ❌

**Tested in v21–v22.** 4 layers (20–23) of percent down_proj blocks:

| Config | Scale | Fixes | Breaks | Net |
|--------|-------|-------|--------|-----|
| Single layer (23) | 0.10 | 1 | 0 | +1 |
| 4 layers (20-23) | 0.10 | 0 | 35 | -35 |

**Conclusion**: Even though each single layer is safe, combined activation produces destructive interference. Cross-layer composition collapses.

### 4.4 Higher Rank = Stronger Repair ❌

**Tested in v23.** Single layer (23) down_proj, same data, rank comparison:

| Rank | Params | Scale | Fixes | Breaks | Net |
|------|--------|-------|-------|--------|-----|
| 16 | 92K | 0.10 | **1** | **0** | **+1** |
| 64 | 368K | 0.03 | 1 | 4 | -3 |
| 64 | 368K | 0.05 | 0 | 18 | -18 |

**Conclusion**: Rank64 overfits the template-generated training data. The bottleneck is data quality and diversity, not parameter capacity.

---

## 5. Updated Bottleneck Analysis

### Previous bottleneck ranking (v20):

```
1. Sampling variance > block utility
2. Block capacity insufficient (net max = +1)
3. Multi-layer composition fails
```

### Current bottleneck ranking (v23):

```
1. 🟢 Training data quality & diversity ← NEW
2. 🟡 Block utility too sparse (data-limited, not capacity-limited) ← UPDATED
3. 🟡 Single-block deterministic net ceiling (+1)
4. 🔴 Always-All still below baseline (0.489 vs 0.778)
5. 🔴 Multi-layer composition collapses
```

### Key insight:

**Rank scaling alone is harmful under low-diversity template data. The next bottleneck is not parameter capacity but correction-data quality and diversity.**

Template-generated data (even at 1500 samples) cannot support higher-capacity blocks because:
1. Limited pattern diversity: same templates recycled with different fill values
2. No genuine reasoning structure: fill-in-the-blank rather than reasoning chains
3. No hard negatives: training data doesn't include near-miss cases
4. Distribution mismatch: template prompts don't match real model error distribution

---

## 6. Current Best Deterministic Evidence

| Setting | Baseline | Best Block | Scale | Fixes | Breaks | Net | Always-All |
|---------|----------|-----------|-------|-------|--------|-----|------------|
| do_sample=False | 0.778 | percent r16 | 0.10–0.15 | 1 | 0 | **+1** | 0.489 |
| temperature=0.1 | 0.830 | v10 pool | — | 6/100 | — | **oracle 0.890** | 0.000 |

---

## 7. Next-Stage Data Roadmap

### v24: Real-Data Sparse Correction Training

**Objective**: Replace template-generated data with real instruction/reasoning/hard-negative data to break the net=+1 ceiling.

**Three parallel data tracks:**

| Track | Source | Purpose |
|-------|--------|---------|
| A: Real instruction | Alpaca/Dolly-style QA | General preservation + diverse repair context |
| B: Reasoning / CoT | GSM8K/MathQA-style | Math symbol manipulation patterns |
| C: Hard negative mining | Baseline error collection | Target the real model failure distribution |

**Recommended training mix:**
- 50% real general instruction (Track A)
- 30% target repair data (Track B + C)
- 20% hard negatives / near-miss (Track C)

**Configuration (starting point):**
- Rank: 16 (not 64 — capacity is not the bottleneck)
- Layer: 23, module: down_proj
- Direction: percent (highest priority, already proven)
- Scale scan: 0.03, 0.05, 0.10, 0.15, 0.20
- Evaluation: deterministic (do_sample=False)

**Success criteria:**

| Level | Target |
|-------|--------|
| Minimum | net ≥ +2, breaks ≤ 1 (one direction) |
| Clear | net ≥ +3 (percent), net ≥ +2 (2nd direction) |
| Paper-level | Deterministic pool beats baseline, router catches fixes |

### Not recommended for v24:
- Rank32/64 (data must improve first)
- Multi-layer composition
- Connection function tuning
- Preservation loss
- Increasing template data volume (risk: scale template errors)

---

## 8. Figures of Merit

| Metric | v10 best | v15 best | v20 best | v23 status |
|--------|----------|----------|----------|------------|
| Oracle (100 samples) | 0.890 | — | — | 0.890 (frozen) |
| Coverage (100 samples) | 6/100 | — | — | 6/100 |
| Oracle (300 samples) | — | 0.903 | — | 0.903 (frozen) |
| Coverage (300 samples) | — | 19/300 | — | 19/300 |
| Safest router strict CV | — | 0.857 (0 brk) | — | 0.857 (frozen) |
| Always-All (old blocks) | 0.000 | 0.000 | 0.000 | 0.000 |
| Always-All (v18 blocks) | — | — | 0.489 | 0.489 |
| Deterministic best block | ✗ | ✗ | percent +1 | **+1** |
| Deterministic Always-All | ✗ | ✗ | 0.489 | 0.489 |
| Rank64 deterministic net | — | — | — | **-3 to -35** ❌ |

---

## 9. Current Claims

### Valid claim:
> BitDPM demonstrates that runtime-selective parameter composition can produce deterministic sparse corrections in a frozen LLM. The first deterministic fix achieves net=+1 with zero breaks under greedy decoding. Mixed-data training and low-scale calibration substantially improve block safety. However, capacity scaling alone (rank64) fails under template-generated data, establishing that the current bottleneck is data quality and diversity rather than parameter capacity.

### Do not claim:
> BitDPM provides broad model improvement or reliable multi-block composition.

---

## 10. Artifacts

| Pool | Location | Blocks | Best Use |
|------|----------|--------|----------|
| v10 admitted | configs/bitdpm_v10_admitted_pool.json | 6 | Oracle/router baseline |
| v11 admitted | configs/bitdpm_v11_admitted_pool.json | 7 | Expanded oracle pool |
| v18 blocks | experiments/outputs/blocks_v18/ | 12 | Safe single-block candidates |
| v21 percent | experiments/outputs/blocks_v21/ | 13 | Deterministic fix evidence |
| v23 rank64 | (just run, not saved) | 1 | Failed experiment |

---

*BitDPM v23 Milestone Report — 2026-06-09*

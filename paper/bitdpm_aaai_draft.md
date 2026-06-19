# BitDPM: Runtime-Selective Sparse Parameter Correction for Efficient LLM Adaptation

## Abstract

Large language models can often be improved on individual failures by small
parameter updates, but naively merging or activating multiple adapters can
introduce destructive interference. We study BitDPM, a runtime-selective
parameter correction framework that represents candidate repairs as independent
low-rank parameter blocks and activates only selected blocks at inference time.
Across BitDPM development we find that useful parameter-block corrections are
real but sparse, sample-specific, scale-dependent, and interference-sensitive.
On a 300-sample mixed validation benchmark, the current block pool improves the
oracle upper bound from a baseline accuracy of 0.840 to 0.903 with 19/300
non-baseline selections, while all-block activation collapses to 0.000. A
conservative zero-break router improves held-out accuracy from 0.840 to 0.857 on
the same benchmark. On a 120-sample targeted validation benchmark, the same
router family improves from 0.442 to 0.500 with seven fixes and zero breaks. The
current evidence supports BitDPM as a sparse correction mechanism rather than a
broad always-on adapter. We also report a provenance audit showing that a
previous strong v31 result is unrecovered and should not be used as current main
evidence. These results motivate selective runtime composition with strict block
admission, scale calibration, and break-controlled routing.

## 1. Introduction

Parameter-efficient adaptation methods such as LoRA-style adapters typically
optimize an always-on update. This is efficient, but it assumes that the update
is broadly helpful or at least broadly safe. In small-data and mixed-task
settings, our experiments show the opposite pattern: parameter updates often
repair rare failures while damaging other examples. This creates a central
problem for efficient adaptation: the useful unit is not only a trained adapter,
but a correction direction that should be activated only when it is likely to
repair the current sample.

BitDPM investigates this setting through independent parameter blocks. Each
block is a low-rank update targeting a specific layer/module region, and runtime
composition chooses which block, if any, participates in the forward pass. The
goal is not to activate all blocks, nor to merge adapters offline. The goal is
selective runtime correction under explicit interference control.

The main empirical conclusion is deliberately conservative. Current BitDPM
blocks do not improve most prompts by default. Instead, they create sparse but
measurable per-sample correction opportunities. The strongest broad-scale
evidence is the v14 300-sample benchmark: oracle selection improves from 0.840
to 0.903, but only 19/300 samples choose a non-baseline block. This supports a
mechanism claim, not yet a high-confidence AAAI main-result claim. A deployable
router exists with zero-break held-out gains, but its gains remain modest.

This paper draft makes three contributions:

1. We define BitDPM as runtime-selective composition of sparse parameter
   correction directions, separating block utility from router quality.
2. We show that all-block activation is a strong negative control: useful
   correction directions become destructive when activated indiscriminately.
3. We introduce a strict evidence discipline for block admission and routing:
   blocks should be admitted by unique per-sample correction coverage, and
   routers should be evaluated by fixes, breaks, net gain, and held-out
   confidence intervals.

## 2. Method

### 2.1 Parameter Blocks

BitDPM represents a correction block as a low-rank parameter update:

```text
Delta W_i = A_i B_i
```

At inference time, the effective update for a target module is:

```text
W_eff = W_main + sum_i g_i s_i Delta W_i
```

where `g_i` is a binary or scalar runtime gate and `s_i` is a scale assigned to
the block. In current experiments, blocks primarily target Qwen2.5-0.5B
down-projection modules. The block manifest records tensor shapes and SHA256
hashes so that block/backbone compatibility can be audited.

### 2.2 Runtime Selective Composition

BitDPM does not treat all blocks as an ensemble. Instead, runtime composition
has three modes:

- Baseline: activate no block.
- Fixed block: activate one candidate block for every sample.
- Routed block: activate a block only when a router predicts positive utility.

Oracle selection is used only to estimate the upper bound of block utility. It
is not a deployable method.

### 2.3 Block Admission

A block is admitted into the pool only if it adds unique per-sample correction
coverage. Aggregate fixed-block score is insufficient because a block can have
low average accuracy while still repairing a sample no existing block can
repair. Conversely, a block that repairs only already-covered samples adds risk
without increasing oracle coverage.

The current rule is:

```text
admit(block) only if unique_fixes(block | existing_pool) > 0
```

The v10/v11 line supports this rule: adding the unique-utility repair direction
improves oracle coverage, while label-driven repair admission can add
destructive risk.

### 2.4 Safety Routing

Deployable routing is evaluated by fixes, breaks, net gain, active ratio, and
held-out validation. The safest current router family is conservative
allow-core-no-log routing. It admits arithmetic-like trigger families that have
shown zero-break behavior under strict validation while excluding risky log and
open-ended factual triggers.

## 3. Experimental Setup

### 3.1 Backbones and Compatibility

Current paper-usable evidence should be treated as Qwen2.5-0.5B block-pool
evidence unless a new compatible 1.5B block is trained or recovered. A v31 audit
found that saved candidate blocks are Qwen2.5-0.5B-compatible and that the
historical v31 strong result lacks the metadata required to attribute it to a
specific block/backbone pair.

The following fields are required for future main-result blocks:

```json
{
  "model": "...",
  "block_path": "...",
  "block_sha256": "...",
  "benchmark_set": "...",
  "deterministic": "...",
  "max_tokens": "..."
}
```

### 3.2 Benchmarks

The current paper-facing evidence uses:

- v08: 100-sample continuity benchmark for block-pool evolution.
- v14: 300-sample mixed validation benchmark.
- v15: 120-sample targeted router-safety benchmark.

### 3.3 Metrics

We report:

- baseline accuracy
- best fixed-block accuracy
- oracle accuracy
- deployable router accuracy
- Always-All accuracy
- fixes / breaks / net
- non-baseline oracle coverage
- bootstrap confidence intervals

Always-All is a negative control, not a deployment mode.

## 4. Results

### 4.1 Sparse Correction Oracle

| Setting | Benchmark | N | Baseline | Oracle | Gain | Coverage | Always-All |
|---|---|---:|---:|---:|---:|---:|---:|
| v15 router validation v11 admitted | v15 | 120 | 0.442 | 0.742 | 0.300 | 36/120 | 0.000 |
| v11 merged candidates | v08 | 100 | 0.830 | 0.900 | 0.070 | 7/100 | 0.000 |
| v14 full v11 admitted | v14 | 300 | 0.840 | 0.903 | 0.063 | 19/300 | 0.000 |
| v10 admitted | v08 | 100 | 0.830 | 0.890 | 0.060 | 6/100 | 0.000 |

The v14 full result is the strongest broad-scale evidence. Oracle selection
finds a 6.3-point improvement over baseline, but coverage is only 19/300. This
supports the sparse-correction interpretation: blocks create useful repair
opportunities, but these opportunities are not broad enough to justify an
always-on claim.

### 4.2 Deployable Router Evidence

| Setting | Router | Baseline | Gain | Fixes | Breaks | Evidence Type |
|---|---:|---:|---:|---:|---:|---|
| v15 allow-core-no-log strict CV | 0.500 | 0.442 | 0.058 | 7 | 0 | held-out cross-validation |
| v14 full allow-core strict CV | 0.857 | 0.840 | 0.017 | 5 | 0 | held-out cross-validation |
| v14 full allow-core-no-log strict CV | 0.857 | 0.840 | 0.017 | 5 | 0 | held-out cross-validation |

Deployable routing is positive but modest. The key result is not a large
absolute gain; it is the existence of zero-break held-out routing after safety
filters. This separates a deployable safety claim from oracle-only utility.

### 4.3 Bootstrap Confidence Intervals

Current bootstrap estimates over v14 full:

| Metric | Mean | 95% CI |
|---|---:|---:|
| Baseline | 0.840 | [0.797, 0.880] |
| Oracle | 0.903 | [0.867, 0.937] |
| Allow-core-no-log router | 0.857 | [0.813, 0.897] |
| Router delta | 0.017 | [0.003, 0.033] |

The router delta is positive but small. A high-confidence AAAI claim needs
larger held-out validation and stronger deployable gains.

### 4.4 All-Block Interference

Always-All consistently collapses to 0.000 for high-scale admitted pools on the
paper-facing v08/v14/v15 reports. This is a central mechanism result: useful
correction directions are not mutually compatible. BitDPM should therefore be
framed as selective runtime composition, not adapter merging or parameter
accumulation.

### 4.5 v31 Provenance Audit

The historical v31 record reports:

```text
allow_math@0.85: baseline 0.822 -> routed 0.956, fixes=6, breaks=0
```

This result is frozen and unrecovered. The saved result lacks exact model,
block path, block hash, benchmark, decoding, and max-token metadata. The block
manifest contains zero Qwen2.5-1.5B-compatible artifacts, and 0.5B recovery
replay did not reproduce the v31 pattern. Therefore v31 must not be used as a
current main result.

## 5. Analysis

### 5.1 Sparse Utility Rather Than Broad Enhancement

The oracle gains show that blocks can repair selected failures. However, the low
coverage shows that the current block pool does not broadly improve model
capability. This suggests that BitDPM is best understood as a sparse repair
library rather than a universal adapter.

### 5.2 Unique Utility Is the Right Admission Criterion

Label-driven block admission can add destructive risk without improving oracle
coverage. The current evidence supports unique per-sample utility as a more
reliable admission criterion.

### 5.3 Router Safety Is as Important as Router Recall

A router that recovers more oracle fixes but introduces breaks is not adequate
for deployment. The current allow-core-no-log router deliberately sacrifices
recall to preserve zero-break held-out behavior.

### 5.4 Provenance Is Part of the Method

The v31 audit exposed a reproducibility failure: a strong result without block
identity and backbone compatibility cannot be used as main evidence. Future
BitDPM experiments must record block hashes, tensor shapes, backbone identity,
benchmark identity, decoding settings, and evaluator version.

## 6. Limitations

1. Current deployable router gains are modest under strict held-out validation.
2. The largest current broad benchmark is 300 samples; AAAI-level claims need
   1k+ held-out validation.
3. Current paper-usable block evidence is primarily 0.5B-scale. A 1.5B main
   result requires newly trained compatible blocks or recovered provenance.
4. External baselines are not yet complete. The paper needs standard LoRA,
   best fixed adapter, random router, prompt-only, and oracle upper-bound
   comparisons.
5. Always-All collapse demonstrates interference but also limits naive
   deployment. Runtime routing quality is essential.

## 7. AAAI Submission Gate

This draft is ready as a mechanism-oriented technical manuscript, but not yet
as a high-confidence AAAI main-result paper. Submission should wait until:

1. A provenance-complete main result exists.
2. A deployable router improves held-out accuracy with zero or very low breaks
   on at least two benchmarks.
3. Oracle coverage remains meaningful on 1k+ prompts.
4. External baselines are included.
5. All result tables are generated by scripts from saved artifacts.

## 8. Reproducibility

Current evidence can be rebuilt with:

```bash
python scripts/build_paper_package.py
```

The generated artifact index is:

```text
experiments/reports/bitdpm_paper_artifact_index.md
```

## 9. Recommended Claim Wording

Safe current claim:

> BitDPM is a runtime-selective sparse parameter correction framework. It shows
> that useful correction directions exist, that indiscriminate block composition
> is unsafe, and that block admission and routing must be governed by unique
> per-sample utility and break control.

Unsafe current claims:

- BitDPM has a confirmed 1.5B main result.
- The v31 `0.956` result is current reproducible evidence.
- BitDPM broadly improves most samples.
- Always-All or adapter merging is a deployment mode.


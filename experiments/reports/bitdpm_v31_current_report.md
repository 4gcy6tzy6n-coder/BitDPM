# BitDPM v31 Current Report

Date: 2026-06-16

> **Superseded by v31-R compatibility audit.** This report preserves the
> historical v31 result record, but it is no longer sufficient as a current main
> result by itself. The v31 JSON does not record the exact `block_path`,
> `block_sha256`, or model metadata. A later v31-R audit found that all currently
> saved block artifacts are Qwen2.5-0.5B-dimensional and no saved
> Qwen2.5-1.5B-compatible block exists. The saved 0.5B candidate pool also did
> not reproduce the v31 `fixes=6, breaks=0` result under `allow_math@0.85`.
> Treat the v31 result as an unrecovered historical record until exact
> provenance is found.

## Executive Summary

BitDPM had advanced beyond the earlier v10/v15/v23 summaries. The latest
historical v31 result artifacts in the worktree are:

- `experiments/reports/v30_fine_scale_20260610_135222.json`
- `experiments/reports/v31_router_20260610_144251.json`

The historical strongest recorded result is v31 router-controlled activation on
the 45-sample core benchmark:

| Router | Scale | Baseline | Block | Fixes | Breaks | Net | Active | Disabled |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| unrestricted | 0.85 | 0.822 | 0.922 | 6 | 2 | +4 | 45 | 0 |
| unrestricted | 1.00 | 0.822 | 0.900 | 6 | 3 | +3 | 45 | 0 |
| blacklist_only | 0.85 | 0.822 | 0.956 | 6 | 0 | +6 | 33 | 12 |
| blacklist_only | 1.00 | 0.822 | 0.956 | 6 | 0 | +6 | 33 | 12 |
| allow_math | 0.85 | 0.822 | 0.956 | 6 | 0 | +6 | 20 | 25 |
| allow_math | 1.00 | 0.822 | 0.933 | 6 | 1 | +5 | 20 | 25 |

This originally appeared to move the project from oracle-only sparse correction
toward safety-routed deterministic repair. After the v31-R audit, the safe claim
is narrower:

> BitDPM v31 recorded a strong safety-routed deterministic repair result:
> baseline 0.822 -> 0.956 with 6 fixes and 0 breaks on the 45-sample benchmark.
> However, the exact block artifact and backbone provenance have not been
> recovered, so the result must be revalidated before being used as a main
> result.

## What Changed Since Older Reports

Older reports remain useful as history, but they are not the final current
state:

- `bitdpm_current_status.md` stops around v22/v23.
- `bitdpm_v23_milestone.md` identifies data quality and capacity limits.
- `bitdpm_v1_technical_report.md` summarizes through v27 and still describes a
  net=+1 deterministic ceiling.
- v30/v31 supersede that ceiling on the core 45-sample benchmark.

The latest evidence shows that the bottleneck has shifted again:

1. Early bottleneck: true block gating was broken.
2. Middle bottleneck: block utility was sparse and sampling-sensitive.
3. Later bottleneck: single-block deterministic net seemed capped near +1.
4. Current v31 bottleneck: the block can fix multiple samples, but unrestricted
   activation causes breaks; safety routing is the key control surface.

## v30 Fine-Scale Result

v30 scanned high activation scales from 0.80 to 1.20. It showed that the repair
block has real strength:

- At scales 0.80/0.85: 6 fixes, 2 breaks, net +4, score 0.922.
- At scales 0.95-1.20: 7 fixes, 3 breaks, net +4, score 0.922.

The recurring fixed samples were:

- `How many continents are there?`
- `If x + 5 = 12, what is x?`
- `What is 25% of 200?`
- `How many seconds are in 2 hours?`
- `What is 2^10?`
- `If a train travels at 60 km/h for 2.5 hours, how far does it go?`

At scale >= 0.95, `Calculate 15 + 27 =` is also fixed, but the number of breaks
increases.

The recurring break-risk samples were:

- `What is the speed of light in vacuum?`
- `Which gas do plants absorb from the atmosphere?`
- `请用中文写一句问候语。`

Interpretation: v30 proves the block is strong enough to repair multiple
deterministic failures, but raw activation is unsafe.

## v31 Router Result

v31 introduced simple safety routing over the same repair block:

- `unrestricted`: activate the block for every sample.
- `blacklist_only`: disable the block for Chinese prompts plus known break-risk
  commonsense prompts.
- `allow_math`: activate only on commonsense/math prompts.

The important result is that both `blacklist_only@0.85` and `allow_math@0.85`
retain all 6 repairs while removing all breaks:

```text
baseline = 0.822
router score = 0.956
fixes = 6
breaks = 0
net = +6
```

This is qualitatively different from early router results. The gating path is
now implemented through `BlockInjector.set_active_blocks()` and
`Composer.active_block_ids`, so router decisions really change the forward pass.

## Current Mechanism Interpretation

BitDPM should now be described as:

> a runtime-selective sparse parameter repair framework with safety-gated block
> activation.

The central mechanism is not broad model improvement, adapter merging, or
all-block accumulation. The current mechanism is:

1. Train or identify a sparse repair direction.
2. Calibrate its scale high enough to fix target failures.
3. Detect where it is unsafe.
4. Activate only on samples that are likely to benefit.

In v31, the router is still simple and hand-built, but it proves the control
principle: fixes can be preserved while breaks are filtered out.

## Reproducibility Gap

The v30/v31 JSON files do not record the exact parameter-block path or training
artifact used for the run. This is the main current reproducibility risk.

Future experiment outputs must record:

- block path
- block id/type/layer/module/rank
- benchmark set
- router rule
- scale
- deterministic vs sampling settings
- active/disabled counts
- per-sample fixes and breaks

The v32 validation script is designed to enforce this.

## Next Experiment: v32

The next high-value step is not another unconstrained block search. It is
validation of the v31 safety-router result under explicit, reproducible settings.

Minimum v32 matrix:

| Benchmark | Router | Scale |
|---|---|---:|
| core 45 | unrestricted | 0.85 |
| core 45 | blacklist_only | 0.85 |
| core 45 | allow_math | 0.85 |
| v08 100 | unrestricted | 0.85 |
| v08 100 | blacklist_only | 0.85 |
| v08 100 | allow_math | 0.85 |
| v15 120 | unrestricted | 0.85 |
| v15 120 | blacklist_only | 0.85 |
| v15 120 | allow_math | 0.85 |

Success criteria:

- Core 45 should reproduce v31: score near 0.956 with 0 breaks.
- Larger benchmark should preserve positive net.
- Router precision matters more than recall; breaks must remain low.

## Current Paper-Level Claim

Historical wording, now requiring a provenance caveat:

> BitDPM has progressed from oracle sparse correction to safety-routed
> deterministic repair. On the core benchmark, an unrestricted repair block
> fixes multiple baseline failures but also introduces breaks. A simple safety
> router preserves the 6 fixes while reducing breaks to zero, improving accuracy
> from 0.822 to 0.956. This supports the view that BitDPM's key challenge is not
> merely learning repair blocks, but safely activating high-impact parameter
> directions at runtime.

Revised safe wording after v31-R:

> v31 provides a promising historical record for safety-routed deterministic
> repair, but the exact block-backbone pair is not currently reproducible from
> saved artifacts. Before treating v31 as a main result, BitDPM must recover the
> original block provenance or retrain a compatible block and rerun the v32
> validation pipeline.

Do not yet claim:

- broad model improvement across large benchmarks
- learned router superiority
- deployment-ready routing
- all-block composition

Those require v32+ validation.
